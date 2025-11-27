# controller/dialogue_controller.py

import asyncio
from typing import List, Dict, Any

from agents.agents_manager import AgentsManager
from llm.model_manager import ModelManager
from tts.SimpleTTS import SimpleTTS

from .speaker_selector import SpeakerSelector
from .interrupt_handler import InterruptHandler
from .debate_logger import DebateLogger


class DialogueController:
    """
    Main controller for free-form philosophical debates.

    Orchestrates:
    - Speaker selection
    - LLM generation
    - TTS playback
    - User interrupts
    - Q&A sessions
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
            Wrapper around local HF models
        agents_manager : AgentsManager
            Loads Agent objects from YAML configs
        tts_engine : SimpleTTS | None
            Optional TTS engine for speech synthesis
        history_window : int
            Number of recent utterances to include in context
        """
        self.model_manager = model_manager
        self.agents_manager = agents_manager
        self.tts = tts_engine
        self.history_window = history_window

        # Cache agent list
        self.agents = self.agents_manager.get_all_agents()
        if not self.agents:
            raise RuntimeError("No agents loaded from AgentsManager.")

        # Dialogue history
        self.history: List[Dict[str, Any]] = []

        # Control flags
        self.is_interrupted = False
        self.should_stop = False
        self.speech_count = 0

        # Initialize sub-modules
        self.speaker_selector = SpeakerSelector(self.agents, self.history)
        self.interrupt_handler = InterruptHandler(self)
        self.logger = None  # Will be initialized when dialogue starts

    def _build_context(self) -> str:
        """
        Build textual context from recent dialogue.

        Returns
        -------
        str
            Formatted context string
        """
        recent = self.history[-self.history_window :]
        if not recent:
            return ""

        lines = [f"{item['agent']}: {item['response']}" for item in recent]
        return "\n".join(lines)

    async def run_dialogue(self, topic: str):
        """
        Run a free-form debate on the given topic.

        Parameters
        ----------
        topic : str
            The philosophical topic to discuss
        """
        # Initialize logger
        participant_names = [a.name for a in self.agents]
        self.logger = DebateLogger(topic, participant_names)

        # Print header
        print(f"\n{'='*60}")
        print(f"  AI Philosophy Salon")
        print(f"  Topic: {topic}")
        print(f"  Participants: {', '.join(participant_names)}")
        print(f"{'='*60}\n")
        print("💡 Press Enter at any time to interrupt the dialogue.\n")

        # Start background listener for interrupts
        listener_task = asyncio.create_task(self.interrupt_handler.listen_for_interrupt())

        try:
            # Continuous dialogue loop
            while not self.should_stop:
                # Check for interrupt
                if self.is_interrupted:
                    # Log interrupt event
                    self.logger.log_interrupt()

                    # Cancel old listener
                    if listener_task and not listener_task.done():
                        listener_task.cancel()
                        try:
                            await listener_task
                        except asyncio.CancelledError:
                            pass

                    # Handle the interrupt menu
                    await self.interrupt_handler.handle_interrupt_menu(topic)
                    if self.should_stop:
                        break

                    # Restart listener
                    listener_task = asyncio.create_task(self.interrupt_handler.listen_for_interrupt())
                    continue

                # Select next speaker
                speaker = self.speaker_selector.select_next_speaker()

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

                # Generate response
                loop = asyncio.get_event_loop()
                generation_task = loop.run_in_executor(
                    None,
                    self.model_manager.chat_once,
                    speaker.model_key,
                    speaker.system_prompt,
                    user_prompt,
                    80,
                    0.7,
                )

                # Wait for generation to complete (no mid-generation interruption)
                reply = await generation_task

                reply = reply.replace("\n", " ").strip()

                # Clean speaker name from reply
                if reply.startswith(speaker.name + ":"):
                    reply = reply[len(speaker.name) + 1:].strip()
                elif reply.startswith(speaker.name):
                    reply = reply[len(speaker.name):].strip()
                    if reply.startswith(":"):
                        reply = reply[1:].strip()

                # Save to memory and history
                speaker.add_memory(user_prompt, reply)
                self.history.append({"agent": speaker.name, "response": reply})
                self.speech_count += 1

                # Log utterance
                self.logger.log_utterance(
                    speaker=speaker.name,
                    content=reply,
                    turn=self.speech_count,
                    is_qa=False
                )

                print(f"💬 {speaker.name}: {reply}\n")

                # TTS playback (complete before checking interrupt)
                if self.tts is not None:
                    try:
                        await self.tts.speak(
                            speaker_name=speaker.name,
                            text=reply,
                            turn=self.speech_count,
                            index=0,
                            is_qa=False,
                        )
                    except Exception as e:
                        print(f"[TTS] Error during speak(): {e}")

                # Check for interrupt after speech completes
                if self.is_interrupted:
                    continue

                # Small delay before next speech
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

        # Finalize and export logs
        self.logger.finalize()
        self.logger.export_all()

        # Show summary
        self._print_summary()

    def _print_summary(self):
        """Print dialogue summary statistics."""
        print(f"\n{'='*60}")
        print(f"  Dialogue Summary")
        print(f"  Total exchanges: {len(self.history)}")
        print(f"  Speeches per philosopher:")
        for agent in self.agents:
            count = sum(1 for item in self.history if item['agent'] == agent.name)
            print(f"    - {agent.name}: {count}")
        print(f"{'='*60}\n")
