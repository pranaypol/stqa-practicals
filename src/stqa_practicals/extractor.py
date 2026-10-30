from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import fitz


PRACTICAL_RE = re.compile(
    r"(?im)^\s*(?:PRACTICAL\s*(?:NO\.?|NUMBER)?\s*[:.\-]*\s*|PRACTICAL\s+)(\d{1,2})\b[^\n]*"
)
AIM_RE = re.compile(r"(?im)^\s*AIM\s*[:.-]\s*(.*)")
STEP_RE = re.compile(r"(?im)^\s*(?:STEP\s*\d+\s*[:.\-]*|\d+[.)]\s+).{0,180}$")
CODE_CUE_RE = re.compile(
    r"(?i)(source\s*code|source\s*code\s*:|code\s*:|\.py\b|\.java\b|import\s+|public\s+class|def\s+\w+\s*\(|#include|<html)"
)
CODE_LINE_RE = re.compile(
    r"(?i)(^\s*(import\s|from\s+\w+\s+import|def\s+|class\s+|public\s+class|public\s+static|private\s+|protected\s+|package\s+|#include|<\?php|<!doctype|<html|<body|<form)|"
    r"\b(driver\.|System\.out\.|print\(|console\.|if\s*\(|for\s*\(|while\s*\(|return\s|try\s*\{|catch\s*\(|SELECT\s+|INSERT\s+INTO))"
)


def _clean(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_pdf(pdf_path: str | Path) -> list[dict[str, Any]]:
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")
    pages = []
    with fitz.open(path) as doc:
        if doc.is_encrypted and not doc.authenticate(""):
            raise ValueError("The PDF is password-protected.")
        for index, page in enumerate(doc, start=1):
            pages.append({"page": index, "text": _clean(page.get_text("text"))})
    return pages


def split_practicals(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    combined = []
    for page in pages:
        combined.append(f"\n\n<!-- PAGE {page['page']} -->\n{page['text']}")
    text = "\n".join(combined)

    matches = list(PRACTICAL_RE.finditer(text))
    if not matches:
        return [{
            "number": None, "heading": "Unclassified content",
            "start_page": pages[0]["page"] if pages else None,
            "end_page": pages[-1]["page"] if pages else None,
            "text": text.strip()
        }]

    items = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[start:end].strip()
        page_nums = [int(x) for x in re.findall(r"<!-- PAGE (\d+) -->", section)]
        heading = match.group(0).strip()
        items.append({
            "number": int(match.group(1)),
            "heading": heading,
            "start_page": min(page_nums) if page_nums else None,
            "end_page": max(page_nums) if page_nums else None,
            "text": section
        })
    return items


def extract_aim(text: str) -> str | None:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = AIM_RE.match(line.strip())
        if not m:
            continue
        value = m.group(1).strip()
        if not value and i + 1 < len(lines):
            value = lines[i + 1].strip()
        collected = [value] if value else []
        for nxt in lines[i + 1:]:
            candidate = nxt.strip()
            if re.match(r"(?i)^(theory|tool|steps?|step\s*\d|procedure|source\s*code)", candidate):
                break
            if candidate and not candidate.startswith("<!-- PAGE"):
                if len(" ".join(collected)) > 600:
                    break
                collected.append(candidate)
        result = re.sub(r"\s+", " ", " ".join(collected)).strip()
        return result or None
    return None


def extract_steps(text: str) -> list[str]:
    lines = text.splitlines()
    steps = []
    active = False
    for line in lines:
        raw = line.strip()
        if not raw or raw.startswith("<!-- PAGE"):
            continue
        if re.match(r"(?i)^(steps?|procedure|step-by-step)", raw):
            active = True
            continue
        if active and re.match(r"(?i)^(source\s*code|theory|output|o/p|aim|tool)\b", raw):
            active = False
        if active and STEP_RE.match(raw):
            steps.append(raw)
    return list(dict.fromkeys(steps))


def extract_code_candidates(text: str, min_code_lines: int = 3) -> list[str]:
    lines = text.splitlines()
    candidates: list[str] = []
    current: list[str] = []
    in_code = False

    def flush() -> None:
        nonlocal current
        while current and not current[0].strip():
            current.pop(0)
        while current and not current[-1].strip():
            current.pop()
        if len([x for x in current if x.strip()]) >= min_code_lines:
            block = "\n".join(current).strip()
            if block and block not in candidates:
                candidates.append(block)
        current = []

    for line in lines:
        raw = line.rstrip()
        stripped = raw.strip()
        if not stripped or stripped.startswith("<!-- PAGE"):
            if in_code:
                current.append(raw)
            else:
                flush()
            continue

        cue = bool(CODE_CUE_RE.search(stripped))
        code_like = bool(CODE_LINE_RE.search(stripped))
        if re.search(r"(?i)source\s*code|code\s*:", stripped):
            flush()
            in_code = True
            continue
        if in_code:
            if re.match(r"(?i)^(step\s*\d|output|o/p|expected output|theory|aim|tool)\b", stripped):
                flush()
                in_code = False
            elif code_like or raw.startswith((" ", "\t")) or re.match(r"^[{}();<>]", stripped):
                current.append(raw)
            else:
                if len(current) and (stripped.endswith(";") or stripped in {"}", "{", ")", "};"}):
                    current.append(raw)
                else:
                    flush()
                    in_code = False
        elif code_like:
            in_code = True
            current.append(raw)
        elif cue:
            flush()

    flush()
    return candidates


def extract_pdf(pdf_path: str | Path, output_dir: str | Path,
                include_code: bool = True, min_code_lines: int = 3) -> dict[str, Any]:
    pages = read_pdf(pdf_path)
    practicals = split_practicals(pages)
    out = Path(output_dir)
    practical_dir = out / "practicals"
    practical_dir.mkdir(parents=True, exist_ok=True)

    result_items = []
    for idx, practical in enumerate(practicals, start=1):
        text = practical["text"]
        codes = extract_code_candidates(text, min_code_lines) if include_code else []
        item = {
            **practical,
            "aim": extract_aim(text),
            "steps": extract_steps(text),
            "code_candidates": codes,
        }
        result_items.append(item)

        num = practical["number"] if practical["number"] is not None else idx
        md = [
            f"# {practical['heading']}",
            "",
            f"**Pages:** {practical['start_page']}–{practical['end_page']}",
            "",
            "## Aim",
            "",
            item["aim"] or "_No clearly labelled AIM line was detected._",
            "",
            "## Steps detected",
            "",
        ]
        md.extend([f"- {step}" for step in item["steps"]] or ["_No numbered steps were detected._"])
        md += ["", "## Extracted code candidates", ""]
        if codes:
            for code_idx, code in enumerate(codes, start=1):
                md += [f"### Code candidate {code_idx}", "", "```text", code, "```", ""]
        else:
            md.append("_No code candidate was detected by the heuristic extractor._")
        md += ["", "## Full practical text", "", text, ""]
        (practical_dir / f"practical-{int(num):02d}.md").write_text("\n".join(md), encoding="utf-8")

        if codes:
            for code_idx, code in enumerate(codes, start=1):
                (practical_dir / f"practical-{int(num):02d}-code-{code_idx:02d}.txt").write_text(
                    code + "\n", encoding="utf-8"
                )

    full_text = "\n\n".join(
        f"## Page {p['page']}\n\n{p['text']}" for p in pages
    )
    (out / "full_text.md").write_text("# Complete PDF text extraction\n\n" + full_text, encoding="utf-8")
    (out / "practicals.json").write_text(
        json.dumps({"source": str(pdf_path), "page_count": len(pages), "practicals": result_items},
                   ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return {
        "page_count": len(pages),
        "practical_count": len(result_items),
        "code_candidate_count": sum(len(x["code_candidates"]) for x in result_items),
        "output_dir": str(out.resolve())
    }
