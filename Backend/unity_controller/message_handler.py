# unity_controller/message_handler.py
# Handles WebSocket messages from Unity

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .controller import UnityDialogueController


class MessageHandler:
    """Handles WebSocket messages received from Unity."""

    def __init__(self, controller: 'UnityDialogueController'):
        self.controller = controller

    async def handle_message(self, message: dict):
        """
        Handle messages received from Unity.

        Supported events:
        - pause/interrupt: Pause the dialogue
        - resume: Resume the dialogue
        - stop/exit: Stop the dialogue
        - set_conviviality: Change conviviality level
        - start_dialogue: Start with topic and settings
        - ask_question: Ask a question
        - stop_speaker: Skip current speaker
        - change_topic: Change debate topic
        """
        event = message.get("event", "")
        data = message.get("data", {})

        if event == "pause":
            await self._handle_pause()

        elif event == "interrupt":
            await self._handle_interrupt()

        elif event == "resume":
            await self._handle_resume()

        elif event == "stop" or event == "exit":
            self._handle_stop()

        elif event == "set_conviviality":
            self._handle_set_conviviality(data)

        elif event == "start_dialogue":
            self._handle_start_dialogue(data)

        elif event == "ask_question":
            await self._handle_ask_question(data)

        elif event == "stop_speaker":
            await self._handle_stop_speaker()

        elif event == "change_topic":
            await self._handle_change_topic(data)

        elif event == "transcribe_audio":
            await self._handle_transcribe_audio(data)

    async def _handle_pause(self):
        """Handle pause event - let current speaker finish, then pause."""
        self.controller.is_paused = True
        self.controller.was_interrupted = False
        self.controller.resume_requested = False
        self.controller.resume_same_speaker = False
        print("[Unity] Pause received - will pause after current speaker finishes")
        # Do NOT cancel the task; the dialogue loop will check is_paused
        # and send 'paused' event after the current turn completes.

    async def _handle_interrupt(self):
        """Handle interrupt event - immediately cancel current speech."""
        self.controller.is_paused = True
        self.controller.was_interrupted = True
        self.controller.resume_requested = False
        self.controller.resume_same_speaker = False
        print("[Unity] Interrupt received - cancelling main loop task immediately")

        # Only cancel the task if it's a normal dialogue loop (not Q&A)
        # Q&A handler checks is_paused internally to support continue/skip
        if not self.controller.is_answering_question:
            if self.controller.main_loop_task and not self.controller.main_loop_task.done():
                self.controller.main_loop_task.cancel()

        # Send paused directly (don't rely on monitor loop)
        await self.controller.ws_server.send_event("paused", {})

    async def _handle_resume(self):
        """Handle resume event."""
        self.controller.is_paused = False
        self.controller.was_interrupted = False
        self.controller.resume_requested = True
        print("[Unity] Resume received")

        # Don't restart dialogue loop if Q&A is running (it handles resume internally)
        if not self.controller.is_answering_question:
            if self.controller.main_loop_task is None or self.controller.main_loop_task.done():
                from .dialogue_loop import run_dialogue_loop
                self.controller.main_loop_task = asyncio.create_task(
                    run_dialogue_loop(self.controller)
                )

    def _handle_stop(self):
        """Handle stop/exit event."""
        self.controller.should_stop = True
        print("[Unity] Stop/Exit received")

    def _handle_set_conviviality(self, data: dict):
        """Handle set_conviviality event."""
        new_value = data.get("value", 0.5)
        self.controller.conviviality = max(0.0, min(1.0, new_value))
        print(f"[Unity] Conviviality set to: {self.controller.conviviality}")

    def _handle_start_dialogue(self, data: dict):
        """Handle start_dialogue event."""
        self.controller.pending_topic = data.get("topic", "What is the meaning of freedom?")
        new_conv = data.get("conviviality", 0.5)
        self.controller.conviviality = max(0.0, min(1.0, new_conv))

        # Support dynamic agent selection
        selected_agents = data.get("selected_agents")
        if selected_agents:
            self.controller.agents = [
                a for a in self.controller.all_agents
                if a.name in selected_agents
            ]
            print(f"[Unity] Selected agents: {[a.name for a in self.controller.agents]}")

        self.controller.settings_received = True
        print(f"[Unity] Start dialogue - Topic: {self.controller.pending_topic}, "
              f"Conviviality: {self.controller.conviviality}")

    async def _handle_ask_question(self, data: dict):
        """Handle ask_question event - runs as task so pause/interrupt can be processed."""
        question = data.get("question")
        target_agents = data.get("target_agents", [])
        if question:
            print(f"[Unity] Received question: {question}, targets: {target_agents}")

            # Cancel current main loop task
            if self.controller.main_loop_task and not self.controller.main_loop_task.done():
                self.controller.main_loop_task.cancel()
                try:
                    await self.controller.main_loop_task
                except asyncio.CancelledError:
                    pass

            # Run as task so handle_message returns immediately
            # This allows pause/interrupt messages to be processed during Q&A
            from .question_handler import handle_question
            self.controller.main_loop_task = asyncio.create_task(
                handle_question(self.controller, question, target_agents=target_agents)
            )

    async def _handle_stop_speaker(self):
        """Handle stop_speaker event - skip to next speaker."""
        print("[Unity] Stop speaker - skipping to next")
        self.controller.is_paused = False
        self.controller.resume_same_speaker = False

        if self.controller.main_loop_task and not self.controller.main_loop_task.done():
            self.controller.main_loop_task.cancel()

        from .dialogue_loop import run_dialogue_loop
        self.controller.main_loop_task = asyncio.create_task(
            run_dialogue_loop(self.controller)
        )

    async def _handle_transcribe_audio(self, data: dict):
        """Handle transcribe_audio event - transcribe user audio via Azure STT."""
        audio_base64 = data.get("audio", "")
        if not audio_base64:
            print("[Unity] transcribe_audio received with no audio data")
            await self.controller.ws_server.send_transcription_result("")
            return

        print(f"[Unity] Received audio for transcription ({len(audio_base64)} chars base64)")
        try:
            text = await self.controller.stt.transcribe_async(audio_base64)
            await self.controller.ws_server.send_transcription_result(text)
        except Exception as e:
            print(f"[Unity] Transcription error: {e}")
            await self.controller.ws_server.send_transcription_result("")

    async def _handle_change_topic(self, data: dict):
        """Handle change_topic event."""
        new_topic = data.get("topic")
        if new_topic:
            print(f"[Unity] Topic changed to: {new_topic}")
            self.controller.current_topic = new_topic
            self.controller.dialogue_topic = new_topic

            # Clear dialogue history so philosophers don't reference old topic
            self.controller.history.clear()
            self.controller.last_speaker = None
            self.controller.speech_count = 0

            # Cancel current task and restart
            if self.controller.main_loop_task and not self.controller.main_loop_task.done():
                self.controller.main_loop_task.cancel()

            self.controller.is_paused = False

            # Notify Unity to clear UI and show new topic
            participant_names = [a.name for a in self.controller.agents]
            await self.controller.ws_server.send_dialogue_start(new_topic, participant_names)

            # Send fresh motivation scores
            motivation_scores = {a.name: a.motivation_score for a in self.controller.agents}
            await self.controller.ws_server.send_motivation_update(motivation_scores)

            from .dialogue_loop import run_dialogue_loop
            self.controller.main_loop_task = asyncio.create_task(
                run_dialogue_loop(self.controller)
            )
