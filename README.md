# stqa-practicals

A Python command-line tool for extracting practical sections and code-like text from STQA practical PDF files.

## Features

- Extracts PDF text into a Markdown file.
- Detects practical sections and exports them individually.
- Extracts labelled aims and numbered steps when detectable.
- Writes a JSON index of detected practicals.
- Identifies code-like text blocks as candidates for review.

> **Important:** Extraction is heuristic. Review the output before using it. Scanned/image-only pages may need OCR and are not guaranteed to be extracted.

## Requirements

- Python 3.9+
- PyMuPDF

## Installation

Install from PyPI:

```bash
python -m pip install stqa-practicals
```

## Usage

```bash
stqa-extract "practicals.pdf" -o extracted
```

Alternatively:

```bash
python -m stqa_practicals "practicals.pdf" -o extracted
```

Useful options:

- `--no-code`: skip code-candidate detection.
- `--min-code-lines 4`: require at least four non-empty lines per code candidate.
- `--json-summary`: print the extraction summary as JSON.

The output directory contains `full_text.md`, `practicals.json`, individual practical Markdown files, and text-based code-candidate files.

## Development

```bash
git clone https://github.com/pranaypol/stqa-practicals.git
cd stqa-practicals
python -m pip install -e .
```

## License

MIT. See [LICENSE](LICENSE).
