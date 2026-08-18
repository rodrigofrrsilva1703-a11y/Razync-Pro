from __future__ import annotations


PLAN_CATALOG = {
    "Essencial": {
        "description": "Organização financeira e fiscal para começar com segurança.",
        "features": (
            "Dashboard e movimentações",
            "DAS, obrigações e DASN-SIMEI",
            "Notas fiscais e documentos",
            "Backup manual e exportações",
        ),
    },
    "Pro": {
        "description": "Automação assistida, produtividade e colaboração com contador.",
        "features": (
            "Tudo do Essencial",
            "Automações e alertas avançados",
            "Conciliação e análise financeira",
            "Espaço do contador e integrações configuradas",
        ),
    },
}


def integration_maturity(item: dict) -> str:
    name = str(item.get("name") or "")
    if item.get("ready") and name in {"Dados e documentos", "Contador"}:
        return "Ativo"
    if name in {"DAS do MEI", "NFS-e Nacional", "Banco e Open Finance", "WhatsApp e e-mail"}:
        return "Assistido"
    if item.get("ready"):
        return "Ativo"
    return "Configurar"


def production_checklist(*, persistent_db: bool, auth_ready: bool, storage_ready: bool, session_secret: bool) -> list[dict]:
    return [
        {"item": "PostgreSQL persistente", "ok": persistent_db, "detail": "Evita perda de dados em reinícios do Streamlit."},
        {"item": "Supabase Auth", "ok": auth_ready, "detail": "Login, recuperação e sessão por usuário."},
        {"item": "Storage privado", "ok": storage_ready, "detail": "Documentos fora do disco temporário do Streamlit."},
        {"item": "Segredo de sessão", "ok": session_secret, "detail": "Protege o token persistido no navegador."},
        {"item": "Testes e CI", "ok": True, "detail": "Suíte automatizada antes de publicação."},
        {"item": "Backup e restauração", "ok": False, "detail": "Validar rotina automática do provedor e teste periódico de restauração."},
        {"item": "Monitoramento externo", "ok": False, "detail": "Conectar observabilidade externa antes de operação em escala."},
    ]


def data_rights_summary() -> list[dict]:
    return [
        {"title": "Exportar meus dados", "status": "Disponível", "detail": "Use o backup completo para obter dados e documentos."},
        {"title": "Corrigir meus dados", "status": "Disponível", "detail": "Dados do MEI e registros podem ser atualizados no sistema."},
        {"title": "Excluir minha conta", "status": "Processo assistido", "detail": "A remoção da identidade Supabase deve ser feita por fluxo administrativo seguro, sem service_role no Streamlit."},
        {"title": "Privacidade e consentimento", "status": "Disponível", "detail": "Termos e política possuem versão registrada no cadastro."},
    ]
