# Contributing

## Dev setup

```bash
uv sync --all-extras --group dev
uv run pre-commit install
```

Format support is split into extras (`pdf`, `docx`, ...) so downstream users
only install what they need - `--all-extras` pulls in everything for local
dev/testing.

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
- No `print()` in library code (enforced by ruff's `T20`), and no
  `logging` either - `Engine.extract()` returns failures as
  `ExtractionResult.error` data rather than logging or raising, so
  library code has never needed a logger. Reconsider only if that design
  actually changes, not preemptively.
- `examples/*.py` are exempt from the `print()` rule (`per-file-ignores`
  in `pyproject.toml`) - printing output is the entire point of a demo
  script. Every example is self-contained (generates its own sample
  documents via `examples/_generate_samples.py`) - see
  [`examples/README.md`](examples/README.md).
