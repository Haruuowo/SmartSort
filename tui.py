import os
import sys
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Input, Static, RichLog
from textual.binding import Binding

from smartsort.classifier import FileClassifier
from smartsort.history import get_history, undo_move, init_db

BANNER = r"""[green]
  ____                       _   ____             _   
 / ___| _ __ ___   __ _ _ __| |_/ ___|  ___  _ __| |_ 
 \___ \| '_ ` _ \ / _` | '__| __\___ \ / _ \| '__| __|
  ___) | | | | | | (_| | |  | |_ ___) | (_) | |  | |_ 
 |____/|_| |_| |_|\__,_|_|   \__|____/ \___/|_|   \__|
[/green]
[dim green] v1.0 — Terminal File Organizer[/dim green]
[dim] Type [bold green]help[/bold green] to see available commands.[/dim]
"""

HELP_TEXT = """[bold green]━━━ Available Commands ━━━[/bold green]

  [bold cyan]sort[/bold cyan] [dim]<path>[/dim]         Organize all files in a directory
  [bold cyan]dry-run[/bold cyan] [dim]<path>[/dim]      Simulate sorting without moving files
  [bold cyan]ls[/bold cyan] [dim]<path>[/dim]            List files in a directory
  [bold cyan]history[/bold cyan]              Show recent move operations
  [bold cyan]undo[/bold cyan]                 Undo the last move operation
  [bold cyan]undo all[/bold cyan]             Undo all recorded moves
  [bold cyan]clear[/bold cyan]                Clear the terminal output
  [bold cyan]pwd[/bold cyan]                  Print current working directory
  [bold cyan]help[/bold cyan]                 Show this help message
  [bold cyan]exit[/bold cyan]                 Quit SmartSort
"""

def get_config_path() -> str:
    """Resolve config path for both dev and bundled exe."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'config', 'rules.yaml')


class SmartSortTUI(App):
    """A Linux-style terminal file organizer."""

    TITLE = "SmartSort"
    
    CSS = """
    Screen {
        background: #0a0a0a;
    }

    #terminal-output {
        background: #0a0a0a;
        color: #33ff33;
        border: none;
        scrollbar-color: #33ff33;
        scrollbar-color-hover: #66ff66;
        scrollbar-color-active: #99ff99;
        height: 1fr;
        padding: 0 1;
    }

    #prompt-line {
        height: auto;
        max-height: 3;
        background: #0a0a0a;
        padding: 0 1;
    }
    
    #prompt-label {
        color: #33ff33;
        text-style: bold;
        width: auto;
        padding: 0;
        margin: 0;
        background: #0a0a0a;
    }
    
    #command-input {
        background: #0a0a0a;
        color: #33ff33;
        border: none;
        width: 1fr;
        padding: 0;
        margin: 0;
    }

    #command-input:focus {
        border: none;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: #1a3a1a;
        color: #33ff33;
        padding: 0 1;
    }

    Header {
        background: #1a3a1a;
        color: #33ff33;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_screen", "Clear", show=True),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(id="terminal-output", highlight=True, markup=True, wrap=True)
        with Container(id="prompt-line"):
            yield Static("[bold green]smartsort>[/bold green] ", id="prompt-label")
            yield Input(placeholder="type a command...", id="command-input")
        yield Static("SmartSort v1.0 | Ctrl+C: Quit | Ctrl+L: Clear", id="status-bar")

    def on_mount(self) -> None:
        log = self.query_one("#terminal-output", RichLog)
        log.write(BANNER)
        self.query_one("#command-input").focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "command-input":
            return
        
        command = event.value.strip()
        event.input.value = ""
        
        if not command:
            return
        
        log = self.query_one("#terminal-output", RichLog)
        log.write(f"[bold green]smartsort>[/bold green] {command}")
        
        self.process_command(command, log)
    
    def process_command(self, raw: str, log: RichLog) -> None:
        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""
        
        if cmd == "help":
            log.write(HELP_TEXT)
        elif cmd == "exit" or cmd == "quit":
            self.exit()
        elif cmd == "clear":
            self.action_clear_screen()
        elif cmd == "pwd":
            log.write(f"[green]{os.getcwd()}[/green]")
        elif cmd == "ls":
            self.cmd_ls(arg, log)
        elif cmd == "sort":
            self.cmd_sort(arg, log, dry_run=False)
        elif cmd == "dry-run":
            self.cmd_sort(arg, log, dry_run=True)
        elif cmd == "history":
            self.cmd_history(log)
        elif cmd == "undo":
            self.cmd_undo(arg, log)
        else:
            log.write(f"[bold red]error:[/bold red] unknown command '{cmd}'. Type [bold green]help[/bold green] for usage.")
    
    def action_clear_screen(self) -> None:
        log = self.query_one("#terminal-output", RichLog)
        log.clear()
        log.write("[dim green]Terminal cleared.[/dim green]")

    # ── ls ──────────────────────────────────────────────
    def cmd_ls(self, path: str, log: RichLog) -> None:
        target = path if path else os.getcwd()
        if not os.path.isdir(target):
            log.write(f"[bold red]error:[/bold red] '{target}' is not a valid directory.")
            return
        
        try:
            entries = sorted(os.listdir(target))
            dirs = [e for e in entries if os.path.isdir(os.path.join(target, e))]
            files = [e for e in entries if os.path.isfile(os.path.join(target, e))]
            
            log.write(f"[dim]── contents of {target} ──[/dim]")
            for d in dirs:
                log.write(f"  [bold blue]{d}/[/bold blue]")
            for f in files:
                size = os.path.getsize(os.path.join(target, f))
                size_str = self._format_size(size)
                log.write(f"  [green]{f}[/green]  [dim]{size_str}[/dim]")
            log.write(f"[dim]{len(dirs)} dirs, {len(files)} files[/dim]")
        except PermissionError:
            log.write(f"[bold red]error:[/bold red] permission denied for '{target}'.")

    # ── sort / dry-run ──────────────────────────────────
    def cmd_sort(self, path: str, log: RichLog, dry_run: bool) -> None:
        if not path:
            log.write(f"[bold red]error:[/bold red] missing path. Usage: [cyan]{'dry-run' if dry_run else 'sort'} <path>[/cyan]")
            return
        
        if not os.path.isdir(path):
            log.write(f"[bold red]error:[/bold red] '{path}' is not a valid directory.")
            return
        
        config_path = get_config_path()
        if not os.path.exists(config_path):
            log.write(f"[bold red]error:[/bold red] config not found at {config_path}")
            return
        
        mode_label = "[bold yellow]DRY RUN[/bold yellow]" if dry_run else "[bold red]EXECUTING[/bold red]"
        log.write(f"\n{mode_label} [dim]sorting files in[/dim] [cyan]{path}[/cyan]")
        log.write("[dim]─────────────────────────────────────────[/dim]")
        
        classifier = FileClassifier(path, config_path)
        
        try:
            files_to_process = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        except Exception as e:
            log.write(f"[bold red]error:[/bold red] {e}")
            return
        
        if not files_to_process:
            log.write("[yellow]No files found in directory.[/yellow]")
            return
        
        moved, duplicate, errors = 0, 0, 0
        
        for item in files_to_process:
            item_path = os.path.join(path, item)
            result = classifier.process_file(item_path, dry_run=dry_run)
            status = result.get('status')
            
            if status == 'moved':
                moved += 1
                dest = result.get('destination', '')
                icon = "→" 
                log.write(f"  [green]{icon}[/green] {item} [dim]→[/dim] [cyan]{dest}[/cyan]")
            elif status == 'duplicate':
                duplicate += 1
                reason = result.get('reason', '')
                log.write(f"  [yellow]⊘[/yellow] {item} [dim]({reason})[/dim]")
            else:
                errors += 1
                reason = result.get('reason', 'Unknown')
                log.write(f"  [red]✗[/red] {item} [dim]({reason})[/dim]")
        
        log.write("[dim]─────────────────────────────────────────[/dim]")
        log.write(
            f"[bold green]moved:[/bold green] {moved}  "
            f"[bold yellow]skipped:[/bold yellow] {duplicate}  "
            f"[bold red]errors:[/bold red] {errors}  "
            f"[dim]total: {len(files_to_process)}[/dim]"
        )

    # ── history ─────────────────────────────────────────
    def cmd_history(self, log: RichLog) -> None:
        try:
            records = get_history(20)
        except Exception as e:
            log.write(f"[bold red]error:[/bold red] {e}")
            return
        
        if not records:
            log.write("[yellow]No move history found.[/yellow]")
            return
        
        log.write("\n[bold green]━━━ Recent Move History ━━━[/bold green]")
        for record in records:
            move_id, orig, dest, rule, ts = record
            log.write(
                f"  [dim]#{move_id}[/dim] [green]{os.path.basename(orig)}[/green] "
                f"[dim]→[/dim] [cyan]{dest}[/cyan] "
                f"[dim]({rule}, {ts})[/dim]"
            )
        log.write(f"[dim]{len(records)} record(s) shown.[/dim]")

    # ── undo ────────────────────────────────────────────
    def cmd_undo(self, arg: str, log: RichLog) -> None:
        try:
            if arg.lower() == "all":
                records = get_history(None)
            else:
                records = get_history(1)
        except Exception as e:
            log.write(f"[bold red]error:[/bold red] {e}")
            return
        
        if not records:
            log.write("[yellow]Nothing to undo.[/yellow]")
            return
        
        undone_count = 0
        for record in records:
            success = undo_move(record)
            name = os.path.basename(record[1])
            if success:
                undone_count += 1
                log.write(f"  [green]↩[/green] Restored [cyan]{name}[/cyan]")
            else:
                log.write(f"  [red]✗[/red] Failed to restore [cyan]{name}[/cyan]")
        
        log.write(f"[dim]Undone {undone_count}/{len(records)} operation(s).[/dim]")
    
    # ── utils ───────────────────────────────────────────
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"


if __name__ == "__main__":
    app = SmartSortTUI()
    app.run()
