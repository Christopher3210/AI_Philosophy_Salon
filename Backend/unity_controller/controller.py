# unity_controller/controller.py
# Main Unity dialogue controller

import asyncio
from typing import List, Dict, Any

from agents.agents_manager import AgentsManager
from llm.cloud_model_manager import CloudModelManager as ModelManager
from tts.AzureTTS import AzureTTS
from tts.AzureSTT import AzureSTT
from unity_bridge import WebSocketServer

from controller.speaker_selector import SpeakerSelector
from controller.motivation_scorer import MotivationScorer
from controller.stance_analyzer import StanceAnalyzer
from controller.debate_logger import DebateLogger
from controller.target_detector import TargetDetector

from .message_handler import MessageHandler
from .dialogue_loop import run_dialogue_loop


class UnityDialogueController:
    """
    Main dialogue controller with WebSocket support for Unity frontend.

    Orchestrates:
    - WebSocket communication with Unity
    - Speaker selection and turn-taking
    - LLM response generation
    - TTS audio generation with viseme data
    - Pause/resume and question handling
    """

    def __init__(
        self,
        model_manager: ModelManager,
        agents_manager: AgentsManager,
        tts_engine: AzureTTS,
        websocket_server: WebSocketServer,
        stt_engine: AzureSTT = None,
        history_window: int = 8,
        conviviality: float = 0.5
    ):
        """
        Parameters
        ----------
        model_manager : ModelManager
            LLM manager for generating responses
        agents_manager : AgentsManager
            Loads agents from config files
        tts_engine : AzureTTS
            Text-to-speech engine with viseme support
        websocket_server : WebSocketServer
            WebSocket server for Unity communication
        stt_engine : AzureSTT, optional
            Speech-to-text engine for voice input
        history_window : int
            Number of recent utterances to include in context
        conviviality : float
            Debate intensity (0.0 = confrontational, 1.0 = friendly)
        """
        self.model_manager = model_manager
        self.agents_manager = agents_manager
        self.tts = tts_engine
        self.stt = stt_engine
        self.ws_server = websocket_server
        self.history_window = history_window
        self.conviviality = conviviality

        # Agent management
        self.all_agents = self.agents_manager.get_all_agents()
        self.agents = self.all_agents  # Can be filtered by start_dialogue

        # Dialogue state
        self.history: List[Dict[str, Any]] = []
        self.should_stop = False
        self.speech_count = 0
        self.last_speaker = None

        # Unity settings
        self.pending_topic = None
        self.settings_received = False

        # Pause state
        self.is_paused = False
        self.was_interrupted = False
        self.resume_requested = False
        self.is_answering_question = False
        self.resume_same_speaker = False

        # Task management
        self.main_loop_task = None
        self.prefetch_task = None  # Pre-computation task for next turn
        self.dialogue_topic = None
        self.current_topic = None

        # Sub-modules
        self.speaker_selector = SpeakerSelector(self.agents, self.history)
        self.motivation_scorer = MotivationScorer(self.model_manager)
        self.stance_analyzer = StanceAnalyzer(self.model_manager)
        self.target_detector = TargetDetector(self.agents, model_manager=self.model_manager)
        self.message_handler = MessageHandler(self)

        # Logger (initialized when dialogue starts)
        self.logger = None

    def reset(self):
        """Reset all dialogue state for a new session."""
        self.history.clear()
        self.should_stop = False
        self.speech_count = 0
        self.last_speaker = None
        self.pending_topic = None
        self.settings_received = False
        self.is_paused = False
        self.was_interrupted = False
        self.resume_requested = False
        self.is_answering_question = False
        self.resume_same_speaker = False
        self.main_loop_task = None
        self.prefetch_task = None
        self.dialogue_topic = None
        self.current_topic = None
        self.logger = None
        self.agents = self.all_agents
        self.speaker_selector = SpeakerSelector(self.agents, self.history)
        self.target_detector = TargetDetector(self.agents, model_manager=self.model_manager)
        # Reset agent motivation scores
        for agent in self.all_agents:
            agent.motivation_score = 5.0
        print("[Controller] State reset for new session")

    def build_context(self) -> str:
        """Build context from recent dialogue history."""
        recent = self.history[-self.history_window:]
        if not recent:
            return ""
        lines = [f"{item['agent']}: {item['response']}" for item in recent]
        return "\n".join(lines)

    async def generate_speech(self, speaker_name: str, text: str, is_qa: bool = False):
        """Generate TTS audio and viseme data."""
        if self.tts is None:
            return "", []

        try:
            audio_path, viseme_data = await self.tts.speak_async(
                speaker_name=speaker_name,
                text=text,
                turn=self.speech_count,
                index=0,
                is_qa=is_qa
            )
            return audio_path or "", viseme_data or []
        except Exception as e:
            print(f"[TTS] Error: {e}")
            return "", []

    async def run_dialogue(self, topic: str = None):
        """
        Run dialogue with Unity frontend integration.

        Parameters
        ----------
        topic : str, optional
            Fallback topic if Unity doesn't provide one
        """
        # Set WebSocket message handler
        self.ws_server.set_message_callback(self.message_handler.handle_message)

        # Wait for Unity to connect
        print("\n" + "=" * 60)
        print("  AI Philosophy Salon - Unity Mode")
        print("  Waiting for Unity to connect...")
        print(f"  WebSocket: ws://{self.ws_server.host}:{self.ws_server.port}")
        print("=" * 60 + "\n")

        while not self.ws_server.has_clients:
            await asyncio.sleep(0.5)
            print(".", end="", flush=True)

        print("\n[Unity] Client connected!")
        print("[Unity] Waiting for start_dialogue message from Unity...")

        # Wait for Unity to send start_dialogue
        while not self.settings_received:
            await asyncio.sleep(0.1)

        # Use topic from Unity or fallback
        actual_topic = self.pending_topic or topic or "What is the meaning of freedom?"
        self.current_topic = actual_topic
        self.dialogue_topic = actual_topic

        # Update speaker selector with current agents (may have been filtered)
        self.speaker_selector = SpeakerSelector(self.agents, self.history)
        self.target_detector = TargetDetector(self.agents, model_manager=self.model_manager)

        # Initialize logger
        participant_names = [a.name for a in self.agents]
        self.logger = DebateLogger(actual_topic, participant_names, conviviality=self.conviviality)
        print(f"[Logger] Session initialized with conviviality: {self.conviviality}")

        # Notify Unity that dialogue is starting
        await self.ws_server.send_dialogue_start(actual_topic, participant_names)

        # Send initial motivation scores
        motivation_scores = {agent.name: agent.motivation_score for agent in self.agents}
        await self.ws_server.send_motivation_update(motivation_scores)

        print(f"\n[Dialogue] Starting topic: {actual_topic}\n")

        # Start main dialogue loop as a cancellable task
        self.main_loop_task = asyncio.create_task(run_dialogue_loop(self))

        # Monitor loop - cleans up done tasks.
        # paused events are sent by dialogue_loop (natural) or message_handler (interrupt).
        try:
            while not self.should_stop:
                if self.main_loop_task and self.main_loop_task.done():
                    try:
                        self.main_loop_task.result()
                    except asyncio.CancelledError:
                        pass  # Interrupt handler already sent paused
                    except Exception as e:
                        print(f"[Dialogue] Task error: {e}")
                    self.main_loop_task = None

                await asyncio.sleep(0.2)

        except asyncio.CancelledError:
            print("\n[Dialogue] Run cancelled")
        finally:
            # Cancel prefetch if running
            if self.prefetch_task and not self.prefetch_task.done():
                self.prefetch_task.cancel()
                try:
                    await self.prefetch_task
                except asyncio.CancelledError:
                    pass

            # Cancel main loop if still running
            if self.main_loop_task and not self.main_loop_task.done():
                self.main_loop_task.cancel()
                try:
                    await self.main_loop_task
                except asyncio.CancelledError:
                    pass

            # Finalize and export logs
            if self.logger:
                self.logger.finalize()
                self.logger.export_all()

            # Send end notification to Unity
            summary = {
                "total_turns": self.speech_count,
                "participants": [a.name for a in self.agents]
            }
            await self.ws_server.send_dialogue_end(summary)

            print("\n[Dialogue] Ended")
