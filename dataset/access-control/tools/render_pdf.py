"""Render a document spec (JSON) into an A4 PDF styled like a Vietnamese administrative document.

Usage: python render_pdf.py <spec.json> [<spec.json> ...] --out <dir>

Spec format:
{
  "doc_id": "A3",
  "file_name": "A3_ke-hoach-nckh-bo-mon-cnpm-2026.pdf",
  "title": "KẾ HOẠCH ...",
  "parent_org": "TRƯỜNG ĐẠI HỌC CÔNG NGHIỆP TP. HỒ CHÍ MINH",
  "issuer": "KHOA CÔNG NGHỆ THÔNG TIN",
  "number": "Số: 2471/KH-CNTT",
  "place_date": "TP. Hồ Chí Minh, ngày 14 tháng 8 năm 2026",
  "confidential": "TÀI LIỆU NỘI BỘ – CẤP ĐỘ 3" | null,
  "blocks": [
    {"type": "h1", "text": "..."}, {"type": "h2", "text": "..."},
    {"type": "p", "text": "..."}, {"type": "bullets", "items": ["..."]},
    {"type": "table", "header": ["..."], "rows": [["..."]], "widths": [0.1, 0.5, 0.4]}
  ],
  "signature": {"title": "TRƯỞNG KHOA", "name": "..."},
  "recipients": ["..."],
  "questions": [{"question": "...", "expected_answer": "...", "evidence": "..."}]
}
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

FONT_DIR = Path("/usr/share/fonts/truetype/liberation")
pdfmetrics.registerFont(TTFont("Serif", FONT_DIR / "LiberationSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Bold", FONT_DIR / "LiberationSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Italic", FONT_DIR / "LiberationSerif-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Serif-BoldItalic", FONT_DIR / "LiberationSerif-BoldItalic.ttf"))
pdfmetrics.registerFontFamily(
    "Serif", normal="Serif", bold="Serif-Bold", italic="Serif-Italic", boldItalic="Serif-BoldItalic"
)

BASE = ParagraphStyle("base", fontName="Serif", fontSize=12.5, leading=18.5, alignment=TA_JUSTIFY)
STYLES = {
    "p": ParagraphStyle("p", parent=BASE, firstLineIndent=10 * mm, spaceAfter=5),
    "h1": ParagraphStyle("h1", parent=BASE, fontName="Serif-Bold", fontSize=13.5, spaceBefore=10, spaceAfter=6),
    "h2": ParagraphStyle("h2", parent=BASE, fontName="Serif-Bold", fontSize=12.5, spaceBefore=6, spaceAfter=4),
    "title": ParagraphStyle("title", parent=BASE, fontName="Serif-Bold", fontSize=15, leading=21, alignment=TA_CENTER),
    "center": ParagraphStyle("center", parent=BASE, alignment=TA_CENTER),
    "center_b": ParagraphStyle("center_b", parent=BASE, fontName="Serif-Bold", alignment=TA_CENTER),
    "center_i": ParagraphStyle("center_i", parent=BASE, fontName="Serif-Italic", alignment=TA_CENTER),
    "cell": ParagraphStyle("cell", parent=BASE, fontSize=11, leading=14.5, alignment=0),
    "cell_b": ParagraphStyle("cell_b", parent=BASE, fontName="Serif-Bold", fontSize=11, leading=14.5, alignment=TA_CENTER),
    "small": ParagraphStyle("small", parent=BASE, fontSize=11, leading=15, alignment=0),
    "conf": ParagraphStyle("conf", parent=BASE, fontName="Serif-Bold", fontSize=11, textColor=colors.HexColor("#b00020"), alignment=TA_CENTER),
}


def esc(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def header(spec: dict, width: float) -> list:
    left = [
        Paragraph(esc(spec.get("parent_org", "")), STYLES["center"]),
        Paragraph(esc(spec.get("issuer", "")), STYLES["center_b"]),
        Paragraph(esc(spec.get("number", "")), STYLES["center"]),
    ]
    right = [
        Paragraph("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", STYLES["center_b"]),
        Paragraph("Độc lập – Tự do – Hạnh phúc", STYLES["center_b"]),
        Paragraph(esc(spec.get("place_date", "")), STYLES["center_i"]),
    ]
    table = Table([[left, right]], colWidths=[width * 0.44, width * 0.56])
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    out: list = [table, Spacer(1, 8)]
    if spec.get("confidential"):
        out += [Paragraph(esc(spec["confidential"]), STYLES["conf"]), Spacer(1, 4)]
    out += [Paragraph(esc(spec["title"]), STYLES["title"]), Spacer(1, 10)]
    return out


def block(b: dict, width: float) -> list:
    kind = b["type"]
    if kind in ("p", "h1", "h2"):
        return [Paragraph(esc(b["text"]), STYLES[kind])]
    if kind == "bullets":
        items = [ListItem(Paragraph(esc(t), STYLES["small"]), leftIndent=14) for t in b["items"]]
        return [ListFlowable(items, bulletType="bullet", start="–", leftIndent=14), Spacer(1, 4)]
    if kind == "table":
        header_row = [Paragraph(esc(c), STYLES["cell_b"]) for c in b["header"]]
        rows = [[Paragraph(esc(c), STYLES["cell"]) for c in row] for row in b["rows"]]
        n = len(b["header"])
        widths = b.get("widths") or [1 / n] * n
        total = sum(widths)
        table = Table([header_row] + rows, colWidths=[width * w / total for w in widths], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        caption = [Paragraph(esc(b["caption"]), STYLES["center_i"])] if b.get("caption") else []
        return [Spacer(1, 4), *caption, table, Spacer(1, 8)]
    raise ValueError(f"unknown block type {kind}")


def footer(spec: dict, width: float) -> list:
    sig = spec.get("signature") or {}
    recipients = spec.get("recipients") or []
    left = [Paragraph("<b><i>Nơi nhận:</i></b>", STYLES["small"])] + [
        Paragraph("– " + esc(r), STYLES["small"]) for r in recipients
    ]
    right = [
        Paragraph(esc(sig.get("title", "")), STYLES["center_b"]),
        Paragraph("<i>(Đã ký)</i>", STYLES["center"]),
        Spacer(1, 18),
        Paragraph(esc(sig.get("name", "")), STYLES["center_b"]),
    ]
    table = Table([[left, right]], colWidths=[width * 0.5, width * 0.5])
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return [Spacer(1, 14), KeepTogether(table)]


def render(spec: dict, out_dir: Path) -> Path:
    path = out_dir / spec["file_name"]
    doc = SimpleDocTemplate(
        str(path), pagesize=A4, leftMargin=30 * mm, rightMargin=20 * mm, topMargin=20 * mm, bottomMargin=20 * mm,
        title=spec["title"], author=spec.get("issuer", ""),
    )
    width = doc.width
    story = header(spec, width)
    for b in spec["blocks"]:
        story += block(b, width)
    story += footer(spec, width)

    def page_number(canvas, d):
        canvas.setFont("Serif", 10)
        canvas.drawCentredString(A4[0] / 2, 10 * mm, f"Trang {d.page}")

    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for s in args.specs:
        spec = json.loads(Path(s).read_text(encoding="utf-8"))
        print(render(spec, out))


if __name__ == "__main__":
    main()
