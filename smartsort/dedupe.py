import os
import hashlib
from difflib import SequenceMatcher
from typing import Dict, List, Optional

_CHUNK = 1024 * 1024


def get_file_hash(filepath: str, chunk_size: int = _CHUNK) -> str:
    """Calculates the SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error hashing {filepath}: {e}")
        return ""


def get_file_size(filepath: str) -> int:
    """Returns the size of the file in bytes."""
    try:
        return os.path.getsize(filepath)
    except OSError:
        return -1


def string_similarity(a: str, b: str) -> float:
    """Returns a similarity ratio between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_duplicate_in_dir(source_filepath: str, target_dir: str, similarity_threshold: float = 0.85):
    """
    Checks if a duplicate or near-duplicate of `source_filepath` exists in `target_dir`.
    Returns a tuple (is_exact_duplicate, duplicate_filepath, reason).
    Exact (hash) matches are always checked across the whole folder before
    near-duplicate names are considered.
    """
    if not os.path.isdir(target_dir):
        return False, None, ""

    source_size = get_file_size(source_filepath)
    source_name = os.path.basename(source_filepath)
    source_hash = None
    near = None

    try:
        entries = list(os.scandir(target_dir))
    except OSError:
        return False, None, ""

    for entry in entries:
        try:
            if not entry.is_file(follow_symlinks=False):
                continue
            target_size = entry.stat(follow_symlinks=False).st_size
        except OSError:
            continue

        if source_size == target_size and source_size > 0:
            if source_hash is None:
                source_hash = get_file_hash(source_filepath)
            if source_hash and get_file_hash(entry.path) == source_hash:
                return True, entry.path, "Exact hash match"

        if near is None and target_size > 0 and source_size > 0:
            size_ratio = min(source_size, target_size) / max(source_size, target_size)
            if size_ratio > 0.8:
                sim = string_similarity(source_name, entry.name)
                if sim >= similarity_threshold:
                    near = (entry.path, f"Near duplicate name (similarity {sim:.2f}) and similar size")

    if near:
        return False, near[0], near[1]
    return False, None, ""


class DuplicateIndex:
    """
    Fast exact-duplicate lookup used while organizing a folder.

    Each destination folder is listed once and indexed by file size; hashes are
    only computed when two files have the same size, and are cached. This turns
    the previous O(n²) "re-list and re-hash the destination for every file"
    behaviour into roughly O(n).
    """

    def __init__(self):
        self._dirs: Dict[str, Dict[int, List[str]]] = {}
        self._hashes: Dict[str, str] = {}

    @staticmethod
    def _key(path: str) -> str:
        return os.path.normcase(os.path.abspath(path))

    def _load(self, directory: str) -> Dict[int, List[str]]:
        key = self._key(directory)
        index = self._dirs.get(key)
        if index is None:
            index = {}
            try:
                with os.scandir(directory) as it:
                    for entry in it:
                        try:
                            if entry.is_file(follow_symlinks=False):
                                size = entry.stat(follow_symlinks=False).st_size
                                index.setdefault(size, []).append(entry.path)
                        except OSError:
                            continue
            except OSError:
                pass
            self._dirs[key] = index
        return index

    def _hash(self, path: str) -> str:
        key = self._key(path)
        h = self._hashes.get(key)
        if h is None:
            h = get_file_hash(path)
            self._hashes[key] = h
        return h

    def find(self, filepath: str, size: int, directory: str) -> Optional[str]:
        """Returns the path of an identical file already in `directory`, if any."""
        if size <= 0:
            return None
        candidates = self._load(directory).get(size)
        if not candidates:
            return None
        source_hash = self._hash(filepath)
        if not source_hash:
            return None
        for candidate in candidates:
            if self._key(candidate) != self._key(filepath) and self._hash(candidate) == source_hash:
                return candidate
        return None

    def add(self, directory: str, readable_path: str, size: int, known_hash_of: Optional[str] = None):
        """Registers a file that is (or will be) in `directory`.

        `readable_path` is where the content can currently be read from (the
        source path during a preview, the new path after a real move).
        """
        if known_hash_of:
            h = self._hashes.get(self._key(known_hash_of))
            if h:
                self._hashes[self._key(readable_path)] = h
        self._load(directory).setdefault(size, []).append(readable_path)
