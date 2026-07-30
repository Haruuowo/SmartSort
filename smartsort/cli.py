import typer
import os
from rich.console import Console
from rich.table import Table
from rich.progress import track

from .watcher import watch_directory
from .classifier import FileClassifier
from .rules import RuleEngine
from .history import get_history, undo_move

app = typer.Typer(help="SmartSort: A rule-based file organizer with undo support.")
console = Console()

def get_default_config() -> str:
    # Assuming config/rules.yaml relative to current working dir or package
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(pkg_dir, 'config', 'rules.yaml')

@app.command()
def watch(
    folder: str = typer.Argument(..., help="The folder to watch and organize."),
    config: str = typer.Option(None, help="Path to rules.yaml"),
):
    """Watches a folder and organizes files as they are added."""
    config_path = config if config else get_default_config()
    watch_directory(folder, config_path, dry_run=False)

@app.command()
def sort(
    folder: str = typer.Argument(..., help="The folder to organize."),
    config: str = typer.Option(None, help="Path to rules.yaml"),
):
    """Organizes all existing files in a folder based on rules."""
    config_path = config if config else get_default_config()
    classifier = FileClassifier(folder, config_path)
    
    if not os.path.exists(folder):
        console.print(f"[red]Error: Directory '{folder}' does not exist.[/red]")
        raise typer.Exit(1)
        
    console.print(f"[*] Sorting existing files in [bold]{folder}[/bold]...")
    
    moved_count = 0
    duplicate_count = 0
    error_count = 0
    
    files_to_process = [item for item in os.listdir(folder) if os.path.isfile(os.path.join(folder, item))]
    
    for item in track(files_to_process, description="Organizing files..."):
        item_path = os.path.join(folder, item)
        result = classifier.process_file(item_path, dry_run=False)
        status = result.get('status')
        if status == 'moved':
            moved_count += 1
        elif status == 'duplicate':
            duplicate_count += 1
        else:
            error_count += 1

    table = Table(title="Sort Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")
    table.add_row("Moved Files", str(moved_count))
    table.add_row("Duplicates Skipped", str(duplicate_count))
    table.add_row("Errors", str(error_count))
    console.print(table)


@app.command("dry-run")
def dry_run(
    folder: str = typer.Argument(..., help="The folder to test sorting on."),
    config: str = typer.Option(None, help="Path to rules.yaml"),
):
    """Previews sorting operations without moving any files."""
    config_path = config if config else get_default_config()
    classifier = FileClassifier(folder, config_path)
    
    if not os.path.exists(folder):
        console.print(f"[red]Error: Directory '{folder}' does not exist.[/red]")
        raise typer.Exit(1)
        
    console.print(f"[*] [yellow]DRY RUN[/yellow] sorting files in [bold]{folder}[/bold]...")
    
    table = Table(title="Dry Run Plan")
    table.add_column("File", style="cyan")
    table.add_column("Action", style="green")
    table.add_column("Destination / Reason", style="magenta")
    
    files_to_process = [item for item in os.listdir(folder) if os.path.isfile(os.path.join(folder, item))]
    
    for item in track(files_to_process, description="Simulating sort..."):
        item_path = os.path.join(folder, item)
        result = classifier.process_file(item_path, dry_run=True)
        status = result.get('status')
        
        if status == 'moved':
            table.add_row(item, "Move", result.get('destination', ''))
        elif status == 'duplicate':
            table.add_row(item, "[yellow]Skip[/yellow]", f"Duplicate: {result.get('reason')}")
        else:
            table.add_row(item, "[red]Error[/red]", result.get('reason', 'Unknown'))
                
    console.print(table)

@app.command()
def undo(
    all: bool = typer.Option(False, "--all", help="Undo all history"),
    limit: int = typer.Option(1, help="Number of recent operations to undo")
):
    """Reverts recent sort operations using the history database."""
    history_limit = None if all else limit
    records = get_history(history_limit)
    
    if not records:
        console.print("[yellow]No operations available to undo.[/yellow]")
        return
        
    console.print(f"[*] Attempting to undo {len(records)} operations...")
    success_count = 0
    for record in records:
        if undo_move(record):
            success_count += 1
            console.print(f"[green]✔ Undid:[/green] {os.path.basename(record[2])} -> {record[1]}")
        else:
            console.print(f"[red]✖ Failed to undo:[/red] {record[2]}")
            
    console.print(f"[*] Successfully reverted {success_count} / {len(records)} files.")

@app.command()
def rules(
    config: str = typer.Option(None, help="Path to rules.yaml"),
):
    """Lists the currently active sorting rules."""
    config_path = config if config else get_default_config()
    engine = RuleEngine(config_path)
    
    table = Table(title=f"Active Rules (from {os.path.basename(config_path)})")
    table.add_column("Rule Name", style="cyan", no_wrap=True)
    table.add_column("Conditions", style="magenta")
    table.add_column("Destination", style="green")
    
    for r in engine.rules:
        name = r.get('name', 'Unnamed')
        dest = r.get('destination', 'Unknown')
        conds = []
        for k, v in r.get('condition', {}).items():
            conds.append(f"{k}: {v}")
        table.add_row(name, ", ".join(conds), dest)
        
    console.print(table)

if __name__ == "__main__":
    app()
