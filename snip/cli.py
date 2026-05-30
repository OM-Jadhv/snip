import os
import subprocess
import tempfile
from pathlib import Path

import typer

from snip.db import get_connection
from snip.display import show_confirmation, show_related, show_snip, show_table
from snip.search import find_related, hybrid_search
from snip.store import add_snip, delete_snip, get_snip, list_snips, update_snip

app = typer.Typer()


def _get_editor() -> str:
    return os.environ.get("EDITOR", "vim")


def _edit_body(initial: str = "") -> str:
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as f:
        f.write(initial)
        f.flush()
        path = f.name

    editor = _get_editor()
    subprocess.call([editor, path])

    with open(path) as f:
        content = f.read()
    os.unlink(path)
    return content


@app.command()
def add(
    title: str,
    body: str | None = typer.Option(None, "--body", "-b", help="Snippet body text"),
    lang: str | None = typer.Option(None, "--lang", "-l", help="Programming language"),
    tags: str | None = typer.Option(None, "--tags", "-t", help="Comma-separated tags"),
    type: str | None = typer.Option(None, "--type", help="'code' or 'thought'"),
    source: str | None = typer.Option(None, "--source", "-s", help="URL or project name"),
    file: str | None = typer.Option(None, "--file", "-f", help="Source file path"),
    line: int | None = typer.Option(None, "--line", "-L", help="Line number in source file"),
):
    if line is not None and file is None:
        typer.echo("Error: --line requires --file", err=True)
        raise typer.Exit(1)
    if file:
        file = str(Path(file).resolve())

    if body is None:
        body = _edit_body()

    if type is None:
        type = "code" if lang else "thought"

    snip_id = add_snip(title, body, type, language=lang, tags=tags, source=source, source_file=file, source_line=line)
    typer.echo(f"Snip {snip_id} saved.")


@app.command()
def list(
    tag: str | None = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    type: str | None = typer.Option(None, "--type", help="Filter by type (code/thought)"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max results"),
):
    snips = list_snips(tag=tag, type=type, limit=limit)
    show_table(snips)


@app.command()
def get(snip_id: int = typer.Argument(..., help="Snip ID")):
    snip = get_snip(snip_id)
    if not snip:
        typer.echo(f"Snip {snip_id} not found.", err=True)
        raise typer.Exit(1)
    show_snip(snip)
    db = get_connection()
    show_related(find_related(db, snip_id))
    db.close()


@app.command()
def find(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(5, "--limit", "-n", help="Max results"),
):
    results = hybrid_search(query, limit=limit)
    if not results:
        typer.echo("No matches found.")
        return
    show_table(results)


@app.command()
def delete(snip_id: int = typer.Argument(..., help="Snip ID")):
    snip = get_snip(snip_id)
    if not snip:
        typer.echo(f"Snip {snip_id} not found.", err=True)
        raise typer.Exit(1)
    if show_confirmation(f"Delete snip {snip_id} ('{snip['title']}')?"):
        delete_snip(snip_id)
        typer.echo(f"Snip {snip_id} deleted.")
    else:
        typer.echo("Cancelled.")


@app.command()
def edit(snip_id: int = typer.Argument(..., help="Snip ID")):
    snip = get_snip(snip_id)
    if not snip:
        typer.echo(f"Snip {snip_id} not found.", err=True)
        raise typer.Exit(1)

    new_body = _edit_body(initial=snip["body"])
    if new_body == snip["body"]:
        typer.echo("No changes made.")
        return

    update_snip(snip_id, new_body)
    typer.echo(f"Snip {snip_id} updated.")


@app.command()
def check():
    db = get_connection()
    rows = db.execute(
        "SELECT id, title, source_file FROM snips WHERE source_file IS NOT NULL"
    ).fetchall()
    db.close()

    if not rows:
        typer.echo("No linked snips to check.")
        return

    from rich.console import Console
    from rich.table import Table
    rconsole = Console()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=4)
    table.add_column("Title")
    table.add_column("Source File")
    table.add_column("Status", width=12)

    missing = 0
    for r in rows:
        exists = Path(r["source_file"]).exists()
        status = "[green]✓ found[/green]" if exists else "[red]✗ missing[/red]"
        if not exists:
            missing += 1
        table.add_row(str(r["id"]), r["title"], r["source_file"], status)

    rconsole.print(table)
    total = len(rows)
    if missing:
        rconsole.print(f"[red]{missing} of {total} linked snips have missing source files.[/red]")
    else:
        rconsole.print(f"[green]All {total} linked snips have source files found.[/green]")


if __name__ == "__main__":
    app()
