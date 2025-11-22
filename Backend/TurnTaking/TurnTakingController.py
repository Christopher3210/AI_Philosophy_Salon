import asyncio

class TurnTakingController:
    def __init__(self, llm_client, agents_manager, tts_engine):
        """
        llm_client:     LLMClient instance
        agents_manager: manages system prompts for philosophers
        tts_engine:     SimpleTTS instance (Edge-TTS)
        """
        self.llm = llm_client
        self.agents = agents_manager
        self.tts = tts_engine

    async def run_dialogue(self, topic: str = "What is happiness?"):
        """Main turn-taking loop + optional Q&A mode."""
        print(f"Host: Today we discuss — {topic}\n")

        last_msg = f"Host: {topic} Please answer briefly."
        turn = 1

        # ===== Main loop =====
        while True:
            print(f"--- Turn {turn} ---\n")

            # ================== Aristotle ==================
            a_prompt = f"{last_msg}\nAristotle, speak in 1-3 sentences."
            a_reply = self.llm.chat_once(
                self.agents.get_system_prompt("aristotle"),
                a_prompt
            )
            print(f"Aristotle: {a_reply}\n")

            # TTS Aristotle (index 1)
            await self.tts.speak("Aristotle", a_reply, turn, 1)

            # ================== Russell ==================
            r_prompt = (
                f"Aristotle just said:\n\"{a_reply}\"\n\n"
                "Russell, respond briefly and challenge one key point."
            )
            r_reply = self.llm.chat_once(
                self.agents.get_system_prompt("russell"),
                r_prompt
            )
            print(f"Russell: {r_reply}\n")

            # TTS Russell (index 2)
            await self.tts.speak("Russell", r_reply, turn, 2)

            # Next turn context
            last_msg = (
                f"Russell just said:\n\"{r_reply}\"\n\n"
                "Aristotle, respond briefly (1-3 sentences)."
            )

            # MENU
            print("Options:")
            print("  [Enter]  → continue the debate")
            print("  q        → ask a question")
            print("  stop     → end the conversation")

            choice = input("Your choice: ").strip().lower()

            if choice == "stop":
                print("\nHost: The conversation is finished. Thank you both.")
                break

            # ================== Q&A MODE ==================
            if choice == "q":
                qa_index = 3   # independent numbering for Q&A

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

                    question = input(f"Your question to {display_name}: ")

                    # Build prompt
                    sys_prompt = self.agents.get_system_prompt(agent_key)
                    user_prompt = (
                        "The human host is asking a question during the debate.\n"
                        f"Question: {question}\n\n"
                        "Answer in 1-3 short sentences and stay in character."
                    )

                    # LLM answer
                    answer = self.llm.chat_once(sys_prompt, user_prompt)
                    print(f"{display_name}: {answer}\n")

                    # Save TTS with independent index
                    await self.tts.speak(display_name, answer, turn, qa_index)
                    qa_index += 1  # next Q&A answer increments

                    # Q&A menu
                    print("Question options:")
                    print("  [Enter] → ask another question")
                    print("  back    → return to debate")
                    print("  stop    → end conversation")

                    follow = input("Your choice: ").strip().lower()

                    if follow == "stop":
                        print("\nHost: The conversation is finished. Thank you both.")
                        return

                    if follow == "back":
                        break  # exit Q&A, return main debate

            # Continue next turn
            turn += 1

        print("Host: We will stop here.\n")
