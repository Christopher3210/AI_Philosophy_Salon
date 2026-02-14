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
