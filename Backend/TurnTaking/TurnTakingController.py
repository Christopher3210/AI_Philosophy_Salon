class TurnTakingController:
    def __init__(self, llm_client, agents_manager):
        self.llm = llm_client
        self.agents = agents_manager

    def run_dialogue(self, topic: str = "What is happiness?"):
        print(f"Host: Today we discuss — {topic}\n")

        last_msg = f"Host: {topic} Please answer briefly."
        turn = 1

        while True:
            print(f"--- Turn {turn} ---\n")

            # ===== Aristotle speaks =====
            a_prompt = f"{last_msg}\nAristotle, speak in 1-3 sentences."
            a_reply = self.llm.chat_once(
                self.agents.get_system_prompt("aristotle"), a_prompt
            )
            print(f"Aristotle: {a_reply}\n")

            # ===== Russell responds =====
            r_prompt = (
                f"Aristotle just said:\n\"{a_reply}\"\n\n"
                "Russell, respond briefly and challenge one key point."
            )
            r_reply = self.llm.chat_once(
                self.agents.get_system_prompt("russell"), r_prompt
            )
            print(f"Russell: {r_reply}\n")

            # Update context for next turn
            last_msg = (
                f"Russell just said:\n\"{r_reply}\"\n\n"
                "Aristotle, respond briefly (1-3 sentences)."
            )

            # ===== Menu: continue / ask question / stop =====
            print("Options:")
            print("  [Enter]  → continue the debate")
            print("  q        → ask a question to one philosopher")
            print("  stop     → end the conversation")
            choice = input("Your choice: ").strip().lower()

            if choice == "stop":
                print("\nHost: The conversation is finished. Thank you both.")
                break

            if choice == "q":
                # Loop for asking multiple questions
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

                    # Ask your question
                    question = input(f"Your question to {display_name}: ")

                    sys_prompt = self.agents.get_system_prompt(agent_key)
                    user_prompt = (
                        "The human host is asking you a question during the debate.\n"
                        f"Question: {question}\n\n"
                        "Answer in 1-3 short sentences and stay in character."
                    )
                    answer = self.llm.chat_once(sys_prompt, user_prompt)

                    print(f"{display_name}: {answer}\n")

                    # Optional: feed answer into next debate context
                    last_msg = (
                        f"The host asked: \"{question}\".\n"
                        f"{display_name} answered: \"{answer}\".\n"
                        "Now continue the debate briefly."
                    )

                    # ===== New menu after a question =====
                    print("Question options:")
                    print("  [Enter] → ask another question")
                    print("  back    → return to the main debate")
                    print("  stop    → end the conversation")

                    follow = input("Your choice: ").strip().lower()

                    if follow == "stop":
                        print("\nHost: The conversation is finished. Thank you both.")
                        return

                    if follow == "back":
                        break  # go back to main debate loop

                    # If Enter → ask another question (loop continues)

            # Continue debate
            turn += 1

        print("Host: We will stop here.\n")
