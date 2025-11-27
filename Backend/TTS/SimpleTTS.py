import edge_tts
import os
from playsound import playsound
from datetime import datetime
import asyncio

class SimpleTTS:
    def __init__(self, voice_map=None, output_dir="tts_output"):
        """
        voice_map: dict mapping speaker → voice ID
        """
        self.voice_map = voice_map or {}
        self.output_dir = output_dir
        self.utterance_count = 0  # Global utterance counter

        os.makedirs(self.output_dir, exist_ok=True)

    async def speak(self, speaker_name: str, text: str, turn: int, index: int, is_qa=False):
        """
        Save audio into turn-based folders + auto play.
        Uses timestamp-based naming to avoid conflicts.
        """
        # Increment global counter for unique naming
        self.utterance_count += 1

        folder_name = f"turn{turn}_QA" if is_qa else f"turn{turn}"
        turn_folder = os.path.join(self.output_dir, folder_name)
        os.makedirs(turn_folder, exist_ok=True)

        # Use timestamp + counter for unique filenames
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{speaker_name}_{timestamp}_{self.utterance_count:03d}.mp3"
        filepath = os.path.join(turn_folder, filename)

        # If file exists (shouldn't happen with timestamp+counter, but be safe)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"[TTS] Warning: Could not remove existing file: {e}")
                # Add microseconds to make it truly unique
                timestamp_micro = datetime.now().strftime("%H%M%S%f")
                filename = f"{speaker_name}_{timestamp_micro}_{self.utterance_count:03d}.mp3"
                filepath = os.path.join(turn_folder, filename)

        # Pick voice
        voice = self.voice_map.get(speaker_name, "en-US-AriaNeural")

        # Generate audio
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filepath)

        print(f"[TTS] Saved → {filepath}")

        # Auto play audio
        try:
            playsound(filepath)
        except Exception as e:
            print(f"[TTS] Could not play audio: {e}")

        return filepath

    def clear_output(self):
        """Delete all mp3 files."""
        removed = 0
        for root, dirs, files in os.walk(self.output_dir):
            for f in files:
                if f.endswith(".mp3"):
                    os.remove(os.path.join(root, f))
                    removed += 1
        print(f"[TTS] Cleaned {removed} audio files.")
