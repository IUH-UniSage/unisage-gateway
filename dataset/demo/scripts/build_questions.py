"""Merge reused + authored base questions into questions_demo.jsonl.

Persona, asker and expect_visible are derived from each document's demo level, never
written by hand. Doc-based questions on a private doc expand to 5 persona rows.
"""

import csv
import json
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent
WORK = DEMO / "question_work_demo"
BATCH = "2026-10-04"
GENERATOR = "claude-sonnet-5-5 (authored inline from document excerpts), reviewed=false"
CASE_ORDER = [
    "normal_guest", "access_private", "access_public_cross", "advisory_single",
    "advisory_multi", "advisory_compare", "calculation", "unanswerable",
    "off_topic", "social", "web_search",
]
# Same-department pairs of reused questions (indexes in reused_base.jsonl) joined into MULTI questions.
MULTI_PAIRS = [(12, 13), (14, 18), (52, 53), (30, 31), (59, 62), (22, 23), (0, 57)]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def other_department(department_id: str) -> str:
    return "PHONG_DAO_TAO" if department_id == "KHOA_QTKD" else "KHOA_QTKD"


def asker_for(persona: str, department_id: str, level: int) -> dict:
    if persona == "guest":
        entries: list[dict] = []
    elif persona == "same_department_exact_level":
        entries = [{"department_id": department_id, "access_level": level}]
    elif persona == "same_department_one_level_below":
        entries = [{"department_id": department_id, "access_level": level - 1}]
    elif persona == "other_department_max_level":
        entries = [{"department_id": other_department(department_id), "access_level": 5}]
    else:
        entries = [{"department_id": "*", "access_level": 5}]
    return {"department_access": entries}


def visible(asker: dict, department_id: str, is_public: bool, level: int) -> bool:
    if is_public:
        return True
    return any(
        entry["department_id"] in (department_id, "*") and entry["access_level"] >= level
        for entry in asker["department_access"]
    )


PRIVATE_PERSONAS = [
    "guest", "same_department_exact_level", "same_department_one_level_below",
    "other_department_max_level", "wildcard_max_level",
]


def main() -> int:
    with (DEMO / "demo_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        docs = {row["file_id"]: row for row in csv.DictReader(handle)}

    reused = read_jsonl(WORK / "reused_base.jsonl")
    bases: list[dict] = []
    for item in reused:
        bases.append({**item, "case": "calculation" if item["case"] == "calculation" else "normal"})
    for name in ("authored_private_1", "authored_private_2", "authored_advisory", "authored_calc", "authored_nodoc"):
        bases.extend(read_jsonl(WORK / f"{name}.jsonl"))
    for first, second in MULTI_PAIRS:
        a, b = reused[first], reused[second]
        question = a["question"].rstrip() + " Ngoài ra, " + b["question"][0].lower() + b["question"][1:]
        bases.append({
            "case": "advisory_multi", "routing_mode": "MULTI", "sub_question_count": 2,
            "doc_ids": a["doc_ids"] + b["doc_ids"], "department_id": a["department_id"],
            "expected_intent": "academic_advisory", "question": question,
            "expected_answer": f"(1) {a['expected_answer']} (2) {b['expected_answer']}",
            "evidence": f"{a['evidence']} || {b['evidence']}",
            "reused_from": a["reused_from"] + b["reused_from"],
        })

    rows: list[dict] = []
    cross_done: set[str] = set()

    def add(base: dict, case: str, persona: str, department_id: str, doc_ids: list[str]) -> None:
        first = docs[doc_ids[0]] if doc_ids else None
        is_public = first["demo_is_public"] == "true" if first else True
        level = int(first["demo_access_level"]) if first and first["demo_access_level"] else 0
        asker = asker_for(persona, department_id, level)
        rows.append({
            "case": case,
            "category": {"normal_guest": "normal", "access_private": "access", "access_public_cross": "access",
                         "advisory_single": "normal", "advisory_multi": "normal", "advisory_compare": "normal",
                         "calculation": "calculation", "unanswerable": "unanswerable", "off_topic": "off_topic",
                         "social": "social", "web_search": "web_search"}[case],
            "question": base["question"],
            "expected_answer": base["expected_answer"],
            "evidence": base.get("evidence", ""),
            "evidence_found": bool(base.get("evidence")),
            "expected_doc_ids": doc_ids,
            "expected_intent": base["expected_intent"],
            "routing_mode": base.get("routing_mode", ""),
            "sub_question_count": base.get("sub_question_count"),
            "expect_web_search": bool(base.get("expect_web_search", False)),
            "department_id": department_id,
            "doc_is_public": is_public if doc_ids else None,
            "doc_access_level": level if doc_ids and not is_public else None,
            "persona": persona,
            "asker": asker,
            "expect_visible": visible(asker, department_id, is_public, level) if doc_ids else True,
            "reviewed": False,
            "generator": GENERATOR,
            "reused_from": ",".join(base.get("reused_from", [])),
            "demo_batch": BATCH,
        })

    for base in bases:
        doc_ids = base.get("doc_ids", [])
        department_id = base.get("department_id", "")
        if not doc_ids:
            add(base, base["case"], "guest", department_id, [])
            continue
        privates = [d for d in doc_ids if docs[d]["demo_is_public"] != "true"]
        if privates and len(doc_ids) > 1:
            raise SystemExit(f"multi-doc question on private doc: {base['question'][:60]}")
        if privates:
            for persona in PRIVATE_PERSONAS:
                add(base, "access_private", persona, department_id, doc_ids)
            continue
        case = "normal_guest" if base["case"] == "normal" else base["case"]
        add(base, case, "guest", department_id, doc_ids)
        if case == "normal_guest" and department_id not in cross_done and len(doc_ids) == 1:
            cross_done.add(department_id)
            add(base, "access_public_cross", "other_department_max_level", department_id, doc_ids)

    rows.sort(key=lambda row: CASE_ORDER.index(row["case"]))
    for number, row in enumerate(rows, 1):
        row["id"] = f"d{number:04d}"
        row["slot_id"] = f"demo-{row['case']}-{number:04d}"
    ordered = ["id", "slot_id"] + [key for key in rows[0] if key not in ("id", "slot_id")]
    with (DEMO / "questions_demo.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps({key: row[key] for key in ordered}, ensure_ascii=False) + "\n")
    review_fields = ["id", "case", "persona", "question", "expected_answer", "evidence", "department_id",
                     "expected_doc_ids", "doc_is_public", "doc_access_level", "expect_visible",
                     "routing_mode", "expect_web_search", "reused_from", "reviewed"]
    with (DEMO / "questions_demo_review.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=review_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: (",".join(row[key]) if key == "expected_doc_ids" else row[key]) for key in review_fields})
    print(f"questions_demo.jsonl: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
