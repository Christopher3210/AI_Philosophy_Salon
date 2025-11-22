import asyncio
from LLM.LLMClient import LLMClient
from Agents.AgentsManager import AgentsManager
from TurnTaking.TurnTakingController import TurnTakingController
from TTS.SimpleTTS import SimpleTTS  


def main():
    llm = LLMClient()
    agents = AgentsManager()
    tts = SimpleTTS(voice_map={
    "Aristotle": "en-US-GuyNeural",
    "Russell": "en-GB-RyanNeural"
})     
    tts.clear_output()
    controller = TurnTakingController(llm, agents, tts)

    asyncio.run(controller.run_dialogue())

if __name__ == "__main__":
    main()
