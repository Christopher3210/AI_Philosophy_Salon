import edge_tts
import os

class SimpleTTS:
    def __init__(self, voice_map=None, output_dir="tts_output"):
        """
        voice_map: dict mapping speaker → voice ID
        Example:
            {
                "Aristotle": "en-US-GuyNeural",
                "Russell": "en-GB-RyanNeural"
            }
        """
        self.voice_map = voice_map or {}
        self.output_dir = output_dir

        os.makedirs(self.output_dir, exist_ok=True)

    async def speak(self, speaker_name: str, text: str, turn: int, index: int, is_qa=False):
        """Save audio into turn-based folders, using speaker-specific voice."""
        folder_name = f"turn{turn}_QA" if is_qa else f"turn{turn}"
        turn_folder = os.path.join(self.output_dir, folder_name)
        os.makedirs(turn_folder, exist_ok=True)

        filename = f"{speaker_name}_turn{turn}_{index}.mp3"
        filepath = os.path.join(turn_folder, filename)

        # Select voice: speaker-specific OR fallback default
        voice = self.voice_map.get(speaker_name, "en-US-AriaNeural")

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filepath)

        print(f"[TTS] Saved → {filepath}")
        return filepath

    def clear_output(self):
        removed = 0
        for root, dirs, files in os.walk(self.output_dir):
            for f in files:
                if f.endswith(".mp3"):
                    os.remove(os.path.join(root, f))
                    removed += 1
        print(f"[TTS] Cleaned {removed} audio files.")
