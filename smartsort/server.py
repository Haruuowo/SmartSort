import os
import sys
import json
import time
import uuid
import shutil
import threading
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from smartsort import __version__
from smartsort.classifier import FileClassifier
from smartsort import history
from smartsort.cleaner import remove_empty_folders
from smartsort.analyzer import analyze_directory, format_size


# ── Paths ────────────────────────────────────────────────────────────────────

def get_base_dir() -> str:
    """Folder that contains the bundled `web/` and `config/` directories."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_user_data_dir() -> str:
    root = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
    path = os.path.join(root, 'SmartSort')
    os.makedirs(path, exist_ok=True)
    return path


def get_config_path() -> str:
    """
    Rules file location. The packaged app copies its default rules to
    %LOCALAPPDATA%\\SmartSort\\rules.yaml so users can edit them (files inside
    the PyInstaller temp folder are wiped on every launch).
    """
    bundled = os.path.join(get_base_dir(), 'config', 'rules.yaml')
    if not getattr(sys, 'frozen', False):
        return bundled
    try:
        user_copy = os.path.join(get_user_data_dir(), 'rules.yaml')
        if not os.path.exists(user_copy) and os.path.exists(bundled):
            shutil.copyfile(bundled, user_copy)
        return user_copy if os.path.exists(user_copy) else bundled
    except OSError:
        return bundled


# ── Native helpers ───────────────────────────────────────────────────────────

def select_folder_native() -> str:
    """Opens a native folder picker (used only when running in a plain browser)."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder = filedialog.askdirectory(title="Choose a folder to organize")
        root.destroy()
        return os.path.normpath(folder) if folder else ""
    except Exception as e:
        print(f"Folder picker error: {e}")
        return ""


def open_in_explorer(path: str) -> bool:
    if not path or not os.path.exists(path):
        return False
    path = os.path.normpath(path)
    try:
        import subprocess
        if os.path.isfile(path):
            subprocess.Popen(['explorer.exe', '/select,', path])
        else:
            os.startfile(path)
        return True
    except Exception as e:
        print(f"Open explorer error: {e}")
        return False


def delete_to_recycle_bin(path: str) -> bool:
    if not path or not os.path.exists(path):
        return False
    path = os.path.normpath(path)
    try:
        if sys.platform == 'win32':
            import ctypes
            from ctypes import wintypes

            class SHFILEOPSTRUCTW(ctypes.Structure):
                _fields_ = [
                    ("hwnd", wintypes.HWND),
                    ("wFunc", wintypes.UINT),
                    ("pFrom", wintypes.LPCWSTR),
                    ("pTo", wintypes.LPCWSTR),
                    ("fFlags", wintypes.WORD),
                    ("fAnyOperationsAborted", wintypes.BOOL),
                    ("hNameMappings", ctypes.c_void_p),
                    ("lpszProgressTitle", wintypes.LPCWSTR)
                ]

            FO_DELETE, FOF_ALLOWUNDO, FOF_NOCONFIRMATION, FOF_SILENT, FOF_NOERRORUI = 0x3, 0x40, 0x10, 0x4, 0x400
            fileop = SHFILEOPSTRUCTW()
            fileop.wFunc = FO_DELETE
            fileop.pFrom = path + '\0\0'
            fileop.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
            return ctypes.windll.shell32.SHFileOperationW(ctypes.byref(fileop)) == 0
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)
        return True
    except Exception as e:
        print(f"Recycle bin delete error: {e}")
        return False


# ── Background jobs ──────────────────────────────────────────────────────────

class Job:
    def __init__(self, kind: str):
        self.id = uuid.uuid4().hex[:12]
        self.kind = kind
        self.status = 'running'
        self.done = 0
        self.total = 0
        self.current = ''
        self.result = None
        self.error = None
        self.cancel_event = threading.Event()
        self.started = time.time()

    def progress(self, done: int, total: int, current: str = ''):
        self.done, self.total, self.current = done, total, current

    def to_dict(self, include_result: bool = True) -> dict:
        data = {
            'id': self.id, 'kind': self.kind, 'status': self.status,
            'done': self.done, 'total': self.total, 'current': self.current,
            'elapsed': round(time.time() - self.started, 1), 'error': self.error,
        }
        if include_result and self.status != 'running':
            data['result'] = self.result
        return data


_jobs = {}
_jobs_lock = threading.Lock()
_busy_job = None  # only one file-moving job may run at a time


def _start_job(kind: str, fn, exclusive: bool):
    global _busy_job
    with _jobs_lock:
        if exclusive and _busy_job is not None and _busy_job.status == 'running':
            return None
        job = Job(kind)
        _jobs[job.id] = job
        if exclusive:
            _busy_job = job
        # keep memory bounded
        finished = [j for j in _jobs.values() if j.status != 'running']
        for old in sorted(finished, key=lambda j: j.started)[:-10]:
            _jobs.pop(old.id, None)

    def runner():
        try:
            job.result = fn(job)
            job.status = 'cancelled' if job.cancel_event.is_set() else 'done'
        except Exception as e:
            job.error = str(e)
            job.status = 'error'

    threading.Thread(target=runner, daemon=True, name=f"smartsort-{kind}").start()
    return job


def _list_root_files(target: str):
    files = []
    with os.scandir(target) as it:
        for entry in it:
            try:
                if entry.is_file(follow_symlinks=False):
                    files.append(entry.path)
            except OSError:
                continue
    files.sort(key=lambda p: os.path.basename(p).casefold())
    return files


def _organize_job(target: str, dry_run: bool):
    def run(job: Job):
        files = _list_root_files(target)
        job.progress(0, len(files))
        classifier = FileClassifier(target, get_config_path())
        batch_id = None if dry_run else history.create_batch(target)
        try:
            items = classifier.organize(files, dry_run=dry_run, batch_id=batch_id,
                                        progress=job.progress, should_cancel=job.cancel_event.is_set)
        finally:
            if batch_id is not None:
                history.finalize_batch(batch_id, classifier.created_dirs)

        counts = {'moved': 0, 'duplicate': 0, 'skipped': 0, 'error': 0}
        moved_size = 0
        for it in items:
            counts[it['status']] = counts.get(it['status'], 0) + 1
            if it['status'] in ('moved', 'duplicate'):
                moved_size += it.get('size', 0) or 0
        return {
            'dry_run': dry_run, 'target': target, 'batch_id': batch_id,
            'total': len(files), 'processed': len(items),
            'moved': counts['moved'], 'duplicates': counts['duplicate'],
            'skipped': counts['skipped'], 'errors': counts['error'],
            'moved_size': format_size(moved_size), 'items': items,
        }
    return run


def _undo_job(batch_id):
    def run(job: Job):
        return history.undo_batch(batch_id, progress=job.progress)
    return run


def _scan(target: str) -> dict:
    summary = analyze_directory(target, get_config_path())
    return {
        'success': True,
        'target': target,
        'total_files': summary['total_files'],
        'total_size': summary['total_size'],
        'formatted_size': format_size(summary['total_size']),
        'categories': {
            cat: {'count': d['count'], 'size': d['size'], 'formatted_size': format_size(d['size'])}
            for cat, d in summary['categories'].items()
        },
        'top_files': [
            {'name': f['name'], 'path': os.path.join(target, f['name']), 'size': f['size'],
             'formatted_size': format_size(f['size']), 'category': f['category']}
            for f in summary['top_files']
        ],
        'subfolders': [
            {**s, 'path': os.path.join(target, s['name'])} for s in summary.get('subfolders', [])
        ],
    }


def _rules_payload() -> dict:
    from smartsort.rules import RuleEngine
    path = get_config_path()
    engine = RuleEngine(path)
    rules = []
    for r in engine.rules:
        cond = r.get('condition', {}) or {}
        rules.append({
            'name': r.get('name', 'Unnamed rule'),
            'destination': r.get('destination', ''),
            'extensions': cond.get('extensions') or [],
            'name_contains': cond.get('name_contains') or [],
            'has_exif_date': cond.get('has_exif_date'),
        })
    return {'success': True, 'path': path, 'rules': rules}


# ── HTTP layer ───────────────────────────────────────────────────────────────

MIME = {
    '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8', '.png': 'image/png',
    '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
    '.woff2': 'font/woff2', '.json': 'application/json',
}


class SmartSortRequestHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, format, *args):
        pass  # Suppress HTTP server output logs

    def _send(self, body: bytes, content_type: str, status: int = 200, cache: bool = False):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'max-age=3600' if cache else 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data: dict, status: int = 200):
        self._send(json.dumps(data).encode('utf-8'), 'application/json', status)

    def _valid_dir(self, path: str) -> bool:
        if not path or not os.path.isdir(path):
            self._json({'success': False, 'error': 'That folder no longer exists.'}, 400)
            return False
        return True

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/job':
            job = _jobs.get(parse_qs(parsed.query).get('id', [''])[0])
            if not job:
                return self._json({'success': False, 'error': 'Unknown job'}, 404)
            return self._json({'success': True, 'job': job.to_dict()})
        if path == '/api/info':
            return self._json({'success': True, 'version': __version__, 'config': get_config_path()})

        web_dir = os.path.realpath(os.path.join(get_base_dir(), 'web'))
        rel = 'index.html' if path in ('', '/') else path.lstrip('/')
        filepath = os.path.realpath(os.path.join(web_dir, rel))
        if not filepath.startswith(web_dir) or not os.path.isfile(filepath):
            return self._send(b'Not found', 'text/plain', 404)
        ext = os.path.splitext(filepath)[1].lower()
        with open(filepath, 'rb') as f:
            self._send(f.read(), MIME.get(ext, 'application/octet-stream'),
                       cache=ext in ('.png', '.jpg', '.ico', '.woff2'))

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0) or 0)
            raw = self.rfile.read(length) if length > 0 else b'{}'
            try:
                payload = json.loads(raw.decode('utf-8') or '{}')
            except ValueError:
                payload = {}
            endpoint = urlparse(self.path).path.rstrip('/')
            target = payload.get('path', '')

            if endpoint == '/api/browse':
                return self._json({'success': True, 'path': select_folder_native()})

            if endpoint == '/api/scan':
                if self._valid_dir(target):
                    self._json(_scan(target))
                return

            if endpoint in ('/api/preview', '/api/organize'):
                if not self._valid_dir(target):
                    return
                dry_run = endpoint == '/api/preview'
                job = _start_job('preview' if dry_run else 'organize',
                                 _organize_job(os.path.abspath(target), dry_run), exclusive=not dry_run)
                if not job:
                    return self._json({'success': False, 'error': 'Another operation is still running.'}, 409)
                return self._json({'success': True, 'job': job.to_dict(False)})

            if endpoint == '/api/undo':
                batch_id = payload.get('batch_id')
                job = _start_job('undo', _undo_job(int(batch_id) if batch_id else None), exclusive=True)
                if not job:
                    return self._json({'success': False, 'error': 'Another operation is still running.'}, 409)
                return self._json({'success': True, 'job': job.to_dict(False)})

            if endpoint == '/api/job/cancel':
                job = _jobs.get(payload.get('id', ''))
                if job:
                    job.cancel_event.set()
                return self._json({'success': bool(job)})

            if endpoint == '/api/history':
                return self._json({'success': True, 'batches': history.list_batches(int(payload.get('limit', 50)))})

            if endpoint == '/api/history/batch':
                return self._json({'success': True, 'moves': history.get_batch_moves(int(payload.get('id', 0)))})

            if endpoint == '/api/rules':
                return self._json(_rules_payload())

            if endpoint == '/api/clean-empty':
                if self._valid_dir(target):
                    self._json({'success': True, 'removed': remove_empty_folders(target, dry_run=False)})
                return

            if endpoint == '/api/open-location':
                return self._json({'success': open_in_explorer(target)})

            if endpoint == '/api/delete-item':
                return self._json({'success': delete_to_recycle_bin(target)})

            self._json({'success': False, 'error': 'Endpoint not found'}, 404)
        except Exception as e:
            self._json({'success': False, 'error': str(e)}, 500)


def bind_and_run_server(port=7860):
    history.init_db()
    httpd = None
    actual_port = port
    for attempt_port in range(port, port + 20):
        try:
            httpd = ThreadingHTTPServer(('127.0.0.1', attempt_port), SmartSortRequestHandler)
            actual_port = attempt_port
            break
        except OSError:
            continue

    if not httpd:
        raise RuntimeError("Could not find an open port for SmartSort server.")

    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True, name='smartsort-http').start()
    return actual_port


def start_server(port=7860, open_browser=False):
    actual_port = bind_and_run_server(port)
    print(f"SmartSort Engine running at http://127.0.0.1:{actual_port}")
    if open_browser:
        webbrowser.open(f"http://127.0.0.1:{actual_port}")
    return actual_port


if __name__ == '__main__':
    start_server(open_browser=True)
    while True:
        time.sleep(1)
