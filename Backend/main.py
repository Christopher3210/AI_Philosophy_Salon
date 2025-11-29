# main.py

import asyncio
from agents.agents_manager import AgentsManager
from controller import TurnTakingController
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

    # 4. Ask user for debate intensity (conviviality)
    print("\n" + "="*60)
    print("  AI Philosophy Salon - Debate Configuration")
    print("="*60)
    print("\nSelect debate intensity:")
    print("  1. Friendly discussion (philosophers agree and build on ideas)")
    print("  2. Balanced debate (mix of agreement and disagreement)")
    print("  3. Heated argument (philosophers challenge each other)")
    print("="*60)

    while True:
        try:
            choice = input("Your choice (1-3): ").strip()
            if choice == "1":
                conviviality = 0.8
                intensity_name = "Friendly"
                break
            elif choice == "2":
                conviviality = 0.5
                intensity_name = "Balanced"
                break
            elif choice == "3":
                conviviality = 0.2
                intensity_name = "Heated"
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        except Exception:
            print("Invalid input. Please try again.")

    print(f"\n✓ Debate intensity set to: {intensity_name} (conviviality: {conviviality})\n")

    # 5. Create controller with chosen conviviality
    controller = TurnTakingController(
        model_manager=model_manager,
        agents_manager=agents_manager,
        tts_engine=tts_engine,
        history_window=8,
        conviviality=conviviality
    )

    asyncio.run(controller.run_dialogue(topic="What is the meaning of freedom?"))


if __name__ == "__main__":
    main()
