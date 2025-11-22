import edge_tts
import os

class SimpleTTS:
    def __init__(self, voice="en-US-AriaNeural", output_dir="tts_output"):
        self.voice = voice
        self.output_dir = output_dir

        # Create root folder
        os.makedirs(self.output_dir, exist_ok=True)

    async def speak(self, speaker_name: str, text: str, turn: int, index: int, is_qa=False):
        """
        Save audio in a folder per turn.
        Normal:  tts_output/turn1/Aristotle_turn1_1.mp3
        Q&A:     tts_output/turn1_QA/Aristotle_turn1_3.mp3
        """

        # Choose subfolder name
        folder_name = f"turn{turn}_QA" if is_qa else f"turn{turn}"
        turn_folder = os.path.join(self.output_dir, folder_name)

        # Create folder if not exist
        os.makedirs(turn_folder, exist_ok=True)

        # Build filename
        filename = f"{speaker_name}_turn{turn}_{index}.mp3"
        filepath = os.path.join(turn_folder, filename)

        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(filepath)

        print(f"[TTS] Saved → {filepath}")
        return filepath

    def clear_output(self):
        """Delete all mp3 files and subfolders."""
        removed = 0
        for root, dirs, files in os.walk(self.output_dir):
            for f in files:
                if f.endswith(".mp3"):
                    os.remove(os.path.join(root, f))
                    removed += 1
        print(f"[TTS] Cleaned {removed} audio files.")
