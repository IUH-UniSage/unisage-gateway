"""Build the access-control test set from catalog.json + specs/*.json.

Outputs (in the dataset folder):
  questions.jsonl  one row per question (3 per document, 60 total)
  cases.csv        one row per (account, question): expect ANSWER or DENY
  accounts.csv     the test accounts (created by seed_accounts.py)

Visibility rule (mirrors unisage-agent qdrant_store filter):
  public doc  -> every account and the guest
  private doc -> account department == doc department AND account level >= doc min_access_level
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def accounts(catalog: dict) -> list[dict]:
    rows = [{"code": "GUEST", "department": "", "department_name": "", "access_level": ""}]
    for key, dept in catalog["departments"].items():
        for level in range(6):
            rows.append({
                "code": f"TST-{key}-L{level}",
                "department": key,
                "department_name": dept["name"],
                "access_level": level,
            })
    return rows


def visible(account: dict, doc: dict) -> bool:
    if doc["is_public"]:
        return True
    if account["code"] == "GUEST":
        return False
    return account["department"] == doc["dept"] and int(account["access_level"]) >= doc["min_access_level"]


def main() -> None:
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    accs = accounts(catalog)

    questions = []
    for doc in catalog["documents"]:
        spec = json.loads((ROOT / "specs" / f"{doc['doc_id']}.json").read_text(encoding="utf-8"))
        for i, q in enumerate(spec["questions"], 1):
            questions.append({
                "id": f"ac-{doc['doc_id']}-{i}",
                "doc_id": doc["doc_id"],
                "file_name": spec["file_name"],
                "title": spec["title"],
                "is_public": doc["is_public"],
                "department": catalog["departments"][doc["dept"]]["name"] if doc["dept"] else None,
                "min_access_level": doc["min_access_level"],
                "question": q["question"],
                "expected_answer": q["expected_answer"],
                "evidence": q["evidence"],
            })

    with (ROOT / "questions.jsonl").open("w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    with (ROOT / "accounts.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(accs[0].keys()))
        w.writeheader()
        w.writerows(accs)

    docs = {d["doc_id"]: d for d in catalog["documents"]}
    with (ROOT / "cases.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "account", "department", "access_level", "question_id", "doc_id",
                    "doc_scope", "expect", "question", "expected_answer"])
        n = 0
        for acc in accs:
            for q in questions:
                doc = docs[q["doc_id"]]
                n += 1
                scope = "public" if doc["is_public"] else f"{doc['dept']}/L{doc['min_access_level']}"
                w.writerow([f"case-{n:04d}", acc["code"], acc["department"], acc["access_level"], q["id"],
                            q["doc_id"], scope, "ANSWER" if visible(acc, doc) else "DENY",
                            q["question"], q["expected_answer"]])
    print(f"{len(questions)} questions, {len(accs)} accounts, {n} cases")


if __name__ == "__main__":
    main()
