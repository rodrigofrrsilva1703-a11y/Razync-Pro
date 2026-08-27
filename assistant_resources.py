from __future__ import annotations

import re
from collections import Counter
from datetime import date
from typing import Iterable

import pandas as pd

from assistant_query_engine import analyze_business_question, parse_period
from assistant_reports import custom_query_pdf
from business_tools import financial_analysis, monthly_closing
from database import get_document
from reports import closing_summary_pdf, dasn_summary_pdf, financial_summary_pdf, monthly_report_pdf
from storage_service import download_document


PRODUCT_AREAS = {
    "Dashboard": "visão geral, prioridades e saúde do MEI",
    "Primeiros Passos": "configuração inicial e onboarding",
    "Meu MEI": "cadastro do negócio, atividade e dados do MEI",
    "Financeiro": "visão financeira consolidada",
    "Movimentações": "receitas, despesas e lançamentos",
    "Recorrências": "receitas e despesas recorrentes",
    "Importar Extrato": "importação de extratos bancários",
    "Conciliação": "conciliação de notas e movimentações",
    "Fluxo de Caixa": "entradas, saídas e saldo por mês",
    "Análise Financeira": "resultado, margem e despesas por categoria",
    "Fiscal": "visão fiscal consolidada do MEI",
    "DAS": "controle mensal do DAS",
    "DASN-SIMEI": "preparação da declaração anual",
    "Obrigações": "prazos e obrigações",
    "Notas Fiscais": "controle de notas fiscais",
    "Importar NFS-e": "importação de notas emitidas",
    "Documentos": "arquivos, comprovantes e documentos anexados",
    "Relatório Mensal": "relatório mensal de receitas brutas",
    "Fechamento Mensal": "checklist e fechamento do mês",
    "Clientes e Fornecedores": "cadastro de contatos comerciais",
    "Empregado": "controle de empregado do MEI",
    "Espaço do Contador": "arquivos e relatórios para o contador",
    "Central de Automações": "automações e revisões assistidas",
    "Central de Notificações": "alertas e calendário",
    "Integrações": "integrações disponíveis",
    "Backup": "backup dos dados",
    "Conta e Sistema": "conta, privacidade e sistema",
}

REPORT_TYPES = (
    "Análise financeira em PDF",
    "Relatório mensal de receitas em PDF",
    "Despesas ou receitas detalhadas em PDF/CSV",
    "Clientes ou fornecedores consolidados em PDF/CSV",
    "Faturamento diário, mensal ou anual em PDF/CSV",
    "Fechamento do mês em PDF",
    "Resumo DASN-SIMEI em PDF",
    "Relatório personalizado da consulta em PDF/CSV",
)

_STOPWORDS = {
    "a", "as", "o", "os", "um", "uma", "de", "da", "do", "das", "dos", "e", "em", "no", "na",
    "meu", "minha", "meus", "minhas", "para", "por", "favor", "quero", "preciso", "baixar", "abrir",
    "arquivo", "arquivos", "documento", "documentos", "anexo", "anexos", "anexado", "anexados", "pdf",
}


def _normalize(value: str) -> str:
    text = str(value or "").lower()
    text = re.sub(r"[^a-z0-9áàâãéêíóôõúç\-_/ .]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def build_product_context(documents: Iterable[dict], current_page: str | None = None) -> dict:
    docs = list(documents or [])
    categories = Counter(str(item.get("category") or "Outros") for item in docs)
    return {
        "current_area": current_page or None,
        "available_areas": PRODUCT_AREAS,
        "documents_available_count": len(docs),
        "document_categories": dict(categories),
        "downloadable_report_types": list(REPORT_TYPES),
        "assistant_capabilities": [
            "explicar como usar qualquer área do Razync",
            "analisar números e movimentações agregadas do negócio",
            "entender períodos naturais como mês passado, últimos meses, trimestres e intervalos entre meses",
            "comparar períodos e identificar maiores categorias, clientes ou fornecedores usando processamento local",
            "indicar a tela correta para executar uma tarefa",
            "localizar documentos do próprio usuário e preparar download quando solicitado",
            "gerar relatórios locais e relatórios personalizados da consulta quando solicitado",
            "preparar cadastros e lançamentos para confirmação do usuário",
        ],
        "assistant_limits": [
            "não executa pagamento, transmissão fiscal ou exclusão automaticamente",
            "não acessa dados de outro usuário",
            "não envia credenciais ou documentos brutos ao provedor de IA",
            "nomes de clientes e fornecedores usados em consultas específicas são processados localmente no Razync",
        ],
    }


def suggest_route(question: str) -> tuple[str | None, str | None]:
    text = _normalize(question)
    rules = (
        (("primeiros passos", "configurar razync", "começar no sistema"), "Primeiros Passos"),
        (("meu mei", "cadastro do mei", "atividade principal", "dados do mei", "cnpj"), "Meu MEI"),
        (("importar extrato", "extrato bancário", "extrato banco"), "Importar Extrato"),
        (("concilia", "conciliar", "vincular nota"), "Conciliação"),
        (("fluxo de caixa", "saldo acumulado"), "Fluxo de Caixa"),
        (("análise financeira", "analise financeira", "margem", "despesas por categoria"), "Análise Financeira"),
        (("recorrência", "recorrencia", "recorrente"), "Recorrências"),
        (("movimentação", "movimentacao", "lançamento", "lancamento", "registrar receita", "registrar despesa", "cadastrar receita", "cadastrar despesa", "cadastro uma receita", "cadastro uma despesa", "cadastro uma nova receita", "cadastro uma nova despesa", "nova receita", "nova despesa"), "Movimentações"),
        (("financeiro", "resultado financeiro"), "Financeiro"),
        (("importar nfs", "importar nota"), "Importar NFS-e"),
        (("nota fiscal", "nfse", "nfs-e"), "Notas Fiscais"),
        (("dasn", "declaração anual", "declaracao anual"), "DASN-SIMEI"),
        (("das mensal", "guia das", "pagar das", "das atrasado"), "DAS"),
        (("obrigação", "obrigacao", "prazo fiscal"), "Obrigações"),
        (("fechamento",), "Fechamento Mensal"),
        (("relatório mensal", "relatorio mensal"), "Relatório Mensal"),
        (("documento", "arquivo anexado", "anexo", "comprovante"), "Documentos"),
        (("contador",), "Espaço do Contador"),
        (("automação", "automacao"), "Central de Automações"),
        (("notificação", "notificacao", "alerta", "calendário", "calendario"), "Central de Notificações"),
        (("cliente", "fornecedor", "contato"), "Clientes e Fornecedores"),
        (("empregado", "funcionário", "funcionario"), "Empregado"),
        (("integração", "integracao"), "Integrações"),
        (("backup",), "Backup"),
        (("conta", "privacidade", "segurança da conta", "seguranca da conta"), "Conta e Sistema"),
    )
    for terms, route in rules:
        if any(term in text for term in terms):
            return route, f"Abrir {route}"
    return None, None


def should_prepare_resources(question: str) -> bool:
    """Avoid report/document work when the answer does not need a system resource."""
    route, _ = suggest_route(question)
    if route:
        return True
    text = _normalize(question)
    return any(
        term in text
        for term in (
            "relatório", "relatorio", "baixar", "download", "csv", "excel",
            "pdf", "arquivo", "documento", "anexo", "comprovante", "fechamento",
        )
    )


def _monthly_rows(transactions: pd.DataFrame, year: int, month: int) -> list[dict]:
    if transactions.empty:
        return [{"month": month, "month_name": f"{month:02d}", "with_doc": 0.0, "without_doc": 0.0, "services": 0.0, "sales": 0.0, "total": 0.0}]
    cur = transactions[
        (transactions["tx_type"] == "Receita")
        & (transactions["tx_date"].dt.year == year)
        & (transactions["tx_date"].dt.month == month)
    ]
    services = float(cur[cur["category"].isin(["Serviços", "Serviço"])]["value"].sum()) if not cur.empty else 0.0
    total = float(cur["value"].sum()) if not cur.empty else 0.0
    sales = total - services
    if cur.empty:
        with_doc = without_doc = 0.0
    else:
        has_doc = cur["document_number"].fillna("").astype(str).str.strip().ne("")
        with_doc = float(cur.loc[has_doc, "value"].sum())
        without_doc = total - with_doc
    return [{
        "month": month,
        "month_name": f"{month:02d}",
        "with_doc": with_doc,
        "without_doc": without_doc,
        "services": services,
        "sales": sales,
        "total": total,
    }]


def _monthly_rows_for_period(transactions: pd.DataFrame, start: date, end: date) -> list[dict]:
    rows: list[dict] = []
    cursor = date(start.year, start.month, 1)
    while cursor <= end:
        rows.extend(_monthly_rows(transactions, cursor.year, cursor.month))
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    return rows


def _document_matches(question: str, documents: list[dict], limit: int = 6) -> list[dict]:
    if not documents:
        return []
    text = _normalize(question)
    explicit = any(term in text for term in ("documento", "arquivo", "anexo", "anexado", "comprovante", "pdf", "guia", "nota"))
    if not explicit:
        return []

    tokens = [token for token in re.split(r"\s+", text) if len(token) >= 3 and token not in _STOPWORDS]
    period = parse_period(question)
    period_keys = set()
    cursor = date(period.start.year, period.start.month, 1)
    while cursor <= period.end:
        period_keys.add(f"{cursor.year}-{cursor.month:02d}")
        cursor = date(cursor.year + 1, 1, 1) if cursor.month == 12 else date(cursor.year, cursor.month + 1, 1)

    scored: list[tuple[int, dict]] = []
    for item in documents:
        filename = _normalize(str(item.get("filename") or ""))
        category = _normalize(str(item.get("category") or ""))
        reference = str(item.get("reference_month") or "").strip()
        haystack = f"{filename} {category} {reference}"
        score = sum(3 if token in filename else 2 if token in category else 1 for token in tokens if token in haystack)
        if reference and reference in period_keys and any(marker in text for marker in ("mes", "janeiro", "fevereiro", "março", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro", "202")):
            score += 4
        scored.append((score, item))

    if tokens and any(score > 0 for score, _ in scored):
        chosen = [item for score, item in sorted(scored, key=lambda pair: pair[0], reverse=True) if score > 0]
    else:
        chosen = list(reversed(documents))
    return chosen[:limit]


def _load_document_asset(*, user_id: int, meta: dict, access_token: str, refresh_token: str) -> dict | None:
    document = get_document(user_id, int(meta["id"]))
    if not document:
        return None
    if document.get("storage_path"):
        content = download_document(access_token, refresh_token, document["storage_path"])
    else:
        content = document.get("content") or b""
    if not content or len(content) > 25 * 1024 * 1024:
        return None
    return {
        "label": f"Baixar {document.get('filename') or 'documento'}",
        "data": content,
        "file_name": str(document.get("filename") or "documento"),
        "mime": str(document.get("mime_type") or "application/octet-stream"),
    }


def _standard_report_assets(
    question: str,
    *,
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    documents: list[dict],
    year: int,
) -> list[dict]:
    text = _normalize(question)
    wants_report = any(term in text for term in ("relatório", "relatorio", "pdf", "fechamento", "dasn")) and any(
        term in text for term in ("baixar", "download", "gerar", "quero", "preciso", "me dê", "me de", "traz", "mande", "pdf", "relatório", "relatorio", "fechamento", "dasn")
    )
    if not wants_report:
        return []

    period = parse_period(question, default_year=year)
    report_year = period.end.year
    report_month = period.end.month
    assets: list[dict] = []
    if "fechamento" in text:
        closing = monthly_closing(transactions, invoices, documents, das_rows, report_year, report_month)
        assets.append({
            "label": f"Baixar fechamento {report_month:02d}/{report_year}",
            "data": closing_summary_pdf(profile, report_year, report_month, closing),
            "file_name": f"fechamento_{report_year}_{report_month:02d}.pdf",
            "mime": "application/pdf",
        })
    elif "dasn" in text or "declaração anual" in text or "declaracao anual" in text:
        if transactions.empty:
            services = sales = 0.0
        else:
            cur = transactions[(transactions["tx_type"] == "Receita") & (transactions["tx_date"].dt.year == report_year)]
            services = float(cur[cur["category"].isin(["Serviços", "Serviço"])]["value"].sum())
            sales = float(cur["value"].sum()) - services
        assets.append({
            "label": f"Baixar resumo DASN-SIMEI {report_year}",
            "data": dasn_summary_pdf(profile, report_year, services, sales, bool(profile.get("has_employee", False))),
            "file_name": f"resumo_DASN_{report_year}.pdf",
            "mime": "application/pdf",
        })
    elif "mensal" in text or "receitas brutas" in text:
        rows = _monthly_rows_for_period(transactions, period.start, period.end)
        assets.append({
            "label": f"Baixar relatório de receitas · {period.label}",
            "data": monthly_report_pdf(profile, report_year, rows),
            "file_name": f"relatorio_receitas_{period.start:%Y%m}_{period.end:%Y%m}.pdf",
            "mime": "application/pdf",
        })
    elif "financeir" in text or "análise" in text or "analise" in text:
        assets.append({
            "label": f"Baixar análise financeira {report_year}",
            "data": financial_summary_pdf(profile, report_year, financial_analysis(transactions, report_year)),
            "file_name": f"analise_financeira_{report_year}.pdf",
            "mime": "application/pdf",
        })
    return assets


def _query_assets(question: str, transactions: pd.DataFrame, year: int) -> tuple[list[dict], str | None]:
    result = analyze_business_question(question, transactions, default_year=year)
    if not result.handled:
        return [], None

    assets: list[dict] = []
    csv_data = result.csv_bytes()
    text = _normalize(question)
    wants_file = any(term in text for term in ("relatório", "relatorio", "baixar", "download", "csv", "excel", "pdf", "arquivo"))
    report_names = {
        "financial_report": ("Relatório financeiro", "relatorio_financeiro_razync"),
        "transaction_report": ("Relatório de movimentações", "relatorio_movimentacoes_razync"),
        "counterparty_report": ("Relatório de clientes e fornecedores", "relatorio_clientes_fornecedores_razync"),
        "revenue_timeline": ("Relatório de faturamento", "relatorio_faturamento_razync"),
    }
    report_title, report_file = report_names.get(result.kind, ("Relatório personalizado do Assistente Razync", "relatorio_personalizado_razync"))
    if csv_data and wants_file:
        assets.append({
            "label": "Baixar dados do relatório em CSV",
            "data": csv_data,
            "file_name": f"{report_file}.csv",
            "mime": "text/csv",
        })
    if wants_file:
        try:
            pdf = custom_query_pdf(
                title=report_title,
                summary=result.summary,
                period_label=result.period.label if result.period else None,
                table=result.table,
            )
        except Exception:
            pdf = b""
        if pdf:
            assets.append({
                "label": "Baixar relatório em PDF",
                "data": pdf,
                "file_name": f"{report_file}.pdf",
                "mime": "application/pdf",
            })
    return assets, result.summary


def build_resource_bundle(
    question: str,
    *,
    user_id: int,
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    obligations: list[dict],
    documents: list[dict],
    year: int,
    access_token: str = "",
    refresh_token: str = "",
) -> dict:
    route, route_label = suggest_route(question)
    downloads = _standard_report_assets(
        question,
        profile=profile,
        transactions=transactions,
        invoices=invoices,
        das_rows=das_rows,
        documents=documents,
        year=year,
    )

    query_downloads, query_summary = _query_assets(question, transactions, year)
    downloads.extend(query_downloads)

    document_errors = 0
    for meta in _document_matches(question, documents):
        try:
            asset = _load_document_asset(
                user_id=user_id,
                meta=meta,
                access_token=access_token,
                refresh_token=refresh_token,
            )
        except Exception:
            asset = None
        if asset:
            downloads.append(asset)
        else:
            document_errors += 1

    notes: list[str] = []
    if query_summary:
        notes.append(query_summary)
    if document_errors:
        notes.append("Alguns documentos encontrados não puderam ser preparados para download agora.")
    elif any(term in _normalize(question) for term in ("documento", "arquivo", "anexo", "anexado")) and not documents:
        notes.append("Não há documentos salvos no Razync para esta conta.")

    return {
        "route": route,
        "route_label": route_label,
        "downloads": downloads[:8],
        "note": "\n\n".join(notes) if notes else None,
    }
