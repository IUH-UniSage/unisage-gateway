"""Build Bo_cau_hoi_phan_quyen.xlsx in the layout of Bo_cau_hoi_danh_gia_RAG.xlsx,
sheet "Official - Đầy đủ" (same 18 columns, same styling), plus one extra column
"Tài khoản test" naming the account to log in with for that row.

Scenarios per question (same vocabulary as the original "Người hỏi" column):
  public doc  : Khách                                   -> Có
  private doc : Cùng đơn vị, đúng cấp     TST-<D>-L<l>   -> Có
                Cùng đơn vị, thấp hơn 1 cấp TST-<D>-L<l-1> -> Không   (l = 0: Khách -> Không)
                Khác đơn vị, cấp cao nhất TST-<other>-L5 -> Không
                Toàn quyền                SA-001         -> Có

Usage: <python with openpyxl> tools/build_xlsx.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Bo_cau_hoi_phan_quyen.xlsx"
HEADERS = [
    "STT", "ID", "Nhóm câu hỏi", "Câu hỏi (chuẩn)", "Câu hỏi kiểu người dùng", "Đáp án kỳ vọng",
    "Bằng chứng trong tài liệu", "Tài liệu nguồn", "Đơn vị", "Tài liệu công khai", "Cấp truy cập",
    "Người hỏi", "Kỳ vọng thấy tài liệu", "Nguồn câu hỏi", "Mức độ thực tế", "Nhận xét",
    "Trùng ý với", "Nhóm trùng (ID đại diện)", "Tài khoản test",
]
WIDTHS = [6, 9, 13, 55, 42, 55, 45, 40, 22, 10, 9, 26, 11, 14, 12, 40, 14, 14, 16]
UNIT_DISPLAY = {
    "BM_CONG_NGHE_PHAN_MEM": "Bộ môn Công nghệ Phần mềm",
    "BM_KE_TOAN": "Bộ môn Kế toán",
    "phong giao vu": "Phòng Giáo vụ",
    "PHONG_CTSV": "Phòng Công tác Sinh viên",
    "PHONG_QLKH_HTQT": "Phòng Quản lý Khoa học - Hợp tác Quốc tế",
}
OTHER = {"CNPM": "KT", "KT": "CNPM"}
SOURCE = "Bộ phân quyền"


def scenarios(doc: dict) -> list[tuple[str, str, str]]:
    """(Người hỏi, tài khoản, kỳ vọng) for one document."""
    if doc["is_public"]:
        return [("Khách", "GUEST", "Có")]
    d, level = doc["dept"], doc["min_access_level"]
    lower = (
        ("Cùng đơn vị, thấp hơn 1 cấp", f"TST-{d}-L{level - 1}", "Không")
        if level > 0
        else ("Khách", "GUEST", "Không")
    )
    return [
        ("Cùng đơn vị, đúng cấp", f"TST-{d}-L{level}", "Có"),
        lower,
        ("Khác đơn vị, cấp cao nhất", f"TST-{OTHER[d]}-L5", "Không"),
        ("Toàn quyền", "SA-001", "Có"),
    ]


def style_sheet(ws, n_rows: int) -> None:
    thin = Side(style="thin", color="FFBFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    head_fill = PatternFill("solid", fgColor="FF1F4E78")
    for i, width in enumerate(WIDTHS[: ws.max_column], 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = width
    for cell in ws[1]:
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFFFF")
        cell.fill = head_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    ws.row_dimensions[1].height = 33.75
    for row in ws.iter_rows(min_row=2, max_row=n_rows + 1):
        for cell in row:
            cell.font = Font(name="Calibri", size=10)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = ws.dimensions


def main() -> None:
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    docs = {d["doc_id"]: d for d in catalog["documents"]}
    with (ROOT / "manifest.csv").open(encoding="utf-8") as f:
        manifest = {r["file_id"]: r for r in csv.DictReader(f)}
    informal = json.loads((ROOT / "user_questions.json").read_text(encoding="utf-8"))
    questions = [json.loads(line) for line in (ROOT / "questions.jsonl").open(encoding="utf-8")]

    wb = Workbook()
    full = wb.active
    full.title = "Phân quyền - Đầy đủ"
    dedup = wb.create_sheet("Phân quyền - Lọc trùng")
    full.append(HEADERS)
    dedup.append(HEADERS)

    n = 0
    for q in questions:
        doc = docs[q["doc_id"]]
        row_m = manifest[q["doc_id"]]
        group_id = f"ac{n + 1:04d}"
        base = {
            "group": "Thông thường" if doc["is_public"] else "Phân quyền",
            "source": f"{q['doc_id']} - {row_m['title']}",
            "unit": UNIT_DISPLAY[row_m["department_id"]],
            "public": "Có" if doc["is_public"] else "Không",
            "level": None if doc["is_public"] else str(doc["min_access_level"]),
        }
        for j, (asker, account, expect) in enumerate(scenarios(doc)):
            n += 1
            values = [
                str(n), f"ac{n:04d}", base["group"], q["question"], informal[q["id"]],
                q["expected_answer"], q["evidence"], base["source"], base["unit"], base["public"],
                base["level"], asker, expect, SOURCE, "Thực tế", None, None, group_id, account,
            ]
            full.append(values)
            if j == 0:
                dedup.append([str(dedup.max_row)] + values[1:])

    accounts = wb.create_sheet("Tài khoản test")
    accounts.append(["Tài khoản", "Mật khẩu", "Vai trò", "Đơn vị", "Cấp truy cập", "Thấy tài liệu private"])
    accounts.append(["GUEST", "(không đăng nhập)", "Khách", None, None, "Không (chỉ P1–P8)"])
    accounts.append(["SA-001", "ADMIN_PASSWORD (.env)", "SUPER_ADMIN", "Tất cả", "Toàn quyền", "Tất cả A0–A5, B0–B5"])
    for key, prefix in (("CNPM", "A"), ("KT", "B")):
        unit = UNIT_DISPLAY[catalog["departments"][key]["name"]]
        for level in range(6):
            accounts.append([f"TST-{key}-L{level}", "TEST_ACCOUNT_PASSWORD (.env)", "USER", unit, level,
                             ", ".join(f"{prefix}{i}" for i in range(level + 1))])

    docs_ws = wb.create_sheet("Tài liệu")
    docs_ws.append(["Mã", "Tên file", "Tiêu đề", "Đơn vị", "Công khai", "Cấp tối thiểu",
                    "document_id", "Trạng thái ingest"])
    for doc_id, r in manifest.items():
        docs_ws.append([doc_id, r["file_name"], r["title"], UNIT_DISPLAY[r["department_id"]],
                        "Có" if r["is_public"] == "true" else "Không", r["access_level"] or None,
                        r["document_id"] or None, r["ingest_status"] or None])

    style_sheet(full, full.max_row - 1)
    style_sheet(dedup, dedup.max_row - 1)
    for ws, widths in ((accounts, [16, 18, 14, 28, 12, 30]), (docs_ws, [6, 50, 60, 28, 10, 11, 38, 14])):
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = w
        for cell in ws[1]:
            cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFFFF")
            cell.fill = PatternFill("solid", fgColor="FF1F4E78")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.font = Font(name="Calibri", size=10)
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        ws.freeze_panes = "A2"

    wb.save(OUT)
    print(f"{full.max_row - 1} rows (full), {dedup.max_row - 1} rows (dedup) -> {OUT}")


if __name__ == "__main__":
    main()
