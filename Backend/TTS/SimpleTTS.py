import edge_tts
import os

class SimpleTTS:
    def __init__(self, voice="en-US-AriaNeural", output_dir="tts_output"):
        """
        voice: Edge-TTS voice ID
        output_dir: folder where audio files are saved
        """
        self.voice = voice
        self.output_dir = output_dir

        # Create output folder if not exists
        os.makedirs(self.output_dir, exist_ok=True)

    async def speak(self, speaker_name: str, text: str, turn: int, index: int):
        """
        Generate speech file with predictable filename:
        Example: Aristotle_turn1_1.mp3
                 Russell_turn1_2.mp3
                 Aristotle_turn3_5.mp3 (if many messages)
        """
        filename = f"{speaker_name}_turn{turn}_{index}.mp3"
        filepath = os.path.join(self.output_dir, filename)

        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(filepath)

        print(f"[TTS] Saved → {filepath}")
        return filepath
    def clear_output(self):
        """Delete all mp3 files in the output folder before a new run."""
        for f in os.listdir(self.output_dir):
            if f.endswith(".mp3"):
                os.remove(os.path.join(self.output_dir, f))
        print("[TTS] Cleaned old audio files.")
