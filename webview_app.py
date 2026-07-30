import os
import sys
import webview
from server import bind_and_run_server, get_base_dir

def run_app():
    # Synchronously bind local server to an available port
    actual_port = bind_and_run_server(7860)

    html_file = os.path.join(get_base_dir(), 'web', 'index.html')
    print(f"SmartSort Engine loading UI from {html_file} with API port {actual_port}")

    # Create PyWebView standalone desktop application window
    window = webview.create_window(
        title="SmartSort Engine",
        url=html_file,
        width=1040,
        height=680,
        resizable=True,
        min_size=(840, 540),
        background_color="#0d080e"
    )

    def set_port():
        window.evaluate_js(f"window.API_PORT = {actual_port};")

    window.events.loaded += set_port

    webview.start()

if __name__ == "__main__":
    run_app()
