from __future__ import annotations

from pathlib import Path

from document_catalog import document_ai_prompt, document_summary, search_documents


def _docs():
    return [
        {"id": 1, "filename": "das_2026-07.pdf", "category": "DAS", "reference_month": "2026-07"},
        {"id": 2, "filename": "nota_cliente_123.pdf", "category": "Nota Fiscal", "reference_month": "2026-08"},
        {"id": 3, "filename": "extrato_santander_julho.pdf", "category": "Extrato Bancário", "reference_month": "2026-07"},
    ]


def test_document_search_uses_safe_metadata():
    assert search_documents("jul 2026", _docs()) == []
    assert search_documents("2026-07", _docs())[0]["reference_month"] == "2026-07"
    assert search_documents("santander", _docs())[0]["id"] == 3
    assert search_documents("nota fiscal", _docs())[0]["id"] == 2


def test_document_summary_counts_metadata_only():
    summary = document_summary(_docs())
    assert summary["count"] == 3
    assert summary["categories"]["DAS"] == 1
    assert summary["references"]["2026-07"] == 2


def test_ai_prompt_contains_only_document_metadata():
    prompt = document_ai_prompt(_docs()[0])
    assert "das_2026-07.pdf" in prompt
    assert "DAS" in prompt
    assert "2026-07" in prompt
    assert "conteúdo" not in prompt.lower()


def test_global_search_receives_document_catalog():
    command_center = Path("command_center.py").read_text(encoding="utf-8")
    sidebar = Path("sidebar_workspace.py").read_text(encoding="utf-8")
    assert "search_documents(query, documents)" in command_center
    assert "document_ai_prompt(document)" in command_center
    assert "documents=documents" in sidebar
    assert '"source": "global_document_search"' in command_center
