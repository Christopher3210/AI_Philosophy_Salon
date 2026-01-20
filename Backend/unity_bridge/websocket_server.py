# websocket_server.py
# WebSocket server for Unity frontend communication

import asyncio
import json
from typing import Set, Dict, Any, Optional
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

    Receives events:
    - interrupt: User wants to interrupt
    - set_conviviality: Change conviviality level
    - ask_question: Ask a specific agent a question
    - stop: Stop the dialogue
    """

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = False

        # Callback for received messages
        self.on_message_callback = None

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
                    print(f"[WebSocket] Received: {data}")

                    # Put message in queue for processing
                    await self.message_queue.put(data)

                    # Call callback if set
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

        # Send to all clients
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)

        # Remove disconnected clients
        self.clients -= disconnected

    async def send_dialogue_start(self, topic: str, participants: list):
        """Notify clients that dialogue has started."""
        await self.broadcast("dialogue_start", {
            "topic": topic,
            "participants": participants
        })

    async def send_agent_speaking(self, agent_name: str):
        """Notify clients that an agent is about to speak."""
        await self.broadcast("agent_speaking", {
            "agent": agent_name
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
        """
        Send agent's response with all data needed for Unity playback.

        Parameters
        ----------
        agent_name : str
            Name of the speaking agent
        text : str
            The response text
        audio_path : str
            Path to the generated audio file
        viseme_data : list
            List of viseme events: [{"time": float, "viseme": str, "weight": float}, ...]
        stance : str
            The agent's stance (agreement, disagreement, neutral, etc.)
        turn : int
            Current turn number
        """
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

    async def send_dialogue_end(self, summary: Dict[str, Any]):
        """Notify clients that dialogue has ended."""
        await self.broadcast("dialogue_end", {
            "summary": summary
        })

    def set_message_callback(self, callback):
        """Set callback function for received messages."""
        self.on_message_callback = callback

    async def get_message(self, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """Get a message from the queue with timeout."""
        try:
            return await asyncio.wait_for(self.message_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    @property
    def has_clients(self) -> bool:
        """Check if any clients are connected."""
        return len(self.clients) > 0
