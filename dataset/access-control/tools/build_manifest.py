"""Write manifest.csv in the format unisage-agent `evals.dataset.ingest` reads, so the
20 access-control PDFs go through the same upload -> chunk -> embed flow as the official set.

Public documents still need an owning unit (docPackageId); it does not change who can read
them (`is_public` wins), it only says which office issued them.

Run once; afterwards the ingest tool keeps document_id / ingest_status in the file, so do not
re-run this over a manifest that already has ingest progress unless you mean to reset it.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = [
    "file_id", "file_name", "source_url", "source_page", "unit", "campus",
    "department_id", "is_public", "access_level", "label_source",
    "pages", "text_chars", "quality", "size_bytes", "sha256", "local_path",
    "tls_verified", "crawled_at",
    "selected", "ingest_status", "document_id", "title", "title_source",
]  # fmt: skip
PUBLIC_UNIT = {
    "P1": "phong giao vu", "P4": "phong giao vu", "P6": "phong giao vu", "P8": "phong giao vu",
    "P2": "PHONG_CTSV", "P3": "PHONG_CTSV", "P7": "PHONG_CTSV",
    "P5": "PHONG_QLKH_HTQT",
}


def main() -> None:
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    rows = []
    for doc in catalog["documents"]:
        spec = json.loads((ROOT / "specs" / f"{doc['doc_id']}.json").read_text(encoding="utf-8"))
        path = ROOT / "files" / spec["file_name"]
        data = path.read_bytes()
        dept = PUBLIC_UNIT[doc["doc_id"]] if doc["is_public"] else catalog["departments"][doc["dept"]]["name"]
        # The number line ("Số: 2471/QĐ-ĐHCN") makes titles unique and searchable like real ones.
        number = spec.get("number", "").removeprefix("Số:").strip()
        title = spec["title"].strip()
        title = title[0] + title[1:].lower() if title.isupper() else title
        rows.append({
            "file_id": doc["doc_id"],
            "file_name": spec["file_name"],
            "source_url": f"local://access-control/{spec['file_name']}",
            "unit": dept,
            "department_id": dept,
            "is_public": str(doc["is_public"]).lower(),
            "access_level": "" if doc["is_public"] else str(doc["min_access_level"]),
            "label_source": "catalog",
            "quality": "text",
            "size_bytes": str(len(data)),
            "sha256": hashlib.sha256(data).hexdigest(),
            "local_path": f"files/{spec['file_name']}",
            "selected": "true",
            "title": f"{title} ({number})" if number else title,
            "title_source": "spec",
        })
    with (ROOT / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    print(f"{len(rows)} rows -> manifest.csv")


if __name__ == "__main__":
    main()
