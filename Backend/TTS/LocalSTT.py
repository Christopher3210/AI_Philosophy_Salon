# tts/LocalSTT.py
# Local Speech-to-Text using OpenAI Whisper (fully offline)

import asyncio
import base64
import os
import tempfile

import whisper


class LocalSTT:
    """
    Local STT using OpenAI Whisper.
    Drop-in replacement for AzureSTT.
    """

    def __init__(self, model_size: str = "base", language: str = "en"):
        """
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
                        "base" is a good balance of speed and accuracy
            language: Language code for transcription
        """
        self.language = language
        print(f"[LocalSTT] Loading Whisper model '{model_size}'...")
        self.model = whisper.load_model(model_size)
        print(f"[LocalSTT] Whisper loaded")

    def transcribe(self, audio_base64: str) -> str:
        """
        Transcribe base64-encoded WAV audio to text.

        Args:
            audio_base64: Base64-encoded WAV audio data

        Returns:
            Transcribed text, or empty string on failure
        """
        audio_bytes = base64.b64decode(audio_base64)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            result = self.model.transcribe(tmp_path, language=self.language)
            text = result.get("text", "").strip()
            print(f"[LocalSTT] Recognized: {text}")
            return text
        except Exception as e:
            print(f"[LocalSTT] Error: {e}")
            return ""
        finally:
            try:
                os.unlink(tmp_path)
            except PermissionError:
                pass

    async def transcribe_async(self, audio_base64: str) -> str:
        """Async wrapper for transcribe."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.transcribe, audio_base64)
