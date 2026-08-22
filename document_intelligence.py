from __future__ import annotations

from io import BytesIO
from pathlib import Path
from functools import lru_cache
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


@lru_cache(maxsize=1)
def _ocr_engine():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR()


def _ocr_image_bytes(content: bytes) -> str:
    """Run local OCR without sending the document to an external provider."""
    from PIL import Image
    image = Image.open(BytesIO(content)).convert("RGB")
    result, _ = _ocr_engine()(image)
    if not result:
        return ""
    return "\n".join(str(item[1]).strip() for item in result if len(item) > 1 and str(item[1]).strip())


def _ocr_scanned_pdf(content: bytes, max_pages: int = 3) -> str:
    """Rasterize only the first pages and OCR them locally to keep latency bounded."""
    import fitz

    document = fitz.open(stream=content, filetype="pdf")
    pieces: list[str] = []
    try:
        for page_number in range(min(len(document), max_pages)):
            page = document.load_page(page_number)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
            pieces.append(_ocr_image_bytes(pixmap.tobytes("png")))
    finally:
        document.close()
    return "\n".join(piece for piece in pieces if piece).strip()


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
        r"(?<!\d)(20\d{2})[-_](0[1-9]|1[0-2])(?!\d)",
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
        r"(?i)(?:n[uú]mero(?:\s+da\s+nota)?|n[º°])\s*[:\-]\s*([A-Z0-9.\/-]{4,30})",
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
    ocr_used = False
    is_pdf = mime_type == "application/pdf" or Path(filename).suffix.lower() == ".pdf"
    if is_pdf:
        try:
            text = _extract_pdf_text(content)
        except Exception:
            warning = "Não foi possível ler o texto deste PDF. Confira os dados manualmente."
        if not text:
            try:
                text = _ocr_scanned_pdf(content)
                ocr_used = bool(text)
                warning = "" if text else "O OCR não encontrou texto legível neste PDF. Confira os dados manualmente."
            except (ImportError, OSError, RuntimeError, ValueError):
                warning = "Este PDF parece escaneado e o OCR local não conseguiu concluir a leitura. Confira os dados manualmente."
    else:
        try:
            text = _ocr_image_bytes(content)
            ocr_used = bool(text)
            if not text:
                warning = "O OCR não encontrou texto legível na imagem. Confira os dados manualmente."
        except (ImportError, OSError, RuntimeError, ValueError):
            warning = "A leitura automática desta imagem não pôde ser concluída. Use as sugestões do nome do arquivo e confira os dados."

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
        "ocr_used": ocr_used,
    }

