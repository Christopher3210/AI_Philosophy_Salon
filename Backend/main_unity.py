# main_unity.py
# Entry point for Unity frontend integration

import asyncio
import os

from agents.agents_manager import AgentsManager
from llm.cloud_model_manager import CloudModelManager as ModelManager
from tts.AzureTTS import AzureTTS
from tts.AzureSTT import AzureSTT
from unity_bridge import WebSocketServer
from unity_controller import UnityDialogueController


async def main():
    """Main entry point for Unity mode."""

    # 1. Initialize model manager (OpenAI API for fast responses)
    model_manager = ModelManager(
        api_key="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"
    )

    # 2. Load agents from config files
    agents_manager = AgentsManager(cfg_dir="agents/configs")

    # 3. Build voice map from agent configs
    voice_map = {agent.name: agent.voice for agent in agents_manager.get_all_agents()}

    # 4. Initialize Azure TTS with viseme support
    tts_engine = AzureTTS(
        subscription_key="9c0352cb32d745a0b5508f4d89097b6a",
        region="southeastasia",
        voice_map=voice_map,
        output_dir="tts_output",
        auto_play=False  # Unity handles audio playback
    )
    tts_engine.clear_output()

    # 4b. Initialize Azure STT (reuses same credentials)
    stt_engine = AzureSTT(
        subscription_key="9c0352cb32d745a0b5508f4d89097b6a",
        region="southeastasia"
    )

    # 5. Start WebSocket server
    ws_server = WebSocketServer(host="localhost", port=8765)
    await ws_server.start()

    # 6. Create controller
    controller = UnityDialogueController(
        model_manager=model_manager,
        agents_manager=agents_manager,
        tts_engine=tts_engine,
        stt_engine=stt_engine,
        websocket_server=ws_server,
        history_window=8,
        conviviality=0.5  # Default, can be changed by Unity
    )

    # 7. Run dialogue loop (supports multiple sessions)
    try:
        while True:
            await controller.run_dialogue()
            print("\n[Main] Dialogue ended. Waiting for next session...")
            controller.reset()
    finally:
        await ws_server.stop()


if __name__ == "__main__":
    # Change to Backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(main())
