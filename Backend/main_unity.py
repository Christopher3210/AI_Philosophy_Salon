# main_unity.py
# Entry point for Unity frontend integration

import asyncio
import os

from agents.agents_manager import AgentsManager
from llm.local_model_manager import LocalModelManager as ModelManager
from tts.LocalTTS import LocalTTS
from tts.AzureSTT import AzureSTT
from unity_bridge import WebSocketServer
from unity_controller import UnityDialogueController


async def main():
    """Main entry point for Unity mode."""

    # 1. Initialize local model manager (Ollama + Mistral 7B)
    # Requires Ollama running locally: https://ollama.com/download
    # Then run: ollama pull mistral
    model_manager = ModelManager()

    # 2. Load agents from config files
    agents_manager = AgentsManager(cfg_dir="agents/configs")

    # 3. Initialize local TTS (XTTS v2 + Rhubarb Lip Sync)
    # Requires reference audio files in voices/ directory
    # (e.g., voices/aristotle.wav, voices/sartre.wav, etc.)
    tts_engine = LocalTTS(
        voice_dir="voices",
        output_dir="tts_output",
    )
    tts_engine.clear_output()

    # 4. Initialize Azure STT for voice input (to be replaced with local Whisper later)
    stt_engine = AzureSTT(
        subscription_key="87MplLeDZRkxrDwt62jOVHtVyY7CWvJrz41zsUCYPg0c8dcMa5PYJQQJ99CCACqBBLyXJ3w3AAAYACOGnHn6",
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
