"""Run unisage-agent's `task eval:ingest` on this dataset until every row is done, retrying
rows that failed because the model provider was overloaded (HTTP 503/504, UNAVAILABLE,
"high demand", DEADLINE_EXCEEDED): such rows go back to `uploaded` (document kept, it is
re-chunked and re-embedded), then the run waits RETRY_WAIT seconds and starts again.
Quota/rate-limit rows are already handled inside the ingest tool (--quota-wait).

Usage (from anywhere):
  UNISAGE_ADMIN_PASSWORD=... python3 tools/ingest_retry.py [--max-rounds 30] [--wait 60]
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENT = ROOT.parents[2] / "unisage-agent"
TRANSIENT = re.compile(r"503|504|UNAVAILABLE|high demand|DEADLINE_EXCEEDED|overloaded|quá tải|sự cố", re.I)


def read() -> tuple[list[str], list[dict[str, str]]]:
    with (ROOT / "manifest.csv").open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def reset_transient() -> list[str]:
    fields, rows = read()
    reset = []
    for row in rows:
        status = row.get("ingest_status", "")
        if status == "quota" or (status.startswith("error:") and TRANSIENT.search(status)):
            row["ingest_status"] = "uploaded" if row.get("document_id") else ""
            reset.append(row["file_id"])
    if reset:
        with (ROOT / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    return reset


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rounds", type=int, default=30)
    ap.add_argument("--wait", type=float, default=60)
    args = ap.parse_args()
    cmd = ["task", "eval:ingest", "env=eval", "set=official", f"dataset={ROOT}", "--",
           "--max-inflight", "3", "--quota-wait", "1", "--max-quota-waits", "120"]
    for round_no in range(1, args.max_rounds + 1):
        reset = reset_transient()
        if reset:
            print(f"[round {round_no}] provider overloaded on {reset}: waiting {args.wait:.0f}s", flush=True)
            time.sleep(args.wait)
        print(f"[round {round_no}] {' '.join(cmd)}", flush=True)
        subprocess.run(cmd, cwd=AGENT, env=os.environ, check=False)
        _, rows = read()
        pending = [r["file_id"] for r in rows if r.get("ingest_status") not in ("done", "empty_text")]
        print(f"[round {round_no}] not done: {pending or 'none'}", flush=True)
        if not pending:
            return
        if not any(
            r.get("ingest_status") == "quota" or TRANSIENT.search(r.get("ingest_status", ""))
            for r in rows
        ):
            print("remaining rows failed for another reason - stopping, see manifest.csv", flush=True)
            return
    print("max rounds reached", flush=True)


if __name__ == "__main__":
    main()
