// UIManager.cs
// Manages all UI elements for the philosophy salon

using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace PhilosophySalon
{
    public class UIManager : MonoBehaviour
    {
        [Header("Connection Status")]
        public GameObject connectionPanel;
        public TextMeshProUGUI connectionStatusText;
        public Image connectionIndicator;
        public Color connectedColor = Color.green;
        public Color disconnectedColor = Color.red;

        [Header("Topic Display")]
        public TextMeshProUGUI topicText;

        [Header("Dialogue Display")]
        public ScrollRect dialogueScrollRect;
        public RectTransform dialogueContent;
        public GameObject dialogueLinePrefab;
        public int maxDialogueLines = 50;

        [Header("Thinking Indicator")]
        public GameObject thinkingPanel;
        public TextMeshProUGUI thinkingText;

        [Header("Motivation Bars")]
        public MotivationBar[] motivationBars;

        [Header("Control Panel")]
        public Slider convivialitySlider;
        public TextMeshProUGUI convivialityValueText;
        public Button interruptButton;
        public Button stopButton;

        [Header("Question Panel")]
        public TMP_InputField questionInput;
        public Button askButton;

        [Header("Philosopher Selection")]
        public Toggle[] philosopherToggles;

        [Header("Microphone / Voice Input")]
        public Button micButton;
        private bool isRecording = false;
        private AudioClip micClip;
        private string micDevice;

        [Header("Pause Panel")]
        public GameObject pausePanel;
        public Button pauseButton;
        public Button resumeButton;
        public Button exitButton;
        public Button askInPauseButton;
        public Button skipSpeakerButton;
        public TMP_InputField changeTopicInput;
        public Button changeTopicButton;
        public TextMeshProUGUI pauseStatusText;

        [Header("Agent Colors")]
        public Color aristotleColor = new Color(0.2f, 0.4f, 0.8f);
        public Color sartreColor = new Color(0.8f, 0.2f, 0.2f);
        public Color wittgensteinColor = new Color(0.2f, 0.7f, 0.3f);
        public Color russellColor = new Color(0.7f, 0.5f, 0.2f);

        private Dictionary<string, Color> agentColors;
        private List<GameObject> dialogueLines = new List<GameObject>();
        private DialogueManager dialogueManager;

        void Awake()
        {
            // Setup agent colors
            agentColors = new Dictionary<string, Color>
            {
                { "Aristotle", aristotleColor },
                { "Sartre", sartreColor },
                { "Wittgenstein", wittgensteinColor },
                { "Russell", russellColor }
            };

            dialogueManager = FindObjectOfType<DialogueManager>();
        }

        void Start()
        {
            // Setup UI event listeners
            if (convivialitySlider != null)
            {
                convivialitySlider.onValueChanged.AddListener(OnConvivialitySliderChanged);
                UpdateConvivialityText(convivialitySlider.value);
            }

            if (interruptButton != null)
            {
                interruptButton.onClick.AddListener(OnInterruptClicked);
            }

            if (stopButton != null)
            {
                stopButton.onClick.AddListener(OnStopClicked);
            }

            if (askButton != null)
            {
                askButton.onClick.AddListener(OnAskClicked);
            }

            if (pauseButton != null)
            {
                pauseButton.onClick.AddListener(OnPauseClicked);
            }

            if (resumeButton != null)
            {
                resumeButton.onClick.AddListener(OnResumeClicked);
            }

            if (exitButton != null)
            {
                exitButton.onClick.AddListener(OnExitClicked);
            }

            if (askInPauseButton != null)
            {
                askInPauseButton.onClick.AddListener(OnAskInPauseClicked);
            }

            if (skipSpeakerButton != null)
            {
                skipSpeakerButton.onClick.AddListener(OnSkipSpeakerClicked);
            }

            if (changeTopicButton != null)
            {
                changeTopicButton.onClick.AddListener(OnChangeTopicClicked);
            }

            if (micButton != null)
            {
                micButton.onClick.AddListener(OnMicClicked);
            }

            // Hide pause panel initially, but keep pause button visible
            HidePausePanel();
            if (pauseButton != null)
            {
                pauseButton.gameObject.SetActive(true);
                pauseButton.interactable = true;
            }


            // Initial state
            SetConnectionStatus(false);
            HideThinking();
        }

        public void SetConnectionStatus(bool connected)
        {
            if (connectionStatusText != null)
            {
                connectionStatusText.text = connected ? "Connected" : "Disconnected";
            }

            if (connectionIndicator != null)
            {
                connectionIndicator.color = connected ? connectedColor : disconnectedColor;
            }

            // Enable/disable controls based on connection
            if (interruptButton != null) interruptButton.interactable = connected;
            if (stopButton != null) stopButton.interactable = connected;
            if (askButton != null) askButton.interactable = connected;
            if (convivialitySlider != null) convivialitySlider.interactable = connected;
            // Pause button should always be enabled
            if (pauseButton != null) pauseButton.interactable = true;
        }

        public void SetTopic(string topic)
        {
            if (topicText != null)
            {
                topicText.text = $"Topic: {topic}";
            }
        }

        public void ClearDialogue()
        {
            foreach (var line in dialogueLines)
            {
                Destroy(line);
            }
            dialogueLines.Clear();
        }

        public void AddDialogueLine(string agentName, string text, string stance)
        {
            if (dialogueContent == null || dialogueLinePrefab == null)
            {
                Debug.LogWarning("[UIManager] Dialogue UI not configured");
                return;
            }

            // Create new dialogue line
            GameObject lineObj = Instantiate(dialogueLinePrefab, dialogueContent);
            dialogueLines.Add(lineObj);

            // Get components
            TextMeshProUGUI nameText = lineObj.transform.Find("AgentName")?.GetComponent<TextMeshProUGUI>();
            TextMeshProUGUI contentText = lineObj.transform.Find("Content")?.GetComponent<TextMeshProUGUI>();
            TextMeshProUGUI stanceText = lineObj.transform.Find("Stance")?.GetComponent<TextMeshProUGUI>();
            Image background = lineObj.GetComponent<Image>();

            // Set agent name
            if (nameText != null)
            {
                nameText.text = agentName;
                if (agentColors.TryGetValue(agentName, out Color color))
                {
                    nameText.color = color;
                }
            }

            // Set content
            if (contentText != null)
            {
                contentText.text = text;
            }

            // Set stance indicator
            if (stanceText != null && !string.IsNullOrEmpty(stance))
            {
                stanceText.text = GetStanceEmoji(stance);
                stanceText.gameObject.SetActive(true);
            }
            else if (stanceText != null)
            {
                stanceText.gameObject.SetActive(false);
            }

            // Set background color (subtle)
            if (background != null && agentColors.TryGetValue(agentName, out Color bgColor))
            {
                bgColor.a = 0.1f;
                background.color = bgColor;
            }

            // Limit number of lines
            while (dialogueLines.Count > maxDialogueLines)
            {
                Destroy(dialogueLines[0]);
                dialogueLines.RemoveAt(0);
            }

            // Scroll to bottom
            StartCoroutine(ScrollToBottom());
        }

        string GetStanceEmoji(string stance)
        {
            switch (stance?.ToLower())
            {
                case "strong_agreement":
                    return "✓✓";
                case "agreement":
                    return "✓";
                case "neutral":
                    return "—";
                case "disagreement":
                    return "✗";
                case "strong_disagreement":
                    return "✗✗";
                default:
                    return "";
            }
        }

        IEnumerator ScrollToBottom()
        {
            yield return new WaitForEndOfFrame();
            if (dialogueScrollRect != null)
            {
                dialogueScrollRect.verticalNormalizedPosition = 0f;
            }
        }

        public void ShowThinking(string agentName)
        {
            if (thinkingPanel != null)
            {
                thinkingPanel.SetActive(true);
            }

            if (thinkingText != null)
            {
                thinkingText.text = $"{agentName} is thinking...";
            }
        }

        public void HideThinking()
        {
            if (thinkingPanel != null)
            {
                thinkingPanel.SetActive(false);
            }
        }

        public void UpdateMotivationBars(Dictionary<string, float> scores)
        {
            foreach (var bar in motivationBars)
            {
                if (bar != null && scores.TryGetValue(bar.agentName, out float value))
                {
                    bar.SetValue(value);
                }
            }
        }

        public void ShowDialogueEnded()
        {
            AddDialogueLine("System", "--- Dialogue Ended ---", null);
        }

        void OnConvivialitySliderChanged(float value)
        {
            UpdateConvivialityText(value);
            dialogueManager?.OnConvivialityChanged(value);
        }

        void UpdateConvivialityText(float value)
        {
            if (convivialityValueText != null)
            {
                string label = value < 0.3f ? "Heated" : value > 0.7f ? "Friendly" : "Balanced";
                convivialityValueText.text = $"{value:F1} ({label})";
            }
        }

        void OnInterruptClicked()
        {
            dialogueManager?.OnInterruptClicked();
        }

        void OnStopClicked()
        {
            dialogueManager?.OnStopClicked();
        }

        void OnPauseClicked()
        {
            dialogueManager?.OnPauseClicked();
        }

        void OnResumeClicked()
        {
            dialogueManager?.OnResumeClicked();
        }

        void OnExitClicked()
        {
            dialogueManager?.OnExitClicked();
        }

        public string[] GetSelectedPhilosophers()
        {
            List<string> selected = new List<string>();
            if (philosopherToggles != null)
            {
                foreach (var toggle in philosopherToggles)
                {
                    if (toggle != null && toggle.isOn)
                    {
                        var label = toggle.GetComponentInChildren<TextMeshProUGUI>();
                        if (label != null)
                            selected.Add(label.text);
                    }
                }
            }
            return selected.ToArray();
        }

        void OnAskClicked()
        {
            if (questionInput == null) return;

            string question = questionInput.text;
            if (string.IsNullOrEmpty(question)) return;

            string[] targets = GetSelectedPhilosophers();
            if (targets.Length == 0)
            {
                Debug.LogWarning("[UIManager] No philosophers selected to answer!");
                return;
            }

            dialogueManager?.OnAskQuestion(question, targets);
            questionInput.text = "";
        }

        void OnAskInPauseClicked()
        {
            if (questionInput == null) return;

            string question = questionInput.text;
            if (string.IsNullOrEmpty(question)) return;

            string[] targets = GetSelectedPhilosophers();
            if (targets.Length == 0)
            {
                Debug.LogWarning("[UIManager] No philosophers selected to answer!");
                return;
            }

            dialogueManager?.OnAskQuestion(question, targets);
            questionInput.text = "";
            HidePausePanel();
        }

        void OnSkipSpeakerClicked()
        {
            dialogueManager?.OnStopSpeakerClicked();
        }

        void OnChangeTopicClicked()
        {
            if (changeTopicInput == null) return;

            string topic = changeTopicInput.text;
            if (!string.IsNullOrEmpty(topic))
            {
                dialogueManager?.OnChangeTopic(topic);
                changeTopicInput.text = "";
            }
        }

        public void SetPauseRequested(bool requested)
        {
            if (pauseStatusText != null)
            {
                pauseStatusText.gameObject.SetActive(requested);
                pauseStatusText.text = "Pausing...";
            }
        }

        // ----- Microphone / Voice Input -----

        void OnMicClicked()
        {
            if (isRecording)
                StopRecording();
            else
                StartRecording();
        }

        void StartRecording()
        {
            if (Microphone.devices.Length == 0)
            {
                Debug.LogWarning("[UIManager] No microphone detected");
                return;
            }

            micDevice = Microphone.devices[0];
            micClip = Microphone.Start(micDevice, false, 30, 16000);
            isRecording = true;

            // Visual feedback - change button color to red
            if (micButton != null)
            {
                var img = micButton.GetComponent<Image>();
                if (img != null) img.color = new Color(0.8f, 0.2f, 0.2f);
                var txt = micButton.GetComponentInChildren<TextMeshProUGUI>();
                if (txt != null) txt.text = "Stop";
            }

            Debug.Log("[UIManager] Recording started");
        }

        void StopRecording()
        {
            if (!isRecording) return;

            int lastPos = Microphone.GetPosition(micDevice);
            Microphone.End(micDevice);
            isRecording = false;

            // Visual feedback - restore button color
            if (micButton != null)
            {
                var img = micButton.GetComponent<Image>();
                if (img != null) img.color = new Color(0.3f, 0.5f, 0.7f);
                var txt = micButton.GetComponentInChildren<TextMeshProUGUI>();
                if (txt != null) txt.text = "Mic";
            }

            if (lastPos <= 0 || micClip == null)
            {
                Debug.LogWarning("[UIManager] No audio recorded");
                return;
            }

            // Trim clip to actual recording length
            float[] samples = new float[lastPos * micClip.channels];
            micClip.GetData(samples, 0);

            // Encode to WAV bytes
            byte[] wavBytes = EncodeToWav(samples, micClip.channels, micClip.frequency);

            // Send to backend for transcription
            dialogueManager?.webSocketClient?.SendAudioForTranscription(wavBytes);
            Debug.Log($"[UIManager] Sent {wavBytes.Length} bytes for transcription");
        }

        byte[] EncodeToWav(float[] samples, int channels, int sampleRate)
        {
            int sampleCount = samples.Length;
            int byteRate = sampleRate * channels * 2; // 16-bit
            int dataSize = sampleCount * 2;
            int fileSize = 44 + dataSize;

            byte[] wav = new byte[fileSize];

            // RIFF header
            System.Text.Encoding.ASCII.GetBytes("RIFF").CopyTo(wav, 0);
            System.BitConverter.GetBytes(fileSize - 8).CopyTo(wav, 4);
            System.Text.Encoding.ASCII.GetBytes("WAVE").CopyTo(wav, 8);

            // fmt sub-chunk
            System.Text.Encoding.ASCII.GetBytes("fmt ").CopyTo(wav, 12);
            System.BitConverter.GetBytes(16).CopyTo(wav, 16);        // sub-chunk size
            System.BitConverter.GetBytes((short)1).CopyTo(wav, 20);  // PCM format
            System.BitConverter.GetBytes((short)channels).CopyTo(wav, 22);
            System.BitConverter.GetBytes(sampleRate).CopyTo(wav, 24);
            System.BitConverter.GetBytes(byteRate).CopyTo(wav, 28);
            System.BitConverter.GetBytes((short)(channels * 2)).CopyTo(wav, 32); // block align
            System.BitConverter.GetBytes((short)16).CopyTo(wav, 34); // bits per sample

            // data sub-chunk
            System.Text.Encoding.ASCII.GetBytes("data").CopyTo(wav, 36);
            System.BitConverter.GetBytes(dataSize).CopyTo(wav, 40);

            // Convert float samples to 16-bit PCM
            int offset = 44;
            for (int i = 0; i < sampleCount; i++)
            {
                short val = (short)(Mathf.Clamp(samples[i], -1f, 1f) * 32767f);
                System.BitConverter.GetBytes(val).CopyTo(wav, offset);
                offset += 2;
            }

            return wav;
        }

        public void OnTranscriptionResult(string text)
        {
            if (!string.IsNullOrEmpty(text) && questionInput != null)
            {
                questionInput.text = text;
                Debug.Log($"[UIManager] Transcription filled: {text}");
            }
        }

        public void ShowPausePanel(bool isInterrupt = false)
        {
            Debug.Log($"[UIManager] ShowPausePanel called - pausePanel null? {pausePanel == null}, isInterrupt: {isInterrupt}");

            // Hide "Pausing..." indicator
            SetPauseRequested(false);

            if (pausePanel != null)
            {
                pausePanel.SetActive(true);
            }
            else
            {
                Debug.LogWarning("[UIManager] pausePanel reference is NULL! Cannot show pause panel.");
            }

            // Skip Speaker only shows for Interrupt, not for Pause
            if (skipSpeakerButton != null)
            {
                skipSpeakerButton.gameObject.SetActive(isInterrupt);
            }

            // Hide pause button while panel is showing
            if (pauseButton != null)
            {
                pauseButton.gameObject.SetActive(false);
            }
        }

        public void HidePausePanel()
        {
            if (pausePanel != null)
            {
                pausePanel.SetActive(false);
            }

            // Show pause button again
            if (pauseButton != null)
            {
                pauseButton.gameObject.SetActive(true);
                pauseButton.interactable = true;
            }
        }
    }

    [System.Serializable]
    public class MotivationBar
    {
        public string agentName;
        public Slider slider;
        public Image fillImage;
        public TextMeshProUGUI valueText;

        public void SetValue(float value)
        {
            if (slider != null)
            {
                slider.value = Mathf.Clamp01(value);
            }

            if (valueText != null)
            {
                valueText.text = $"{value:F2}";
            }
        }
    }
}
