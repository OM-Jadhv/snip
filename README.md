# snip

Local-first snippet and thought manager with semantic search.

## What it does

Save short pieces of code or text thoughts from the terminal, then find them later by describing what you vaguely remember. Uses both keyword matching and vector similarity to find results — so you can search "divide a list into chunks" even if the snippet says `for i in range(0, len(x), n)`. Everything runs offline. No LLM calls, no cloud, no API keys.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) — for installation and dependency management
- fzf — required only for `snip use` ([install](https://github.com/junegunn/fzf#installation)):
  - macOS: `brew install fzf`
  - Ubuntu: `apt install fzf`
  - Windows: `winget install junegunn.fzf` or `choco install fzf`
- The `all-MiniLM-L6-v2` embedding model downloads automatically on first run (~80 MB as ONNX, cached to `~/.snip/model/`)

## Installation

```bash
git clone <repo-url>
cd snip
uv tool install .
```

After install the `snip` command is available globally. No virtualenv activation needed.

To pre-download the embedding model (≈80 MB) before using search:

```bash
snip init
```

The model downloads automatically on first `snip find` if you skip this step.

## Quick start

```bash
# 1. Save a code snippet
snip add "Flatten a list" --body "flat = [item for sub in nested for item in sub]" --lang python --tags "list,comprehension"

# 2. Save a thought
snip add "Why 42?" --body "Deep Thought computed it after 7.5 million years." --type thought

# 3. Import a file as a snip
snip add "Database module" --from-file ./snip/db.py

# 4. Find by describing it
snip find "nest loop flatten join"

# 5. Pick interactively with fzf
snip use
```

## Commands

### snip add

Save a new snip.

```bash
snip add <title> [--body] [--lang] [--tags] [--type] [--source] [--file] [--line] [--from-file]
```

| Flag | Default | Description |
|------|---------|-------------|
| `title` | (required) | Snip title |
| `--body`, `-b` | `$EDITOR` / stdin | Snippet body text |
| `--lang`, `-l` | auto-detect | Programming language |
| `--tags`, `-t` | None | Comma-separated tags |
| `--type` | auto-detect | `code` or `thought` |
| `--source`, `-s` | None | URL or project name |
| `--file`, `-f` | None | Source file path (absolute resolved) |
| `--line`, `-L` | None | Line number in source file (requires `--file`) |
| `--from-file` | None | Read body from a file, auto-sets `--file` and `--line=1` |

Body resolution priority:
1. `--body` flag (explicit body text)
2. `--from-file` flag (read from file)
3. stdin pipe (when piped input is detected)
4. `$EDITOR` (interactive fallback, defaults to `vim` on macOS/Linux or `notepad` on Windows)

Type auto-detection: if `--lang` is provided, type defaults to `code`; otherwise `thought`.

Conflicts: `--from-file` cannot be used with `--body` or `--file`. `--line` requires `--file`.

### snip list

List recent snips.

```bash
snip list [--tag] [--type] [--limit]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--tag`, `-t` | None | Filter by tag (substring match) |
| `--type` | None | Filter by type (`code` or `thought`) |
| `--limit`, `-n` | 20 | Max results |

### snip get

Show a snip with syntax-highlighted body and source context.

```bash
snip get <id> [--no-vector]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--no-vector` | False | Skip related snips (avoids loading embedding model) |

Displays the full body with syntax highlighting, copies it to clipboard, shows a source file context panel if `source_file` is set, and lists up to 3 related snips based on semantic similarity. Use `--no-vector` for instant display without loading the embedding model.

### snip find

Search by keyword or description.

```bash
snip find <query> [--limit] [--text-only]
```

| Flag | Default | Description |
|------|---------|-------------|
| `query` | (required) | Search query |
| `--limit`, `-n` | 5 | Max results |
| `--text-only` | False | Keyword-only search (skips embedding model) |

Runs both keyword search (LIKE on title, body, tags) and vector similarity search (embedding KNN), merges results with vector-ranked results first, keyword-only results appended after. Use `--text-only` for instant text matching without loading the model.

### snip delete

Delete a snip. Prompts for confirmation (default no).

```bash
snip delete <id>
```

### snip edit

Opens the snip body in `$EDITOR` for editing. Re-embeds the body on save.

```bash
snip edit <id>
```

### snip check

Scans all snips with a `source_file` reference and reports whether each file still exists on disk.

```bash
snip check
```

### snip use

Opens an interactive fzf picker over all snips. Selecting a snip copies its body to clipboard.

```bash
snip use
```

Displays each snip as `id | language | tags | title`. Shows a body preview panel. Requires `fzf` on your PATH. Fzf flags used: `--height 40%`, `--layout reverse`, `--border`, `--prompt "snip>"`.

### snip init

Pre-download the embedding model to cache so the first search is instant.

```bash
snip init
```

Idempotent — safe to run multiple times.

> **About the "unauthenticated requests" warning:** During model download you may see
> `Warning: You are sending unauthenticated requests to the HF Hub.` This comes from
> the Hugging Face Hub server — it's harmless and purely informational. The download
> works fine without authentication. Set `HF_TOKEN` in your environment to silence it
> and get higher rate limits.

### snip reindex

Re-embed all snips with the current model. Run this after migrating the embedding backend to realign existing vectors with new queries.

```bash
snip reindex
```

Shows a progress bar during processing. The database and model cache are preserved.

### snip stats

Shows a dashboard with overview, language breakdown, top tags, and 7-day activity.

```bash
snip stats
```

### snip export

Export all snips to JSON or Markdown.

```bash
snip export [--format] [--output]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--format` | `json` | Output format: `json` or `markdown` |
| `--output`, `-o` | stdout | Output file path |

### snip import

Import snips from a JSON backup or a directory of files.

```bash
snip import <source> [--lang] [--collection] [--dry-run]
```

| Flag | Default | Description |
|------|---------|-------------|
| `source` | (required) | Path to a `.json` file or a directory |
| `--lang` | None | Language override for all imported snips (directory mode only) |
| `--collection` | None | Tag to append to every imported snip |
| `--dry-run` | False | Preview what would be imported without writing |

Directory import infers language from file extension:

| Extension | Language |
|-----------|----------|
| `.py` | python |
| `.js` | javascript |
| `.ts` | typescript |
| `.sh` | bash |
| `.go` | go |
| `.rs` | rust |
| `.md` | markdown |
| *other* | None (type = thought) |

Directory import skips hidden files (`.` prefix), files larger than 1 MB, and files that fail UTF-8 decoding.

## How search works

When you run `snip find`, it does two searches in parallel:

- **Keyword search** scans title, body, and tags for literal matches (SQL LIKE). This catches exact terms you remember.
- **Vector search** embeds your query into a 384-dimensional vector using `all-MiniLM-L6-v2`, then finds the nearest neighbors in the database by cosine distance. This catches semantic matches — conceptually related snips even if they use different words.

Results are merged: vector matches are ranked by similarity score, then keyword-only matches are appended below them. Duplicates are removed in favor of the vector result. The top N results are returned.

This means "how do I open a file and read it" will find a snippet titled `with open` even though none of those exact words appear in the title.

## Data

All data lives in your home directory. Nothing leaves your machine.

```
~/.snip/
  snip.db      SQLite database with vector search (snips + vec_snips tables)
  config.toml  Configuration (optional)
  model/       Cached embedding model
```

No API keys, no accounts, no telemetry.

## Platform notes

- **Data directory**: `~/.snip/` resolves to `C:\Users\<you>\.snip\` on Windows. The dot-prefix works correctly on modern Windows but the folder may be hidden by default in File Explorer.
- **Clipboard**: On Linux, pyperclip requires `xclip` or `xsel` to be installed (`sudo apt install xclip`). On macOS and Windows the clipboard works out of the box.
- **fzf on Windows**: Requires `winget install junegunn.fzf` or `choco install fzf`. Works in PowerShell, cmd, and Windows Terminal.
- **`snip edit` editor**: Defaults to `notepad` on Windows, `vim` on macOS/Linux. Override with `$EDITOR` environment variable or `~/.snip/config.toml`.

## Configuration

`~/.snip/config.toml` is created on first run with commented-out defaults:

```toml
# db_path = "~/.snip/snip.db"
# editor = "vim"
```

- `db_path` — override the database location
- `editor` — override the editor used by `snip add` and `snip edit` (also respects `$EDITOR`; defaults to `notepad` on Windows, `vim` elsewhere)

## Import / Export

Round-trip a library:

```bash
snip export --format json --output backup.json
snip import backup.json --collection backup
```

Import a directory of source files:

```bash
snip import ./src --lang python --collection myproject
```

Preview without importing:

```bash
snip import ./src --dry-run
```

## Shell integration

```bash
alias ss="snip use"
```

## Development

For local development (not installing as a global tool):

```bash
git clone <repo-url>
cd snip
uv sync
uv run snip --help
```

`uv sync` installs all dependencies from `pyproject.toml` into `.venv/` at the project root.

## License

MIT License. See [LICENSE](LICENSE).
