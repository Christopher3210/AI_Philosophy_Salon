# test_websocket.py
# Simple WebSocket client to test backend without Unity

import asyncio
import json
import websockets


async def test_client():
    """
    Test WebSocket connection to backend.
    Run main_unity.py first, then run this script.
    """
    uri = "ws://localhost:8765"

    print("=" * 50)
    print("  WebSocket Test Client")
    print("=" * 50)
    print(f"\nConnecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("[OK] Connected!\n")

            # Receive messages
            message_count = 0
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60)
                    data = json.loads(message)
                    message_count += 1

                    event = data.get("event", "unknown")
                    event_data = data.get("data", {})

                    print(f"\n[Message #{message_count}] Event: {event}")
                    print("-" * 40)

                    if event == "dialogue_start":
                        print(f"  Topic: {event_data.get('topic')}")
                        print(f"  Participants: {event_data.get('participants')}")

                    elif event == "agent_speaking":
                        print(f"  Agent: {event_data.get('agent')} is thinking...")

                    elif event == "agent_response":
                        print(f"  Agent: {event_data.get('agent')}")
                        print(f"  Text: {event_data.get('text')}")
                        print(f"  Stance: {event_data.get('stance')}")
                        print(f"  Audio: {event_data.get('audio_path')}")
                        viseme_count = len(event_data.get('viseme_data', []))
                        print(f"  Visemes: {viseme_count} events")

                        # Show first few visemes
                        visemes = event_data.get('viseme_data', [])[:5]
                        for v in visemes:
                            print(f"    - {v.get('time'):.2f}s: {v.get('viseme')} (weight: {v.get('weight')})")
                        if len(event_data.get('viseme_data', [])) > 5:
                            print(f"    ... and {len(event_data.get('viseme_data', [])) - 5} more")

                    elif event == "motivation_update":
                        print("  Motivation Scores:")
                        scores = event_data.get('scores', {})
                        for agent, score in scores.items():
                            print(f"    - {agent}: {score:.2f}")

                    elif event == "dialogue_end":
                        print("  Dialogue ended!")
                        break

                    else:
                        print(f"  Data: {json.dumps(event_data, indent=2)}")

                except asyncio.TimeoutError:
                    print("\n[Timeout] No message received in 60 seconds")
                    # Send interrupt to test
                    print("Sending interrupt...")
                    await websocket.send(json.dumps({"event": "interrupt"}))

    except ConnectionRefusedError:
        print("[ERROR] Connection refused!")
        print("\nMake sure main_unity.py is running first:")
        print("  python main_unity.py")
    except Exception as e:
        print(f"[ERROR] Error: {e}")


async def test_send_commands():
    """
    Interactive test - send commands to backend.
    """
    uri = "ws://localhost:8765"

    print("=" * 50)
    print("  Interactive WebSocket Test")
    print("=" * 50)

    try:
        async with websockets.connect(uri) as websocket:
            print("[OK] Connected!\n")

            # Start receiver task
            async def receiver():
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        event = data.get("event")
                        print(f"\n[IN] Received: {event}")
                    except:
                        break

            receiver_task = asyncio.create_task(receiver())

            # Interactive sender
            print("Commands:")
            print("  i - Send interrupt")
            print("  s - Send stop")
            print("  c - Set conviviality (0.2)")
            print("  q - Ask Aristotle a question")
            print("  x - Exit")
            print()

            while True:
                cmd = await asyncio.get_event_loop().run_in_executor(
                    None, input, "Enter command: "
                )

                if cmd == 'i':
                    await websocket.send(json.dumps({"event": "interrupt"}))
                    print("[OUT] Sent: interrupt")

                elif cmd == 's':
                    await websocket.send(json.dumps({"event": "stop"}))
                    print("[OUT] Sent: stop")
                    break

                elif cmd == 'c':
                    await websocket.send(json.dumps({
                        "event": "set_conviviality",
                        "data": {"value": 0.2}
                    }))
                    print("[OUT] Sent: conviviality = 0.2")

                elif cmd == 'q':
                    await websocket.send(json.dumps({
                        "event": "ask_question",
                        "data": {
                            "agent": "Aristotle",
                            "question": "What is virtue?"
                        }
                    }))
                    print("[OUT] Sent: question to Aristotle")

                elif cmd == 'x':
                    break

            receiver_task.cancel()

    except ConnectionRefusedError:
        print("[ERROR] Connection refused! Run main_unity.py first.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "-i":
        # Interactive mode
        asyncio.run(test_send_commands())
    else:
        # Simple receive mode
        asyncio.run(test_client())
