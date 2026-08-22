from __future__ import annotations

from io import BytesIO
from pathlib import Path


class AssistantAudioError(RuntimeError):
    """Erro seguro durante a transcrição de áudio."""


_AUDIO_EXTENSIONS = {".flac", ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".ogg", ".wav", ".webm"}
MAX_AUDIO_BYTES = 6 * 1024 * 1024


def transcribe_audio(content: bytes, filename: str, *, api_key: str, model: str = "gpt-4o-mini-transcribe") -> str:
    if not api_key.strip():
        raise AssistantAudioError("O recurso de áudio precisa da OPENAI_API_KEY configurada nos Secrets.")
    if not content or len(content) > MAX_AUDIO_BYTES:
        raise AssistantAudioError("Envie um áudio válido de até 6 MB.")
    suffix = Path(filename or "audio.webm").suffix.lower() or ".webm"
    if suffix not in _AUDIO_EXTENSIONS:
        raise AssistantAudioError("Formato de áudio não suportado. Use MP3, M4A, OGG, WAV ou WEBM.")

    try:
        from openai import OpenAI

        audio_file = BytesIO(content)
        audio_file.name = f"audio{suffix}"
        client = OpenAI(api_key=api_key.strip(), timeout=30.0, max_retries=1)
        transcript = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            language="pt",
            prompt="Lançamentos financeiros e fiscais de um MEI brasileiro no sistema Razync.",
        )
        text = str(getattr(transcript, "text", "") or "").strip()
    except AssistantAudioError:
        raise
    except Exception as exc:
        raise AssistantAudioError("Não foi possível transcrever o áudio agora.") from exc
    if not text:
        raise AssistantAudioError("Não consegui identificar uma fala clara neste áudio.")
    return text[:4000]

