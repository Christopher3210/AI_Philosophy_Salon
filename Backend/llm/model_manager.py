# llm/model_manager.py

from typing import Dict
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os


class ModelManager:
    """
    Manages multiple local language models and provides a simple chat_once() API.
    """

    def __init__(self, device: str | None = None):
        self.model_id_map: Dict[str, str] = {
            "mistral": "mistralai/Mistral-7B-Instruct-v0.3",
        }

        # Explicit GPU or auto-detect
        self.device = device
        self.tokenizers: Dict[str, AutoTokenizer] = {}
        self.models: Dict[str, AutoModelForCausalLM] = {}

        # Enable faster attention if available
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"

    def _get_device(self) -> str:
        if self.device:
            return self.device
        return "cuda" if torch.cuda.is_available() else "cpu"

    def _ensure_loaded(self, model_key: str):
        if model_key in self.models:
            return

        if model_key not in self.model_id_map:
            raise ValueError(f"Unknown model key: {model_key}")

        model_id = self.model_id_map[model_key]
        device = self._get_device()

        print(f"\n[ModelManager] Loading model '{model_key}' from '{model_id}' on {device}...\n")

        # Tokenizer caching
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            local_files_only=False,
            use_fast=True,
        )

        # Choose dtype
        if device == "cuda" and torch.cuda.is_available():
            dtype = torch.float16  # reduce VRAM usage
        else:
            dtype = torch.float32

        # Load model w/ caching
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=dtype,
            local_files_only=False,
        )

        model.to(device)

        # Optional GPU optimization
        if device == "cuda":
            try:
                model = torch.compile(model)
                print("[ModelManager] GPU optimization: torch.compile enabled.")
            except Exception:
                print("[ModelManager] torch.compile not available (ignored).")

        self.tokenizers[model_key] = tokenizer
        self.models[model_key] = model

        print(f"[ModelManager] Loaded model '{model_key}' successfully on {device} ({torch.cuda.get_device_name(0) if device=='cuda' else 'CPU'}).")

    def chat_once(
        self,
        model_key: str,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int = 128,
        temperature: float = 0.6,
    ) -> str:
        self._ensure_loaded(model_key)

        model = self.models[model_key]
        tokenizer = self.tokenizers[model_key]
        device = model.device

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

        text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        reply = text.split("Assistant:")[-1].strip()
        return reply
