import os
import sys
import webview
from server import start_server, get_base_dir
import threading

def run_app():
    # Start local backend API server on port 7860 in daemon thread
    server_thread = threading.Thread(target=start_server, args=(7860, False), daemon=True)
    server_thread.start()

    # Create PyWebView standalone desktop application window
    window = webview.create_window(
        title="SmartSort Engine",
        url="http://127.0.0.1:7860",
        width=1040,
        height=680,
        resizable=True,
        min_size=(840, 540),
        background_color="#0d080e"
    )

    webview.start()

if __name__ == "__main__":
    run_app()
