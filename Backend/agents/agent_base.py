# agents/agent_base.py

class Agent:
    """
    A philosophical agent with a persona, memory, and associated model + voice.
    """

    def __init__(self, name: str, system_prompt: str, model_key: str, voice: str | None = None):
        self.name = name
        self.system_prompt = system_prompt
        self.model_key = model_key  # logical model key, e.g. "llama3", "phi3"
        self.voice = voice or "en-US-AriaNeural"
        self.memory: list[dict] = []

        # Motivation system fields
        self.motivation_score: float = 0.0         # Accumulated motivation to speak
        self.turns_since_last_speech: int = 0      # Silence duration tracker

    def add_memory(self, user_input: str, response: str):
        """
        Append a memory entry for future context use.
        """
        self.memory.append({"user": user_input, "response": response})
