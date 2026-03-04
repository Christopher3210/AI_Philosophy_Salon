# llm/local_model_manager.py
# Local model manager using Ollama (OpenAI-compatible API)
#
# Setup:
#   1. Download Ollama: https://ollama.com/download
#   2. Run: ollama pull mistral
#   3. Ollama starts automatically on http://localhost:11434

from openai import OpenAI


class LocalModelManager:
    """
    Local model manager using Ollama.
    Requires Ollama running locally with the mistral model pulled.

    Setup:
        1. Install Ollama: https://ollama.com/download
        2. Pull model: ollama pull mistral
        3. Ollama runs automatically in the background
    """

    def __init__(self, base_url: str = "http://localhost:11434/v1"):
        self.client = OpenAI(
            base_url=base_url,
            api_key="ollama"  # Required by OpenAI client but not used by Ollama
        )
        # Map agent model keys to Ollama model names
        self.model_map = {
            "mistral": "mistral",
            "llama": "llama3.2",
            "gpt35": "mistral",
            "gpt4": "mistral",
        }
        print(f"[LocalModelManager] Using Ollama at {base_url}")

    def chat_once(
        self,
        model_key: str,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int = 128,
        temperature: float = 0.7,
    ) -> str:
        model_name = self.model_map.get(model_key, "mistral")

        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_new_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[LocalModelManager] Ollama error: {e}")
            print("[LocalModelManager] Make sure Ollama is running: https://ollama.com/download")
            return "I apologize, but I encountered an error generating my response."
