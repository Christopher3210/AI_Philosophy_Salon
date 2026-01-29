// WebSocketClient.cs
// Handles WebSocket communication with Python backend

using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;

// You need to install NativeWebSocket package:
// Window -> Package Manager -> + -> Add package from git URL:
// https://github.com/endel/NativeWebSocket.git#upm

using NativeWebSocket;

namespace PhilosophySalon
{
    [Serializable]
    public class DialogueStartData
    {
        public string topic;
        public string[] participants;
    }

    [Serializable]
    public class AgentSpeakingData
    {
        public string agent;
    }

    [Serializable]
    public class VisemeEvent
    {
        public float time;
        public string viseme;
        public float weight;
        public float duration;
    }

    [Serializable]
    public class AgentResponseData
    {
        public string agent;
        public string text;
        public string audio_path;
        public VisemeEvent[] viseme_data;
        public string stance;
        public int turn;
    }

    [Serializable]
    public class MotivationScores
    {
        public Dictionary<string, float> scores;
    }

    [Serializable]
    public class MotivationUpdateData
    {
        public SerializableDict scores;
    }

    [Serializable]
    public class SerializableDict
    {
        // Will be populated from JSON
    }

    [Serializable]
    public class WebSocketMessage
    {
        public string @event;
        public string data;
    }

    public class WebSocketClient : MonoBehaviour
    {
        [Header("Connection Settings")]
        public string serverUrl = "ws://localhost:8765";
        public bool autoConnect = true;
        public float reconnectDelay = 3f;

        [Header("Events")]
        public UnityEvent OnConnected;
        public UnityEvent OnDisconnected;
        public UnityEvent<string, string[]> OnDialogueStart; // topic, participants
        public UnityEvent<string> OnAgentSpeaking; // agent name
        public UnityEvent<AgentResponseData> OnAgentResponse;
        public UnityEvent<Dictionary<string, float>> OnMotivationUpdate;
        public UnityEvent OnDialogueEnd;
        public UnityEvent OnPaused; // dialogue paused, show options

        private WebSocket websocket;
        private bool isConnected = false;
        private bool shouldReconnect = true;

        async void Start()
        {
            if (autoConnect)
            {
                await Connect();
            }
        }

        void Update()
        {
            #if !UNITY_WEBGL || UNITY_EDITOR
            if (websocket != null)
            {
                websocket.DispatchMessageQueue();
            }
            #endif
        }

        public async System.Threading.Tasks.Task Connect()
        {
            Debug.Log($"[WebSocket] Connecting to {serverUrl}...");

            websocket = new WebSocket(serverUrl);

            websocket.OnOpen += () =>
            {
                Debug.Log("[WebSocket] Connected!");
                isConnected = true;
                OnConnected?.Invoke();
            };

            websocket.OnError += (e) =>
            {
                Debug.LogError($"[WebSocket] Error: {e}");
            };

            websocket.OnClose += (e) =>
            {
                Debug.Log("[WebSocket] Disconnected");
                isConnected = false;
                OnDisconnected?.Invoke();

                if (shouldReconnect)
                {
                    StartCoroutine(TryReconnect());
                }
            };

            websocket.OnMessage += (bytes) =>
            {
                string message = System.Text.Encoding.UTF8.GetString(bytes);
                HandleMessage(message);
            };

            await websocket.Connect();
        }

        IEnumerator TryReconnect()
        {
            yield return new WaitForSeconds(reconnectDelay);
            if (!isConnected && shouldReconnect)
            {
                Debug.Log("[WebSocket] Attempting to reconnect...");
                _ = Connect();
            }
        }

        void HandleMessage(string json)
        {
            try
            {
                // Parse the outer message
                var wrapper = JsonUtility.FromJson<MessageWrapper>(json);

                Debug.Log($"[WebSocket] Received event: {wrapper.@event}");

                switch (wrapper.@event)
                {
                    case "dialogue_start":
                        var startData = JsonUtility.FromJson<DialogueStartDataWrapper>(json);
                        OnDialogueStart?.Invoke(startData.data.topic, startData.data.participants);
                        break;

                    case "agent_speaking":
                        var speakingData = JsonUtility.FromJson<AgentSpeakingDataWrapper>(json);
                        OnAgentSpeaking?.Invoke(speakingData.data.agent);
                        break;

                    case "agent_response":
                        var responseData = JsonUtility.FromJson<AgentResponseDataWrapper>(json);
                        OnAgentResponse?.Invoke(responseData.data);
                        break;

                    case "motivation_update":
                        // Parse motivation scores manually due to dictionary
                        ParseMotivationUpdate(json);
                        break;

                    case "dialogue_end":
                        OnDialogueEnd?.Invoke();
                        break;

                    case "paused":
                        OnPaused?.Invoke();
                        break;

                    default:
                        Debug.Log($"[WebSocket] Unknown event: {wrapper.@event}");
                        break;
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[WebSocket] Error parsing message: {e.Message}\nJSON: {json}");
            }
        }

        void ParseMotivationUpdate(string json)
        {
            try
            {
                // Simple parsing for motivation scores
                // Expected format: {"event": "motivation_update", "data": {"scores": {"Aristotle": 0.5, ...}}}
                var scores = new Dictionary<string, float>();

                int scoresStart = json.IndexOf("\"scores\"");
                if (scoresStart >= 0)
                {
                    int braceStart = json.IndexOf("{", scoresStart);
                    int braceEnd = json.IndexOf("}", braceStart);
                    string scoresJson = json.Substring(braceStart, braceEnd - braceStart + 1);

                    // Parse key-value pairs
                    scoresJson = scoresJson.Trim('{', '}');
                    string[] pairs = scoresJson.Split(',');

                    foreach (string pair in pairs)
                    {
                        string[] kv = pair.Split(':');
                        if (kv.Length == 2)
                        {
                            string key = kv[0].Trim().Trim('"');
                            if (float.TryParse(kv[1].Trim(), out float value))
                            {
                                scores[key] = value;
                            }
                        }
                    }
                }

                OnMotivationUpdate?.Invoke(scores);
            }
            catch (Exception e)
            {
                Debug.LogError($"[WebSocket] Error parsing motivation update: {e.Message}");
            }
        }

        // Send methods
        public async void SendInterrupt()
        {
            if (!isConnected) return;
            string json = "{\"event\": \"interrupt\"}";
            await websocket.SendText(json);
            Debug.Log("[WebSocket] Sent interrupt");
        }

        public async void SendStop()
        {
            if (!isConnected) return;
            string json = "{\"event\": \"stop\"}";
            await websocket.SendText(json);
            Debug.Log("[WebSocket] Sent stop");
        }

        public async void SendSetConviviality(float value)
        {
            if (!isConnected) return;
            string json = $"{{\"event\": \"set_conviviality\", \"data\": {{\"value\": {value}}}}}";
            await websocket.SendText(json);
            Debug.Log($"[WebSocket] Sent conviviality: {value}");
        }

        public async void SendAskQuestion(string question)
        {
            if (!isConnected) return;
            string escapedQuestion = question.Replace("\"", "\\\"");
            string json = $"{{\"event\": \"ask_question\", \"data\": {{\"question\": \"{escapedQuestion}\"}}}}";
            await websocket.SendText(json);
            Debug.Log($"[WebSocket] Sent question: {question}");
        }

        public async void SendStartDialogue(string topic, float conviviality)
        {
            if (!isConnected) return;
            // Escape quotes in topic
            string escapedTopic = topic.Replace("\"", "\\\"");
            string json = $"{{\"event\": \"start_dialogue\", \"data\": {{\"topic\": \"{escapedTopic}\", \"conviviality\": {conviviality}}}}}";
            await websocket.SendText(json);
            Debug.Log($"[WebSocket] Sent start_dialogue - Topic: {topic}, Conviviality: {conviviality}");
        }

        public async void SendPause()
        {
            if (!isConnected) return;
            string json = "{\"event\": \"pause\"}";
            await websocket.SendText(json);
            Debug.Log("[WebSocket] Sent pause");
        }

        public async void SendResume()
        {
            if (!isConnected) return;
            string json = "{\"event\": \"resume\"}";
            await websocket.SendText(json);
            Debug.Log("[WebSocket] Sent resume");
        }

        public async void SendExit()
        {
            if (!isConnected) return;
            string json = "{\"event\": \"exit\"}";
            await websocket.SendText(json);
            Debug.Log("[WebSocket] Sent exit");
        }

        async void OnApplicationQuit()
        {
            shouldReconnect = false;
            if (websocket != null)
            {
                await websocket.Close();
            }
        }

        public bool IsConnected => isConnected;
    }

    // Wrapper classes for JSON parsing
    [Serializable]
    public class MessageWrapper
    {
        public string @event;
    }

    [Serializable]
    public class DialogueStartDataWrapper
    {
        public string @event;
        public DialogueStartData data;
    }

    [Serializable]
    public class AgentSpeakingDataWrapper
    {
        public string @event;
        public AgentSpeakingData data;
    }

    [Serializable]
    public class AgentResponseDataWrapper
    {
        public string @event;
        public AgentResponseData data;
    }
}
