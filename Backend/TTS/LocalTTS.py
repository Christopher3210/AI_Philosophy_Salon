# tts/LocalTTS.py
# Local TTS using Coqui XTTS v2 + Rhubarb Lip Sync for viseme generation
# Uses low-level XTTS API to avoid torchcodec/FFmpeg dependency on Windows

import asyncio
import json
import os
import random
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import soundfile as sf
import torch


class LocalTTS:
    """
    Local TTS engine using XTTS v2 for speech synthesis
    and Rhubarb Lip Sync for viseme generation.

    Drop-in replacement for AzureTTS — exposes the same
    speak_async() interface returning (audio_path, viseme_data).
    """

    # Rhubarb mouth shapes (A-H) to Oculus viseme mapping
    RHUBARB_TO_OCULUS = {
        "A": "sil",   # Closed mouth / silence
        "B": "DD",    # Slightly open (generic consonant)
        "C": "E",     # EE sound
        "D": "aa",    # AI / wide open
        "E": "O",     # O shape
        "F": "U",     # OO / W puckered
        "G": "FF",    # F / V
        "H": "TH",    # L / TH tongue
        "X": "sil",   # Idle / silence
    }

    # Weight per viseme for mouth opening intensity
    VISEME_WEIGHTS = {
        "sil": 0.0,
        "aa": 1.0,
        "O": 0.8,
        "E": 0.7,
        "I": 0.6,
        "U": 0.7,
        "nn": 0.3,
        "RR": 0.5,
        "kk": 0.4,
        "TH": 0.4,
        "FF": 0.3,
        "DD": 0.5,
        "SS": 0.3,
        "PP": 0.1,
        "CH": 0.4,
    }

    def __init__(
        self,
        voice_dir: str = "voices",
        output_dir: str = "tts_output",
        rhubarb_path: str = None,
        device: str = None,
    ):
        self.voice_dir = voice_dir
        self.output_dir = output_dir
        self.utterance_count = 0

        # Auto-detect rhubarb path
        if rhubarb_path is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rhubarb_path = os.path.join(
                base, "tools", "rhubarb",
                "Rhubarb-Lip-Sync-1.14.0-Windows", "rhubarb.exe"
            )
        self.rhubarb_path = rhubarb_path

        if not os.path.exists(self.rhubarb_path):
            raise FileNotFoundError(f"Rhubarb not found at {self.rhubarb_path}")

        # Auto-detect device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        print(f"[LocalTTS] Loading XTTS v2 on {device}...")
        self.model = self._load_model(device)
        print("[LocalTTS] XTTS v2 loaded")

        # Cache speaker embeddings to avoid re-computing each call
        self._speaker_cache = {}

        # Pre-generated filler clips per speaker: {name: [(audio_path, viseme_data), ...]}
        self.fillers = {}

        os.makedirs(self.output_dir, exist_ok=True)

    def _load_model(self, device: str):
        """Load XTTS v2 model using low-level API (bypasses torchcodec check)."""
        import importlib
        import sys

        # Bypass coqui-tts torchcodec check by patching __init__
        tts_init = sys.modules.get("TTS")
        if tts_init is None:
            # Create a dummy TTS package module to skip the __init__.py check
            import types
            dummy = types.ModuleType("TTS")
            dummy.__path__ = [os.path.dirname(importlib.util.find_spec("TTS").submodule_search_locations[0])]
            dummy.__path__ = importlib.util.find_spec("TTS").submodule_search_locations
            sys.modules["TTS"] = dummy

        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
        from TTS.utils.manage import ModelManager

        # Monkey-patch torchaudio.load to use soundfile (avoids torchcodec)
        import torchaudio
        _original_load = torchaudio.load

        def _soundfile_load(filepath, *args, **kwargs):
            audio_np, sr = sf.read(filepath, dtype="float32")
            if len(audio_np.shape) > 1:
                audio_np = audio_np.mean(axis=1)
            audio_tensor = torch.FloatTensor(audio_np).unsqueeze(0)
            return audio_tensor, sr

        torchaudio.load = _soundfile_load

        # Allow loading XTTS checkpoint (contains custom classes)
        import trainer.io
        trainer.io._WEIGHTS_ONLY = False

        # Download model if needed
        manager = ModelManager()
        model_path, config_path, _ = manager.download_model("tts_models/multilingual/multi-dataset/xtts_v2")

        config = XttsConfig()
        config.load_json(config_path)
        model = Xtts.init_from_config(config)
        model.load_checkpoint(config, checkpoint_dir=model_path)
        model = model.to(device)
        model.eval()
        return model

    def _get_voice_ref(self, speaker_name: str) -> str:
        """Get reference audio path for a speaker."""
        for name in [speaker_name, speaker_name.lower()]:
            path = os.path.join(self.voice_dir, f"{name}.wav")
            if os.path.exists(path):
                return path
        raise FileNotFoundError(
            f"No reference audio for '{speaker_name}' in {self.voice_dir}. "
            f"Expected: {self.voice_dir}/{speaker_name.lower()}.wav"
        )

    def _get_speaker_latents(self, speaker_name: str):
        """Get or compute speaker conditioning latents (cached)."""
        if speaker_name in self._speaker_cache:
            return self._speaker_cache[speaker_name]

        ref_path = self._get_voice_ref(speaker_name)
        gpt_latents, speaker_embedding = self.model.get_conditioning_latents(
            audio_path=[ref_path],
        )

        self._speaker_cache[speaker_name] = (gpt_latents, speaker_embedding)
        return gpt_latents, speaker_embedding

    def _split_text(self, text: str, max_chars: int = 240) -> List[str]:
        """Split text into chunks under max_chars, breaking at sentence boundaries."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        chunks = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= max_chars:
                current = (current + " " + sentence).strip()
            else:
                if current:
                    chunks.append(current)
                # If a single sentence exceeds limit, split at comma/semicolon
                if len(sentence) > max_chars:
                    parts = re.split(r'(?<=[,;])\s+', sentence)
                    sub = ""
                    for part in parts:
                        if len(sub) + len(part) + 1 <= max_chars:
                            sub = (sub + " " + part).strip()
                        else:
                            if sub:
                                chunks.append(sub)
                            sub = part
                    if sub:
                        chunks.append(sub)
                    current = ""
                else:
                    current = sentence
        if current:
            chunks.append(current)
        return chunks if chunks else [text[:max_chars]]

    def _generate_audio(self, speaker_name: str, text: str, output_path: str):
        """Generate speech audio using XTTS v2 low-level API."""
        gpt_latents, speaker_embedding = self._get_speaker_latents(speaker_name)

        # Let XTTS handle splitting internally — avoids multi-chunk overhead
        all_wavs = []

        out = self.model.inference(
            text=text,
            language="en",
            gpt_cond_latent=gpt_latents,
            speaker_embedding=speaker_embedding,
            temperature=0.65,
            speed=1.1,
            enable_text_splitting=True,
        )
        wav = out["wav"]
        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()
        wav = np.squeeze(wav)

        # Save as WAV (24kHz, XTTS default sample rate)
        sf.write(output_path, wav, 24000)

    def _generate_visemes(self, audio_path: str) -> List[Dict]:
        """Run Rhubarb Lip Sync on audio file and return viseme data."""
        try:
            # Write to temp file because -q suppresses stdout
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
                tmp_path = tmp.name

            result = subprocess.run(
                [
                    self.rhubarb_path,
                    audio_path,
                    "-f", "json",
                    "--recognizer", "phonetic",
                    "-q",
                    "-o", tmp_path,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                print(f"[LocalTTS] Rhubarb error: {result.stderr}")
                os.unlink(tmp_path)
                return []

            with open(tmp_path, "r") as f:
                rhubarb_data = json.load(f)
            os.unlink(tmp_path)
            mouth_cues = rhubarb_data.get("mouthCues", [])

            visemes = []
            for cue in mouth_cues:
                shape = cue.get("value", "X")
                oculus_viseme = self.RHUBARB_TO_OCULUS.get(shape, "sil")
                start = cue.get("start", 0.0)
                end = cue.get("end", 0.0)
                duration = end - start

                visemes.append({
                    "time": round(start, 3),
                    "viseme": oculus_viseme,
                    "weight": self.VISEME_WEIGHTS.get(oculus_viseme, 0.5),
                    "duration": round(duration, 3),
                })

            return visemes

        except subprocess.TimeoutExpired:
            print("[LocalTTS] Rhubarb timed out")
            return []
        except Exception as e:
            print(f"[LocalTTS] Viseme generation error: {e}")
            return []

    def speak(
        self,
        speaker_name: str,
        text: str,
        turn: int = 0,
        index: int = 0,
        is_qa: bool = False,
    ) -> Tuple[str, List[Dict]]:
        """
        Generate speech and viseme data (synchronous).

        Returns:
            (audio_path, viseme_data) matching AzureTTS interface
        """
        self.utterance_count += 1

        # Create turn folder
        turn_folder = f"turn{turn}_QA" if is_qa else f"turn{turn}"
        turn_dir = os.path.join(self.output_dir, turn_folder)
        os.makedirs(turn_dir, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%H%M%S")
        base_name = f"{speaker_name}_{timestamp}_{self.utterance_count:03d}"
        audio_path = os.path.join(turn_dir, f"{base_name}.wav")
        viseme_path = os.path.join(turn_dir, f"{base_name}_visemes.json")

        # Generate audio
        print(f"[LocalTTS] Generating speech for {speaker_name}...")
        self._generate_audio(speaker_name, text, audio_path)
        audio_path = os.path.abspath(audio_path)
        print(f"[LocalTTS] Saved -> {audio_path}")

        # Generate visemes from audio
        print(f"[LocalTTS] Generating visemes...")
        viseme_data = self._generate_visemes(audio_path)

        # Save viseme JSON
        if viseme_data:
            with open(viseme_path, "w") as f:
                json.dump(viseme_data, f, indent=2)
            print(f"[LocalTTS] Visemes -> {viseme_path} ({len(viseme_data)} events)")
        else:
            print("[LocalTTS] Warning: No viseme data generated")

        return audio_path, viseme_data

    async def speak_async(
        self,
        speaker_name: str,
        text: str,
        turn: int = 0,
        index: int = 0,
        is_qa: bool = False,
    ) -> Tuple[str, List[Dict]]:
        """Async wrapper for speak() — matches AzureTTS.speak_async() interface."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.speak, speaker_name, text, turn, index, is_qa
        )

    def generate_fillers(self, speaker_names: List[str], count: int = 3):
        """
        Pre-generate filler clips for each speaker at startup.
        These short clips fill the gap when pre-computation isn't ready.
        """
        filler_phrases = [
            "Hmm, that is an interesting point.",
            "Let me consider that for a moment.",
            "Indeed, that raises an important question.",
            "Well, I must think carefully about this.",
            "That is a provocative claim.",
            "I find myself compelled to respond to that.",
            "Now that is worth examining more closely.",
            "A fair point, but I wonder.",
            "There is something to what you say.",
            "I have been reflecting on precisely this.",
            "That touches on something fundamental.",
            "How curious, I was thinking along similar lines.",
        ]

        filler_dir = os.path.join(self.output_dir, "fillers")
        os.makedirs(filler_dir, exist_ok=True)

        for name in speaker_names:
            self.fillers[name] = []
            # Pick unique phrases for this speaker
            chosen = random.sample(filler_phrases, min(count, len(filler_phrases)))

            for i, phrase in enumerate(chosen):
                fpath = os.path.join(filler_dir, f"{name.lower()}_filler_{i}.wav")
                print(f"[LocalTTS] Generating filler {i+1}/{count} for {name}...")
                try:
                    self._generate_audio(name, phrase, fpath)
                    visemes = self._generate_visemes(os.path.abspath(fpath))
                    self.fillers[name].append({
                        "audio_path": os.path.abspath(fpath),
                        "viseme_data": visemes,
                        "text": phrase,
                    })
                except Exception as e:
                    print(f"[LocalTTS] Filler generation failed for {name}: {e}")

            print(f"[LocalTTS] {len(self.fillers[name])} fillers ready for {name}")

    def get_filler(self, speaker_name: str) -> dict | None:
        """Get a random filler clip for a speaker. Returns None if none available."""
        clips = self.fillers.get(speaker_name, [])
        if not clips:
            return None
        import random
        return random.choice(clips)

    def clear_output(self):
        """Delete all generated audio and viseme files."""
        import shutil
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
            os.makedirs(self.output_dir, exist_ok=True)
            print(f"[LocalTTS] Cleared {self.output_dir}")
