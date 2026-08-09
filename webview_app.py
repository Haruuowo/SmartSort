import os
import sys
import webview
from smartsort.server import bind_and_run_server, get_base_dir, open_in_explorer, delete_to_recycle_bin

class DesktopAPI:
    def browse_folder(self):
        try:
            if webview.windows and len(webview.windows) > 0:
                res = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
                if res and len(res) > 0:
                    return res[0]
        except Exception as e:
            print(f"PyWebView browse error: {e}")
        return ""

    def open_location(self, path):
        return open_in_explorer(path)

    def delete_item(self, path):
        return delete_to_recycle_bin(path)

def run_app():
    actual_port = bind_and_run_server(7860)
    url = f"http://127.0.0.1:{actual_port}"
    print(f"SmartSort Engine loading UI from {url}")

    api = DesktopAPI()

    webview.create_window(
        title="SmartSort",
        url=url,
        width=1040,
        height=680,
        resizable=True,
        min_size=(840, 540),
        background_color="#09090b",
        js_api=api
    )

    webview.start()

if __name__ == "__main__":
    run_app()
