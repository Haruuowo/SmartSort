import os
import webview
from smartsort.server import bind_and_run_server, get_user_data_dir, open_in_explorer, delete_to_recycle_bin


class DesktopAPI:
    def browse_folder(self):
        try:
            if webview.windows:
                res = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
                if res:
                    return os.path.normpath(res[0])
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

    webview.create_window(
        title="SmartSort",
        url=url,
        width=1180,
        height=760,
        resizable=True,
        min_size=(960, 620),
        background_color="#0c0c10",
        text_select=False,
        js_api=DesktopAPI()
    )

    # private_mode=False lets the UI remember the last folder between launches
    webview.start(private_mode=False, storage_path=os.path.join(get_user_data_dir(), 'webview'))


if __name__ == "__main__":
    run_app()
