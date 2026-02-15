# unity_bridge/websocket_server.py
# WebSocket server for Unity frontend communication

import asyncio
import json
from typing import Set, Dict, Any, Callable, Awaitable
import websockets
from websockets.server import WebSocketServerProtocol


class WebSocketServer:
    """
    WebSocket server for communicating with Unity frontend.

    Sends events:
    - dialogue_start: Dialogue session started
    - agent_speaking: An agent is about to speak
    - agent_response: Agent's response with text, audio path, and viseme data
    - motivation_update: Updated motivation scores
    - dialogue_end: Dialogue session ended
    - paused: Dialogue paused, show options panel

    Receives events:
    - pause/interrupt: User wants to pause
    - resume: Resume dialogue
    - stop/exit: Stop the dialogue
    - set_conviviality: Change conviviality level
    - start_dialogue: Start with topic and settings
    - ask_question: Ask a question
    """

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        self.running = False
        self.on_message_callback: Callable[[Dict], Awaitable[None]] = None

    async def start(self):
        """Start the WebSocket server."""
        self.running = True
        self.server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port
        )
        print(f"[WebSocket] Server started on ws://{self.host}:{self.port}")

    async def stop(self):
        """Stop the WebSocket server."""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            print("[WebSocket] Server stopped")

    async def _handle_client(self, websocket: WebSocketServerProtocol):
        """Handle a client connection."""
        self.clients.add(websocket)
        client_id = id(websocket)
        print(f"[WebSocket] Client connected: {client_id}")

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"[WebSocket] Received: {data.get('event', 'unknown')}")

                    if self.on_message_callback:
                        await self.on_message_callback(data)

                except json.JSONDecodeError:
                    print(f"[WebSocket] Invalid JSON: {message}")
        except websockets.exceptions.ConnectionClosed:
            print(f"[WebSocket] Client disconnected: {client_id}")
        finally:
            self.clients.discard(websocket)

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        if not self.clients:
            return

        message = json.dumps({
            "event": event_type,
            "data": data
        })

        disconnected = set()
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)

        self.clients -= disconnected

    def set_message_callback(self, callback: Callable[[Dict], Awaitable[None]]):
        """Set callback function for received messages."""
        self.on_message_callback = callback

    @property
    def has_clients(self) -> bool:
        """Check if any clients are connected."""
        return len(self.clients) > 0

    # ----- Event sending methods -----

    async def send_event(self, event_type: str, data: Dict[str, Any] = None):
        """Send a generic event to all clients."""
        await self.broadcast(event_type, data or {})

    async def send_dialogue_start(self, topic: str, participants: list):
        """Notify clients that dialogue has started."""
        await self.broadcast("dialogue_start", {
            "topic": topic,
            "participants": participants
        })

    async def send_agent_speaking(self, agent_name: str, last_speaker: str = None):
        """Notify clients that an agent is about to speak."""
        await self.broadcast("agent_speaking", {
            "agent": agent_name,
            "last_speaker": last_speaker
        })

    async def send_agent_response(
        self,
        agent_name: str,
        text: str,
        audio_path: str,
        viseme_data: list,
        stance: str,
        turn: int
    ):
        """Send agent's response with all data needed for Unity playback."""
        await self.broadcast("agent_response", {
            "agent": agent_name,
            "text": text,
            "audio_path": audio_path,
            "viseme_data": viseme_data,
            "stance": stance,
            "turn": turn
        })

    async def send_motivation_update(self, motivation_scores: Dict[str, float]):
        """Send updated motivation scores to clients."""
        await self.broadcast("motivation_update", {
            "scores": motivation_scores
        })

    async def send_transcription_result(self, text: str):
        """Send transcription result back to Unity."""
        await self.broadcast("transcription_result", {
            "text": text
        })

    async def send_dialogue_end(self, summary: Dict[str, Any]):
        """Notify clients that dialogue has ended."""
        await self.broadcast("dialogue_end", {
            "summary": summary
        })
