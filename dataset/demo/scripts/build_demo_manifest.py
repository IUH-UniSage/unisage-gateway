"""Build demo_manifest.csv from selection.csv and verify each PDF against the official manifest."""

import csv
import hashlib
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent
OFFICIAL = DEMO.parent / "official"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    with (OFFICIAL / "manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        official = {row["file_id"]: row for row in csv.DictReader(handle)}
    with (DEMO / "selection.csv").open(encoding="utf-8-sig", newline="") as handle:
        selection = list(csv.DictReader(handle))

    errors: list[str] = []
    rows: list[dict[str, str]] = []
    for item in selection:
        source = official.get(item["file_id"])
        if source is None:
            errors.append(f"{item['file_id']}: not in official manifest")
            continue
        pdf = OFFICIAL / source["local_path"]
        if not pdf.is_file():
            errors.append(f"{item['file_id']}: missing {source['local_path']}")
            continue
        if sha256_of(pdf) != source["sha256"]:
            errors.append(f"{item['file_id']}: sha256 mismatch")
            continue
        rows.append(
            {
                "file_id": item["file_id"],
                "file_name": source["file_name"],
                "department_id": source["department_id"],
                "group": item["group"],
                "pages": source["pages"],
                "text_chars": source["text_chars"],
                "sha256": source["sha256"],
                "local_path": source["local_path"],
                "orig_is_public": source["is_public"],
                "orig_access_level": source["access_level"],
                "demo_is_public": item["demo_is_public"],
                "demo_access_level": item["demo_access_level"],
                "existing_questions": item["existing_questions"],
            }
        )

    if errors:
        print("\n".join(errors))
        return 1

    with (DEMO / "demo_manifest.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"demo_manifest.csv: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
