# stqa-practicals

A Python command-line tool for extracting text and practical sections from STQA practical PDFs.

## Features

- Extracts PDF text into a Markdown file.
- Detects practical sections and exports them individually.
- Writes a JSON index of detected practicals.
- Identifies code-like text blocks as candidates for review.

> **Note:** Extraction is heuristic. Review the output before using it. Scanned/image-only pages may require OCR and are not guaranteed to be extracted.

## Installation

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

The output directory contains:
- `full_text.md`
- `practicals.json`
- Individual practical Markdown files
- Text-based code candidate files

## Requirements

- Python 3.9+
- PyMuPDF

## Development

Clone the repository and install in editable mode:

```bash
git clone https://github.com/pranaypol/stqa-practicals.git
cd stqa-practicals
python -m pip install -e .
```

## License

No license has been selected yet. Until a license is added, standard copyright restrictions apply.
