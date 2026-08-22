import unittest
from unittest.mock import patch

from assistant_audio import AssistantAudioError, transcribe_audio


class AssistantAudioTests(unittest.TestCase):
    def test_audio_requires_private_api_key(self):
        with self.assertRaisesRegex(AssistantAudioError, "OPENAI_API_KEY"):
            transcribe_audio(b"audio", "pedido.webm", api_key="")

    def test_audio_rejects_unsupported_extension(self):
        with self.assertRaisesRegex(AssistantAudioError, "Formato"):
            transcribe_audio(b"audio", "pedido.exe", api_key="secret")

    @patch("openai.OpenAI")
    def test_audio_transcription_uses_portuguese_and_safe_model(self, openai_client):
        openai_client.return_value.audio.transcriptions.create.return_value.text = (
            "Gastei 80 reais de combustível hoje"
        )
        result = transcribe_audio(b"valid-audio", "pedido.webm", api_key="secret")
        self.assertTrue(result.startswith("Gastei 80"))
        kwargs = openai_client.return_value.audio.transcriptions.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "gpt-4o-mini-transcribe")
        self.assertEqual(kwargs["language"], "pt")


if __name__ == "__main__":
    unittest.main()

