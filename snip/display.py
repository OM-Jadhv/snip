from pathlib import Path

import pyperclip
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.style import Style
from rich.syntax import Syntax
from rich.table import Table

console = Console()


def show_snip(snip: dict) -> None:
    console.print(f"\n[bold]{snip['title']}[/bold]")
    console.print(f"ID: {snip['id']}  |  Type: {snip['type']}  |  "
                  f"Language: {snip.get('language', '') or '-'}  |  "
                  f"Tags: {snip.get('tags', '') or '-'}")
    console.print(f"Created: {snip['created_at']}  |  Updated: {snip['updated_at']}")
    if snip.get("source"):
        console.print(f"Source: {snip['source']}")

    lang = snip.get("language") or "text"
    syntax = Syntax(snip["body"], lang, theme="monokai", line_numbers=True)
    console.print(syntax)

    try:
        pyperclip.copy(snip["body"])
        console.print("[dim]Copied to clipboard[/dim]")
    except Exception:
        pass

    source_file = snip.get("source_file")
    source_line = snip.get("source_line")
    if source_file:
        spath = Path(source_file)
        if spath.exists():
            lines = spath.read_text().splitlines()
            start = max(0, (source_line or 1) - 4)
            end = min(len(lines), (source_line or 1) + 3)
            context_lines = []
            for i in range(start, end):
                lineno = i + 1
                marker = "▸" if source_line and lineno == source_line else " "
                style = "bold yellow" if source_line and lineno == source_line else ""
                context_lines.append(f"  {marker} {lineno:4d}  {lines[i]}")
            text = "\n".join(context_lines)
            console.print(Panel(text, title=f"Source: {source_file}:{source_line}" if source_line else f"Source: {source_file}", border_style="blue"))
        else:
            console.print(Panel(f"[red]Source file no longer found at[/red]\n[dim]{source_file}[/dim]", border_style="red", title="Source Missing"))


def show_table(snips: list[dict]) -> None:
    if not snips:
        console.print("[yellow]No snips found[/yellow]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Title")
    table.add_column("Lang", width=8)
    table.add_column("Tags", width=20)
    table.add_column("Created")

    for s in snips:
        table.add_row(
            str(s["id"]),
            s["title"],
            s.get("language", "") or "-",
            s.get("tags", "") or "-",
            s["created_at"],
        )
    console.print(table)


def show_confirmation(message: str) -> bool:
    return Confirm.ask(message, default=False)


def show_related(related: list[dict]) -> None:
    if not related:
        return
    table = Table(title="Related Snips", title_style="dim", show_header=True, header_style="dim")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Title", style="dim")
    table.add_column("Lang", style="dim", width=8)
    table.add_column("Tags", style="dim", width=20)
    for s in related:
        table.add_row(
            str(s["id"]),
            s["title"],
            s.get("language", "") or "-",
            s.get("tags", "") or "-",
        )
    console.print(table)
