# LLMClient.py
from openai import OpenAI
import random

class LLMClient:
    def __init__(self, base_url="http://127.0.0.1:1234/v1", api_key="lm-studio"):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model_id = "openai/gpt-oss-20b"

    def chat_once(self, system_prompt: str, user_prompt: str):
        """Send one chat turn to the LLM and return its reply."""
        resp = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=128,
            seed=random.randint(1, 999999)
        )
        return resp.choices[0].message.content.strip()