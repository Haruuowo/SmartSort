import os
import sys
import json
import time
import threading
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import tkinter as tk
from tkinter import filedialog

from smartsort.classifier import FileClassifier
from smartsort.history import get_history, undo_move, init_db
from smartsort.cleaner import remove_empty_folders
from smartsort.analyzer import analyze_directory, format_size

def get_base_dir() -> str:
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_config_path() -> str:
    return os.path.join(get_base_dir(), 'config', 'rules.yaml')

def select_folder_native() -> str:
    """Opens native Windows folder picker dialog via PowerShell subprocess or Tkinter fallback."""
    try:
        cmd = [
            "powershell", "-NoProfile", "-NonInteractive", "-Command",
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$f = New-Object System.Windows.Forms.FolderBrowserDialog; "
            "$f.Description = 'Select Target Folder to Organize'; "
            "if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Host $f.SelectedPath }"
        ]
        import subprocess
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60, creationflags=creationflags)
        out = res.stdout.strip()
        if out and os.path.exists(out):
            return out
    except Exception as e:
        print(f"PowerShell folder picker error: {e}")

    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder = filedialog.askdirectory(title="Select Target Folder to Organize")
        root.destroy()
        return folder or ""
    except Exception as e:
        print(f"Tkinter folder picker error: {e}")
        return ""

def open_in_explorer(path: str) -> bool:
    if not path or not os.path.exists(path):
        return False
    path = os.path.normpath(path)
    try:
        import subprocess
        if os.path.isfile(path):
            subprocess.run(['explorer.exe', '/select,', path])
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
            shell32 = ctypes.windll.shell32
            FO_DELETE = 0x0003
            FOF_ALLOWUNDO = 0x0040
            FOF_NOCONFIRMATION = 0x0010

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

            p_from = path + '\0\0'
            fileop = SHFILEOPSTRUCTW()
            fileop.wFunc = FO_DELETE
            fileop.pFrom = p_from
            fileop.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION
            res = shell32.SHFileOperationW(ctypes.byref(fileop))
            return res == 0
        else:
            if os.path.isfile(path):
                os.remove(path)
            else:
                import shutil
                shutil.rmtree(path)
            return True
    except Exception as e:
        print(f"Recycle bin delete error: {e}")
        return False

class SmartSortRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress HTTP server output logs

    def _set_headers(self, content_type="application/json", status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(status=204)

    def do_GET(self):
        base_dir = get_base_dir()
        web_dir = os.path.join(base_dir, 'web')
        
        path = self.path.split('?')[0]
        if path == '/':
            path = '/index.html'

        filepath = os.path.join(web_dir, path.lstrip('/'))
        if os.path.exists(filepath) and os.path.isfile(filepath):
            ext = os.path.splitext(filepath)[1].lower()
            mime = {
                '.html': 'text/html',
                '.css': 'text/css',
                '.js': 'application/javascript',
                '.png': 'image/png',
                '.svg': 'image/svg+xml',
                '.ico': 'image/x-icon'
            }.get(ext, 'text/plain')

            self._set_headers(content_type=mime)
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "File Not Found")

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(length) if length > 0 else b'{}'
            try:
                payload = json.loads(raw_body.decode('utf-8'))
            except Exception:
                payload = {}

            endpoint = self.path.split('?')[0].rstrip('/')

            if endpoint == '/api/browse':
                selected = select_folder_native()
                self._set_headers()
                self.wfile.write(json.dumps({'success': True, 'path': selected}).encode())

            elif endpoint == '/api/scan':
                target_path = payload.get('path', '')
                config_path = get_config_path()
                if not target_path or not os.path.exists(target_path):
                    self._set_headers(status=400)
                    self.wfile.write(json.dumps({'success': False, 'error': 'Invalid target path'}).encode())
                    return

                summary = analyze_directory(target_path, config_path)
                
                # Format sizes
                categories_fmt = {}
                for cat, data in summary['categories'].items():
                    categories_fmt[cat] = {
                        'count': data['count'],
                        'size': data['size'],
                        'formatted_size': format_size(data['size'])
                    }

                top_files_fmt = []
                for item in summary['top_files']:
                    top_files_fmt.append({
                        'name': item['name'],
                        'size': item['size'],
                        'formatted_size': format_size(item['size']),
                        'category': item['category']
                    })

                response_data = {
                    'success': True,
                    'total_files': summary['total_files'],
                    'total_size': summary['total_size'],
                    'formatted_size': format_size(summary['total_size']),
                    'categories': categories_fmt,
                    'top_files': top_files_fmt,
                    'subfolders': summary.get('subfolders', [])
                }

                self._set_headers()
                self.wfile.write(json.dumps(response_data).encode())

            elif endpoint == '/api/sort':
                target_path = payload.get('path', '')
                dry_run = payload.get('dry_run', False)
                config_path = get_config_path()

                if not target_path or not os.path.exists(target_path):
                    self._set_headers(status=400)
                    self.wfile.write(json.dumps({'success': False, 'error': 'Invalid target path'}).encode())
                    return

                classifier = FileClassifier(target_path, config_path)
                files = []
                try:
                    for f in os.listdir(target_path):
                        fp = os.path.join(target_path, f)
                        try:
                            if os.path.isfile(fp):
                                files.append(f)
                        except (PermissionError, OSError):
                            continue
                except (PermissionError, OSError):
                    files = []
                
                moved, duplicates, errors = 0, 0, 0
                items_log = []
                for item in files:
                    res = classifier.process_file(os.path.join(target_path, item), dry_run=dry_run)
                    st = res.get('status')
                    if st == 'moved':
                        moved += 1
                    elif st == 'duplicate':
                        duplicates += 1
                    else:
                        errors += 1
                    items_log.append(res)

                self._set_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'moved': moved,
                    'duplicates': duplicates,
                    'errors': errors,
                    'total': len(files),
                    'items': items_log
                }).encode())

            elif endpoint == '/api/clean-empty':
                target_path = payload.get('path', '')
                if not target_path or not os.path.exists(target_path):
                    self._set_headers(status=400)
                    self.wfile.write(json.dumps({'success': False, 'error': 'Invalid path'}).encode())
                    return

                removed = remove_empty_folders(target_path, dry_run=False)
                self._set_headers()
                self.wfile.write(json.dumps({'success': True, 'removed': removed}).encode())

            elif endpoint == '/api/undo':
                records = get_history(1)
                undone = []
                if records:
                    for r in records:
                        if undo_move(r):
                            undone.append(os.path.basename(r[1]))

                self._set_headers()
                self.wfile.write(json.dumps({'success': True, 'undone': undone}).encode())

            elif endpoint == '/api/history':
                records = get_history(20)
                fmt_records = []
                if records:
                    for r in records:
                        fmt_records.append({
                            'id': r[0],
                            'src': r[1],
                            'dest': r[2],
                            'timestamp': r[3]
                        })

                self._set_headers()
                self.wfile.write(json.dumps({'success': True, 'records': fmt_records}).encode())

            elif endpoint == '/api/open-location':
                target_path = payload.get('path', '')
                ok = open_in_explorer(target_path)
                self._set_headers()
                self.wfile.write(json.dumps({'success': ok}).encode())

            elif endpoint == '/api/delete-item':
                target_path = payload.get('path', '')
                ok = delete_to_recycle_bin(target_path)
                self._set_headers()
                self.wfile.write(json.dumps({'success': ok}).encode())

            else:
                self._set_headers(status=404)
                self.wfile.write(json.dumps({'success': False, 'error': 'Endpoint not found'}).encode())
        except Exception as e:
            self._set_headers(status=500)
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

def bind_and_run_server(port=7860):
    init_db()
    server_address = ('127.0.0.1', port)
    
    actual_port = port
    httpd = None
    for attempt_port in range(port, port + 20):
        try:
            server_address = ('127.0.0.1', attempt_port)
            httpd = ThreadingHTTPServer(server_address, SmartSortRequestHandler)
            actual_port = attempt_port
            break
        except OSError:
            continue

    if not httpd:
        raise RuntimeError("Could not find an open port for SmartSort server.")

    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(0.15)
    return actual_port

def start_server(port=7860, open_browser=False):
    actual_port = bind_and_run_server(port)
    print(f"SmartSort Engine running at http://127.0.0.1:{actual_port}")
    if open_browser:
        webbrowser.open(f"http://127.0.0.1:{actual_port}")
    return actual_port

if __name__ == '__main__':
    port = start_server(open_browser=True)
    import time
    while True:
        time.sleep(1)
