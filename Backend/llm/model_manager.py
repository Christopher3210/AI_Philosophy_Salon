# llm/model_manager.py

from typing import Dict
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


class ModelManager:
    """
    Manages multiple local language models and provides a simple chat_once() API.

    - Each model is identified by a logical key, e.g. "llama3", "phi3", ...
    - Agents refer to models via the logical key (model_key).
    """

    def __init__(self, device: str | None = None):
        # Map from logical model key to HuggingFace model ID
        self.model_id_map: Dict[str, str] = {
            # You may need access / accept licenses for some of these:
            "mistral": "mistralai/Mistral-7B-Instruct-v0.3",
            "phi3":    "microsoft/Phi-3-medium-4k-instruct",
            "qwen2":   "Qwen/Qwen2-7B-Instruct",
            "gemma":   "google/gemma-2b",
        }

        self.device = device  # e.g. "cuda" or "cpu"; if None, detect automatically.
        self.tokenizers: Dict[str, AutoTokenizer] = {}
        self.models: Dict[str, AutoModelForCausalLM] = {}

    def _get_device(self) -> str:
        if self.device:
            return self.device
        return "cuda" if torch.cuda.is_available() else "cpu"

    def _ensure_loaded(self, model_key: str):
        """
        Lazy-load the model and tokenizer for the given logical key if not loaded yet.
        """
        if model_key in self.models:
            return

        if model_key not in self.model_id_map:
            raise ValueError(f"Unknown model key: {model_key}")

        model_id = self.model_id_map[model_key]
        device = self._get_device()

        print(f"[ModelManager] Loading model '{model_key}' from '{model_id}' on {device} ...")

        tokenizer = AutoTokenizer.from_pretrained(model_id)
        # Use bfloat16/float16 if available to save VRAM
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=dtype,
            device_map="auto" if device == "cuda" else None,
        )

        if device != "cuda":
            model.to(device)

        self.tokenizers[model_key] = tokenizer
        self.models[model_key] = model

        print(f"[ModelManager] Loaded model '{model_key}'.")

    def chat_once(
        self,
        model_key: str,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int = 128,
        temperature: float = 0.6,
    ) -> str:
        """
        Generate a single reply using the specified model.

        The prompt is composed in a simple "System / User / Assistant" style.
        For more advanced behavior you can plug in chat templates later.
        """
        self._ensure_loaded(model_key)

        tokenizer = self.tokenizers[model_key]
        model = self.models[model_key]
        device = self._get_device()

        # A simple prompt template; can be replaced by the model's official chat template
        prompt = (
            f"System: {system_prompt}\n"
            f"User: {user_prompt}\n"
            f"Assistant:"
        )

        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=temperature,
                pad_token_id=tokenizer.eos_token_id,
            )

        full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Try to extract only the assistant's part after the last "Assistant:"
        if "Assistant:" in full_text:
            reply = full_text.split("Assistant:")[-1].strip()
        else:
            reply = full_text.strip()

        return reply
