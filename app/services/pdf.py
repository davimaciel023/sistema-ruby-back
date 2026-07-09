"""Geração dos PDFs personalizados de repertório (RF25), com a logo da banda."""

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.repertoire import Repertoire

RUBY = colors.HexColor("#b00020")
INK = colors.HexColor("#222222")
MUTED = colors.HexColor("#666666")

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"

TITLE_STYLE = ParagraphStyle(
    "title", fontName="Helvetica-Bold", fontSize=22, textColor=RUBY, spaceAfter=8, leading=26
)
BLOCK_STYLE = ParagraphStyle(
    "block", fontName="Helvetica-Bold", fontSize=15, textColor=RUBY, spaceAfter=2
)
SUB_STYLE = ParagraphStyle(
    "sub", fontName="Helvetica", fontSize=11, textColor=MUTED, leading=14
)
CELL_STYLE = ParagraphStyle("cell", fontName="Helvetica", fontSize=10.5, textColor=INK)
FOOTER_STYLE = ParagraphStyle(
    "footer", fontName="Helvetica-Oblique", fontSize=9, textColor=MUTED, alignment=1
)


def _fmt_duration(seconds: int) -> str:
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}min"
    return f"{minutes}min {secs:02d}s"


def _logo_elements() -> list:
    if not LOGO_PATH.exists():
        return []
    logo = Image(str(LOGO_PATH))
    ratio = logo.imageWidth / logo.imageHeight
    logo.drawHeight = 28 * mm
    logo.drawWidth = 28 * mm * ratio
    logo.hAlign = "CENTER"
    return [logo, Spacer(1, 10 * mm)]


def _song_table(rep: Repertoire, start_position: int = 1) -> Table:
    header = ["#", "Música", "Tom", "Cifra", "BPM", "Duração"]
    rows = [header]
    for offset, item in enumerate(rep.items):
        key = item.performed_key or item.song.key
        bpm = str(item.song.bpm) if item.song.bpm else "—"
        rows.append(
            [
                str(start_position + offset),
                Paragraph(item.song.title, CELL_STYLE),
                key,
                Paragraph(item.song.chords or "—", CELL_STYLE),
                bpm,
                _fmt_duration(item.song.duration_seconds),
            ]
        )

    table = Table(
        rows, colWidths=[10 * mm, 50 * mm, 14 * mm, 48 * mm, 14 * mm, 28 * mm], repeatRows=1
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), RUBY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10.5),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (2, 0), (2, -1), "CENTER"),
                ("ALIGN", (4, 0), (5, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fdf3f4")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e6c9cd")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _build_doc(buffer: BytesIO, title: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        title=title,
    )


def build_repertoire_pdf(rep: Repertoire, total_seconds: int) -> bytes:
    buffer = BytesIO()
    doc = _build_doc(buffer, f"Repertório — {rep.name}")

    elements = _logo_elements()
    elements.append(Paragraph(f"Repertório — {rep.name}", TITLE_STYLE))
    meta = []
    if rep.date:
        meta.append(rep.date.strftime("%d/%m/%Y"))
    meta.append(f"{len(rep.items)} músicas")
    meta.append(f"Tempo estimado de show: {_fmt_duration(total_seconds)}")
    elements.append(Paragraph(" • ".join(meta), SUB_STYLE))
    if rep.notes:
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph(rep.notes, SUB_STYLE))
    elements.append(Spacer(1, 8 * mm))
    elements.append(_song_table(rep))
    elements.append(Spacer(1, 8 * mm))
    elements.append(Paragraph("Forró Ruby — gerado pelo sistema da banda", FOOTER_STYLE))

    doc.build(elements)
    return buffer.getvalue()


def build_combined_pdf(blocks: list[tuple[Repertoire, int]], grand_total_seconds: int) -> bytes:
    """PDF único juntando vários repertórios (blocos), com tempo total do show."""
    buffer = BytesIO()
    doc = _build_doc(buffer, "Forró Ruby — Repertório do Show")

    total_songs = sum(len(rep.items) for rep, _ in blocks)
    elements = _logo_elements()
    elements.append(Paragraph("Repertório do Show", TITLE_STYLE))
    meta = [
        f"{len(blocks)} blocos",
        f"{total_songs} músicas",
        f"Tempo estimado de show: {_fmt_duration(grand_total_seconds)}",
    ]
    elements.append(Paragraph(" • ".join(meta), SUB_STYLE))
    elements.append(Spacer(1, 8 * mm))

    position = 1
    for rep, total_seconds in blocks:
        block_meta = [f"{len(rep.items)} músicas", _fmt_duration(total_seconds)]
        if rep.date:
            block_meta.insert(0, rep.date.strftime("%d/%m/%Y"))
        elements.append(Paragraph(rep.name, BLOCK_STYLE))
        elements.append(Paragraph(" • ".join(block_meta), SUB_STYLE))
        elements.append(Spacer(1, 3 * mm))
        elements.append(_song_table(rep, start_position=position))
        elements.append(Spacer(1, 8 * mm))
        position += len(rep.items)

    elements.append(Paragraph("Forró Ruby — gerado pelo sistema da banda", FOOTER_STYLE))
    doc.build(elements)
    return buffer.getvalue()
