import azure.cognitiveservices.speech as speechsdk
import os
import json
from datetime import datetime
from typing import List, Dict, Tuple

# Audio playback - try pygame first (more stable), fallback to playsound
HAS_AUDIO = False
AUDIO_BACKEND = None

try:
    import pygame
    pygame.mixer.init()
    HAS_AUDIO = True
    AUDIO_BACKEND = "pygame"
except ImportError:
    try:
        from playsound import playsound
        HAS_AUDIO = True
        AUDIO_BACKEND = "playsound"
    except ImportError:
        pass

class AzureTTS:
    """
    Azure Speech Services TTS with Viseme support.
    Outputs both audio file and viseme timeline for lip sync.
    """

    # Azure Viseme ID to Oculus Viseme mapping
    # Azure uses 22 viseme IDs, we map to standard 15 Oculus visemes
    AZURE_TO_OCULUS_VISEME = {
        0: "sil",   # Silence
        1: "aa",    # æ, ə, ʌ
        2: "aa",    # ɑ
        3: "O",     # ɔ
        4: "E",     # ɛ, ʊ
        5: "E",     # ɝ
        6: "I",     # i, j
        7: "I",     # ɪ
        8: "O",     # o
        9: "U",     # u
        10: "O",    # oʊ
        11: "aa",   # aʊ
        12: "O",    # ɔɪ
        13: "aa",   # aɪ
        14: "E",    # eɪ
        15: "nn",   # n, l
        16: "RR",   # r
        17: "kk",   # k, g, ŋ
        18: "TH",   # θ, ð
        19: "FF",   # f, v
        20: "DD",   # d, t
        21: "SS",   # s, z
    }

    def __init__(self, subscription_key: str, region: str, voice_map: Dict[str, str] = None, output_dir: str = "tts_output", auto_play: bool = False):
        """
        Initialize Azure TTS.

        Args:
            subscription_key: Azure Speech Services API key
            region: Azure region (e.g., "eastus")
            voice_map: Dict mapping speaker name to Azure voice name
            output_dir: Directory to save audio files
            auto_play: Whether to automatically play audio after generation
        """
        self.subscription_key = subscription_key
        self.region = region
        self.output_dir = output_dir
        self.utterance_count = 0
        self.auto_play = auto_play

        # Default voice map for philosophers (should match agents/configs/*.yaml)
        self.voice_map = voice_map or {
            "Aristotle": "en-US-GuyNeural",
            "Sartre": "en-US-ChristopherNeural",
            "Russell": "en-GB-RyanNeural",
            "Wittgenstein": "en-GB-ThomasNeural",
        }

        os.makedirs(self.output_dir, exist_ok=True)

        if self.auto_play and not HAS_AUDIO:
            print("[AzureTTS] Warning: No audio backend available. Run: pip install pygame")

    def _create_speech_config(self, voice_name: str) -> speechsdk.SpeechConfig:
        """Create speech config with viseme enabled."""
        speech_config = speechsdk.SpeechConfig(
            subscription=self.subscription_key,
            region=self.region
        )
        speech_config.speech_synthesis_voice_name = voice_name
        speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_SynthOutputFormat,
            "audio-24khz-48kbitrate-mono-mp3"
        )
        return speech_config

    def speak(self, speaker_name: str, text: str, turn: int, index: int = 0, is_qa: bool = False) -> Tuple[str, List[Dict]]:
        """
        Generate speech and viseme data.

        Args:
            speaker_name: Name of the speaker
            text: Text to synthesize
            turn: Current turn number
            index: Index within turn
            is_qa: Whether this is a Q&A response

        Returns:
            Tuple of (audio_path, viseme_data)
            viseme_data: List of {"time": float, "viseme": str, "duration": float}
        """
        self.utterance_count += 1

        # Create output folder (use absolute path for Unity compatibility)
        folder_name = f"turn{turn}_QA" if is_qa else f"turn{turn}"
        turn_folder = os.path.abspath(os.path.join(self.output_dir, folder_name))
        os.makedirs(turn_folder, exist_ok=True)

        # Generate filename with absolute path
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{speaker_name}_{timestamp}_{self.utterance_count:03d}.mp3"
        filepath = os.path.join(turn_folder, filename)

        # Get voice
        voice = self.voice_map.get(speaker_name, "en-US-AriaNeural")

        # Setup speech config and audio output
        speech_config = self._create_speech_config(voice)
        audio_config = speechsdk.audio.AudioOutputConfig(filename=filepath)

        # Create synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        # Collect viseme events
        viseme_events = []

        def viseme_callback(evt):
            viseme_id = evt.viseme_id
            audio_offset_ms = evt.audio_offset / 10000  # Convert to milliseconds
            oculus_viseme = self.AZURE_TO_OCULUS_VISEME.get(viseme_id, "sil")
            viseme_events.append({
                "time": audio_offset_ms / 1000.0,  # Convert to seconds
                "viseme": oculus_viseme,
                "azure_id": viseme_id
            })

        # Subscribe to viseme events
        synthesizer.viseme_received.connect(viseme_callback)

        # Synthesize
        print(f"[AzureTTS] Generating speech for {speaker_name}...")
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"[AzureTTS] Saved → {filepath}")

            # Process viseme data - add durations
            viseme_data = self._process_visemes(viseme_events)

            # Save viseme data alongside audio
            viseme_path = filepath.replace(".mp3", "_visemes.json")
            with open(viseme_path, "w") as f:
                json.dump(viseme_data, f, indent=2)
            print(f"[AzureTTS] Visemes → {viseme_path} ({len(viseme_data)} events)")

            # Auto play if enabled
            if self.auto_play and HAS_AUDIO:
                try:
                    if AUDIO_BACKEND == "pygame":
                        import pygame
                        pygame.mixer.music.load(filepath)
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            pygame.time.wait(100)
                    else:
                        playsound(filepath)
                except Exception as e:
                    print(f"[AzureTTS] Playback error: {e}")

            return filepath, viseme_data

        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            print(f"[AzureTTS] Error: {cancellation.reason}")
            if cancellation.reason == speechsdk.CancellationReason.Error:
                print(f"[AzureTTS] Error details: {cancellation.error_details}")
            return None, []

    def _process_visemes(self, viseme_events: List[Dict]) -> List[Dict]:
        """
        Process raw viseme events to add durations and weights.
        """
        if not viseme_events:
            return []

        processed = []
        for i, event in enumerate(viseme_events):
            # Calculate duration (time until next viseme)
            if i < len(viseme_events) - 1:
                duration = viseme_events[i + 1]["time"] - event["time"]
            else:
                duration = 0.1  # Default duration for last viseme

            # Determine weight based on viseme type
            viseme = event["viseme"]
            if viseme == "sil":
                weight = 0.0
            elif viseme in ["aa", "O", "E"]:
                weight = 1.0  # Full open mouth
            elif viseme in ["I", "U"]:
                weight = 0.8
            else:
                weight = 0.7

            processed.append({
                "time": round(event["time"], 3),
                "viseme": viseme,
                "weight": weight,
                "duration": round(duration, 3)
            })

        return processed

    async def speak_async(self, speaker_name: str, text: str, turn: int, index: int = 0, is_qa: bool = False) -> Tuple[str, List[Dict]]:
        """
        Async wrapper for speak method.
        Azure SDK is not truly async, so this just wraps the sync method.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.speak, speaker_name, text, turn, index, is_qa)

    def clear_output(self):
        """Delete all generated files."""
        removed = 0
        for root, dirs, files in os.walk(self.output_dir):
            for f in files:
                if f.endswith((".mp3", ".json")):
                    os.remove(os.path.join(root, f))
                    removed += 1
        print(f"[AzureTTS] Cleaned {removed} files.")


# Convenience function
def create_azure_tts(output_dir: str = "tts_output") -> AzureTTS:
    """Create AzureTTS instance with default credentials."""
    return AzureTTS(
        subscription_key="GGOrbCc2fBt6m6hbwdrZH0oi8VyX7uq1Vl2wvb63X8XJ6b0PScL2JQQJ99CAACYeBjFXJ3w3AAAYACOGEacn",
        region="eastus",
        output_dir=output_dir
    )
