# main_unity.py
# Main entry point for Unity frontend integration

import asyncio
import os
from agents.agents_manager import AgentsManager
from controller import TurnTakingController
from llm.cloud_model_manager import CloudModelManager as ModelManager
from tts.AzureTTS import AzureTTS
from unity_bridge import WebSocketServer


class UnityDialogueController:
    """
    Extended dialogue controller with WebSocket support for Unity frontend.
    """

    def __init__(
        self,
        model_manager: ModelManager,
        agents_manager: AgentsManager,
        tts_engine: AzureTTS,
        websocket_server: WebSocketServer,
        history_window: int = 8,
        conviviality: float = 0.5
    ):
        self.model_manager = model_manager
        self.agents_manager = agents_manager
        self.tts = tts_engine
        self.ws_server = websocket_server
        self.history_window = history_window
        self.conviviality = conviviality

        self.agents = self.agents_manager.get_all_agents()
        self.history = []
        self.is_interrupted = False
        self.should_stop = False
        self.speech_count = 0

        # Initial settings from Unity
        self.pending_topic = None
        self.settings_received = False

        # Pause state
        self.is_paused = False
        self.resume_requested = False

        # Import sub-modules
        from controller.speaker_selector import SpeakerSelector
        from controller.motivation_scorer import MotivationScorer
        from controller.stance_analyzer import StanceAnalyzer
        from controller.debate_logger import DebateLogger

        self.speaker_selector = SpeakerSelector(self.agents, self.history)
        self.motivation_scorer = MotivationScorer(self.model_manager)
        self.stance_analyzer = StanceAnalyzer(self.model_manager)
        self.DebateLogger = DebateLogger
        self.logger = None

    def _build_context(self) -> str:
        """Build context from recent dialogue."""
        recent = self.history[-self.history_window:]
        if not recent:
            return ""
        lines = [f"{item['agent']}: {item['response']}" for item in recent]
        return "\n".join(lines)

    async def handle_websocket_message(self, message: dict):
        """Handle messages received from Unity."""
        event = message.get("event", "")

        if event == "interrupt" or event == "pause":
            self.is_paused = True
            self.resume_requested = False
            print("[Unity] Pause received - will pause after current speaker finishes")
            # Notify Unity that we're entering pause state
            await self.ws_server.send_event("paused", {})

        elif event == "resume":
            self.is_paused = False
            self.resume_requested = True
            print("[Unity] Resume received")

        elif event == "stop" or event == "exit":
            self.should_stop = True
            print("[Unity] Stop/Exit received")

        elif event == "set_conviviality":
            new_value = message.get("data", {}).get("value", 0.5)
            self.conviviality = max(0.0, min(1.0, new_value))
            print(f"[Unity] Conviviality set to: {self.conviviality}")

        elif event == "start_dialogue":
            data = message.get("data", {})
            self.pending_topic = data.get("topic", "What is the meaning of freedom?")
            new_conv = data.get("conviviality", 0.5)
            self.conviviality = max(0.0, min(1.0, new_conv))
            self.settings_received = True
            print(f"[Unity] Start dialogue received - Topic: {self.pending_topic}, Conviviality: {self.conviviality}")

        elif event == "ask_question":
            # Handle directed question
            data = message.get("data", {})
            agent_name = data.get("agent")
            question = data.get("question")
            if agent_name and question:
                await self._handle_question(agent_name, question)

    async def _handle_question(self, agent_name: str, question: str):
        """Handle a directed question to a specific agent."""
        # Find the agent
        agent = None
        for a in self.agents:
            if a.name.lower() == agent_name.lower():
                agent = a
                break

        if not agent:
            print(f"[Unity] Agent not found: {agent_name}")
            return

        # Notify Unity
        await self.ws_server.send_agent_speaking(agent.name)

        # Generate response
        user_prompt = (
            f"A question has been directed to you: {question}\n"
            f"Please respond directly and thoughtfully in 1-3 sentences."
        )

        loop = asyncio.get_event_loop()
        reply = await loop.run_in_executor(
            None,
            self.model_manager.chat_once,
            agent.model_key,
            agent.system_prompt,
            user_prompt,
            150,
            0.7,
        )

        reply = reply.replace("\n", " ").strip()

        # Generate TTS and viseme data (Azure returns both)
        audio_path, viseme_data = await self._generate_speech(agent.name, reply, is_qa=True)

        # Send to Unity
        await self.ws_server.send_agent_response(
            agent_name=agent.name,
            text=reply,
            audio_path=audio_path,
            viseme_data=viseme_data,
            stance="neutral",
            turn=self.speech_count
        )

        # Update history
        self.history.append({"agent": agent.name, "response": reply})
        self.speech_count += 1

    async def _generate_speech(self, speaker_name: str, text: str, is_qa: bool = False):
        """Generate TTS audio and viseme data using Azure TTS."""
        if self.tts is None:
            return "", []

        try:
            # AzureTTS.speak_async returns (audio_path, viseme_data)
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
        """Run dialogue with Unity frontend integration."""
        # Set WebSocket message handler first to receive start_dialogue event
        self.ws_server.set_message_callback(self.handle_websocket_message)

        # Wait for Unity to connect
        print("\n" + "="*60)
        print("  AI Philosophy Salon - Unity Mode")
        print("  Waiting for Unity to connect...")
        print(f"  WebSocket: ws://{self.ws_server.host}:{self.ws_server.port}")
        print("="*60 + "\n")

        # Wait for at least one client
        while not self.ws_server.has_clients:
            await asyncio.sleep(0.5)
            print(".", end="", flush=True)

        print("\n[Unity] Client connected!")
        print("[Unity] Waiting for start_dialogue message from Unity...")

        # Wait for Unity to send start_dialogue with topic and conviviality
        while not self.settings_received:
            await asyncio.sleep(0.1)

        # Use topic from Unity or fallback to parameter
        actual_topic = self.pending_topic or topic or "What is the meaning of freedom?"

        # Initialize logger with settings from Unity
        participant_names = [a.name for a in self.agents]
        self.logger = self.DebateLogger(actual_topic, participant_names, conviviality=self.conviviality)
        print(f"[Logger] Session initialized with conviviality: {self.conviviality}")
        topic = actual_topic

        # Notify Unity that dialogue is starting
        await self.ws_server.send_dialogue_start(topic, participant_names)

        # Send initial motivation scores
        motivation_scores = {agent.name: agent.motivation_score for agent in self.agents}
        await self.ws_server.send_motivation_update(motivation_scores)

        print(f"\n[Dialogue] Starting topic: {topic}\n")

        # Main dialogue loop
        try:
            while not self.should_stop:
                # Check for pause state - wait until resumed
                while self.is_paused and not self.should_stop:
                    await asyncio.sleep(0.1)

                if self.should_stop:
                    break

                # Select next speaker
                speaker = self.speaker_selector.select_next_speaker()

                # Notify Unity that agent is thinking
                await self.ws_server.send_agent_speaking(speaker.name)
                print(f"\n{speaker.name} is thinking...")

                # Analyze stance
                stance = self.stance_analyzer.analyze_stance(
                    agent=speaker,
                    recent_history=self.history[-3:],
                    conviviality=self.conviviality
                )

                # Get tone instruction
                tone_instruction = self.stance_analyzer.get_tone_instruction(
                    stance=stance,
                    conviviality=self.conviviality
                )

                # Build context and prompt
                context = self._build_context()
                context_block = f"Recent dialogue:\n{context}\n\n" if context else ""

                user_prompt = (
                    f"Debate topic: {topic}\n\n"
                    f"{context_block}"
                    f"Respond to this debate directly in first person.\n"
                    f"- Use 1–3 concise sentences.\n"
                    f"- {tone_instruction}\n"
                    f"- Avoid repeating what has already been said.\n"
                    f"- Do NOT say 'As {speaker.name}' or refer to yourself in third person.\n"
                )

                # Generate response
                loop = asyncio.get_event_loop()
                reply = await loop.run_in_executor(
                    None,
                    self.model_manager.chat_once,
                    speaker.model_key,
                    speaker.system_prompt,
                    user_prompt,
                    150,
                    0.7,
                )

                if self.is_interrupted or self.should_stop:
                    continue

                reply = reply.replace("\n", " ").strip()

                # Clean speaker name from reply
                if reply.startswith(speaker.name + ":"):
                    reply = reply[len(speaker.name) + 1:].strip()
                elif reply.startswith(speaker.name):
                    reply = reply[len(speaker.name):].strip()
                    if reply.startswith(":"):
                        reply = reply[1:].strip()

                # Generate TTS audio and viseme data (Azure returns both)
                audio_path, viseme_data = await self._generate_speech(speaker.name, reply)

                # Send response to Unity
                await self.ws_server.send_agent_response(
                    agent_name=speaker.name,
                    text=reply,
                    audio_path=audio_path,
                    viseme_data=viseme_data,
                    stance=stance,
                    turn=self.speech_count
                )

                # Update local state
                speaker.add_memory(user_prompt, reply)
                self.history.append({"agent": speaker.name, "response": reply})
                self.speech_count += 1

                # Log utterance
                motivation_snapshot = {agent.name: agent.motivation_score for agent in self.agents}
                self.logger.log_utterance(
                    speaker=speaker.name,
                    content=reply,
                    turn=self.speech_count,
                    is_qa=False,
                    stance=stance,
                    motivation_scores=motivation_snapshot
                )

                # Update motivation scores
                self.motivation_scorer.analyze_utterance(
                    speaker_name=speaker.name,
                    text=reply,
                    all_agents=self.agents,
                    recent_history=self.history[-5:],
                    conviviality=self.conviviality
                )

                # Send updated motivation scores to Unity
                motivation_scores = {agent.name: agent.motivation_score for agent in self.agents}
                await self.ws_server.send_motivation_update(motivation_scores)

                print(f"[{speaker.name}] {reply}\n")

                # Wait for audio to finish playing before next turn
                # Estimate duration: ~150 words per minute, average 5 chars per word
                words = len(reply.split())
                estimated_duration = max(2.0, words / 2.5)  # At least 2 seconds
                thinking_pause = 3.0  # Extra pause for natural pacing
                total_wait = estimated_duration + thinking_pause
                print(f"[Dialogue] Waiting {total_wait:.1f}s (audio: {estimated_duration:.1f}s + thinking: {thinking_pause:.1f}s)")
                await asyncio.sleep(total_wait)

        except asyncio.CancelledError:
            print("\n[Dialogue] Cancelled")
        finally:
            # Finalize and export logs
            self.logger.finalize()
            self.logger.export_all()

            # Send end notification to Unity
            summary = {
                "total_turns": self.speech_count,
                "participants": [a.name for a in self.agents]
            }
            await self.ws_server.send_dialogue_end(summary)

            print("\n[Dialogue] Ended")


async def main():
    """Main entry point for Unity mode."""

    # 1. Initialize components (using OpenAI API for fast responses)
    model_manager = ModelManager(
        api_key="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"
    )
    agents_manager = AgentsManager(cfg_dir="agents/configs")

    # Build voice map from agent configs
    voice_map = {agent.name: agent.voice for agent in agents_manager.get_all_agents()}

    # Initialize Azure TTS with viseme support (no auto_play, Unity handles playback)
    tts_engine = AzureTTS(
        subscription_key="GGOrbCc2fBt6m6hbwdrZH0oi8VyX7uq1Vl2wvb63X8XJ6b0PScL2JQQJ99CAACYeBjFXJ3w3AAAYACOGEacn",
        region="eastus",
        voice_map=voice_map,
        output_dir="tts_output",
        auto_play=False  # Unity frontend handles audio playback
    )
    tts_engine.clear_output()

    # 2. Start WebSocket server
    ws_server = WebSocketServer(host="localhost", port=8765)
    await ws_server.start()

    # 3. Create controller
    controller = UnityDialogueController(
        model_manager=model_manager,
        agents_manager=agents_manager,
        tts_engine=tts_engine,
        websocket_server=ws_server,
        history_window=8,
        conviviality=0.5  # Default, can be changed by Unity
    )

    # 4. Run dialogue (topic will be received from Unity)
    try:
        await controller.run_dialogue()
    finally:
        await ws_server.stop()


if __name__ == "__main__":
    # Change to Backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(main())
