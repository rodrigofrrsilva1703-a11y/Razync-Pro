from __future__ import annotations

from io import BytesIO
from numbers import Real

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _safe_text(value) -> str:
    return str(value if value is not None else "-")[:180]


def _format_value(value) -> str:
    if isinstance(value, Real) and not isinstance(value, bool):
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return _safe_text(value)


def custom_query_pdf(*, title: str, summary: str, period_label: str | None, table: pd.DataFrame | None) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("RAZYNC PRO", styles["Title"]),
        Paragraph(_safe_text(title), styles["Heading2"]),
        Spacer(1, 3 * mm),
    ]
    if period_label:
        story.append(Paragraph(f"Período: {_safe_text(period_label)}", styles["Normal"]))
        story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(_safe_text(summary), styles["BodyText"]))

    if table is not None and not table.empty:
        frame = table.head(80).copy()
        headers = [_safe_text(column) for column in frame.columns]
        rows = [headers]
        for _, row in frame.iterrows():
            rows.append([_format_value(row[column]) for column in frame.columns])
        available = 180 * mm
        width = available / max(1, len(headers))
        grid = Table(rows, repeatRows=1, colWidths=[width] * len(headers))
        grid.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1220")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story += [Spacer(1, 5 * mm), grid]

    story += [
        Spacer(1, 5 * mm),
        Paragraph(
            "Relatório gerencial gerado localmente a partir dos dados registrados no Razync Pro. Confira os registros antes de utilizar para decisões ou obrigações oficiais.",
            styles["BodyText"],
        ),
    ]
    doc.build(story)
    return buffer.getvalue()
