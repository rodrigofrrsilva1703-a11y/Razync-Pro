from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
import unicodedata

from pypdf import PdfReader

CATEGORIES = ("Nota Fiscal", "Comprovante", "Extrato Bancário", "DAS", "Contrato", "Outro")

_CATEGORY_KEYWORDS = {
    "DAS": ("documento de arrecadacao do simples", "das mei", "simples nacional", "pgmei"),
    "Nota Fiscal": ("nota fiscal", "nf-e", "nfe", "nfs-e", "nfse"),
    "Extrato Bancário": ("extrato bancario", "saldo anterior", "saldo disponivel", "lancamentos"),
    "Contrato": ("contrato", "contratante", "contratado", "clausula"),
    "Comprovante": ("comprovante", "pagamento efetuado", "pix realizado", "autenticacao"),
}


def _plain(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value.lower())
        if not unicodedata.combining(char)
    )


def _extract_pdf_text(content: bytes, max_pages: int = 8) -> str:
    reader = PdfReader(BytesIO(content))
    pieces = []
    for page in reader.pages[:max_pages]:
        pieces.append(page.extract_text() or "")
    return "\n".join(pieces).strip()


def _category(text: str, filename: str) -> str:
    haystack = _plain(f"{filename} {text}")
    scores = {
        category: sum(keyword in haystack for keyword in keywords)
        for category, keywords in _CATEGORY_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] else "Outro"


def _competence(text: str, filename: str) -> str:
    haystack = f"{text}\n{filename}"
    patterns = (
        r"(?i)(?:compet[eê]ncia|refer[eê]ncia)\s*[:\-]?\s*(0[1-9]|1[0-2])[\/-](20\d{2})",
        r"(?i)(?:compet[eê]ncia|refer[eê]ncia)\s*[:\-]?\s*(20\d{2})[\/-](0[1-9]|1[0-2])",
        r"\b(20\d{2})[-_](0[1-9]|1[0-2])\b",
    )
    for index, pattern in enumerate(patterns):
        match = re.search(pattern, haystack)
        if match:
            first, second = match.groups()
            return f"{second}-{first}" if index == 0 else f"{first}-{second}"
    date_match = re.search(r"\b(?:0?[1-9]|[12]\d|3[01])[\/-](0[1-9]|1[0-2])[\/-](20\d{2})\b", haystack)
    return f"{date_match.group(2)}-{date_match.group(1)}" if date_match else ""


def _money_values(text: str) -> list[float]:
    values = []
    for raw in re.findall(r"R\$\s*([\d.]+,\d{2})", text, flags=re.IGNORECASE):
        try:
            values.append(float(raw.replace(".", "").replace(",", ".")))
        except ValueError:
            continue
    return values


def _document_number(text: str) -> str:
    patterns = (
        r"(?i)(?:n[uú]mero|n[º°]|nota)\s*[:\-]?\s*([A-Z0-9.\/-]{4,30})",
        r"\b(\d{44})\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return ""


def analyze_document(content: bytes, mime_type: str, filename: str) -> dict:
    """Extract local, confirmable suggestions from a document without external APIs."""
    text = ""
    warning = ""
    is_pdf = mime_type == "application/pdf" or Path(filename).suffix.lower() == ".pdf"
    if is_pdf:
        try:
            text = _extract_pdf_text(content)
        except Exception:
            warning = "Não foi possível ler o texto deste PDF. Confira os dados manualmente."
        if not text and not warning:
            warning = "Este PDF parece escaneado e não possui texto pesquisável. Confira os dados manualmente."
    else:
        warning = "Imagens ainda não possuem leitura automática. Use as sugestões do nome do arquivo e confira os dados."

    category = _category(text, filename)
    competence = _competence(text, filename)
    values = _money_values(text)
    number = _document_number(text)
    signals = sum(bool(value) for value in (text, category != "Outro", competence, values, number))
    confidence = "Alta" if signals >= 4 else "Média" if signals >= 2 else "Baixa"
    preview = " ".join(text.split())[:280]
    return {
        "category": category,
        "reference_month": competence,
        "value": max(values) if values else None,
        "document_number": number,
        "text_preview": preview,
        "confidence": confidence,
        "warning": warning,
        "has_searchable_text": bool(text),
    }
