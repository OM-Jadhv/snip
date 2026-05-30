# snip

Local-first snippet and thought manager with semantic search.

No LLM calls. No cloud. Everything runs offline.

## Install

```bash
uv tool install .
```

The `snip` command will be available globally in your terminal.

## Usage

```
snip add "List files in Python" --body "import os; os.listdir('.')" --lang python --tags "fs,os"
snip list --tag python --limit 10
snip get 42
snip find "how do I list directory contents"
snip edit 42
snip delete 42
```

## Data

All data lives in `~/.snip/`:
- `snip.db` — SQLite database with vector search
- `config.toml` — configuration (db path, editor)
- `model/` — cached sentence-transformer model
