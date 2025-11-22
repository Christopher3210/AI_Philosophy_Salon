import asyncio

class TurnTakingController:
    def __init__(self, llm_client, agents_manager, tts_engine):
        """
        llm_client:   your LLMClient instance
        agents_manager: manages system prompts for philosophers
        tts_engine:   SimpleTTS instance (Edge-TTS version)
        """
        self.llm = llm_client
        self.agents = agents_manager
        self.tts = tts_engine

    async def run_dialogue(self, topic: str = "What is happiness?"):
        """Main dialogue loop with turn-taking + optional Q&A."""
        print(f"Host: Today we discuss — {topic}\n")

        last_msg = f"Host: {topic} Please answer briefly."
        turn = 1

        # ===== Main loop =====
        while True:
            print(f"--- Turn {turn} ---\n")

            # ===== Aristotle speaks =====
            a_prompt = f"{last_msg}\nAristotle, speak in 1-3 sentences."
            a_reply = self.llm.chat_once(
                self.agents.get_system_prompt("aristotle"), 
                a_prompt
            )
            print(f"Aristotle: {a_reply}\n")

            # Play Aristotle's audio
            await self.tts.speak(a_reply, filename="aristotle_turn.mp3")

            # ===== Russell responds =====
            r_prompt = (
                f"Aristotle just said:\n\"{a_reply}\"\n\n"
                "Russell, respond briefly and challenge one key point."
            )
            r_reply = self.llm.chat_once(
                self.agents.get_system_prompt("russell"), 
                r_prompt
            )
            print(f"Russell: {r_reply}\n")

            # Play Russell's audio
            await self.tts.speak(r_reply, filename="russell_turn.mp3")

            # Update conversation state for next turn
            last_msg = (
                f"Russell just said:\n\"{r_reply}\"\n\n"
                "Aristotle, respond briefly (1-3 sentences)."
            )

            # ===== After each turn: allow user action =====
            print("Options:")
            print("  [Enter]  → continue the debate")
            print("  q        → ask a question to a philosopher")
            print("  stop     → end the conversation")
            choice = input("Your choice: ").strip().lower()

            if choice == "stop":
                print("\nHost: The conversation is finished. Thank you both.")
                break

            # ===== Q&A Mode =====
            if choice == "q":
                while True:
                    target = input("Ask whom? (a = Aristotle, r = Russell): ").strip().lower()

                    if target.startswith("a"):
                        agent_key = "aristotle"
                        display_name = "Aristotle"
                    elif target.startswith("r"):
                        agent_key = "russell"
                        display_name = "Russell"
                    else:
                        print("Host: I did not understand.\n")
                        continue

                    # Human question
                    question = input(f"Your question to {display_name}: ")

                    sys_prompt = self.agents.get_system_prompt(agent_key)
                    user_prompt = (
                        "The human host is asking a question during the debate.\n"
                        f"Question: {question}\n\n"
                        "Answer in 1-3 short sentences and stay in character."
                    )

                    # LLM answer
                    answer = self.llm.chat_once(sys_prompt, user_prompt)
                    print(f"{display_name}: {answer}\n")

                    # Play answer audio
                    await self.tts.speak(answer, filename=f"{agent_key}_answer.mp3")

                    # After answering, allow more questions or return
                    print("Question options:")
                    print("  [Enter] → ask another question")
                    print("  back    → return to the main debate")
                    print("  stop    → end the conversation")
                    follow = input("Your choice: ").strip().lower()

                    if follow == "stop":
                        print("\nHost: The conversation is finished. Thank you both.")
                        return

                    if follow == "back":
                        break  # Return to main loop

                    # If Enter → ask another question

            # Continue to next turn
            turn += 1

        print("Host: We will stop here.\n")
