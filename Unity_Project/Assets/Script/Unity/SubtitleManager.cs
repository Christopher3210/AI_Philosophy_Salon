// SubtitleManager.cs
// Displays scrolling subtitles with line-by-line animation

using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace PhilosophySalon
{
    public class SubtitleManager : MonoBehaviour
    {
        [Header("UI References")]
        public GameObject subtitlePanel;
        public TextMeshProUGUI speakerNameText;
        public TextMeshProUGUI subtitleText;
        public Image backgroundImage;

        [Header("Settings")]
        public int maxLines = 3;
        public float lineDisplayTime = 2.0f;
        public float fadeInDuration = 0.2f;
        public float fadeOutDuration = 0.3f;

        [Header("Colors")]
        public Color defaultSpeakerColor = Color.yellow;
        public Color defaultTextColor = Color.white;
        public Color backgroundColor = new Color(0, 0, 0, 0.75f);

        [Header("Agent Colors")]
        public Color aristotleColor = new Color(0.4f, 0.6f, 1f);
        public Color sartreColor = new Color(1f, 0.4f, 0.4f);
        public Color wittgensteinColor = new Color(0.4f, 0.9f, 0.5f);
        public Color russellColor = new Color(1f, 0.7f, 0.3f);

        private CanvasGroup canvasGroup;
        private List<string> displayedLines = new List<string>();
        private List<string> pendingLines = new List<string>();
        private string currentSpeaker = "";
        private bool isShowing = false;
        private Coroutine scrollCoroutine;

        void Awake()
        {
            if (subtitlePanel != null)
            {
                canvasGroup = subtitlePanel.GetComponent<CanvasGroup>();
                if (canvasGroup == null)
                {
                    canvasGroup = subtitlePanel.AddComponent<CanvasGroup>();
                }
            }

            if (backgroundImage != null)
            {
                backgroundImage.color = backgroundColor;
            }

            HideImmediate();
        }

        public void ShowSubtitle(string speakerName, string text, float duration = 0f)
        {
            if (subtitlePanel == null) return;

            if (scrollCoroutine != null)
            {
                StopCoroutine(scrollCoroutine);
            }

            if (speakerName != currentSpeaker)
            {
                displayedLines.Clear();
                currentSpeaker = speakerName;
            }

            if (speakerNameText != null)
            {
                speakerNameText.text = speakerName + ":";
                speakerNameText.color = GetSpeakerColor(speakerName);
            }

            pendingLines = SplitIntoLines(text);

            float timePerLine = lineDisplayTime;
            if (duration > 0 && pendingLines.Count > 0)
            {
                timePerLine = duration / pendingLines.Count;
                timePerLine = Mathf.Clamp(timePerLine, 0.5f, 3.0f);
            }

            if (!isShowing)
            {
                subtitlePanel.SetActive(true);
                StartCoroutine(FadeIn());
            }

            isShowing = true;
            scrollCoroutine = StartCoroutine(ScrollLines(timePerLine));
        }

        List<string> SplitIntoLines(string text)
        {
            List<string> lines = new List<string>();
            char[] separators = { '.', '!', '?', ';', ',', ':', '。', '！', '？', '；', '，', '：' };

            string currentLine = "";
            int maxCharsPerLine = 80;

            for (int i = 0; i < text.Length; i++)
            {
                currentLine += text[i];

                bool isSeparator = System.Array.IndexOf(separators, text[i]) >= 0;

                if (isSeparator || currentLine.Length >= maxCharsPerLine)
                {
                    string trimmed = currentLine.Trim();
                    if (!string.IsNullOrEmpty(trimmed))
                    {
                        lines.Add(trimmed);
                    }
                    currentLine = "";
                }
            }

            if (!string.IsNullOrEmpty(currentLine.Trim()))
            {
                lines.Add(currentLine.Trim());
            }

            return lines;
        }

        IEnumerator ScrollLines(float timePerLine)
        {
            displayedLines.Clear();

            foreach (string line in pendingLines)
            {
                displayedLines.Add(line);

                while (displayedLines.Count > maxLines)
                {
                    displayedLines.RemoveAt(0);
                }

                UpdateDisplay();
                yield return new WaitForSeconds(timePerLine);
            }

            pendingLines.Clear();
        }

        void UpdateDisplay()
        {
            if (subtitleText == null) return;
            subtitleText.text = string.Join("\n", displayedLines);
        }

        public void ShowSubtitleWithAudio(string speakerName, string text, float audioDuration)
        {
            ShowSubtitle(speakerName, text, audioDuration);
        }

        IEnumerator FadeIn()
        {
            if (canvasGroup == null) yield break;

            float elapsed = 0f;
            canvasGroup.alpha = 0f;

            while (elapsed < fadeInDuration)
            {
                elapsed += Time.deltaTime;
                canvasGroup.alpha = Mathf.Lerp(0f, 1f, elapsed / fadeInDuration);
                yield return null;
            }

            canvasGroup.alpha = 1f;
        }

        IEnumerator FadeOut()
        {
            if (canvasGroup == null) yield break;

            float elapsed = 0f;
            float startAlpha = canvasGroup.alpha;

            while (elapsed < fadeOutDuration)
            {
                elapsed += Time.deltaTime;
                canvasGroup.alpha = Mathf.Lerp(startAlpha, 0f, elapsed / fadeOutDuration);
                yield return null;
            }

            canvasGroup.alpha = 0f;
        }

        public void HideSubtitle()
        {
            if (!isShowing) return;
            StartCoroutine(HideSubtitleCoroutine());
        }

        IEnumerator HideSubtitleCoroutine()
        {
            if (scrollCoroutine != null)
            {
                StopCoroutine(scrollCoroutine);
                scrollCoroutine = null;
            }

            yield return StartCoroutine(FadeOut());
            HideImmediate();
        }

        public void HideImmediate()
        {
            if (scrollCoroutine != null)
            {
                StopCoroutine(scrollCoroutine);
                scrollCoroutine = null;
            }

            if (subtitlePanel != null)
            {
                subtitlePanel.SetActive(false);
            }

            if (canvasGroup != null)
            {
                canvasGroup.alpha = 0f;
            }

            if (subtitleText != null)
            {
                subtitleText.text = "";
            }

            displayedLines.Clear();
            pendingLines.Clear();
            currentSpeaker = "";
            isShowing = false;
        }

        Color GetSpeakerColor(string speakerName)
        {
            switch (speakerName)
            {
                case "Aristotle": return aristotleColor;
                case "Sartre": return sartreColor;
                case "Wittgenstein": return wittgensteinColor;
                case "Russell": return russellColor;
                default: return defaultSpeakerColor;
            }
        }

        public bool IsShowing => isShowing;
    }
}
