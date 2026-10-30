import argparse
import json
import sys

from .extractor import extract_pdf


def build_parser():
    parser = argparse.ArgumentParser(
        prog="stqa-extract",
        description="Extract practicals, aims, steps, code candidates, and text from a PDF."
    )
    parser.add_argument("pdf", help="Path to the source PDF")
    parser.add_argument("-o", "--output", default="stqa-extracted", help="Output directory")
    parser.add_argument("--no-code", action="store_true", help="Do not attempt code-block detection")
    parser.add_argument("--min-code-lines", type=int, default=3,
                        help="Minimum non-empty lines for a code candidate (default: 3)")
    parser.add_argument("--json-summary", action="store_true", help="Print summary as JSON")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.min_code_lines < 1:
        print("Error: --min-code-lines must be at least 1.", file=sys.stderr)
        return 2
    try:
        summary = extract_pdf(
            args.pdf, args.output,
            include_code=not args.no_code,
            min_code_lines=args.min_code_lines
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if args.json_summary:
        print(json.dumps(summary, indent=2))
    else:
        print("STQA PDF extraction completed.")
        print(f"Pages processed: {summary['page_count']}")
        print(f"Practicals detected: {summary['practical_count']}")
        print(f"Code candidates detected: {summary['code_candidate_count']}")
        print(f"Output folder: {summary['output_dir']}")
    return 0
