import os
import sys
import time
import ctypes
from ctypes import wintypes
from collections import defaultdict
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor

from .rules import RuleEngine

SKIP_FOLDERS = {
    '$recycle.bin', 'system volume information', 'msocache', '$winre_backup', 'recovery'
}

MAX_SCAN_DEPTH = 6
MAX_FILES_PER_FOLDER = 100_000
MAX_FOLDER_TIME_SECONDS = 4.0

def format_size(b: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"

def generate_bar(pct: float, width: int = 12) -> str:
    """Generates ASCII visual bar e.g. [████████░░]"""
    filled = int(round(width * (pct / 100.0)))
    filled = min(max(filled, 0), width)
    return "█" * filled + "░" * (width - filled)

# ── Win32 C-API Definitions for C-Speed File System Scanning ──
IS_WINDOWS = sys.platform == 'win32'

if IS_WINDOWS:
    kernel32 = ctypes.windll.kernel32
    INVALID_HANDLE_VALUE = -1
    FILE_ATTRIBUTE_DIRECTORY = 0x10
    FILE_ATTRIBUTE_REPARSE_POINT = 0x400  # Reparse Points / Junctions / Symlinks

    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

    class WIN32_FIND_DATAW(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", FILETIME),
            ("ftLastAccessTime", FILETIME),
            ("ftLastWriteTime", FILETIME),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("dwReserved0", wintypes.DWORD),
            ("dwReserved1", wintypes.DWORD),
            ("cFileName", wintypes.WCHAR * 260),
            ("cAlternateFileName", wintypes.WCHAR * 14),
        ]

    FindFirstFileW = kernel32.FindFirstFileW
    FindFirstFileW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(WIN32_FIND_DATAW)]
    FindFirstFileW.restype = wintypes.HANDLE

    FindNextFileW = kernel32.FindNextFileW
    FindNextFileW.argtypes = [wintypes.HANDLE, ctypes.POINTER(WIN32_FIND_DATAW)]
    FindNextFileW.restype = wintypes.BOOL

    FindClose = kernel32.FindClose
    FindClose.argtypes = [wintypes.HANDLE]
    FindClose.restype = wintypes.BOOL

def _win32_full_subfolder_stats(folder_path: str) -> Dict:
    """
    Ultra-fast C-level Win32 directory scanner with depth control and safety timeout.
    Calculates total size and file count for any folder (Steam games, Apps, Documents).
    """
    folder_name = os.path.basename(folder_path)
    if folder_name.lower() in SKIP_FOLDERS:
        return {'name': folder_name, 'count': 0, 'size': 0, 'formatted_size': "0.0 B"}

    total_size = 0
    total_files = 0
    start_time = time.time()

    if IS_WINDOWS:
        stack = [(folder_path, 0)]
        find_data = WIN32_FIND_DATAW()

        while stack:
            # Safety timeout check per subfolder
            if time.time() - start_time > MAX_FOLDER_TIME_SECONDS or total_files >= MAX_FILES_PER_FOLDER:
                break

            current_path, depth = stack.pop()
            search_path = os.path.join(current_path, "*")

            handle = FindFirstFileW(search_path, ctypes.byref(find_data))
            if handle == INVALID_HANDLE_VALUE:
                continue

            try:
                while True:
                    name = find_data.cFileName
                    attrs = find_data.dwFileAttributes

                    if name not in ('.', '..'):
                        is_dir = bool(attrs & FILE_ATTRIBUTE_DIRECTORY)
                        is_junction = bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)

                        if not is_junction:
                            if is_dir:
                                if depth < MAX_SCAN_DEPTH and name.lower() not in SKIP_FOLDERS:
                                    stack.append((os.path.join(current_path, name), depth + 1))
                            else:
                                size = (find_data.nFileSizeHigh << 32) + find_data.nFileSizeLow
                                total_size += size
                                total_files += 1

                    if not FindNextFileW(handle, ctypes.byref(find_data)):
                        break
            finally:
                FindClose(handle)
    else:
        # Fallback for non-Windows
        try:
            for root, dirs, files in os.walk(folder_path):
                if time.time() - start_time > MAX_FOLDER_TIME_SECONDS:
                    break
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        total_size += os.path.getsize(fp)
                        total_files += 1
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            pass

    return {
        'name': folder_name,
        'count': total_files,
        'size': total_size,
        'formatted_size': format_size(total_size)
    }

def analyze_subfolders(target_dir: str) -> List[Dict]:
    """Parallelized C-speed subfolder size analysis with safety guards."""
    subfolder_paths = []
    if not os.path.exists(target_dir):
        return []

    try:
        with os.scandir(target_dir) as entries:
            for entry in entries:
                try:
                    if entry.is_dir(follow_symlinks=False) and entry.name.lower() not in SKIP_FOLDERS:
                        subfolder_paths.append(entry.path)
                except (PermissionError, OSError):
                    continue
    except (PermissionError, OSError):
        return []

    if not subfolder_paths:
        return []

    # Limit max workers to 12 threads
    max_workers = min(12, len(subfolder_paths))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        subfolders = list(executor.map(_win32_full_subfolder_stats, subfolder_paths))

    subfolders.sort(key=lambda x: x['size'], reverse=True)
    return subfolders

def analyze_directory(target_dir: str, config_path: str) -> Dict:
    """
    Ultra-fast directory storage breakdown analyzer using Win32 C-API and multithreading.
    """
    summary = {
        'total_files': 0,
        'total_size': 0,
        'categories': defaultdict(lambda: {'count': 0, 'size': 0}),
        'extensions': defaultdict(lambda: {'count': 0, 'size': 0}),
        'top_files': [],
        'subfolders': []
    }

    if not os.path.exists(target_dir):
        return summary

    rule_engine = RuleEngine(config_path)
    all_files_info = []

    try:
        with os.scandir(target_dir) as entries:
            for entry in entries:
                try:
                    if entry.is_file(follow_symlinks=False):
                        size = entry.stat(follow_symlinks=False).st_size
                        filename = entry.name
                        _, ext = os.path.splitext(filename)
                        ext = ext.lower() or 'no-ext'

                        info = {'name': filename.lower(), 'extension': ext}
                        rule_name, dest_template = rule_engine.evaluate(info)
                        category = dest_template.split('/')[0] if dest_template else "Unsorted"

                        summary['total_files'] += 1
                        summary['total_size'] += size

                        summary['categories'][category]['count'] += 1
                        summary['categories'][category]['size'] += size

                        summary['extensions'][ext]['count'] += 1
                        summary['extensions'][ext]['size'] += size

                        all_files_info.append({
                            'name': filename,
                            'size': size,
                            'category': category,
                            'ext': ext
                        })
                except (PermissionError, OSError):
                    continue
    except (PermissionError, OSError):
        return summary

    # Sort largest 10 files
    all_files_info.sort(key=lambda x: x['size'], reverse=True)
    summary['top_files'] = all_files_info[:10]

    # Concurrent subfolder analysis
    summary['subfolders'] = analyze_subfolders(target_dir)

    return summary
