"""Collect reusable base questions from the official question set.

A question is reusable when every expected doc is in the demo set. Persona-expanded
duplicates of the same question collapse to one base question; visibility, persona
and asker are recomputed later from the demo level (build_questions.py).
"""

import csv
import json
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent
OFFICIAL = DEMO.parent / "official"
OUT = DEMO / "question_work_demo" / "reused_base.jsonl"


def main() -> int:
    with (DEMO / "demo_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        demo_docs = {row["file_id"]: row for row in csv.DictReader(handle)}

    base: dict[tuple[str, str], dict] = {}
    for line in (OFFICIAL / "questions.jsonl").read_text(encoding="utf-8").splitlines():
        old = json.loads(line)
        doc_ids = list(old.get("expected_doc_ids") or [])
        if not doc_ids or any(doc_id not in demo_docs for doc_id in doc_ids):
            continue
        key = (old["question"], ",".join(sorted(doc_ids)))
        if key in base:
            base[key]["reused_from"].append(old["id"])
            continue
        case = "calculation" if old["category"] == "calculation" else "normal"
        base[key] = {
            "case": case,
            "question": old["question"],
            "expected_answer": old["expected_answer"],
            "evidence": old["evidence"],
            "evidence_found": old.get("evidence_found"),
            "doc_ids": doc_ids,
            "department_id": old["department_id"],
            "expected_intent": old["expected_intent"],
            "routing_mode": "",
            "reused_from": [old["id"]],
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as handle:
        for item in base.values():
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"reusable base questions: {len(base)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
