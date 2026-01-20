// DialogueManager.cs
// Main manager for the philosophy salon dialogue system

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace PhilosophySalon
{
    public class DialogueManager : MonoBehaviour
    {
        [Header("References")]
        public WebSocketClient webSocketClient;
        public UIManager uiManager;
        public AudioSource audioSource;

        [Header("Agent Controllers")]
        public AgentController[] agentControllers;

        [Header("Settings")]
        public float conviviality = 0.5f;

        private Dictionary<string, AgentController> agentMap = new Dictionary<string, AgentController>();
        private AgentController currentSpeaker;
        private bool isPlaying = false;

        void Start()
        {
            // Build agent map
            foreach (var agent in agentControllers)
            {
                if (agent != null && !string.IsNullOrEmpty(agent.agentName))
                {
                    agentMap[agent.agentName] = agent;
                    Debug.Log($"[DialogueManager] Registered agent: {agent.agentName}");
                }
            }

            // Subscribe to WebSocket events
            if (webSocketClient != null)
            {
                webSocketClient.OnConnected.AddListener(OnConnected);
                webSocketClient.OnDisconnected.AddListener(OnDisconnected);
                webSocketClient.OnDialogueStart.AddListener(OnDialogueStart);
                webSocketClient.OnAgentSpeaking.AddListener(OnAgentSpeaking);
                webSocketClient.OnAgentResponse.AddListener(OnAgentResponse);
                webSocketClient.OnMotivationUpdate.AddListener(OnMotivationUpdate);
                webSocketClient.OnDialogueEnd.AddListener(OnDialogueEnd);
            }
        }

        void OnConnected()
        {
            Debug.Log("[DialogueManager] Connected to backend");
            uiManager?.SetConnectionStatus(true);
        }

        void OnDisconnected()
        {
            Debug.Log("[DialogueManager] Disconnected from backend");
            uiManager?.SetConnectionStatus(false);
            StopAllAgentAnimations();
        }

        void OnDialogueStart(string topic, string[] participants)
        {
            Debug.Log($"[DialogueManager] Dialogue started - Topic: {topic}");
            Debug.Log($"[DialogueManager] Participants: {string.Join(", ", participants)}");

            uiManager?.SetTopic(topic);
            uiManager?.ClearDialogue();

            // Reset all agents
            foreach (var agent in agentControllers)
            {
                agent?.SetIdle();
            }
        }

        void OnAgentSpeaking(string agentName)
        {
            Debug.Log($"[DialogueManager] {agentName} is thinking...");

            // Highlight the thinking agent
            if (agentMap.TryGetValue(agentName, out AgentController agent))
            {
                // Show thinking animation
                agent.SetThinking();
                currentSpeaker = agent;
            }

            uiManager?.ShowThinking(agentName);
        }

        void OnAgentResponse(AgentResponseData response)
        {
            Debug.Log($"[DialogueManager] {response.agent}: {response.text}");

            // Get the agent controller
            if (!agentMap.TryGetValue(response.agent, out AgentController agent))
            {
                Debug.LogWarning($"[DialogueManager] Agent not found: {response.agent}");
                return;
            }

            // Update UI
            uiManager?.AddDialogueLine(response.agent, response.text, response.stance);
            uiManager?.HideThinking();

            // Start speaking animation and lip sync
            StartCoroutine(PlayAgentResponse(agent, response));
        }

        IEnumerator PlayAgentResponse(AgentController agent, AgentResponseData response)
        {
            isPlaying = true;

            // Set agent to speaking state
            agent.SetSpeaking();

            // Load and play audio if available
            if (!string.IsNullOrEmpty(response.audio_path))
            {
                yield return StartCoroutine(LoadAndPlayAudio(response.audio_path, agent, response.viseme_data));
            }
            else
            {
                // No audio, just simulate with viseme data timing
                if (response.viseme_data != null && response.viseme_data.Length > 0)
                {
                    float totalDuration = 0;
                    foreach (var v in response.viseme_data)
                    {
                        totalDuration = Mathf.Max(totalDuration, v.time + v.duration);
                    }

                    // Play lip sync without audio
                    agent.PlayLipSync(response.viseme_data);
                    yield return new WaitForSeconds(totalDuration);
                }
                else
                {
                    // Estimate duration from text length
                    float duration = response.text.Split(' ').Length / 2.5f;
                    yield return new WaitForSeconds(duration);
                }
            }

            // Return to idle
            agent.SetIdle();
            isPlaying = false;
        }

        IEnumerator LoadAndPlayAudio(string audioPath, AgentController agent, VisemeEvent[] visemeData)
        {
            // Convert path for Unity
            string unityPath = audioPath.Replace("\\", "/");

            // Check if file exists
            if (!System.IO.File.Exists(unityPath))
            {
                Debug.LogWarning($"[DialogueManager] Audio file not found: {unityPath}");
                yield break;
            }

            // Load audio file
            using (var www = UnityEngine.Networking.UnityWebRequestMultimedia.GetAudioClip("file:///" + unityPath, AudioType.MPEG))
            {
                yield return www.SendWebRequest();

                if (www.result == UnityEngine.Networking.UnityWebRequest.Result.Success)
                {
                    AudioClip clip = UnityEngine.Networking.DownloadHandlerAudioClip.GetContent(www);

                    if (clip != null)
                    {
                        // Play audio
                        audioSource.clip = clip;
                        audioSource.Play();

                        // Start lip sync
                        if (visemeData != null && visemeData.Length > 0)
                        {
                            agent.PlayLipSync(visemeData);
                        }

                        // Wait for audio to finish
                        yield return new WaitForSeconds(clip.length);
                    }
                }
                else
                {
                    Debug.LogError($"[DialogueManager] Failed to load audio: {www.error}");
                }
            }
        }

        void OnMotivationUpdate(Dictionary<string, float> scores)
        {
            Debug.Log("[DialogueManager] Motivation scores updated");

            foreach (var kvp in scores)
            {
                Debug.Log($"  {kvp.Key}: {kvp.Value:F2}");

                // Update agent visualization
                if (agentMap.TryGetValue(kvp.Key, out AgentController agent))
                {
                    agent.SetMotivation(kvp.Value);
                }
            }

            // Update UI
            uiManager?.UpdateMotivationBars(scores);
        }

        void OnDialogueEnd()
        {
            Debug.Log("[DialogueManager] Dialogue ended");
            uiManager?.ShowDialogueEnded();
            StopAllAgentAnimations();
        }

        void StopAllAgentAnimations()
        {
            foreach (var agent in agentControllers)
            {
                agent?.SetIdle();
            }
        }

        // Public methods for UI buttons
        public void OnInterruptClicked()
        {
            webSocketClient?.SendInterrupt();
        }

        public void OnStopClicked()
        {
            webSocketClient?.SendStop();
        }

        public void OnConvivialityChanged(float value)
        {
            conviviality = value;
            webSocketClient?.SendSetConviviality(value);
        }

        public void OnAskQuestion(string agentName, string question)
        {
            webSocketClient?.SendAskQuestion(agentName, question);
        }

        public bool IsPlaying => isPlaying;
    }
}
