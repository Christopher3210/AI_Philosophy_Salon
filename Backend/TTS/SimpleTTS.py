import edge_tts

class SimpleTTS:
    def __init__(self, voice="en-US-AriaNeural"):
        self.voice = voice

    async def speak(self, text, filename="output.mp3"):
        """Generate speech using Microsoft's Edge TTS."""
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(filename)
        print(f"[TTS] Saved → {filename}")
        return filename
