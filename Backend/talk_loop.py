from LLM.LLMClient import LLMClient
from Agents.AgentsManager import AgentsManager
from TurnTaking.TurnTakingController import TurnTakingController



def main():
    llm = LLMClient()
    agents = AgentsManager()
    controller = TurnTakingController(llm, agents)
    controller.run_dialogue()

if __name__ == "__main__":
    main()
