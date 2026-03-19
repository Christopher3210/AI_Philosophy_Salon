# tts/AzureSTT.py
# Azure Speech-to-Text for transcribing user audio input

import azure.cognitiveservices.speech as speechsdk
import asyncio
import base64
import os
import tempfile


class AzureSTT:
    """
    Azure Speech Services STT.
    Transcribes WAV audio bytes to text.
    """

    def __init__(self, subscription_key: str, region: str, language: str = "en-US"):
        self.subscription_key = subscription_key
        self.region = region
        self.language = language

    def transcribe(self, audio_base64: str) -> str:
        """
        Transcribe base64-encoded WAV audio to text.

        Args:
            audio_base64: Base64-encoded WAV audio data

        Returns:
            Transcribed text, or empty string on failure
        """
        # Decode base64 to bytes
        audio_bytes = base64.b64decode(audio_base64)

        # Write to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key,
                region=self.region
            )
            speech_config.speech_recognition_language = self.language

            audio_config = speechsdk.AudioConfig(filename=tmp_path)
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )

            result = recognizer.recognize_once()

            # Release file handles before deleting
            del recognizer
            del audio_config

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                print(f"[AzureSTT] Recognized: {result.text}")
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                print(f"[AzureSTT] No speech recognized")
                return ""
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                print(f"[AzureSTT] Canceled: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    print(f"[AzureSTT] Error: {cancellation.error_details}")
                return ""
        finally:
            try:
                os.unlink(tmp_path)
            except PermissionError:
                pass  # File still locked, OS will clean up temp dir

    async def transcribe_async(self, audio_base64: str) -> str:
        """Async wrapper for transcribe."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.transcribe, audio_base64)


def create_azure_stt() -> AzureSTT:
    """Create AzureSTT instance with default credentials."""
    return AzureSTT(
        subscription_key="87MplLeDZRkxrDwt62jOVHtVyY7CWvJrz41zsUCYPg0c8dcMa5PYJQQJ99CCACqBBLyXJ3w3AAAYACOGnHn6",
        region="eastus"
    )
