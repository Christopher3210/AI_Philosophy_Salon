# controller/TurnTakingController.py

import asyncio
from typing import List, Dict, Any

from agents.agents_manager import AgentsManager
from llm.model_manager import ModelManager
from tts.SimpleTTS import SimpleTTS


class TurnTakingController:
    """
    Simple multi-philosopher debate controller.

    - Uses AgentsManager to get all philosophical agents
    - Uses ModelManager to call the local LLM (e.g. Mistral)
    - Optionally uses SimpleTTS to speak each reply
    - Keeps a sliding window of recent utterances as context
    """

    def __init__(
        self,
        model_manager: ModelManager,
        agents_manager: AgentsManager,
        tts_engine: SimpleTTS | None = None,
        history_window: int = 6,
    ):
        """
        Parameters
        ----------
        model_manager : ModelManager
            Wrapper around local HF models (e.g. mistral).
        agents_manager : AgentsManager
            Loads Agent objects from YAML configs.
        tts_engine : SimpleTTS | None
            If provided, each reply will be synthesized and optionally played.
        history_window : int
            Number of most recent utterances to include in the context.
        """
        self.model_manager = model_manager
        self.agents_manager = agents_manager
        self.tts = tts_engine
        self.history_window = history_window

        # Cache agent list in a stable order
        self.agents = self.agents_manager.get_all_agents()
        if not self.agents:
            raise RuntimeError("No agents loaded from AgentsManager.")

        # In-memory dialogue history: list of {"agent": name, "response": text}
        self.history: List[Dict[str, Any]] = []

    # ---------------- internal helpers ----------------

    def _build_context(self) -> str:
        """
        Build a short textual context from recent dialogue.

        Only the last `history_window` utterances are used for the prompt,
        but the full history is stored in self.history.
        """
        recent = self.history[-self.history_window :]
        if not recent:
            return ""

        lines = [f"{item['agent']}: {item['response']}" for item in recent]
        return "\n".join(lines)

    # ---------------- main loop ----------------

    async def run_dialogue(self, topic: str, turns: int = 4):
        """
        Run a simple round-robin debate on the given topic.

        Each turn, all agents speak once in order.
        """
        print(f"Host: Today we discuss — {topic}\n")
        print(f"Participants: {', '.join(a.name for a in self.agents)} \n")

        for turn_idx in range(turns):
            print(f"\n========== Turn {turn_idx + 1} ==========\n")

            for idx, agent in enumerate(self.agents):
                print(f"{agent.name} thinking...")

                # Build sliding-window context for this reply
                context = self._build_context()
                context_block = f"Recent dialogue:\n{context}\n\n" if context else ""

                user_prompt = (
                    f"Debate topic: {topic}\n\n"
                    f"{context_block}"
                    f"Now respond in the voice of {agent.name}.\n"
                    f"- Use 1–3 concise sentences.\n"
                    f"- Engage directly with the previous speakers.\n"
                    f"- Do not repeat long definitions already given.\n"
                )

                # Call local model
                reply = self.model_manager.chat_once(
                    model_key=agent.model_key,
                    system_prompt=agent.system_prompt,
                    user_prompt=user_prompt,
                    max_new_tokens=80,
                    temperature=0.7,
                )

                # Clean up whitespace
                reply = reply.replace("\n", " ").strip()

                # Save to agent memory + global history
                agent.add_memory(user_prompt, reply)
                self.history.append({"agent": agent.name, "response": reply})

                # Print to console
                print(f"{agent.name}: {reply}\n")

                # Optional: TTS synthesis + playback
                if self.tts is not None:
                    try:
                        # SimpleTTS.speak is async(speaker, text, turn, index, is_qa=False)
                        await self.tts.speak(
                            speaker_name=agent.name,
                            text=reply,
                            turn=turn_idx,
                            index=idx,
                            is_qa=False,
                        )
                    except Exception as e:
                        print(f"[TTS] Error during speak(): {e}")

                # Small async sleep to yield control
                await asyncio.sleep(0.05)

        print("\n======== Debate Finished ========\n")
