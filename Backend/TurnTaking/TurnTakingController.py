# TurnTakingController.py

class TurnTakingController:
    def __init__(self, llm_client, agents_manager):
        self.llm = llm_client
        self.agents = agents_manager

    def run_dialogue(self, topic: str = "What is happiness?"):
        print(f"Host: Today we discuss — {topic}\n")

        # This message goes to Aristotle first
        last_msg = f"Host: {topic} Please answer briefly."
        turn = 1

        # No fixed number of turns, run until user stops
        while True:
            print(f"--- Turn {turn} ---\n")

            # ===== Aristotle speaks first =====
            a_prompt = f"{last_msg}\nAristotle, speak in 1-3 sentences."
            a_reply = self.llm.chat_once(
                self.agents.get_system_prompt("aristotle"),
                a_prompt
            )
            print(f"Aristotle: {a_reply}\n")

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

            # Update message for next Aristotle turn
            last_msg = (
                f"Russell just said:\n\"{r_reply}\"\n\n"
                "Aristotle, respond briefly (1-3 sentences)."
            )

            # ===== Simple menu: continue / ask question / stop =====
            print("Options:")
            print("  [Enter]  → continue the debate")
            print("  q        → ask a question to one philosopher")
            print("  stop     → end the conversation")

            choice = input("Your choice: ").strip().lower()

            # === User ends the conversation ===
            if choice == "stop":
                print("\nHost: The conversation is finished. Thank you both.")
                break

            # === User asks a question to a philosopher ===
            if choice == "q":
                target = input("Ask whom? (a = Aristotle, r = Russell): ").strip().lower()

                if target.startswith("a"):
                    agent_key = "aristotle"
                    display_name = "Aristotle"
                elif target.startswith("r"):
                    agent_key = "russell"
                    display_name = "Russell"
                else:
                    print("Host: I did not understand. I will continue the debate.\n")
                    turn += 1
                    continue

                question = input(f"Type your question to {display_name}: ")

                # Ask LLM and get answer
                sys_prompt = self.agents.get_system_prompt(agent_key)
                user_prompt = (
                    "The human host is asking you a question during the debate.\n"
                    f"Question: {question}\n\n"
                    "Answer in 1-3 short sentences and stay in character."
                )
                answer = self.llm.chat_once(sys_prompt, user_prompt)

                print(f"{display_name}: {answer}\n")

                # Make this answer part of future context
                last_msg = (
                    f"The host asked: \"{question}\".\n"
                    f"{display_name} answered: \"{answer}\".\n"
                    "Now continue the debate briefly."
                )

            # Direct Enter or any other input → continue next turn
            turn += 1

        print("Host: We will stop here.\n")
