class TurnTakingController:
    def __init__(self, llm_client, agents_manager):
        self.llm = llm_client
        self.agents = agents_manager

    def run_dialogue(self, topic="What is happiness?", turns=4):
        print(f"Host: Today we discuss — {topic}\n")

        last_msg = f"Host: {topic} Please answer briefly."

        for _ in range(turns):
            # Aristotle speaks first
            a_prompt = f"{last_msg}\nAristotle, speak in 1-3 sentences."
            a_reply = self.llm.chat_once(
                self.agents.get_system_prompt("aristotle"),
                a_prompt
            )
            print(f"Aristotle: {a_reply}\n")

            # Russell responds
            r_prompt = (
                f"Aristotle just said:\n\"{a_reply}\"\n\n"
                "Russell, respond briefly and challenge one key point."
            )
            r_reply = self.llm.chat_once(
                self.agents.get_system_prompt("russell"),
                r_prompt
            )
            print(f"Russell: {r_reply}\n")

            # Pass Russell → Aristotle
            last_msg = (
                f"Russell just said:\n\"{r_reply}\"\n\n"
                "Aristotle, respond briefly (1-3 sentences)."
            )

        print("Host: Thank you both — we will stop here.")