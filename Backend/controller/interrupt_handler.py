# controller/interrupt_handler.py

import asyncio
import sys


class InterruptHandler:
    """
    Handles user interrupts during dialogue.

    Provides:
    - Background listening for Enter key press
    - Interrupt menu (ask question, continue, end)
    - Interrupt state management
    """

    def __init__(self, dialogue_controller):
        """
        Parameters
        ----------
        dialogue_controller : DialogueController
            Reference to the main controller
        """
        self.controller = dialogue_controller

    async def listen_for_interrupt(self):
        """
        Background task that listens for Enter key press.
        Sets interrupt flag when user presses Enter.
        """
        loop = asyncio.get_event_loop()

        try:
            # Wait for Enter key (blocking call in executor)
            await loop.run_in_executor(None, input, "")
            if not self.controller.should_stop:
                self.controller.is_interrupted = True
                print("\n>>> Interrupting dialogue... <<<\n")
        except Exception as e:
            if not self.controller.should_stop:
                print(f"[Error in interrupt listener]: {e}")

    async def handle_interrupt_menu(self, topic: str):
        """
        Show menu when user interrupts the dialogue.

        Parameters
        ----------
        topic : str
            Current dialogue topic
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

        # Delay to allow input buffer to clear and prevent spurious interrupts
        await asyncio.sleep(0.3)

        if choice == 'q':
            # Import here to avoid circular dependency
            from .question_handler import QuestionHandler
            handler = QuestionHandler(self.controller)
            await handler.handle_player_question(topic)
            # After Q&A, ask again
            await self.handle_interrupt_menu(topic)
        elif choice == 'e':
            self.controller.should_stop = True
            self.controller.is_interrupted = False  # Reset interrupt flag
            print("\n======== Dialogue Ended by User ========\n")
        else:
            # Continue - reset interrupt flag
            self.controller.is_interrupted = False
            print("\n>>> Resuming dialogue... <<<\n")
