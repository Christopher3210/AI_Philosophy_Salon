# Dissertation: System Architecture and Technical Implementation

---

## 3. System Architecture and Technical Implementation

### 3.1 System Overview

The AI Philosophy Salon is a real-time multi-agent dialogue installation that simulates a philosophical debate among four historical thinkers: Aristotle, Sartre, Wittgenstein, and Russell. The system integrates a Python-based backend with a Unity 3D frontend, connected via a WebSocket bridge. Figure 1 illustrates the overall architecture.

```
┌─────────────────────────────────────────────────────────┐
│                   Unity Frontend (C#)                    │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │DialogueMgr  │  │  UIManager   │  │ AgentController│  │
│  │(orchestrate)│  │(pause/input) │  │(3D anim/lipsync│  │
│  └──────┬──────┘  └──────┬───────┘  └────────────────┘  │
│         └────────────────┘                               │
│                     │ WebSocket (ws://localhost:8765)     │
└─────────────────────┼───────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────┐
│              Python Backend (asyncio)                    │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │WebSocketServer│  │UnityDialogue │  │AgentsManager │  │
│  │  (bridge)     │  │ Controller   │  │(YAML configs)│  │
│  └───────────────┘  └──────┬───────┘  └──────────────┘  │
│                             │                            │
│  ┌──────────────┐  ┌────────┴──────┐  ┌──────────────┐  │
│  │LocalModelMgr │  │ DialogueLoop  │  │  AzureTTS    │  │
│  │(Ollama/Mistral│ │(turn logic)   │  │ + AzureSTT   │  │
│  └──────────────┘  └───────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

The architecture follows a strict separation of concerns: the backend handles all AI inference, speech synthesis, and dialogue state; the frontend handles 3D rendering, animation, audio playback, and user interaction. This decoupling allows either component to be updated independently.

---

### 3.2 Backend Architecture

#### 3.2.1 Agent Configuration and Persona Design

Each philosopher is defined as a YAML configuration file specifying their name, LLM model key, Azure TTS voice, and system prompt. The system prompt encodes the philosopher's rhetorical style, references to their canonical works, and behavioural constraints:

```yaml
name: "Wittgenstein"
model_key: "mistral"
voice: "en-GB-ThomasNeural"
system: |
  You are Ludwig Wittgenstein, the Austrian-British philosopher of language and logic.
  You speak in a terse, aphoristic style — questioning the meaning of words...
  When relevant, explicitly reference your own works — such as the Tractatus
  Logico-Philosophicus, Philosophical Investigations...
  Respond in 2-3 precise, challenging sentences. Speak entirely in first person.
```

The `AgentsManager` class parses these files at startup and constructs `Agent` objects that carry the persona state, including a floating-point `motivation_score` (range 0–10) that dynamically adjusts based on dialogue conviviality and engagement level.

#### 3.2.2 Dialogue Loop and Turn Management

The core dialogue engine (`dialogue_loop.py`) implements an asynchronous turn-based loop using Python's `asyncio`. Each turn proceeds through five stages:

**1. Speaker selection** — A weighted probability distribution selects the next speaker, biased away from the most recent speaker and toward agents with higher motivation scores. A `next_speaker_override` field allows an explicitly named philosopher to be prioritised when the previous speaker addressed them directly by name.

**2. Prompt construction** — A context-aware prompt is assembled from: (a) a fixed system prompt encoding the agent's persona, (b) a structured conversation history window (configurable, default 8 turns), and (c) a dynamically generated engagement instruction that directs the agent to respond to the most recent argument specifically:

```python
engagement_instruction = (
    f"IMPORTANT: {current_speaker.name}, you MUST directly respond to what "
    f"{last_speaker} just said. Reference their specific argument or claim. "
    "Do NOT start with generic openers..."
)
```

With 40% probability, an additional instruction prompts self-citation of a specific work. With 30% probability, an invitation instruction encourages the agent to address a named peer by name with a question, which the system then detects to set the `next_speaker_override`.

**3. LLM inference** — The prompt is sent to a locally-hosted Mistral 7B model via Ollama's OpenAI-compatible REST API (`http://localhost:11434/v1`). This eliminates cloud API dependency and latency, enabling the installation to run fully offline after initial model download.

**4. Speech synthesis** — The reply text is synthesised using Azure Cognitive Services TTS with voice mapped to each philosopher (e.g., `en-GB-ThomasNeural` for Wittgenstein, `en-GB-RyanNeural` for Russell). The TTS engine returns both an MP3 audio file and a sequence of viseme events — phoneme-level timing data specifying mouth shape codes and durations — which are forwarded to Unity for lip synchronisation.

**5. State update** — Motivation scores are recalculated, dialogue history is updated, and the backend broadcasts the response to the Unity frontend via WebSocket.

#### 3.2.3 WebSocket Event Protocol

The backend communicates with Unity through a JSON event protocol over a persistent WebSocket connection. Table 1 lists the key events:

| Direction          | Event                 | Key Payload Fields                              |
|--------------------|-----------------------|-------------------------------------------------|
| Backend → Unity    | `dialogue_start`      | topic, participants[]                           |
| Backend → Unity    | `agent_speaking`      | agent name (signals "thinking" state)           |
| Backend → Unity    | `agent_response`      | agent, text, audio_path, viseme_data[], stance  |
| Backend → Unity    | `paused`              | — (signals panel should appear)                |
| Backend → Unity    | `transcription_result`| text                                            |
| Unity → Backend    | `start_dialogue`      | topic, conviviality, selected_agents[]          |
| Unity → Backend    | `pause` / `interrupt` | — (two distinct pause modes)                   |
| Unity → Backend    | `resume`              | —                                               |
| Unity → Backend    | `ask_question`        | question, target_agents[]                       |
| Unity → Backend    | `transcribe_audio`    | audio (base64-encoded WAV)                      |
| Unity → Backend    | `change_topic`        | topic                                           |
| Unity → Backend    | `stop_speaker`        | — (skip current speaker)                       |

The distinction between `pause` and `interrupt` reflects two different interaction modes: **Pause** allows the current philosopher to complete their sentence before halting, preserving narrative coherence; **Interrupt** immediately cancels the current asyncio task, enabling audience members to interject during live performance.

#### 3.2.4 Interaction Control Model

Three orthogonal control primitives support live performance:

- **Pause** (`is_paused=True`, `was_interrupted=False`): Backend sets a flag checked at the start of each new turn. The current speaker finishes, then the system halts and notifies Unity.
- **Interrupt** (`is_paused=True`, `was_interrupted=True`): Backend cancels the running asyncio task immediately via `Task.cancel()`, sends `paused` at once. Unity pauses (not stops) the audio so it can be resumed from the same point.
- **Stop Speaker**: Backend cancels the task and restarts the dialogue loop, selecting a new speaker — effectively skipping the interrupted turn.

Resume from interrupt restores the paused audio clip and waits for it to finish before sending the `resume` event to the backend, maintaining audio–text synchronisation.

---

### 3.3 Frontend Architecture

#### 3.3.1 Dialogue Management

`DialogueManager.cs` acts as the central coordinator on the Unity side. It subscribes to all WebSocket events and orchestrates three subsystems: the `AgentController` array (3D character animation), the `SubtitleManager` (on-screen text display), and the `CameraController` (cinematic camera movement).

State is tracked through four boolean flags:
- `isPaused` — whether the dialogue is currently halted
- `isPlaying` — whether audio is currently playing
- `isAnsweringQuestion` — whether a user question is being addressed (suppresses normal pause guards)
- `hasInterruptedAudio` — whether audio was paused mid-sentence (determines resume behaviour)

#### 3.3.2 Lip Synchronisation

Azure TTS returns viseme data as an array of events, each specifying a `time` offset (seconds from audio start), a viseme ID (one of 22 standardised mouth shapes), and a `duration`. The `LipSyncController` component receives this array alongside a reference to the `AudioSource` and drives blendshape weights on the character's facial mesh in real time:

```csharp
// During Update():
float audioTime = audioSource.time;
while (visemeIndex < visemeData.Length &&
       visemeData[visemeIndex].time <= audioTime)
{
    ApplyViseme(visemeData[visemeIndex]);
    visemeIndex++;
}
```

A `TeethSyncController` component supplements this by mapping jaw-open blendshape weight to the mouth-open viseme amplitude, with a configurable `weightMultiplier` to control opening extent.

#### 3.3.3 Camera Control

The `CameraController` implements smooth cinematic transitions between an overview position (capturing all four philosophers) and close-up positions focused on the active speaker. A key design constraint was that the camera must remain within the salon interior regardless of speaker orientation.

Early attempts using `speaker.forward` to position the camera placed it outside the building for philosophers facing toward walls. The final solution uses the audience direction — the vector from the speaker toward the overview camera position — as the approach axis, guaranteeing the camera always stays on the audience side:

```csharp
Vector3 toAudience = (overviewPosition - speakerPos);
toAudience.y = 0;
toAudience.Normalize();
targetPosition = speakerPos + toAudience * closeupDistance;
```

Transitions use `Vector3.Lerp` and `Quaternion.Slerp` with configurable speeds for smooth, non-jarring movement appropriate for a gallery installation context.

#### 3.3.4 Voice Input (Speech-to-Text)

A microphone input feature allows audience members to ask questions by voice rather than keyboard. When the mic button is pressed, Unity records audio using `Microphone.Start()` at 16kHz mono. On stopping, the float PCM samples are encoded into a standard 44-byte WAV format and transmitted to the backend as a base64-encoded string within a `transcribe_audio` WebSocket event.

The backend's `AzureSTT` module decodes the audio, writes it to a temporary WAV file, and passes it to `azure.cognitiveservices.speech.SpeechRecognizer.recognize_once()`. The recognised text is returned to Unity as a `transcription_result` event and automatically populated into the question input field, reducing friction for audience participation.

---

### 3.4 Local Model Deployment

A significant architectural decision was the switch from a cloud-hosted LLM (OpenAI GPT) to a locally-deployed open-source model (Mistral 7B via Ollama). This was driven by two considerations: elimination of per-token API costs for extended exhibition runs, and the ability to operate the installation entirely offline after initial setup.

The `LocalModelManager` uses the OpenAI Python client library pointed at Ollama's OpenAI-compatible endpoint (`http://localhost:11434/v1`), requiring only a change of `base_url` and a placeholder API key. This design preserves full interface compatibility with the rest of the system while enabling local inference. At 128 max output tokens per turn and approximately 2–5 seconds inference time on a mid-range GPU, the response latency is acceptable for gallery pacing where natural pauses between philosophers are expected.

---

*Word count (Section 3): approximately 1,500 words*
