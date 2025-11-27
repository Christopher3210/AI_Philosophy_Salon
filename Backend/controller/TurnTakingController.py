# controller/TurnTakingController.py

import asyncio
from typing import List, Dict, Any

from agents.agents_manager import AgentsManager
from llm.model_manager import ModelManager
from tts.SimpleTTS import SimpleTTS


class TurnTakingController:
    """
    Free-form multi-philosopher debate controller.

    - Philosophers speak freely based on their desire to respond
    - User can press Enter at any time to interrupt
    - Supports continuous dialogue flow without rigid turn-taking
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

        # Flag to control dialogue flow
        self.is_interrupted = False
        self.should_stop = False

        # Counter for speech turns
        self.speech_count = 0

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

    async def _select_next_speaker(self, topic: str) -> Any:
        """
        Select the next speaker based on simple logic.

        For now, we use a simple approach:
        - If no one has spoken, first agent starts
        - Otherwise, pick randomly or based on desire (to be enhanced later)
        """
        import random

        # For initial implementation, use weighted random
        # Later we can add LLM-based desire scoring

        if not self.history:
            # First speaker - could be any philosopher
            return random.choice(self.agents)

        # Track recent speakers to avoid monopoly
        recent_speakers = [item['agent'] for item in self.history[-3:]]

        # Give lower weight to recent speakers
        weights = []
        for agent in self.agents:
            recent_count = recent_speakers.count(agent.name)
            weight = max(1, 5 - recent_count * 2)  # Reduce weight for recent speakers
            weights.append(weight)

        # Weighted random selection
        return random.choices(self.agents, weights=weights, k=1)[0]

    async def _listen_for_interrupt(self):
        """
        Background task that listens for Enter key press.
        Sets interrupt flag when user presses Enter.
        """
        loop = asyncio.get_event_loop()

        try:
            # Wait for Enter key (blocking call in executor)
            await loop.run_in_executor(None, input, "")
            if not self.should_stop:
                self.is_interrupted = True
                print("\n>>> Interrupting dialogue... <<<\n")
        except Exception as e:
            if not self.should_stop:
                print(f"[Error in interrupt listener]: {e}")

    async def _handle_interrupt_menu(self, topic: str):
        """
        Show menu when user interrupts the dialogue.
        """
        loop = asyncio.get_event_loop()

        print("\n" + "="*50)
        print("What would you like to do?")
        print("  [q] - Ask a question")
        print("  [e] - End dialogue")
        print("  [c] - Continue dialogue")
        print("="*50)

        choice = await loop.run_in_executor(None, input, "Your choice: ")
        choice = choice.strip().lower()

        if choice == 'q':
            await self._handle_player_question(topic)
            # After Q&A, ask again
            await self._handle_interrupt_menu(topic)
        elif choice == 'e':
            self.should_stop = True
            print("\n======== Dialogue Ended by User ========\n")
        else:
            # Continue - reset interrupt flag
            self.is_interrupted = False
            print("\n>>> Resuming dialogue... <<<\n")

    def _detect_target_philosophers(self, question: str) -> list:
        """
        Detect which philosophers are mentioned in the question.
        Returns list of agent names, or empty list if none/all should respond.
        """
        question_lower = question.lower()
        mentioned = []

        for agent in self.agents:
            # Check if agent name is mentioned in the question
            name_lower = agent.name.lower()
            if name_lower in question_lower:
                mentioned.append(agent.name)

        return mentioned

    async def _handle_player_question(self, topic: str):
        """
        Handle player question - targeted or all philosophers respond.
        """
        loop = asyncio.get_event_loop()
        question = await loop.run_in_executor(None, input, "\nYour question: ")
        question = question.strip()

        if not question:
            print("No question provided.")
            return

        print(f"\n[You ask]: {question}\n")

        # Detect if question targets specific philosophers
        target_names = self._detect_target_philosophers(question)

        # Determine who should respond
        if target_names:
            # Only mentioned philosophers respond
            responding_agents = [a for a in self.agents if a.name in target_names]
            print(f"💡 Directing question to: {', '.join(target_names)}\n")
        else:
            # Everyone responds
            responding_agents = self.agents

        # Each selected philosopher responds to the player's question
        for idx, agent in enumerate(responding_agents):
            print(f"{agent.name} responding...")

            context = self._build_context()
            context_block = f"Recent dialogue:\n{context}\n\n" if context else ""

            user_prompt = (
                f"Debate topic: {topic}\n\n"
                f"{context_block}"
                f"A participant asks: {question}\n\n"
                f"Respond as {agent.name} in 1-3 concise sentences."
            )

            reply = self.model_manager.chat_once(
                model_key=agent.model_key,
                system_prompt=agent.system_prompt,
                user_prompt=user_prompt,
                max_new_tokens=80,
                temperature=0.7,
            )

            reply = reply.replace("\n", " ").strip()

            # Remove agent name if it appears at the start of the reply
            if reply.startswith(agent.name + ":"):
                reply = reply[len(agent.name) + 1:].strip()
            elif reply.startswith(agent.name):
                reply = reply[len(agent.name):].strip()
                if reply.startswith(":"):
                    reply = reply[1:].strip()

            agent.add_memory(user_prompt, reply)
            self.history.append({"agent": agent.name, "response": reply, "is_qa": True})

            print(f"{agent.name}: {reply}\n")

            # TTS for Q&A
            if self.tts is not None:
                try:
                    await self.tts.speak(
                        speaker_name=agent.name,
                        text=reply,
                        turn=self.speech_count,
                        index=idx,
                        is_qa=True,
                    )
                except Exception as e:
                    print(f"[TTS] Error during speak(): {e}")

            await asyncio.sleep(0.05)

    # ---------------- main loop ----------------

    async def run_dialogue(self, topic: str):
        """
        Run a free-form debate on the given topic.

        Philosophers speak continuously based on their desire to respond.
        User can press Enter at any time to interrupt.
        """
        print(f"\n{'='*60}")
        print(f"  AI Philosophy Salon")
        print(f"  Topic: {topic}")
        print(f"  Participants: {', '.join(a.name for a in self.agents)}")
        print(f"{'='*60}\n")
        print("💡 Press Enter at any time to interrupt the dialogue.\n")

        # Start background listener for interrupts
        listener_task = asyncio.create_task(self._listen_for_interrupt())

        try:
            # Continuous dialogue loop
            while not self.should_stop:
                # Check for interrupt
                if self.is_interrupted:
                    # Cancel old listener if it exists and is running
                    if listener_task and not listener_task.done():
                        listener_task.cancel()
                        try:
                            await listener_task
                        except asyncio.CancelledError:
                            pass

                    # Handle the interrupt menu
                    await self._handle_interrupt_menu(topic)
                    if self.should_stop:
                        break

                    # Restart listener after handling interrupt
                    listener_task = asyncio.create_task(self._listen_for_interrupt())
                    continue

                # Select next speaker
                speaker = await self._select_next_speaker(topic)

                print(f"\n{speaker.name} is thinking...")

                # Build context
                context = self._build_context()
                context_block = f"Recent dialogue:\n{context}\n\n" if context else ""

                user_prompt = (
                    f"Debate topic: {topic}\n\n"
                    f"{context_block}"
                    f"Now respond in the voice of {speaker.name}.\n"
                    f"- Use 1–3 concise sentences.\n"
                    f"- Engage directly with previous speakers or introduce new perspectives.\n"
                    f"- Avoid repeating what has already been said.\n"
                )

                # Generate response (run in executor to allow interruption)
                loop = asyncio.get_event_loop()
                generation_task = loop.run_in_executor(
                    None,
                    self.model_manager.chat_once,
                    speaker.model_key,
                    speaker.system_prompt,
                    user_prompt,
                    80,  # max_new_tokens
                    0.7,  # temperature
                )

                # Wait for generation, but check for interrupt periodically
                while not generation_task.done():
                    if self.is_interrupted:
                        generation_task.cancel()
                        break
                    await asyncio.sleep(0.05)  # Check every 50ms

                # If interrupted during generation, skip this speech
                if self.is_interrupted:
                    continue

                try:
                    reply = await generation_task
                except asyncio.CancelledError:
                    continue  # Generation was cancelled

                reply = reply.replace("\n", " ").strip()

                # Remove speaker name if it appears at the start of the reply
                if reply.startswith(speaker.name + ":"):
                    reply = reply[len(speaker.name) + 1:].strip()
                elif reply.startswith(speaker.name):
                    reply = reply[len(speaker.name):].strip()
                    if reply.startswith(":"):
                        reply = reply[1:].strip()

                speaker.add_memory(user_prompt, reply)
                self.history.append({"agent": speaker.name, "response": reply})
                self.speech_count += 1

                print(f"💬 {speaker.name}: {reply}\n")

                # TTS playback
                if self.tts is not None:
                    try:
                        tts_task = asyncio.create_task(self.tts.speak(
                            speaker_name=speaker.name,
                            text=reply,
                            turn=self.speech_count,
                            index=0,
                            is_qa=False,
                        ))

                        # Wait for TTS, but allow interruption
                        while not tts_task.done():
                            if self.is_interrupted:
                                tts_task.cancel()
                                try:
                                    await tts_task
                                except asyncio.CancelledError:
                                    pass
                                break
                            await asyncio.sleep(0.05)  # Check every 50ms

                        # If interrupted, skip to next iteration
                        if self.is_interrupted:
                            continue

                        # Complete TTS if not interrupted
                        if not tts_task.cancelled():
                            await tts_task

                    except Exception as e:
                        print(f"[TTS] Error during speak(): {e}")

                # Small delay before next speech (unless interrupted)
                if not self.is_interrupted:
                    await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            print("\n[Dialogue cancelled]")
        finally:
            # Clean up listener task
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass

        # Show summary
        print(f"\n{'='*60}")
        print(f"  Dialogue Summary")
        print(f"  Total exchanges: {len(self.history)}")
        print(f"  Speeches per philosopher:")
        for agent in self.agents:
            count = sum(1 for item in self.history if item['agent'] == agent.name)
            print(f"    - {agent.name}: {count}")
        print(f"{'='*60}\n")
