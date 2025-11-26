# controller/TurnTakingController.py

import asyncio
from agents.agents_manager import AgentsManager
from llm.model_manager import ModelManager
from tts.SimpleTTS import SimpleTTS


class TurnTakingController:
    """
    Manages the debate turns among multiple philosophical agents
    and supports host interruptions and Q&A mode.
    """

    def __init__(self, model_manager: ModelManager, agents_manager: AgentsManager, tts_engine: SimpleTTS):
        self.models = model_manager
        self.agents = agents_manager
        self.tts = tts_engine

    async def run_dialogue(self, topic: str = "What is happiness?"):
        """
        Main debate loop with turn taking and Q&A support.
        """
        print(f"Host: Today we discuss — {topic}\n")

        agents = self.agents.get_all_agents()
        if len(agents) == 0:
            print("No agents found. Please check your configs.")
            return

        print("Participants:", ", ".join(a.name for a in agents), "\n")

        last_message = f"Host: {topic} Please answer briefly."
        last_reply = None
        turn = 1

        while True:
            print(f"========== Turn {turn} ==========\n")

            # Each agent speaks in order
            for idx, agent in enumerate(agents, start=1):
                if turn == 1 and idx == 1:
                    user_prompt = last_message
                else:
                    context = last_reply or last_message
                    user_prompt = (
                        f"The previous speaker said:\n\"{context}\"\n\n"
                        f"{agent.name}, respond briefly from your own perspective."
                    )

                reply = self.models.chat_once(
                    model_key=agent.model_key,
                    system_prompt=agent.system_prompt,
                    user_prompt=user_prompt,
                    max_new_tokens=128,
                    temperature=0.6,
                )

                print(f"{agent.name}: {reply}\n")

                agent.add_memory(user_prompt, reply)

                await self.tts.speak(agent.name, reply, turn, idx, is_qa=False)

                last_reply = reply

            # ===== MENU =====
            print("Options:")
            print("  [Enter] → continue the debate")
            print("  q       → ask a question (Q&A)")
            print("  stop    → end the conversation")

            choice = input("Your choice: ").strip().lower()

            if choice == "stop":
                print("\nHost: The conversation is finished. Thank you all.")
                break

            if choice == "q":
                await self._qa_loop(agents, turn)

            turn += 1

        print("Host: We will stop here.\n")

    async def _qa_loop(self, agents, turn: int):
        """
        Q&A mode where the host can ask individual agents questions.
        """
        qa_index = 100
        name_map = {a.name.lower(): a for a in agents}

        while True:
            print("\nQ&A mode.")
            print("Available agents:", ", ".join(a.name for a in agents))
            target_name = input("Ask whom? (type name, or 'back' to return): ").strip()

            if target_name.lower() == "back":
                print("Returning to debate...\n")
                break

            agent = name_map.get(target_name.lower())
            if not agent:
                print("Host: I did not recognize this name.\n")
                continue

            question = input(f"Your question to {agent.name}: ")

            user_prompt = (
                "The human host is asking a question.\n"
                f"Question: {question}\n\n"
                "Answer in 1-3 short sentences."
            )

            answer = self.models.chat_once(
                model_key=agent.model_key,
                system_prompt=agent.system_prompt,
                user_prompt=user_prompt,
                max_new_tokens=128,
                temperature=0.6,
            )

            print(f"{agent.name}: {answer}\n")

            await self.tts.speak(agent.name, answer, turn, qa_index, is_qa=True)
            qa_index += 1

            print("Q&A options:")
            print("  [Enter] → ask another question")
            print("  back    → return to debate")
            print("  stop    → end conversation")

            follow = input("Your choice: ").strip().lower()

            if follow == "stop":
                print("\nHost: The conversation is finished. Thank you all.")
                exit(0)

            if follow == "back":
                print("Returning to debate...\n")
                break
