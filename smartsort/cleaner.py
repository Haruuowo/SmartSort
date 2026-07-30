import os

def find_empty_folders(target_dir: str):
    """
    Recursively scans target_dir for empty subdirectories.
    Returns a list of empty directory paths.
    """
    empty_dirs = []
    if not os.path.exists(target_dir):
        return empty_dirs

    # Bottom-up traversal so nested empty folders are caught
    for root, dirs, files in os.walk(target_dir, topdown=False):
        # Skip the root target_dir itself
        if os.path.abspath(root) == os.path.abspath(target_dir):
            continue

        # Ignore hidden folders (like .git, .vscode)
        folder_name = os.path.basename(root)
        if folder_name.startswith('.'):
            continue

        # Check if directory is completely empty
        try:
            items = os.listdir(root)
            if not items:
                empty_dirs.append(root)
        except PermissionError:
            continue

    return empty_dirs

def remove_empty_folders(target_dir: str, dry_run: bool = False):
    """
    Finds and removes empty subdirectories inside target_dir.
    Returns a summary list of removed directory paths.
    """
    empty_dirs = find_empty_folders(target_dir)
    removed = []

    for folder_path in empty_dirs:
        if not dry_run:
            try:
                os.rmdir(folder_path)
                removed.append(folder_path)
            except Exception as e:
                print(f"Error removing {folder_path}: {e}")
        else:
            removed.append(folder_path)

    return removed
