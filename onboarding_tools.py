from __future__ import annotations


def onboarding_progress(profile: dict, has_transactions: bool, has_das: bool, has_documents: bool) -> dict:
    steps = [
        {"key":"identity", "title":"Identifique seu MEI", "done":bool(profile.get("cnpj") and (profile.get("business_name") or profile.get("trade_name"))), "detail":"CNPJ e nome do negócio"},
        {"key":"activity", "title":"Informe sua atividade", "done":bool(profile.get("main_activity") and profile.get("activity_type")), "detail":"Usado em alertas e organização fiscal"},
        {"key":"opening", "title":"Confirme a data de abertura", "done":bool(profile.get("opening_date")), "detail":"Define limites proporcionais no ano de abertura"},
        {"key":"financial", "title":"Registre a primeira movimentação", "done":bool(has_transactions), "detail":"Ativa dashboard, fluxo de caixa e relatórios"},
        {"key":"das", "title":"Prepare o controle do DAS", "done":bool(has_das), "detail":"Acompanha competências e vencimentos"},
        {"key":"documents", "title":"Guarde o primeiro documento", "done":bool(has_documents), "detail":"Organiza comprovantes e fechamento mensal"},
    ]
    done = sum(1 for s in steps if s["done"])
    return {"steps": steps, "done": done, "total": len(steps), "percent": round(done / len(steps) * 100) if steps else 0, "complete": done == len(steps)}


def first_session_plan(progress: dict) -> list[dict]:
    """Short onboarding path for a new MEI without exposing every system module."""
    routes = {
        "identity": "Primeiros Passos",
        "activity": "Primeiros Passos",
        "opening": "Primeiros Passos",
        "financial": "Movimentações",
        "das": "DAS",
        "documents": "Documentos",
    }
    return [
        {
            "title": step["title"],
            "detail": step["detail"],
            "done": bool(step["done"]),
            "page": routes.get(step["key"], "Primeiros Passos"),
        }
        for step in progress.get("steps", [])
    ]


def recommended_setup(profile: dict) -> list[str]:
    activity_type = str(profile.get("activity_type") or "").lower()
    recs = ["Cadastre receitas e despesas com frequência para manter os relatórios atualizados."]
    if "serv" in activity_type:
        recs.append("Use a categoria Serviços para receitas de prestação de serviços e vincule o número da NFS-e quando existir.")
    if any(x in activity_type for x in ["comércio", "comercio", "misto", "indústria", "industria"]):
        recs.append("Separe receitas de vendas das receitas de serviços para a DASN-SIMEI ficar mais fácil de conferir.")
    recs.append("Importe o extrato bancário periodicamente para reduzir lançamentos manuais e facilitar a conciliação.")
    return recs