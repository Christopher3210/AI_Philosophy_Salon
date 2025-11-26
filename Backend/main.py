# main.py

import asyncio

from agents.agents_manager import AgentsManager
from controller.TurnTakingController import TurnTakingController
from llm.model_manager import ModelManager
from tts.SimpleTTS import SimpleTTS


def main():
    # 1. Load models (lazy loading per model_key)
    model_manager = ModelManager()

    # 2. Load agents from YAML configs
    agents_manager = AgentsManager(cfg_dir="agents/configs")

    # 3. Setup TTS engine with per-agent voices (optional override)
    voice_map = {}
    for agent in agents_manager.get_all_agents():
        voice_map[agent.name] = agent.voice

    tts_engine = SimpleTTS(voice_map=voice_map, output_dir="tts_output")
    tts_engine.clear_output()

    # 4. Create controller and start the debate
    controller = TurnTakingController(model_manager, agents_manager, tts_engine)

    asyncio.run(controller.run_dialogue(topic="What is the meaning of freedom?"))


if __name__ == "__main__":
    main()
