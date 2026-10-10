"""Extract plain text of every demo PDF into question_work_demo/excerpts/<file_id>.txt.

Run with the unisage-agent venv (has pymupdf):
  D:\\KLTN\\Main\\unisage-agent\\.venv\\Scripts\\python.exe build_excerpts.py
"""

import csv
import sys
from pathlib import Path

import pymupdf

DEMO = Path(__file__).resolve().parent.parent
OFFICIAL = DEMO.parent / "official"
OUT = DEMO / "question_work_demo" / "excerpts"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with (DEMO / "demo_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    empty: list[str] = []
    for row in rows:
        with pymupdf.open(OFFICIAL / row["local_path"]) as document:
            pages = [f"[Trang {number}]\n{page.get_text().strip()}" for number, page in enumerate(document, 1)]
        text = "\n\n".join(pages)
        (OUT / f"{row['file_id']}.txt").write_text(text, encoding="utf-8")
        if len(text) < 500:
            empty.append(row["file_id"])

    print(f"excerpts: {len(rows)} files, short/empty: {empty}")
    return 1 if empty else 0


if __name__ == "__main__":
    sys.exit(main())
