from __future__ import annotations

import re
import unicodedata
from collections import Counter


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text.lower()).strip()


def search_documents(query: str, documents: list[dict], *, limit: int = 5) -> list[dict]:
    """Search only safe document metadata; never inspect or expose raw bytes here."""
    needle = _normalize(query)
    if not needle or not documents:
        return []
    terms = [term for term in needle.split() if len(term) >= 2]
    scored: list[tuple[int, dict]] = []
    for item in documents:
        filename = str(item.get("filename") or "")
        category = str(item.get("category") or "")
        reference = str(item.get("reference_month") or "")
        haystack = _normalize(f"{filename} {category} {reference}")
        if not all(term in haystack for term in terms):
            continue
        score = 0
        normalized_filename = _normalize(filename)
        normalized_category = _normalize(category)
        if needle in normalized_filename:
            score += 8
        if needle in normalized_category:
            score += 5
        if reference and needle in _normalize(reference):
            score += 4
        score += sum(1 for term in terms if term in normalized_filename) * 2
        scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], str(pair[1].get("filename") or "")))
    return [item for _score, item in scored[:limit]]


def document_summary(documents: list[dict]) -> dict:
    docs = list(documents or [])
    categories = Counter(str(item.get("category") or "Outro") for item in docs)
    references = Counter(str(item.get("reference_month") or "Sem competência") for item in docs)
    return {
        "count": len(docs),
        "categories": dict(categories),
        "references": dict(references),
    }


def document_ai_prompt(document: dict) -> str:
    """Prepare an assistant request using metadata only; the resource layer may locate the file locally later."""
    filename = str(document.get("filename") or "documento")
    category = str(document.get("category") or "Outro")
    reference = str(document.get("reference_month") or "sem competência")
    return (
        f"Quero ajuda com o documento {filename}. Ele está cadastrado como {category} e competência {reference}. "
        "Diga o que você consegue verificar com segurança, como ele se relaciona com minha organização no Razync e, se eu pedir, prepare o download do próprio arquivo."
    )
