# test_websocket_server.py
# Simple WebSocket server for testing (no dependencies on agents module)

import asyncio
import json
from unity_bridge import WebSocketServer

async def main():
    """Simple test server that sends mock dialogue events."""
    print("=" * 50)
    print("  WebSocket Test Server")
    print("=" * 50)

    server = WebSocketServer(host="localhost", port=8765)

    # Message handler
    async def handle_message(data):
        event = data.get("event", "")
        print(f"[Server] Received event: {event}")

        if event == "interrupt":
            print("[Server] Interrupt requested")
        elif event == "stop":
            print("[Server] Stop requested")

    server.set_message_callback(handle_message)

    await server.start()
    print("\n[Server] Waiting for clients...")
    print("[Server] Will send mock dialogue when client connects\n")

    try:
        # Wait for client
        while not server.has_clients:
            await asyncio.sleep(0.5)

        print("[Server] Client connected! Sending mock dialogue...\n")

        # Send dialogue start
        await server.send_dialogue_start(
            topic="The nature of freedom",
            participants=["Aristotle", "Sartre", "Wittgenstein", "Russell"]
        )
        await asyncio.sleep(1)

        # Send agent speaking
        await server.send_agent_speaking("Aristotle")
        await asyncio.sleep(1)

        # Send agent response
        await server.send_agent_response(
            agent_name="Aristotle",
            text="Freedom, in my view, is the capacity to act according to reason.",
            audio_path="audio/aristotle_001.wav",
            viseme_data=[
                {"time": 0.0, "viseme": "FF", "weight": 0.8, "duration": 0.08},
                {"time": 0.1, "viseme": "RR", "weight": 0.7, "duration": 0.06},
                {"time": 0.18, "viseme": "ih", "weight": 0.6, "duration": 0.05},
                {"time": 0.25, "viseme": "DD", "weight": 0.7, "duration": 0.06},
                {"time": 0.32, "viseme": "aa", "weight": 0.9, "duration": 0.08},
            ],
            stance="neutral",
            turn=1
        )
        await asyncio.sleep(2)

        # Send motivation update
        await server.send_motivation_update({
            "Aristotle": 0.6,
            "Sartre": 0.8,
            "Wittgenstein": 0.4,
            "Russell": 0.5
        })
        await asyncio.sleep(1)

        # Send dialogue end
        await server.send_dialogue_end({
            "total_turns": 1,
            "final_topic": "The nature of freedom"
        })

        print("[Server] Mock dialogue complete!")

        # Keep running for more messages
        while server.has_clients:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n[Server] Shutting down...")
    finally:
        await server.stop()

if __name__ == "__main__":
    asyncio.run(main())
