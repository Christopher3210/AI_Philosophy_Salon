# main.py

import asyncio
import time
from agents.agents_manager import AgentsManager
from controller import TurnTakingController
from llm.model_manager import ModelManager
from tts.AzureTTS import AzureTTS


def main():
    # 1. Model Manager (lazy loading local HF models)
    model_manager = ModelManager()

    # 2. Load agents from YAML configs
    agents_manager = AgentsManager(cfg_dir="agents/configs")

    # 3. Setup Azure TTS with viseme support (auto_play for terminal mode)
    voice_map = {agent.name: agent.voice for agent in agents_manager.get_all_agents()}
    tts_engine = AzureTTS(
        subscription_key="GGOrbCc2fBt6m6hbwdrZH0oi8VyX7uq1Vl2wvb63X8XJ6b0PScL2JQQJ99CAACYeBjFXJ3w3AAAYACOGEacn",
        region="eastus",
        voice_map=voice_map,
        output_dir="tts_output",
        auto_play=True  # Play audio in terminal mode
    )
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

    # Small delay to clear input buffer before starting dialogue
    time.sleep(0.5)

    # 5. Create controller with chosen conviviality
    controller = TurnTakingController(
        model_manager=model_manager,
        agents_manager=agents_manager,
        tts_engine=tts_engine,
        history_window=8,
        conviviality=conviviality
    )

    asyncio.run(controller.run_dialogue(topic="what is the meaning of freedom?"))


if __name__ == "__main__":
    main()
