# semantic-git-diff

> `git diff` tells you *what* changed. This tells you *what it means.*

Summarize any git diff in plain English using a local LLM — no API keys, no data leaving your machine.

```
sgd main..feature/auth
```

---

## Install

```bash
pip install semantic-git-diff
```

Requires Python ≥ 3.10 and [Ollama](https://ollama.com) running locally.

Pull a model:

```bash
ollama pull qwen3:8b        # recommended — best quality
ollama pull qwen2.5:3b      # smaller, works on CPU
```

---

## Usage

```bash
# Compare branches
sgd main..feature/auth

# Compare commits
sgd HEAD~3..HEAD

# Save to file
sgd main..feature/auth -o summary.md

# JSON output
sgd main..feature/auth --format json

# Dry-run (inspect chunks and prompt, no LLM call)
sgd main..feature/auth --dry-run

# Use a different model
sgd main..feature/auth --model llama3.2:3b

# Respond in French
sgd main..feature/auth --lang fr
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--output` / `-o` | stdout | Write output to file |
| `--model` / `-m` | `qwen3:8b` | Ollama model name |
| `--lang` / `-l` | `en` | Output language |
| `--format` / `-f` | `markdown` | `markdown` or `json` |
| `--dry-run` | `false` | Show prompt + chunks without calling LLM |
| `--max-chunks` | `50` | Max code regions to process |
| `--version` | | Show version |

---

## Example

Given this diff (migrating from sqlite3 to asyncpg, adding password hashing and a health endpoint):

### `sgd --dry-run HEAD~1..HEAD`

```
# semantic-git-diff --dry-run
  Refs: HEAD~1..HEAD
  Files: 3
  Chunks: 7
  Estimated tokens: 561

## Chunks
  1. auth.py
     Region: def hash_password
     Old: 0 chars
     New: 129 chars
  2. auth.py
     Region: def login
     Old: 244 chars
     New: 289 chars
  3. auth.py
     Region: def get_user
     Old: 65 chars
     New: 0 chars
  4. auth.py
     Region: def _find_user
     Old: 0 chars
     New: 41 chars
  5. db.py
     Region: def init_db
     Old: 141 chars
     New: 0 chars
  6. db.py
     Region: async def init_db
     Old: 0 chars
     New: 300 chars
  7. new_feature.py
     Region: def health_check
     Old: 0 chars
     New: 52 chars
```

### Actual output (with qwen3:8b)

```markdown
## Summary
Migrated from synchronous sqlite3 to asyncpg with connection pooling,
replaced hardcoded password comparison with PBKDF2 hashing, and added
a health check endpoint.

## Changes

### `auth.py`
- Added `hash_password()` with PBKDF2-SHA256 and random salt
- Refactored `login()` to query `_find_user()` and verify password hash instead of hardcoded comparison
- Removed `get_user()` (unused)
- Added `_find_user()` as a private lookup helper

### `db.py`
- Rewrote `init_db()` from synchronous sqlite3 to asyncpg with `DATABASE_URL`
- Updated schema: `users` table now uses `SERIAL PRIMARY KEY` and `BYTES` for password hashes

### `new_feature.py`
- Added `health_check()` returning `{"status": "healthy"}`
```

---

## How it works

```
git diff (raw)
    │
    ▼
unidiff parser          → PatchSet → PatchedFile → Hunk
    │
    ▼
Semantic chunker        → regex on def/class/fn/func/function/arrow
    │                      fallback: whole hunk if no boundary
    ▼
Prompt builder          → old_code + new_code as separate blocks (no +/-)
    │
    ▼
LLM (Ollama)            → Single global prompt per diff (no summary-of-summaries)
    │
    ▼
Formatter               → Markdown (default) or JSON
    │
    ▼
stdout / file
```

- **Parser**: [`unidiff`](https://github.com/matiasb/python-unidiff) parses raw git diff into structured hunks
- **Chunker**: Detects function/class boundaries across Python, JS/TS, Go, Rust, Java, and more
- **Prompt**: Strips `+`/`-` prefixes; sends clean old/new code blocks directly to the LLM
- **LLM**: Single pass — all chunks in one prompt, no lossy summary-of-summaries
- **Guard**: Warns and truncates when estimated tokens exceed 24k

> **CPU users:** Large diffs (>~3000 tokens) may time out on CPU with bigger models. Use `--dry-run` to check the estimated token count first, or limit scope with `HEAD~1..HEAD`.

---

## Requirements

- Python ≥ 3.10
- [Ollama](https://ollama.com) running locally
- A model pulled (recommended: `qwen3:8b`, or `qwen2.5:3b` for CPU/smaller machines)

---

## License

MIT
