# controller/question_handler.py

import asyncio
from .target_detector import TargetDetector


class QuestionHandler:
    """
    Handles player questions during dialogue interrupts.

    Supports:
    - Targeted questions (only specific philosophers respond)
    - Exclusion patterns (all except specific philosophers)
    - General questions (all respond)
    """

    def __init__(self, dialogue_controller):
        """
        Parameters
        ----------
        dialogue_controller : DialogueController
            Reference to the main controller
        """
        self.controller = dialogue_controller
        self.target_detector = TargetDetector(self.controller.agents)

    async def handle_player_question(self, topic: str):
        """
        Handle player question - targeted or all philosophers respond.

        Parameters
        ----------
        topic : str
            Current dialogue topic
        """
        loop = asyncio.get_event_loop()
        question = await loop.run_in_executor(None, input, "\nYour question: ")
        question = question.strip()

        if not question:
            print("No question provided.")
            return

        # Reset interrupt flag (the Enter press to submit question may have triggered it)
        self.controller.is_interrupted = False

        print(f"\n[You ask]: {question}\n")

        # Detect if question targets specific philosophers
        target_names = self.target_detector.detect_targets(question)

        # Determine who should respond
        if target_names:
            # Only mentioned philosophers respond
            responding_agents = [a for a in self.controller.agents if a.name in target_names]
            print(f"💡 Directing question to: {', '.join(target_names)}\n")
        else:
            # Everyone responds
            responding_agents = self.controller.agents

        # Each selected philosopher responds to the player's question
        for idx, agent in enumerate(responding_agents):
            # Check for interrupt before each response
            if self.controller.is_interrupted or self.controller.should_stop:
                print("\n[Q&A interrupted by user]\n")
                break

            print(f"{agent.name} responding...")

            context = self.controller._build_context()
            context_block = f"Recent dialogue:\n{context}\n\n" if context else ""

            user_prompt = (
                f"Debate topic: {topic}\n\n"
                f"{context_block}"
                f"A participant asks: {question}\n\n"
                f"Respond as {agent.name} in 1-3 concise sentences."
            )

            # Generate response asynchronously to allow interrupts
            generation_task = loop.run_in_executor(
                None,
                self.controller.model_manager.chat_once,
                agent.model_key,
                agent.system_prompt,
                user_prompt,
                80,
                0.7,
            )

            reply = await generation_task

            # Check for interrupt after generation
            if self.controller.is_interrupted or self.controller.should_stop:
                print("\n[Q&A interrupted by user]\n")
                break

            reply = reply.replace("\n", " ").strip()

            # Remove agent name if it appears at the start of the reply
            if reply.startswith(agent.name + ":"):
                reply = reply[len(agent.name) + 1:].strip()
            elif reply.startswith(agent.name):
                reply = reply[len(agent.name):].strip()
                if reply.startswith(":"):
                    reply = reply[1:].strip()

            agent.add_memory(user_prompt, reply)
            self.controller.history.append({"agent": agent.name, "response": reply, "is_qa": True})

            # Log Q&A utterance
            if self.controller.logger:
                self.controller.logger.log_utterance(
                    speaker=agent.name,
                    content=reply,
                    turn=self.controller.speech_count,
                    is_qa=True,
                    metadata={"question": question}
                )

            print(f"{agent.name}: {reply}\n")

            # Check for interrupt before TTS
            if self.controller.is_interrupted or self.controller.should_stop:
                break

            # TTS for Q&A
            if self.controller.tts is not None:
                try:
                    await self.controller.tts.speak(
                        speaker_name=agent.name,
                        text=reply,
                        turn=self.controller.speech_count,
                        index=idx,
                        is_qa=True,
                    )
                except Exception as e:
                    print(f"[TTS] Error during speak(): {e}")

            # Check for interrupt after TTS
            if self.controller.is_interrupted or self.controller.should_stop:
                break

            await asyncio.sleep(0.05)
