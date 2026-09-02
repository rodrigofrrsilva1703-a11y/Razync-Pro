from __future__ import annotations

import re
import unicodedata

import streamlit as st

from document_catalog import document_ai_prompt, search_documents
from navigation_config import SIDEBAR_ICONS


COMMANDS = (
    ("Dashboard", "Início", "inicio dashboard resumo hoje mei"),
    ("Movimentações", "Nova movimentação", "nova receita despesa entrada saida lançamento"),
    ("Financeiro", "Financeiro", "financeiro dinheiro receitas despesas caixa resultado"),
    ("Importar Extrato", "Importar extrato", "banco extrato ofx csv importar"),
    ("Conciliação", "Conciliação financeira", "conciliar notas lançamentos duplicidade"),
    ("Fluxo de Caixa", "Fluxo de caixa", "fluxo caixa saldo previsão"),
    ("Análise Financeira", "Análise financeira", "analise margem categorias faturamento"),
    ("Fiscal", "Fiscal MEI", "fiscal imposto mei das notas obrigação"),
    ("DAS", "DAS mensal", "das guia imposto pagamento competência"),
    ("Notas Fiscais", "Notas fiscais", "nfse nota fiscal clientes faturamento"),
    ("Importar NFS-e", "Importar NFS-e", "nfse xml importar nota"),
    ("Obrigações", "Prazos e obrigações", "prazo vencimento obrigação calendario"),
    ("DASN-SIMEI", "Declaração anual", "dasn simei declaração anual"),
    ("Fechamento Mensal", "Fechamento mensal", "fechamento checklist mês documentos"),
    ("Relatório Mensal", "Relatório mensal", "relatorio faturamento pdf mensal"),
    ("Documentos", "Documentos", "arquivo pdf documento comprovante anexo"),
    ("Clientes e Fornecedores", "Clientes e fornecedores", "cliente fornecedor contato cadastro"),
    ("Empregado", "Empregado", "funcionario empregado folha"),
    ("Produtividade", "Produtividade", "automação produtividade alertas rotina"),
    ("Central de Automações", "Automações", "automacao recorrencia rotina"),
    ("Central de Notificações", "Alertas e calendário", "alerta notificação calendário vencimento"),
    ("Assistente Razync", "Perguntar à IA", "ia assistente ajuda pergunta razync"),
    ("Meu MEI", "Dados do MEI", "cnpj atividade cadastro empresa mei"),
    ("Conta e Sistema", "Conta e sistema", "conta preferencia sistema"),
    ("Histórico de Atividades", "Histórico de atividades", "historico auditoria ações"),
    ("Backup", "Backup dos dados", "backup exportar baixar dados"),
)

QUICK_ACTIONS = (
    ("Movimentações", "Nova movimentação"),
    ("Documentos", "Abrir documentos"),
    ("DAS", "Ver DAS"),
    ("Assistente Razync", "Perguntar à IA"),
)


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text.lower()).strip()


def search_commands(query: str, *, limit: int = 7) -> list[tuple[str, str, str]]:
    needle = _normalize(query)
    if not needle:
        return []
    terms = needle.split()
    scored: list[tuple[int, tuple[str, str, str]]] = []
    for page, label, keywords in COMMANDS:
        haystack = _normalize(f"{page} {label} {keywords}")
        if not all(term in haystack for term in terms):
            continue
        score = 0
        normalized_label = _normalize(label)
        normalized_page = _normalize(page)
        if normalized_label.startswith(needle) or normalized_page.startswith(needle):
            score += 8
        if needle in normalized_label:
            score += 5
        if needle in normalized_page:
            score += 4
        score += sum(1 for term in terms if term in normalized_label) * 2
        scored.append((score, (page, label, keywords)))
    scored.sort(key=lambda item: (-item[0], item[1][1]))
    return [item for _, item in scored[:limit]]


def _open_floating_question(question: str) -> None:
    st.session_state["razync_ai_pending_question"] = question
    st.session_state["razync_floating_open"] = True
    st.rerun()


def _go_to(page: str, navigate) -> None:
    if page == "Assistente Razync":
        _open_floating_question("Como você pode me ajudar com meu MEI agora?")
        return
    navigate(page)


def _open_document_in_assistant(document: dict, navigate) -> None:
    st.session_state["razync_ai_pending_question"] = document_ai_prompt(document)
    st.session_state["razync_ai_pending_context"] = {
        "source": "global_document_search",
        "title": str(document.get("filename") or "Documento"),
        "detail": f"{document.get('category') or 'Outro'} · {document.get('reference_month') or 'Sem competência'}",
        "page": "Documentos",
        "document_id": document.get("id"),
    }
    st.session_state["razync_floating_open"] = True
    st.rerun()


def render_command_center(*, navigate, current_page: str, documents: list[dict] | None = None) -> None:
    """Global command/search surface for tools and safe document metadata."""
    documents = list(documents or [])
    with st.popover("Buscar ou ir para...", icon=":material/search:"):
        st.caption("Encontre ferramentas, ações e documentos sem procurar no menu.")
        query = st.text_input(
            "Buscar no Razync",
            key="rz_command_query",
            placeholder="Ex.: DAS, documento julho, nova despesa...",
            label_visibility="collapsed",
        )
        results = search_commands(query)
        document_results = search_documents(query, documents) if query else []

        if document_results:
            st.caption("Documentos")
            for index, document in enumerate(document_results):
                filename = str(document.get("filename") or "Documento")
                category = str(document.get("category") or "Outro")
                reference = str(document.get("reference_month") or "Sem competência")
                if st.button(
                    f"{filename} · {category} · {reference}",
                    key=f"rz_command_document_{index}_{document.get('id')}",
                    icon=":material/description:",
                    width="stretch",
                    help="Abrir a IA flutuante com este documento em contexto. O arquivo bruto não é enviado ao provedor de IA.",
                ):
                    _open_document_in_assistant(document, navigate)

        if results:
            st.caption("Ferramentas")
            for index, (page, label, _keywords) in enumerate(results):
                if st.button(
                    label,
                    key=f"rz_command_result_{index}_{page}",
                    icon=SIDEBAR_ICONS.get(page, ":material/arrow_forward:"),
                    disabled=page == current_page,
                    width="stretch",
                ):
                    _go_to(page, navigate)
            return

        if query and not document_results:
            st.caption("Nenhum item encontrado. Você pode perguntar à IA flutuante.")
            if st.button("Perguntar à IA", key="rz_command_ai_fallback", width="stretch"):
                _open_floating_question(query)
            return

        if query:
            return

        st.caption("Atalhos")
        columns = st.columns(2)
        for index, (page, label) in enumerate(QUICK_ACTIONS):
            with columns[index % 2]:
                if st.button(
                    label,
                    key=f"rz_command_quick_{index}",
                    icon=SIDEBAR_ICONS.get(page, ":material/arrow_forward:"),
                    disabled=page == current_page,
                    width="stretch",
                ):
                    _go_to(page, navigate)
