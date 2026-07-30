import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console
from rich.table import Table

from .classifier import FileClassifier

console = Console()

class SortEventHandler(FileSystemEventHandler):
    def __init__(self, classifier: FileClassifier, dry_run: bool = False):
        self.classifier = classifier
        self.dry_run = dry_run
        super().__init__()

    def on_created(self, event):
        if event.is_directory:
            return
            
        filepath = event.src_path
        
        # Give the file a small delay to finish writing
        time.sleep(0.5)
        
        if os.path.exists(filepath):
            result = self.classifier.process_file(filepath, dry_run=self.dry_run)
            self._print_result(result)

    def _print_result(self, result):
        status = result.get('status')
        filename = result.get('file', 'Unknown')
        rule = result.get('rule', 'None')
        
        if status == 'moved':
            dest = result.get('destination', '')
            console.print(f"[green]✔ Moved[/green] [bold]{filename}[/bold] -> [cyan]{dest}[/cyan] (Rule: {rule})")
        elif status == 'duplicate':
            reason = result.get('reason', '')
            console.print(f"[yellow]⚠ Duplicate Skipped[/yellow] [bold]{filename}[/bold] (Reason: {reason})")
        else:
            console.print(f"[red]✖ Error[/red] [bold]{filename}[/bold]: {result.get('reason', 'Unknown')}")

def watch_directory(target_dir: str, config_path: str, dry_run: bool = False):
    """
    Watches a directory for new files and organizes them automatically.
    """
    if not os.path.exists(target_dir):
        console.print(f"[red]Error: Directory '{target_dir}' does not exist.[/red]")
        return

    classifier = FileClassifier(target_dir, config_path)
    event_handler = SortEventHandler(classifier, dry_run)
    observer = Observer()
    observer.schedule(event_handler, target_dir, recursive=False)
    
    console.print(f"[*] Watching [bold]{target_dir}[/bold] for new files...")
    if dry_run:
        console.print("[yellow][DRY RUN MODE] No files will actually be moved.[/yellow]")
        
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[*] Stopped watching.")
    observer.join()
