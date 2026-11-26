"""Create the access-control test accounts (2 departments x access levels 0..5) through the API.

Idempotent: an account whose code already exists is skipped.

Usage:
  python seed_accounts.py [--base http://localhost:8400/api/v1/master] [--admin SA-001] [--admin-pass PASSWORD]  (default: ADMIN_PASSWORD from .env)
Writes nothing to disk; accounts.csv in the parent folder documents the result.
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request

from local_env import env

# Set in the gateway .env (git-ignored) or the environment.
PASSWORD = env("TEST_ACCOUNT_PASSWORD")
DEPARTMENTS = {
    "CNPM": ("BM_CONG_NGHE_PHAN_MEM", "Cnpm"),
    "KT": ("BM_KE_TOAN", "KeToan"),
}
LEVELS = range(0, 6)


def call(base: str, method: str, path: str, token: str | None = None, body: dict | None = None) -> dict:
    req = urllib.request.Request(base + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=30) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return json.loads(exc.read() or b"{}") | {"_status": exc.code}


def items(payload: dict) -> list:
    data = payload.get("data")
    if isinstance(data, dict):
        return data.get("content") or data.get("items") or data.get("data") or []
    return data or []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8400/api/v1/master")
    ap.add_argument("--admin", default="SA-001")
    ap.add_argument("--admin-pass", default=None, help="default: ADMIN_PASSWORD from .env")
    args = ap.parse_args()

    token = call(args.base, "POST", "/auth/login", body={"code": args.admin, "password": args.admin_pass or env("ADMIN_PASSWORD")})["data"]["accessToken"]

    departments = {d["name"]: d["id"] for d in _flatten(items(call(args.base, "GET", "/departments/roots", token)))}
    levels = {a["level"]: a["id"] for a in items(call(args.base, "GET", "/access-levels?size=100", token))}
    roles = {r["name"]: r["id"] for r in items(call(args.base, "GET", "/rbac/roles?size=100", token))}

    for key, (dept_name, slug) in DEPARTMENTS.items():
        for level in LEVELS:
            code = f"TST-{key}-L{level}"
            body = {
                "code": code,
                "email": f"tst.{key.lower()}.l{level}@unisage.test",
                "password": PASSWORD,
                "firstName": f"L{level}",
                "lastName": f"Test {slug}",
                "roleId": roles["USER"],
                "accessLevelId": levels[level],
                "departmentAccesses": [{"departmentId": departments[dept_name], "accessLevelId": levels[level]}],
            }
            res = call(args.base, "POST", "/users", token, body)
            print(code, res.get("code"), res.get("message"))


def _flatten(nodes: list) -> list:
    out = []
    for n in nodes:
        out.append(n)
        out += _flatten(n.get("children") or [])
    return out


if __name__ == "__main__":
    main()
