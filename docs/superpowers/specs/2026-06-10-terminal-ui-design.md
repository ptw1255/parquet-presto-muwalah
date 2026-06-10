# Terminal UI/UX Design Spec

## Overview

Single-command interactive NL-to-SQL interface for Muwalah Commerce. Run `python3 muwalah.py`, get a fully bootstrapped analytics stack with an English-language query prompt.

## Entry Point

`python3 muwalah.py` at the repo root.

## Startup Sequence

All steps are automatic. Each step shows a spinner while in progress, then a checkmark on success or an error message on failure.

1. **Check Docker** -- verify Docker daemon is running (`docker info`). If not, print error and exit.
2. **Check Ollama** -- verify Ollama is running and has the Granite model (`http://localhost:11434/api/tags`). If not, print install/pull instructions and exit.
3. **Start Trino** -- run `docker compose up -d`, then poll `SELECT 1` via `docker exec` until Trino is healthy (up to 60s).
4. **Check tables** -- query `SHOW TABLES FROM muwalah.main`. If fewer than 5 tables exist, run the full data load (reuse logic from `scripts/load_data.py`). Show progress during load.
5. **Enter REPL** -- display welcome banner, drop into interactive prompt.

## REPL Behavior

- **Prompt:** `muwalah ->` (using `rich` styling)
- **Input:** User types a natural-language question
- **Output:**
  1. Generated SQL displayed in a `rich.syntax.Syntax` panel (SQL highlighting)
  2. Query results displayed in a `rich.table.Table`
- **Exit:** `exit`, `quit`, or Ctrl+C -- all handled gracefully (no stack trace)
- **Errors:** Trino query errors shown inline, then re-prompt

## Rich Components

| Component | Usage |
|---|---|
| `Panel` | Welcome banner |
| `Status` (spinner) | Startup steps (Docker, Trino, data load) |
| `Syntax` | SQL output with syntax highlighting |
| `Table` | Query results |
| `Console.print` | Checkmarks, errors, prompt styling |

## Error States

| Condition | Behavior |
|---|---|
| Docker not running | Print error, exit |
| Ollama not running | Print error with install instructions, exit |
| Granite model not pulled | Print `ollama pull sam860/granite-4.0:7b` instruction, exit |
| Trino fails to start (60s timeout) | Print error, exit |
| Data load fails | Print error, exit |
| Generated SQL fails in Trino | Show error inline, re-prompt |
| Ctrl+C during startup | Clean exit |
| Ctrl+C during REPL | Clean exit with goodbye message |

## Dependencies

- Add `rich` to `requirements.txt`
- All other deps are stdlib (`subprocess`, `urllib`, `json`, `sys`, `time`)

## Files

- **Create:** `muwalah.py` (repo root)
- **Modify:** `requirements.txt` (add `rich`)
- Reuses schema context and SQL generation logic from `queries/ai/nl2sql.py`
- Reuses data loading logic from `scripts/load_data.py` (imported as module)
