from __future__ import annotations

from document_intelligence import analyze_document


def analyze_das_guide(content: bytes, filename: str = "das.pdf") -> dict:
    """Return confirmable DAS suggestions without external APIs or automatic writes."""
    result = analyze_document(content, "application/pdf", filename)
    warnings: list[str] = []
    if result.get("category") != "DAS":
        warnings.append("O arquivo não foi identificado com segurança como guia DAS.")
    if not result.get("reference_month"):
        warnings.append("A competência não foi encontrada automaticamente.")
    if result.get("value") is None:
        warnings.append("O valor da guia não foi encontrado automaticamente.")
    if result.get("warning"):
        warnings.append(str(result["warning"]))
    return {
        "competence": result.get("reference_month") or "",
        "amount": result.get("value"),
        "confidence": result.get("confidence") or "Baixa",
        "preview": result.get("text_preview") or "",
        "recognized_as_das": result.get("category") == "DAS",
        "warnings": warnings,
    }
