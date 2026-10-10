"""Validate questions_demo.jsonl: schema, integrity, access rule, evidence, coverage, isolation."""

import collections
import csv
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent
OFFICIAL = DEMO.parent / "official"
REQUIRED = [
    "id", "slot_id", "case", "category", "question", "expected_answer", "evidence", "evidence_found",
    "expected_doc_ids", "expected_intent", "routing_mode", "expect_web_search", "department_id",
    "persona", "asker", "expect_visible", "reviewed", "generator", "reused_from", "demo_batch",
]
CASES = {
    "normal_guest": 24, "access_private": 140, "access_public_cross": 11, "advisory_single": 12,
    "advisory_multi": 12, "advisory_compare": 4, "calculation": 8, "unanswerable": 10,
    "off_topic": 8, "social": 6, "web_search": 6,
}
PERSONAS = {"guest", "same_department_exact_level", "same_department_one_level_below",
            "other_department_max_level", "wildcard_max_level"}
INTENTS = {"academic_advisory", "academic_calculation", "off_topic", "social_chat"}


def norm(text: str) -> str:
    """Letters and digits only, so line breaks, bullets and quote styles never decide a match."""
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFC", text).lower())


def visible(asker: dict, department_id: str, is_public: bool, level: int) -> bool:
    if is_public:
        return True
    return any(
        entry["department_id"] in (department_id, "*") and entry["access_level"] >= level
        for entry in asker["department_access"]
    )


def tree_stats(path: Path) -> tuple[int, int]:
    files = [item for item in path.rglob("*") if item.is_file() and ".cache" not in item.parts]
    return len(files), sum(item.stat().st_size for item in files)


def main() -> int:
    errors: list[str] = []
    with (DEMO / "demo_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        docs = {row["file_id"]: row for row in csv.DictReader(handle)}
    rows = [json.loads(line) for line in (DEMO / "questions_demo.jsonl").read_text(encoding="utf-8").splitlines()]
    texts: dict[str, str] = {}

    def doc_text(file_id: str) -> str:
        if file_id not in texts:
            texts[file_id] = norm((DEMO / "question_work_demo" / "excerpts" / f"{file_id}.txt").read_text(encoding="utf-8"))
        return texts[file_id]

    ids = collections.Counter(row["id"] for row in rows)
    errors += [f"duplicate id {key}" for key, count in ids.items() if count > 1]
    for row in rows:
        tag = row["id"]
        errors += [f"{tag}: missing {key}" for key in REQUIRED if key not in row]
        if row["case"] not in CASES:
            errors.append(f"{tag}: bad case {row['case']}")
        if row["persona"] not in PERSONAS:
            errors.append(f"{tag}: bad persona {row['persona']}")
        if row["expected_intent"] not in INTENTS:
            errors.append(f"{tag}: bad intent {row['expected_intent']}")
        if not str(row["id"]).startswith("d"):
            errors.append(f"{tag}: id prefix")
        doc_ids = row["expected_doc_ids"]
        for doc_id in doc_ids:
            if doc_id not in docs:
                errors.append(f"{tag}: unknown doc {doc_id}")
        if doc_ids and all(doc_id in docs for doc_id in doc_ids):
            first = docs[doc_ids[0]]
            is_public = first["demo_is_public"] == "true"
            level = int(first["demo_access_level"]) if first["demo_access_level"] else 0
            if row["doc_is_public"] != is_public:
                errors.append(f"{tag}: doc_is_public mismatch")
            if visible(row["asker"], row["department_id"], is_public, level) != row["expect_visible"]:
                errors.append(f"{tag}: expect_visible mismatch")
            if row["evidence"]:
                parts = [norm(part) for part in row["evidence"].split(" || ")]
                haystack = " ".join(doc_text(doc_id) for doc_id in doc_ids)
                errors += [f"{tag}: evidence not in doc: {part[:60]}" for part in parts if part not in haystack]
        if row["case"] == "advisory_multi" and row["routing_mode"] != "MULTI":
            errors.append(f"{tag}: routing_mode")
        if row["case"] in ("advisory_single", "advisory_compare") and row["routing_mode"] != "SINGLE":
            errors.append(f"{tag}: routing_mode")
        if row["case"] == "web_search" and not row["expect_web_search"]:
            errors.append(f"{tag}: expect_web_search")

    counts = collections.Counter(row["case"] for row in rows)
    for case, minimum in CASES.items():
        if counts[case] < minimum:
            errors.append(f"coverage {case}: {counts[case]} < {minimum}")
    private_docs = [doc_id for doc_id, doc in docs.items() if doc["demo_is_public"] != "true"]
    for doc_id in private_docs:
        personas = {row["persona"] for row in rows if row["case"] == "access_private" and row["expected_doc_ids"] == [doc_id]}
        if personas != PERSONAS:
            errors.append(f"private doc {doc_id}: personas {sorted(personas)}")
    for level in ("1", "2", "3"):
        n = len({row["expected_doc_ids"][0] for row in rows if row["case"] == "access_private" and str(row["doc_access_level"]) == level})
        if n < 8:
            errors.append(f"level L{level}: only {n} private docs tested")
    per_dept = collections.Counter(row["department_id"] for row in rows if row["case"] == "normal_guest")
    errors += [f"dept {dep}: {per_dept[dep]} normal_guest < 2" for dep in {d["department_id"] for d in docs.values()} if per_dept[dep] < 2]

    # Isolation: official small files byte-identical, large trees unchanged in count/size.
    for line in (DEMO / "official_hash_before.txt").read_text(encoding="utf-8-sig").splitlines():
        digest, name = line.split(" ", 1)
        if hashlib.sha256((OFFICIAL / name.strip()).read_bytes()).hexdigest().upper() != digest.upper():
            errors.append(f"official file changed: {name}")
    baseline_path = DEMO / "official_tree_baseline.json"
    stats = {name: tree_stats(OFFICIAL / name) for name in ("files", "scanned_pdf", "question_work")}
    if not baseline_path.exists():
        baseline_path.write_text(json.dumps(stats), encoding="utf-8")
    elif json.loads(baseline_path.read_text(encoding="utf-8")) != {k: list(v) for k, v in stats.items()}:
        errors.append("official tree changed")

    print("cases:", dict(counts), "total:", len(rows))
    print("\n".join(errors) if errors else "OK: 0 errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
