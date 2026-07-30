import os
import sys
import json
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
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
    """Opens native Windows folder picker dialog."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder = filedialog.askdirectory(title="Select Target Folder to Organize")
    root.destroy()
    return folder or ""

class SmartSortRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress HTTP server output logs

    def _set_headers(self, content_type="application/json", status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

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
        length = int(self.headers.get('Content-Length', 0))
        raw_body = self.rfile.read(length) if length > 0 else b'{}'
        try:
            payload = json.loads(raw_body.decode('utf-8'))
        except Exception:
            payload = {}

        endpoint = self.path.rstrip('/')

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
                'top_files': top_files_fmt
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
            files = [f for f in os.listdir(target_path) if os.path.isfile(os.path.join(target_path, f))]
            
            moved, duplicates, errors = 0, 0, 0
            for item in files:
                res = classifier.process_file(os.path.join(target_path, item), dry_run=dry_run)
                st = res.get('status')
                if st == 'moved':
                    moved += 1
                elif st == 'duplicate':
                    duplicates += 1
                else:
                    errors += 1

            self._set_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'moved': moved,
                'duplicates': duplicates,
                'errors': errors,
                'total': len(files)
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

        else:
            self.send_error(404, "Endpoint not found")

def start_server(port=7860):
    init_db()
    server = HTTPServer(('127.0.0.1', port), SmartSortRequestHandler)
    print(f"SmartSort Web App running at http://127.0.0.1:{port}")
    webbrowser.open(f"http://127.0.0.1:{port}")
    server.serve_forever()

if __name__ == '__main__':
    start_server()
