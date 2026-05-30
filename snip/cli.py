import json
import os
import shutil
from datetime import datetime
import subprocess
import sys
import tempfile
from pathlib import Path

import typer

from rich.console import Console
from rich.panel import Panel

from snip.db import get_connection
from snip.display import show_confirmation, show_related, show_snip, show_stats, show_table
from snip.search import find_related, hybrid_search
from snip.store import add_snip, bulk_add_snips, delete_snip, get_all_snips, get_snip, get_stats, list_snips, update_snip

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
    from_file: str | None = typer.Option(None, "--from-file", help="Read body from file, auto-set source"),
):
    if line is not None and file is None:
        typer.echo("Error: --line requires --file", err=True)
        raise typer.Exit(1)
    if from_file:
        if body is not None:
            typer.echo("Error: Cannot use --body and --from-file together.", err=True)
            raise typer.Exit(1)
        if file is not None:
            typer.echo("Error: Cannot use --file and --from-file together. --from-file sets the source file automatically.", err=True)
            raise typer.Exit(1)
        body = Path(from_file).read_text()
        file = str(Path(from_file).resolve())
        line = 1
    if file:
        file = str(Path(file).resolve())

    if body is None and not sys.stdin.isatty():
        body = sys.stdin.read().strip()

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


@app.command()
def use():
    if not shutil.which("fzf"):
        console = Console()
        console.print(Panel(
            "[red]fzf is required but not installed.[/red]\n\n"
            "Install it:\n"
            "  macOS:   [bold]brew install fzf[/bold]\n"
            "  Ubuntu:  [bold]apt install fzf[/bold]\n"
            "  Others:  [bold]https://github.com/junegunn/fzf#installation[/bold]",
            title="fzf Not Found",
            border_style="red",
        ))
        raise typer.Exit(1)

    db = get_connection()
    rows = db.execute("SELECT id, title, language, tags, body FROM snips ORDER BY created_at DESC").fetchall()
    db.close()

    if not rows:
        typer.echo("No snips to pick from.")
        return

    preview_dir = Path(tempfile.mkdtemp(prefix="snip_preview_"))
    try:
        for r in rows:
            (preview_dir / f"{r['id']}.txt").write_text(r["body"])

        fzf_input = "\n".join(
            f"{r['id']} | {r.get('language') or 'text'} | {r.get('tags') or 'no tags'} | {r['title']}"
            for r in rows
        )

        preview_cmd = f"cat {shlex.quote(str(preview_dir))}/$(echo {{}} | cut -d'|' -f1 | xargs).txt"
        proc = subprocess.Popen(
            ["fzf", "--height", "40%", "--layout", "reverse", "--border",
             "--prompt", "snip> ", "--preview", preview_cmd],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, _ = proc.communicate(input=fzf_input)

        if proc.returncode != 0:
            return

        selected = stdout.strip()
        if not selected:
            return

        snip_id = int(selected.split("|")[0].strip())
        snip = get_snip(snip_id)
        if snip:
            try:
                pyperclip.copy(snip["body"])
            except Exception:
                pass
            typer.echo(f"Copied snip {snip['id']}: {snip['title']}")

    finally:
        shutil.rmtree(str(preview_dir), ignore_errors=True)


@app.command(name="import")
def import_snips(
    source: str = typer.Argument(..., help="JSON file or directory path"),
    lang: str | None = typer.Option(None, "--lang", help="language tag for directory import"),
    collection: str | None = typer.Option(None, "--collection", help="tag to apply to all imported snips"),
    dry_run: bool = typer.Option(False, "--dry-run", help="preview without saving"),
):
    from snip.embeddings import encode

    src = Path(source)
    if src.is_file() and src.suffix == ".json":
        snips = _import_from_json(src, collection, dry_run)
        label = str(src)
    elif src.is_dir():
        snips = _import_from_directory(src, lang, collection, dry_run)
        label = str(src) + "/"
    else:
        typer.echo(f"Error: {source} is not a .json file or a directory", err=True)
        raise typer.Exit(1)

    if not snips:
        typer.echo("No snips to import.")
        return

    if dry_run:
        typer.echo(f"Would import {len(snips)} snips from {label}:")
        for s in snips:
            typer.echo(f"  - {s['title']} ({s.get('language', '-')})")
        return

    from rich.progress import Progress
    db = get_connection()
    count = 0
    with Progress() as progress:
        task = progress.add_task("Importing...", total=len(snips))
        for s in snips:
            embedding = encode(s["body"])
            cursor = db.execute(
                "INSERT INTO snips (title, body, type, language, tags, source, source_file, source_line) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (s["title"], s["body"], s.get("type", "code"), s.get("language"), s.get("tags"), s.get("source"), s.get("source_file"), s.get("source_line")),
            )
            db.execute("INSERT INTO vec_snips(id, embedding) VALUES (?, ?)", (cursor.lastrowid, embedding))
            count += 1
            progress.update(task, advance=1)
    db.commit()
    db.close()
    typer.echo(f"Imported {count} snips from {label}")


LANG_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".sh": "bash", ".go": "go", ".rs": "rust", ".md": "markdown",
}


def _import_from_json(source: Path, collection: str | None, dry_run: bool) -> list[dict]:
    data = json.loads(source.read_text())
    snips = []
    for item in data:
        snip = {
            "title": item["title"],
            "body": item["body"],
            "type": item.get("type", "code"),
            "language": item.get("language"),
            "tags": item.get("tags"),
            "source": item.get("source"),
            "source_file": item.get("source_file"),
            "source_line": item.get("source_line"),
        }
        if collection:
            existing = snip["tags"] or ""
            snip["tags"] = (existing + "," + collection).strip(",")
        snips.append(snip)
    return snips


def _import_from_directory(source: Path, lang: str | None, collection: str | None, dry_run: bool) -> list[dict]:
    snips = []
    for fp in sorted(source.rglob("*")):
        if not fp.is_file() or fp.name.startswith("."):
            continue
        if fp.stat().st_size > 1_000_000:
            continue
        try:
            body = fp.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        ext = fp.suffix.lower()
        language = lang or LANG_MAP.get(ext)
        snips.append({
            "title": fp.stem,
            "body": body,
            "type": "code" if language else "thought",
            "language": language,
            "tags": collection or None,
            "source": None,
            "source_file": str(fp.resolve()),
            "source_line": 1,
        })
    return snips


@app.command()
def export(
    format: str = typer.Option("json", "--format", help="json or markdown"),
    output: str | None = typer.Option(None, "--output", "-o", help="output file path"),
):
    db = get_connection()
    snips = get_all_snips(db)
    db.close()

    if format == "json":
        content = json.dumps(snips, indent=2, default=str)
    else:
        lines = ["# Snip Library Export", f"_Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_", "---", ""]
        for s in snips:
            lines.append(f"## {s['title']}")
            lines.append(f"**ID:** {s['id']} | **Language:** {s.get('language', '') or '-'} | **Tags:** {s.get('tags', '') or '-'} | **Type:** {s['type']}")
            lines.append(f"**Created:** {s['created_at']}")
            if s.get("source_file"):
                line_ref = f":{s['source_line']}" if s.get("source_line") else ""
                lines.append(f"**Source:** {s['source_file']}{line_ref}")
            lines.append("")
            lang = s.get("language") or ""
            lines.append(f"```{lang}")
            lines.append(s["body"])
            lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")
        content = "\n".join(lines)

    if output:
        Path(output).write_text(content)
        typer.echo(f"Exported {len(snips)} snips to {output}")
    else:
        typer.echo(content)


@app.command()
def stats():
    db = get_connection()
    data = get_stats(db)
    db.close()
    show_stats(data)


if __name__ == "__main__":
    app()
