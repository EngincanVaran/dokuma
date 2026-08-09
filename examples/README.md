# dokuma examples

Runnable scripts demonstrating dokuma's API. Each one is self-contained -
it generates its own small sample document on the fly (via
`_generate_samples.py`, using the same generator libraries dokuma's own
test suite relies on), so there's nothing to download and nothing to run
out of order.

## Setup

From the repo root:

```bash
uv sync --all-extras --group dev
```

(or `pip install -e ".[all,pandas]" fpdf2 python-docx openpyxl pillow` if
you're not using `uv`.)

## Running

```bash
uv run python examples/01_inspect.py
```

## What's here

| Script | Shows |
|---|---|
| [`01_inspect.py`](01_inspect.py) | `dokuma.inspect()` - fast metadata, no full extraction |
| [`02_extract_basics.py`](02_extract_basics.py) | `dokuma.extract()` - regions, `.text`, `.tables`, `.to_markdown()` |
| [`03_pdf_engines.py`](03_pdf_engines.py) | PDF's two swappable engines - default vs. real bbox/page data |
| [`04_images.py`](04_images.py) | Extracting embedded pictures (PDF/DOCX/XLSX) and saving them to disk |
| [`05_config.py`](05_config.py) | `ExtractConfig` - `table_format` and `extract_images` |
| [`06_batch_processing.py`](06_batch_processing.py) | Looping over many files safely - engines never raise |

`04_images.py` writes the pictures it extracts into `examples/output/`
(gitignored) so you can actually open them afterward.
