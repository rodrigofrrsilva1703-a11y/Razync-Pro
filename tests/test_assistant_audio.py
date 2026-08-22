from unittest.mock import patch

import pytest

from assistant_audio import AssistantAudioError, transcribe_audio


def test_audio_requires_private_api_key():
    with pytest.raises(AssistantAudioError, match="OPENAI_API_KEY"):
        transcribe_audio(b"audio", "pedido.webm", api_key="")


def test_audio_rejects_unsupported_extension():
    with pytest.raises(AssistantAudioError, match="Formato"):
        transcribe_audio(b"audio", "pedido.exe", api_key="secret")


@patch("openai.OpenAI")
def test_audio_transcription_uses_portuguese_and_safe_model(openai_client):
    openai_client.return_value.audio.transcriptions.create.return_value.text = "Gastei 80 reais de combustível hoje"
    result = transcribe_audio(b"valid-audio", "pedido.webm", api_key="secret")
    assert result.startswith("Gastei 80")
    kwargs = openai_client.return_value.audio.transcriptions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-4o-mini-transcribe"
    assert kwargs["language"] == "pt"

