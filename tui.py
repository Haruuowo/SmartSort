import os
import sys
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Input, Static, DataTable, Label
from textual.reactive import reactive

from smartsort.classifier import FileClassifier

def get_config_path() -> str:
    """Resolve config path, works both in dev and when bundled as exe."""
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'config', 'rules.yaml')

class SmartSortTUI(App):
    """A Textual app to organize files."""

    TITLE = "SmartSort"
    SUB_TITLE = "Terminal File Organizer"
    
    CSS = """
    Screen {
        background: $surface-darken-1;
    }
    
    #main-container {
        padding: 1 2;
    }

    #controls {
        height: auto;
        padding-bottom: 1;
        margin-bottom: 1;
        border-bottom: solid $primary;
    }
    
    #folder-input {
        width: 1fr;
    }
    
    #buttons {
        width: auto;
        margin-left: 1;
    }
    
    #buttons Button {
        margin-left: 1;
    }

    #results-area {
        height: 1fr;
    }
    
    #stats-panel {
        width: 30;
        border-right: solid $primary;
        padding-right: 1;
        margin-right: 1;
    }
    
    .stat-label {
        margin-top: 1;
        text-align: center;
        color: $text-muted;
    }
    
    #stats-title {
        text-style: bold;
        color: $primary;
    }
    
    .stat-value {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #results-table {
        height: 1fr;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with Horizontal(id="controls"):
                yield Input(placeholder="Enter folder path (e.g. C:\\Users\\...)", id="folder-input")
                with Horizontal(id="buttons"):
                    yield Button("Dry Run", id="btn-dry-run", variant="primary")
                    yield Button("Execute", id="btn-execute", variant="error")
                    
            with Horizontal(id="results-area"):
                with Vertical(id="stats-panel"):
                    yield Label("STATISTICS", id="stats-title", classes="stat-label")
                    yield Label("Moved Files", classes="stat-label")
                    yield Label("0", id="stat-moved", classes="stat-value")
                    yield Label("Duplicates", classes="stat-label")
                    yield Label("0", id="stat-duplicate", classes="stat-value")
                    yield Label("Errors", classes="stat-label")
                    yield Label("0", id="stat-error", classes="stat-value")
                    yield Label("Total", classes="stat-label")
                    yield Label("0", id="stat-total", classes="stat-value")
                
                yield DataTable(id="results-table")
                
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("File", "Status", "Destination / Reason")
        self.query_one("#folder-input").value = "C:\\"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        folder_path = self.query_one("#folder-input").value
        if not os.path.isdir(folder_path):
            self.notify("Invalid folder path!", severity="error")
            return
            
        dry_run = event.button.id == "btn-dry-run"
        self.run_sort(folder_path, dry_run)

    def run_sort(self, folder: str, dry_run: bool) -> None:
        table = self.query_one(DataTable)
        table.clear()
        
        config_path = get_config_path()
        if not os.path.exists(config_path):
            self.notify(f"Config not found: {config_path}", severity="error")
            return
        
        file_classifier = FileClassifier(folder, config_path)
        
        try:
            files_to_process = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        except Exception as e:
            self.notify(f"Error reading directory: {e}", severity="error")
            return

        moved, duplicate, errors = 0, 0, 0
        
        for item in files_to_process:
            item_path = os.path.join(folder, item)
            result = file_classifier.process_file(item_path, dry_run=dry_run)
            status = result.get('status')
            
            dest_or_reason = ""
            if status == 'moved':
                moved += 1
                dest_or_reason = result.get('destination', '')
            elif status == 'duplicate':
                duplicate += 1
                dest_or_reason = result.get('reason', '')
            else:
                errors += 1
                dest_or_reason = result.get('reason', 'Unknown')
                
            table.add_row(item, status.capitalize() if status else "Error", dest_or_reason)
            
        self.query_one("#stat-moved").update(str(moved))
        self.query_one("#stat-duplicate").update(str(duplicate))
        self.query_one("#stat-error").update(str(errors))
        self.query_one("#stat-total").update(str(len(files_to_process)))
        
        mode = "Simulated" if dry_run else "Executed"
        self.notify(f"{mode} organization of {len(files_to_process)} files.", severity="information")

if __name__ == "__main__":
    app = SmartSortTUI()
    app.run()
