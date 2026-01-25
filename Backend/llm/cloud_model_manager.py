# llm/cloud_model_manager.py
# Cloud-based model manager using OpenAI API (much faster than local models)

import os
from typing import Dict

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class CloudModelManager:
    """
    Cloud-based language model manager using OpenAI API.
    Much faster than local models - recommended for real-time applications.

    Usage:
        manager = CloudModelManager(api_key="sk-xxx")
        response = manager.chat_once("mistral", system_prompt, user_prompt)
    """

    def __init__(self, api_key: str = None):
        """
        Initialize CloudModelManager.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
        """
        if not HAS_OPENAI:
            raise ImportError("OpenAI not installed. Run: pip install openai")

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No OpenAI API key found! "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter"
            )

        self.client = OpenAI(api_key=self.api_key)
        print("[CloudModelManager] Using OpenAI API (fast mode)")

        # Map agent model keys to OpenAI models
        # You can customize this mapping
        self.model_map: Dict[str, str] = {
            "mistral": "gpt-3.5-turbo",       # Default: fast and cheap
            "gpt35": "gpt-3.5-turbo",
            "gpt4": "gpt-4-turbo-preview",    # Smarter but more expensive
            "gpt4o": "gpt-4o",                # Latest GPT-4
        }

    def chat_once(
        self,
        model_key: str,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int = 128,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a single chat response using OpenAI API.

        Args:
            model_key: Model identifier (e.g., "mistral" -> maps to gpt-3.5-turbo)
            system_prompt: System/persona prompt
            user_prompt: User message
            max_new_tokens: Max tokens to generate
            temperature: Sampling temperature (0.0-2.0)

        Returns:
            Generated response text
        """
        # Map model key to OpenAI model name
        model_name = self.model_map.get(model_key, "gpt-3.5-turbo")

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
            print(f"[CloudModelManager] OpenAI API error: {e}")
            return "I apologize, but I encountered an error generating my response."


# Alias for compatibility - can be used as drop-in replacement
ModelManager = CloudModelManager
