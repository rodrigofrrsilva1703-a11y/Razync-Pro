from __future__ import annotations

# Navegação principal: mostra apenas a rotina mais frequente do MEI.
SIDEBAR_LABELS = {
    "Dashboard": "Início",
    "Central de Automações": "Automações",
    "Assistente Razync": "Assistente",
    "Movimentações": "Receitas e despesas",
    "Recorrências": "Lançamentos recorrentes",
    "Importar Extrato": "Importar extrato",
    "Conciliação": "Conciliação financeira",
    "Fluxo de Caixa": "Fluxo de caixa",
    "Análise Financeira": "Análise financeira",
    "DAS": "DAS mensal",
    "DASN-SIMEI": "Declaração anual",
    "Obrigações": "Prazos e obrigações",
    "Notas Fiscais": "Notas fiscais",
    "Importar NFS-e": "Importar NFS-e",
    "Relatório Mensal": "Relatório mensal",
    "Fechamento Mensal": "Fechamento mensal",
    "Clientes e Fornecedores": "Clientes e fornecedores",
    "Empregado": "Empregado",
    "Documentos": "Documentos",
    "Espaço do Contador": "Espaço do contador",
    "Primeiros Passos": "Primeiros passos",
    "Meu MEI": "Dados do MEI",
    "Central de Notificações": "Alertas e calendário",
    "Integrações": "Integrações",
    "Plano e Assinatura": "Plano e assinatura",
    "Segurança da Conta": "Segurança da conta",
    "Histórico de Atividades": "Histórico de atividades",
    "Status do Sistema": "Status do sistema",
    "Backup": "Backup dos dados",
}

SIDEBAR_GROUPS = {
    "Financeiro": ["Movimentações", "Conciliação", "Análise Financeira"],
    "Fiscal MEI": ["DAS", "Notas Fiscais", "Obrigações", "DASN-SIMEI"],
    "Gestão": ["Documentos", "Clientes e Fornecedores"],
    "Ajuda inteligente": ["Central de Automações", "Assistente Razync"],
    "Meu negócio": ["Meu MEI"],
}

# Recursos importantes, mas de uso menos frequente. Permanecem disponíveis sem poluir a rotina principal.
# Importar NFS-e não aparece aqui porque a própria tela de Notas Fiscais já leva ao importador.
SIDEBAR_SECONDARY_GROUPS = {
    "Financeiro avançado": ["Recorrências", "Importar Extrato", "Fluxo de Caixa"],
    "Fiscal e relatórios": ["Relatório Mensal", "Fechamento Mensal"],
    "Gestão complementar": ["Empregado", "Espaço do Contador"],
    "Conta e sistema": [
        "Central de Notificações", "Integrações", "Plano e Assinatura",
        "Segurança da Conta", "Histórico de Atividades", "Status do Sistema", "Backup",
    ],
}

SIDEBAR_ICONS = {
    "Dashboard": ":material/home:",
    "Movimentações": ":material/swap_vert:",
    "Recorrências": ":material/event_repeat:",
    "Importar Extrato": ":material/upload_file:",
    "Conciliação": ":material/rule:",
    "Fluxo de Caixa": ":material/timeline:",
    "Análise Financeira": ":material/monitoring:",
    "DAS": ":material/receipt_long:",
    "Notas Fiscais": ":material/request_quote:",
    "Importar NFS-e": ":material/upload:",
    "Obrigações": ":material/event:",
    "DASN-SIMEI": ":material/description:",
    "Documentos": ":material/folder_open:",
    "Clientes e Fornecedores": ":material/groups:",
    "Empregado": ":material/badge:",
    "Fechamento Mensal": ":material/task_alt:",
    "Relatório Mensal": ":material/assessment:",
    "Espaço do Contador": ":material/business_center:",
    "Central de Automações": ":material/bolt:",
    "Central de Notificações": ":material/notifications:",
    "Assistente Razync": ":material/auto_awesome:",
    "Integrações": ":material/hub:",
    "Meu MEI": ":material/store:",
    "Plano e Assinatura": ":material/credit_card:",
    "Segurança da Conta": ":material/shield:",
    "Histórico de Atividades": ":material/history:",
    "Status do Sistema": ":material/health_and_safety:",
    "Backup": ":material/backup:",
}
