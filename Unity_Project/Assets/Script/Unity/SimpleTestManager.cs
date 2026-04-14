// SimpleTestManager.cs
// Simplified test script for lip sync - no UI required

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace PhilosophySalon
{
    /// <summary>
    /// Simple test manager to verify lip sync without full UI setup.
    /// Just attach this to an empty GameObject and assign the references.
    /// </summary>
    public class SimpleTestManager : MonoBehaviour
    {
        [Header("WebSocket")]
        public string serverUrl = "ws://localhost:8765";

        [Header("Audio")]
        public AudioSource audioSource;

        [Header("Agent (Aristotle)")]
        public AgentController aristotleAgent;

        [Header("Debug")]
        public bool showDebugLogs = true;

        private WebSocketClient wsClient;
        private bool isConnected = false;

        void Start()
        {
            // Create WebSocket client
            GameObject wsObj = new GameObject("WebSocketClient");
            wsClient = wsObj.AddComponent<WebSocketClient>();
            wsClient.serverUrl = serverUrl;
            wsClient.autoConnect = true;

            // Subscribe to events
            wsClient.OnConnected.AddListener(OnConnected);
            wsClient.OnDisconnected.AddListener(OnDisconnected);
            wsClient.OnAgentSpeaking.AddListener(OnAgentSpeaking);
            wsClient.OnAgentResponse.AddListener(OnAgentResponse);
            wsClient.OnDialogueStart.AddListener(OnDialogueStart);

            Log("SimpleTestManager started. Waiting for backend connection...");
            Log($"Make sure backend is running: python main_unity.py");
        }

        void OnConnected()
        {
            isConnected = true;
            Log("Connected to backend!");
        }

        void OnDisconnected()
        {
            isConnected = false;
            Log("Disconnected from backend");
        }

        void OnDialogueStart(string topic, string[] participants)
        {
            Log($"Dialogue started! Topic: {topic}");
            Log($"Participants: {string.Join(", ", participants)}");
        }

        void OnAgentSpeaking(string agentName)
        {
            Log($"{agentName} is thinking...");

            // Show thinking state on agent
            if (agentName == "Aristotle" && aristotleAgent != null)
            {
                aristotleAgent.SetThinking();
            }
        }

        void OnAgentResponse(AgentResponseData response)
        {
            Log($"{response.agent}: {response.text}");
            Log($"  Audio: {response.audio_path}");
            Log($"  Visemes: {response.viseme_data?.Length ?? 0} events");

            // Only handle Aristotle for this test
            if (response.agent == "Aristotle" && aristotleAgent != null)
            {
                StartCoroutine(PlayResponse(response));
            }
        }

        IEnumerator PlayResponse(AgentResponseData response)
        {
            // Set speaking state
            aristotleAgent.SetSpeaking();

            // Load and play audio if available
            if (!string.IsNullOrEmpty(response.audio_path))
            {
                yield return StartCoroutine(LoadAndPlayAudio(response.audio_path, response.viseme_data));
            }
            else if (response.viseme_data != null && response.viseme_data.Length > 0)
            {
                // No audio, just play visemes with estimated timing
                aristotleAgent.PlayLipSync(response.viseme_data, null);

                // Wait for viseme duration
                float duration = response.viseme_data[response.viseme_data.Length - 1].time + 0.5f;
                yield return new WaitForSeconds(duration);
            }

            // Return to idle
            aristotleAgent.SetIdle();
        }

        IEnumerator LoadAndPlayAudio(string audioPath, VisemeEvent[] visemeData)
        {
            // Convert path for Unity
            string unityPath = audioPath.Replace("\\", "/");

            Log($"Loading audio: {unityPath}");

            // Check if file exists
            if (!System.IO.File.Exists(unityPath))
            {
                Log($"Audio file not found: {unityPath}");
                yield break;
            }

            // Load audio file (support both MP3 and WAV)
            string fileUrl = "file:///" + unityPath;
            AudioType audioType = unityPath.EndsWith(".wav", System.StringComparison.OrdinalIgnoreCase) ? AudioType.WAV : AudioType.MPEG;
            using (var www = UnityEngine.Networking.UnityWebRequestMultimedia.GetAudioClip(fileUrl, audioType))
            {
                yield return www.SendWebRequest();

                if (www.result == UnityEngine.Networking.UnityWebRequest.Result.Success)
                {
                    AudioClip clip = UnityEngine.Networking.DownloadHandlerAudioClip.GetContent(www);

                    if (clip != null && audioSource != null)
                    {
                        Log($"Playing audio ({clip.length:F2}s) with {visemeData?.Length ?? 0} visemes");

                        // Play audio
                        audioSource.clip = clip;
                        audioSource.Play();

                        // Start lip sync with audio source for sync
                        if (visemeData != null && visemeData.Length > 0)
                        {
                            aristotleAgent.PlayLipSync(visemeData, audioSource);
                        }

                        // Wait for audio to finish
                        yield return new WaitForSeconds(clip.length);
                    }
                }
                else
                {
                    Log($"Failed to load audio: {www.error}");
                }
            }
        }

        void Log(string message)
        {
            if (showDebugLogs)
            {
                Debug.Log($"[Test] {message}");
            }
        }

        void OnGUI()
        {
            // Simple on-screen debug info
            GUILayout.BeginArea(new Rect(10, 10, 400, 200));
            GUILayout.Label($"Status: {(isConnected ? "CONNECTED" : "DISCONNECTED")}");
            GUILayout.Label($"Server: {serverUrl}");
            GUILayout.Label("Press Play in Unity, then run backend:");
            GUILayout.Label("  cd Backend && python main_unity.py");
            GUILayout.EndArea();
        }
    }
}
