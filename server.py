from smartsort.server import (
    bind_and_run_server,
    start_server,
    get_base_dir,
    get_config_path,
    select_folder_native,
    open_in_explorer,
    delete_to_recycle_bin,
    SmartSortRequestHandler
)

if __name__ == '__main__':
    start_server(open_browser=True)
