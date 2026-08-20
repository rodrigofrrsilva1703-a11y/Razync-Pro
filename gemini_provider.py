from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai_assistant import INSTRUCTIONS, RazyncAIError


DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"
_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiAIError(RazyncAIError):
    """Safe application error for Gemini provider failures."""


def _endpoint(model: str) -> str:
    safe_model = (model or DEFAULT_GEMINI_MODEL).strip()
    return f"{_GEMINI_BASE_URL}/{safe_model}:generateContent"


def _request_gemini(*, api_key: str, model: str, prompt: str, max_output_tokens: int) -> str:
    if not api_key or not api_key.strip():
        raise GeminiAIError("GEMINI_API_KEY não configurada.")

    payload = {
        "systemInstruction": {"parts": [{"text": INSTRUCTIONS}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "candidateCount": 1,
            "maxOutputTokens": int(max_output_tokens),
            "temperature": 0.2,
        },
    }
    request = Request(
        _endpoint(model),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key.strip(),
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=25.0) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        status = int(getattr(exc, "code", 0) or 0)
        if status in (401, 403):
            raise GeminiAIError("A chave do Gemini foi recusada ou não tem permissão para este modelo.") from exc
        if status == 404:
            raise GeminiAIError("O modelo configurado do Gemini não está disponível para esta chave.") from exc
        if status == 429:
            raise GeminiAIError("O Gemini atingiu o limite gratuito ou o limite de requisições do projeto.") from exc
        if status == 400:
            raise GeminiAIError("O Gemini recusou a configuração da chamada.") from exc
        if status >= 500:
            raise GeminiAIError("O Gemini está temporariamente indisponível.") from exc
        raise GeminiAIError("O Gemini não conseguiu responder agora.") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise GeminiAIError("Não foi possível conectar ao Gemini agora.") from exc
    except Exception as exc:
        raise GeminiAIError("O Gemini está temporariamente indisponível.") from exc

    candidates = data.get("candidates") or []
    if not candidates:
        raise GeminiAIError("O Gemini não retornou uma resposta utilizável.")

    parts = ((candidates[0].get("content") or {}).get("parts") or [])
    text = "\n".join(str(part.get("text") or "").strip() for part in parts if part.get("text"))
    text = text.strip()
    if not text:
        raise GeminiAIError("O Gemini não retornou uma resposta utilizável.")
    return text


def diagnose_gemini(api_key: str, model: str = DEFAULT_GEMINI_MODEL) -> tuple[bool, str]:
    """Run a minimal provider request without sending any user/business data."""
    if not api_key or not api_key.strip():
        return False, "GEMINI_API_KEY não foi encontrada nos Secrets do Streamlit."
    try:
        _request_gemini(
            api_key=api_key,
            model=model,
            prompt="Responda somente com OK.",
            max_output_tokens=32,
        )
        return True, f"Conexão com o Gemini funcionando. Modelo validado: {model}."
    except GeminiAIError as exc:
        return False, str(exc)


def ask_razync_gemini(
    question: str,
    *,
    context: dict,
    api_key: str,
    model: str = DEFAULT_GEMINI_MODEL,
) -> str:
    if not question or not question.strip():
        raise ValueError("A pergunta não pode ficar vazia.")

    prompt = (
        "Pergunta do usuário:\n"
        + question.strip()
        + "\n\nContexto agregado e autorizado do Razync (JSON):\n"
        + json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    )
    return _request_gemini(
        api_key=api_key,
        model=model,
        prompt=prompt,
        max_output_tokens=700,
    )
