from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

def header(text: str):
    console.print(f"\n[bold cyan]── {text}[/bold cyan]")

def success(text: str):
    console.print(f"[bold green]✓[/bold green] {text}")

def warn(text: str):
    console.print(f"[bold yellow]⚠[/bold yellow]  {text}")

def error(text: str):
    console.print(f"[bold red]✗[/bold red] {text}")

def info(text: str):
    console.print(f"[dim]→[/dim] {text}")

def blank():
    console.print()

def banner():
    console.print(Panel.fit(
        "[bold cyan]TrainCLI[/bold cyan]  [dim]v0.1.0 — train ML models from a single command[/dim]",
        border_style="cyan"
    ))

def model_picker_table(models: list, recommended_key: str):
    """Render the interactive model picker table."""
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("Model", style="bold")
    table.add_column("Description")
    table.add_column("", width=15)

    for i, m in enumerate(models, 1):
        tag = "[bold green]✓ recommended[/bold green]" if m["key"] == recommended_key else ""
        table.add_row(str(i), m["label"], m["description"], tag)

    console.print(table)

def profile_table(profile: dict):
    """Render dataset profile summary."""
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("Key", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Rows", f"{profile['rows']:,}")
    table.add_row("Columns", str(profile['cols']))
    table.add_row("Target", profile['target'])
    table.add_row("Null cells", f"{profile['null_count']:,} ({profile['null_pct']:.1f}%)")

    console.print(table)

def metrics_table(metrics: dict, problem_type: str):
    """Render evaluation metrics."""
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Value", style="bold cyan")

    for k, v in metrics.items():
        table.add_row(k, str(v))

    console.print(table)