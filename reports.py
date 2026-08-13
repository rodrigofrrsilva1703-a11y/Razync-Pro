from __future__ import annotations

from io import BytesIO
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _doc_buffer(title: str):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("RazyncTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=18, leading=22)
    return buffer, doc, styles, title_style


def monthly_report_pdf(profile: dict, year: int, rows: Iterable[dict]) -> bytes:
    buffer, doc, styles, title_style = _doc_buffer("Relatório Mensal de Receitas Brutas")
    story = [Paragraph("RAZYNC PRO", title_style), Paragraph("Relatório Mensal de Receitas Brutas - MEI", styles["Heading2"]), Spacer(1, 5*mm)]
    story.append(Paragraph(f"Empresa: {profile.get('business_name') or profile.get('trade_name') or '-'}", styles["Normal"]))
    story.append(Paragraph(f"CNPJ: {profile.get('cnpj') or '-'} | Ano: {year}", styles["Normal"]))
    story.append(Spacer(1, 4*mm))
    data = [["Mês", "Com documento", "Sem documento", "Serviços", "Vendas", "Total"]]
    total = 0.0
    for row in rows:
        total += float(row.get("total", 0))
        data.append([
            str(row.get("month_name", "")), _brl(float(row.get("with_doc", 0))), _brl(float(row.get("without_doc", 0))),
            _brl(float(row.get("services", 0))), _brl(float(row.get("sales", 0))), _brl(float(row.get("total", 0)))
        ])
    data.append(["TOTAL", "", "", "", "", _brl(total)])
    table = Table(data, repeatRows=1, colWidths=[29*mm, 31*mm, 31*mm, 29*mm, 29*mm, 31*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0B1220")), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,-1), 8),
        ("GRID", (0,0), (-1,-1), .3, colors.HexColor("#94A3B8")), ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#E2E8F0")), ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [table, Spacer(1, 5*mm), Paragraph("Documento de apoio gerado a partir dos dados cadastrados no Razync Pro. Confira os valores antes de utilizar para cumprimento de obrigações oficiais.", styles["BodyText"])]
    doc.build(story)
    return buffer.getvalue()


def dasn_summary_pdf(profile: dict, year: int, services: float, sales: float, employee: bool) -> bytes:
    buffer, doc, styles, title_style = _doc_buffer("Resumo DASN-SIMEI")
    total = services + sales
    story = [Paragraph("RAZYNC PRO", title_style), Paragraph("Resumo para conferência da DASN-SIMEI", styles["Heading2"]), Spacer(1, 5*mm)]
    story += [
        Paragraph(f"Empresa: {profile.get('business_name') or profile.get('trade_name') or '-'}", styles["Normal"]),
        Paragraph(f"CNPJ: {profile.get('cnpj') or '-'}", styles["Normal"]),
        Paragraph(f"Ano-calendário: {year}", styles["Normal"]), Spacer(1, 4*mm)
    ]
    data = [
        ["Informação", "Valor"],
        ["Receita de serviços", _brl(services)],
        ["Receita de comércio/mercadorias", _brl(sales)],
        ["Receita bruta total", _brl(total)],
        ["Teve empregado no período", "Sim" if employee else "Não"],
    ]
    table = Table(data, colWidths=[95*mm, 65*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0B1220")), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#94A3B8")),
        ("ALIGN", (1,1), (1,-1), "RIGHT"), ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story += [table, Spacer(1, 5*mm), Paragraph("Este resumo não envia a declaração. Ele serve para conferência dos dados antes do preenchimento no serviço oficial.", styles["BodyText"])]
    doc.build(story)
    return buffer.getvalue()
