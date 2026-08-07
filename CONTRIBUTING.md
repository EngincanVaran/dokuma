# Contributing

`dokuma` is at the concept stage (see `README.md`) - the most useful
contribution right now is design feedback on the sketch, not code.

## Dev setup

```bash
uv sync --group dev
uv run pre-commit install
```

## Before committing

```bash
uv run pre-commit run --all-files
uv run pytest
uv run mypy --strict dokuma
```

`pre-commit install` wires these in as git hooks, so this is mostly automatic
after setup.

## Conventions

- Python >=3.11, managed with `uv` (`pyproject.toml` + `uv.lock`).
- `ruff` for lint + format (line length 100, double quotes).
- `mypy --strict` - all public functions need type hints.
- No `print()` in library code - not wired up yet, but plan to use
  `logging` (e.g. `loguru`) once there's real code.
