import os
import sys
import webview
from server import start_server, get_base_dir
import threading

def run_app():
    # Start local backend API server on port 7860 in daemon thread
    server_thread = threading.Thread(target=start_server, args=(7860,), daemon=True)
    server_thread.start()

    # Create PyWebView standalone desktop application window
    window = webview.create_window(
        title="SmartSort — Modern File Organizer",
        url="http://127.0.0.1:7860",
        width=1040,
        height=680,
        resizable=True,
        min_size=(840, 540),
        background_color="#0b0f17"
    )

    webview.start()

if __name__ == "__main__":
    run_app()
