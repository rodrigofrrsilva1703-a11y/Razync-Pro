from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable


OFFICIAL_SERVICES = {
    "das": {
        "name": "PGMEI oficial",
        "url": "https://www8.receita.fazenda.gov.br/simplesnacional/aplicacoes/atspo/pgmei.app/identificacao",
    },
    "nfse": {
        "name": "Emissor Nacional de NFS-e",
        "url": "https://www.nfse.gov.br/EmissorNacional",
    },
    "mei": {
        "name": "Portal do Empreendedor",
        "url": "https://www.gov.br/mei",
    },
}


def next_onboarding_step(progress: dict) -> dict | None:
    routes = {
        "identity": "Primeiros Passos",
        "activity": "Primeiros Passos",
        "opening": "Primeiros Passos",
        "financial": "Movimentações",
        "das": "DAS",
        "documents": "Documentos",
    }
    labels = {
        "identity": "Completar dados do MEI",
        "activity": "Informar atividade",
        "opening": "Confirmar abertura",
        "financial": "Registrar primeira movimentação",
        "das": "Preparar controle do DAS",
        "documents": "Guardar primeiro documento",
    }
    for step in progress.get("steps", []):
        if not step.get("done"):
            key = str(step.get("key") or "")
            return {
                **step,
                "page": routes.get(key, "Primeiros Passos"),
                "action": labels.get(key, "Continuar configuração"),
            }
    return None


def build_today_plan(
    priorities: Iterable[dict],
    notifications: Iterable[dict],
    progress: dict,
    *,
    limit: int = 6,
) -> dict:
    """Merge product signals into one short, deterministic daily routine."""
    items: list[dict] = []

    for item in priorities:
        items.append({
            "priority": int(item.get("priority") or 4),
            "title": str(item.get("title") or "Revisar informação"),
            "detail": str(item.get("detail") or ""),
            "page": str(item.get("page") or "Dashboard"),
            "source": "Razync",
        })

    notification_priority = {"urgent": 1, "warning": 2, "info": 3}
    for item in notifications:
        items.append({
            "priority": notification_priority.get(str(item.get("level")), 3),
            "title": str(item.get("title") or "Prazo do MEI"),
            "detail": str(item.get("detail") or ""),
            "page": str(item.get("page") or "Central de Notificações"),
            "source": "Prazo",
        })

    onboarding = next_onboarding_step(progress)
    if onboarding:
        items.append({
            "priority": 3,
            "title": onboarding["action"],
            "detail": str(onboarding.get("detail") or "Continue a configuração inicial."),
            "page": onboarding["page"],
            "source": "Configuração",
        })

    deduplicated: dict[tuple[str, str], dict] = {}
    for item in items:
        key = (item["page"], item["title"].strip().lower())
        current = deduplicated.get(key)
        if current is None or item["priority"] < current["priority"]:
            deduplicated[key] = item

    ordered = sorted(
        deduplicated.values(),
        key=lambda item: (item["priority"], item["title"].lower()),
    )
    meaningful = [
        item for item in ordered
        if not (item["page"] == "Dashboard" and item["priority"] >= 4)
    ]
    if not meaningful:
        meaningful = [{
            "priority": 4,
            "title": "Rotina em dia",
            "detail": "Nenhuma pendência importante foi identificada com os dados cadastrados.",
            "page": "Dashboard",
            "source": "Razync",
        }]

    visible = meaningful[: max(1, int(limit))]
    return {
        "items": visible,
        "total": len(meaningful),
        "urgent": sum(1 for item in meaningful if item["priority"] == 1),
        "all_clear": len(meaningful) == 1 and meaningful[0]["priority"] == 4,
    }


def financial_story(
    revenue: float,
    expense: float,
    annual_revenue: float,
    annual_limit: float,
    *,
    previous_revenue: float = 0.0,
) -> list[dict]:
    """Explain financial indicators in plain Portuguese without giving tax advice."""
    revenue = float(revenue or 0)
    expense = float(expense or 0)
    annual_revenue = float(annual_revenue or 0)
    annual_limit = float(annual_limit or 0)
    result = revenue - expense
    notes: list[dict] = []

    if revenue <= 0 and expense <= 0:
        notes.append({
            "tone": "info",
            "title": "Comece registrando o mês",
            "detail": "Ainda não há entradas ou saídas suficientes para explicar o resultado.",
        })
    elif result >= 0:
        margin = (result / revenue * 100) if revenue else 0
        notes.append({
            "tone": "ok",
            "title": "O mês está positivo",
            "detail": f"Depois das despesas registradas, sobraram {margin:.1f}% das entradas.",
        })
    else:
        notes.append({
            "tone": "danger",
            "title": "As saídas superaram as entradas",
            "detail": "Revise despesas e recebimentos pendentes antes de tomar novas decisões.",
        })

    if previous_revenue > 0 and revenue > 0:
        change = (revenue / previous_revenue - 1) * 100
        direction = "cresceu" if change >= 0 else "caiu"
        notes.append({
            "tone": "info" if change >= 0 else "warn",
            "title": f"Faturamento {direction} no mês",
            "detail": f"Variação de {abs(change):.1f}% em relação ao mês anterior.",
        })

    if annual_limit > 0:
        used = annual_revenue / annual_limit * 100
        notes.append({
            "tone": "danger" if used >= 95 else "warn" if used >= 80 else "info",
            "title": "Acompanhamento do limite MEI",
            "detail": f"{used:.1f}% do limite monitorado está utilizado no ano.",
        })

    return notes[:3]


def das_journey(
    competence: str,
    das_rows: Iterable[dict],
    documents: Iterable[dict],
    payment_matches: Iterable[dict] = (),
) -> dict:
    current = next(
        (row for row in das_rows if str(row.get("competence") or "") == competence),
        None,
    )
    has_guide = any(
        str(doc.get("category") or "").upper() == "DAS"
        and str(doc.get("reference_month") or "") == competence
        for doc in documents
    )
    paid = bool(current and str(current.get("status") or "").lower() == "pago")
    matched = any(
        str(item.get("competence") or "") == competence
        or item.get("das_id") == (current or {}).get("id")
        for item in payment_matches
    )
    steps = [
        {
            "title": "Emitir no PGMEI",
            "done": bool(current),
            "detail": "A emissão acontece somente no portal oficial.",
        },
        {
            "title": "Registrar a guia",
            "done": bool(current),
            "detail": "Valor, vencimento e competência ficam organizados no Razync.",
        },
        {
            "title": "Guardar o PDF",
            "done": has_guide,
            "detail": "Anexe a guia para encontrá-la no fechamento e no backup.",
        },
        {
            "title": "Confirmar pagamento",
            "done": paid,
            "detail": (
                "O extrato contém um possível pagamento para revisar."
                if matched and not paid
                else "Atualize somente depois de conferir o comprovante."
            ),
        },
    ]
    done = sum(1 for step in steps if step["done"])
    return {"steps": steps, "done": done, "total": len(steps), "percent": round(done / len(steps) * 100)}


def integration_catalog(config: dict, database_persistent: bool) -> list[dict]:
    """Describe safe capabilities without pretending third-party credentials exist."""
    supabase_ready = bool(
        database_persistent
        and config.get("SUPABASE_URL")
        and config.get("SUPABASE_PUBLISHABLE_KEY")
    )
    return [
        {
            "name": "Dados e documentos",
            "status": "Ativo" if supabase_ready else "Configurar",
            "ready": supabase_ready,
            "mode": "Automático",
            "detail": "Banco persistente, login e arquivos privados por usuário.",
            "page": "Status do Sistema",
            "url": "",
        },
        {
            "name": "DAS do MEI",
            "status": "Assistido",
            "ready": True,
            "mode": "Portal oficial",
            "detail": "Jornada guiada, controle da guia, PDF e detecção de pagamento.",
            "page": "DAS",
            "url": OFFICIAL_SERVICES["das"]["url"],
        },
        {
            "name": "NFS-e Nacional",
            "status": "Assistido",
            "ready": True,
            "mode": "Emissor oficial + importação",
            "detail": "Preparo da emissão e importação de CSV/XLSX sem guardar o arquivo-fonte.",
            "page": "Notas Fiscais",
            "url": OFFICIAL_SERVICES["nfse"]["url"],
        },
        {
            "name": "Banco e Open Finance",
            "status": "Importação ativa",
            "ready": True,
            "mode": "Arquivo bancário",
            "detail": "Conciliação por extrato disponível; conexão direta depende de provedor regulado e consentimento.",
            "page": "Importar Extrato",
            "url": str(config.get("OPEN_FINANCE_PROVIDER_URL") or ""),
        },
        {
            "name": "WhatsApp e e-mail",
            "status": "Assistido",
            "ready": True,
            "mode": "Mensagem preparada",
            "detail": "O Razync prepara cobranças; o usuário revisa antes de enviar.",
            "page": "Central de Automações",
            "url": str(config.get("WHATSAPP_BUSINESS_URL") or ""),
        },
        {
            "name": "Assinatura do Razync",
            "status": "Ativo" if str(config.get("CHECKOUT_PRO_URL") or "").startswith("https://") else "Configurar",
            "ready": str(config.get("CHECKOUT_PRO_URL") or "").startswith("https://"),
            "mode": "Checkout externo",
            "detail": "Dados de cartão permanecem no provedor de pagamento.",
            "page": "Plano e Assinatura",
            "url": str(config.get("CHECKOUT_PRO_URL") or ""),
        },
        {
            "name": "Contador",
            "status": "Ativo",
            "ready": True,
            "mode": "Exportação segura",
            "detail": "Relatórios e backup sem compartilhar senhas do cliente.",
            "page": "Espaço do Contador",
            "url": "",
        },
    ]


def security_checklist(
    *,
    auth_enabled: bool,
    database_persistent: bool,
    storage_enabled: bool,
    leaked_password_protection: bool,
) -> list[dict]:
    return [
        {"title": "Autenticação por usuário", "done": auth_enabled, "detail": "Supabase Auth ou acesso GitHub autorizado."},
        {"title": "Banco persistente", "done": database_persistent, "detail": "Dados não dependem do disco temporário do Streamlit."},
        {"title": "Documentos privados", "done": storage_enabled, "detail": "Arquivos protegidos por sessão e regras de acesso."},
        {"title": "Proteção contra senhas vazadas", "done": leaked_password_protection, "detail": "Ative no painel do Supabase Auth quando disponível no plano."},
        {"title": "Histórico e backup", "done": True, "detail": "Auditoria e exportação já disponíveis no Razync."},
    ]


def transaction_restore_payload(row: dict[str, Any]) -> dict[str, Any]:
    allowed = (
        "tx_date", "tx_type", "description", "category", "value",
        "document_number", "counterparty", "payment_method",
    )
    payload = {key: row.get(key) for key in allowed}
    value = payload.get("tx_date")
    if isinstance(value, datetime):
        payload["tx_date"] = value.date()
    elif hasattr(value, "date") and not isinstance(value, date):
        payload["tx_date"] = value.date()
    payload["value"] = float(payload.get("value") or 0)
    return payload
