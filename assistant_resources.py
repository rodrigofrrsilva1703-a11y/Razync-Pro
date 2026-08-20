from __future__ import annotations

import re
from collections import Counter
from datetime import date
from typing import Iterable

import pandas as pd

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
    "Fechamento do mês em PDF",
    "Resumo DASN-SIMEI em PDF",
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
            "indicar a tela correta para executar uma tarefa",
            "localizar documentos do próprio usuário e preparar download quando solicitado",
            "gerar relatórios locais do Razync para download quando solicitado",
        ],
        "assistant_limits": [
            "não executa pagamento, transmissão fiscal ou exclusão automaticamente",
            "não acessa dados de outro usuário",
            "não envia credenciais ou documentos brutos ao provedor de IA",
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
        (("movimentação", "movimentacao", "lançamento", "lancamento", "registrar receita", "registrar despesa"), "Movimentações"),
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


def _document_matches(question: str, documents: list[dict], limit: int = 4) -> list[dict]:
    if not documents:
        return []
    text = _normalize(question)
    explicit = any(term in text for term in ("documento", "arquivo", "anexo", "anexado", "comprovante", "pdf", "guia"))
    if not explicit:
        return []

    tokens = [token for token in re.split(r"\s+", text) if len(token) >= 3 and token not in _STOPWORDS]
    scored: list[tuple[int, dict]] = []
    for item in documents:
        haystack = _normalize(" ".join([
            str(item.get("filename") or ""),
            str(item.get("category") or ""),
            str(item.get("reference_month") or ""),
        ]))
        score = sum(2 if token in _normalize(str(item.get("filename") or "")) else 1 for token in tokens if token in haystack)
        scored.append((score, item))

    if tokens and any(score > 0 for score, _ in scored):
        chosen = [item for score, item in sorted(scored, key=lambda pair: pair[0], reverse=True) if score > 0]
    else:
        chosen = list(reversed(documents))
    return chosen[:limit]


def _load_document_asset(
    *,
    user_id: int,
    meta: dict,
    access_token: str,
    refresh_token: str,
) -> dict | None:
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


def _report_assets(
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

    today = date.today()
    assets: list[dict] = []
    if "fechamento" in text:
        closing = monthly_closing(transactions, invoices, documents, das_rows, year, today.month)
        assets.append({
            "label": "Baixar fechamento do mês",
            "data": closing_summary_pdf(profile, year, today.month, closing),
            "file_name": f"fechamento_{year}_{today.month:02d}.pdf",
            "mime": "application/pdf",
        })
    elif "dasn" in text or "declaração anual" in text or "declaracao anual" in text:
        if transactions.empty:
            services = sales = 0.0
        else:
            cur = transactions[(transactions["tx_type"] == "Receita") & (transactions["tx_date"].dt.year == year)]
            services = float(cur[cur["category"].isin(["Serviços", "Serviço"])]["value"].sum())
            sales = float(cur["value"].sum()) - services
        assets.append({
            "label": "Baixar resumo DASN-SIMEI",
            "data": dasn_summary_pdf(profile, year, services, sales, bool(profile.get("has_employee", False))),
            "file_name": f"resumo_DASN_{year}.pdf",
            "mime": "application/pdf",
        })
    elif "mensal" in text or "receitas brutas" in text:
        assets.append({
            "label": "Baixar relatório mensal",
            "data": monthly_report_pdf(profile, year, _monthly_rows(transactions, year, today.month)),
            "file_name": f"relatorio_mensal_{year}_{today.month:02d}.pdf",
            "mime": "application/pdf",
        })
    else:
        assets.append({
            "label": "Baixar análise financeira",
            "data": financial_summary_pdf(profile, year, financial_analysis(transactions, year)),
            "file_name": f"analise_financeira_{year}.pdf",
            "mime": "application/pdf",
        })
    return assets


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
    downloads = _report_assets(
        question,
        profile=profile,
        transactions=transactions,
        invoices=invoices,
        das_rows=das_rows,
        documents=documents,
        year=year,
    )

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

    note = None
    if document_errors:
        note = "Alguns documentos encontrados não puderam ser preparados para download agora."
    elif any(term in _normalize(question) for term in ("documento", "arquivo", "anexo", "anexado")) and not documents:
        note = "Não há documentos salvos no Razync para esta conta."

    return {
        "route": route,
        "route_label": route_label,
        "downloads": downloads[:5],
        "note": note,
    }
