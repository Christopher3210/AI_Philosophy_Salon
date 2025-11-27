# main.py

import asyncio
from agents.agents_manager import AgentsManager
from controller.TurnTakingController import TurnTakingController
from llm.model_manager import ModelManager
from tts.SimpleTTS import SimpleTTS


def main():
    # 1. Model Manager (lazy loading local HF models)
    model_manager = ModelManager()

    # 2. Load agents from YAML configs
    agents_manager = AgentsManager(cfg_dir="agents/configs")

    # 3. Setup TTS (optional but recommended)
    voice_map = {agent.name: agent.voice for agent in agents_manager.get_all_agents()}
    tts_engine = SimpleTTS(voice_map=voice_map, output_dir="tts_output")
    tts_engine.clear_output()

    # 4. Create controller — correct parameter order + TTS enabled
    controller = TurnTakingController(
        model_manager=model_manager,
        agents_manager=agents_manager,
        tts_engine=tts_engine,
        history_window=8
    )

    asyncio.run(controller.run_dialogue(topic="What is the meaning of freedom?"))


if __name__ == "__main__":
    main()
