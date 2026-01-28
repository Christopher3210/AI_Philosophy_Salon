// SubtitleManager.cs
// Displays subtitles at the bottom of the screen during dialogue

using System.Collections;
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
        public bool useTypewriterEffect = true;
        public float typewriterSpeed = 30f;  // Characters per second
        public float fadeInDuration = 0.2f;
        public float fadeOutDuration = 0.3f;
        public float displayPadding = 0.5f;  // Extra time to show subtitle after audio ends

        [Header("Colors")]
        public Color defaultSpeakerColor = Color.yellow;
        public Color defaultTextColor = Color.white;
        public Color backgroundColor = new Color(0, 0, 0, 0.7f);

        [Header("Agent Colors")]
        public Color aristotleColor = new Color(0.4f, 0.6f, 1f);
        public Color sartreColor = new Color(1f, 0.4f, 0.4f);
        public Color wittgensteinColor = new Color(0.4f, 0.9f, 0.5f);
        public Color russellColor = new Color(1f, 0.7f, 0.3f);

        private Coroutine currentSubtitleCoroutine;
        private Coroutine typewriterCoroutine;
        private CanvasGroup canvasGroup;
        private string currentFullText = "";
        private bool isShowing = false;

        void Awake()
        {
            // Get or add CanvasGroup for fading
            if (subtitlePanel != null)
            {
                canvasGroup = subtitlePanel.GetComponent<CanvasGroup>();
                if (canvasGroup == null)
                {
                    canvasGroup = subtitlePanel.AddComponent<CanvasGroup>();
                }
            }

            // Set background color
            if (backgroundImage != null)
            {
                backgroundImage.color = backgroundColor;
            }

            // Hide initially
            HideImmediate();
        }

        /// <summary>
        /// Show subtitle with speaker name and text
        /// </summary>
        public void ShowSubtitle(string speakerName, string text, float duration = 0f)
        {
            if (subtitlePanel == null) return;

            // Stop any current subtitle
            StopCurrentSubtitle();

            // Set speaker name
            if (speakerNameText != null)
            {
                speakerNameText.text = speakerName + ":";
                speakerNameText.color = GetSpeakerColor(speakerName);
            }

            // Store full text
            currentFullText = text;

            // Start showing subtitle
            currentSubtitleCoroutine = StartCoroutine(ShowSubtitleCoroutine(text, duration));
        }

        /// <summary>
        /// Show subtitle synced with audio duration
        /// </summary>
        public void ShowSubtitleWithAudio(string speakerName, string text, float audioDuration)
        {
            ShowSubtitle(speakerName, text, audioDuration + displayPadding);
        }

        IEnumerator ShowSubtitleCoroutine(string text, float duration)
        {
            isShowing = true;
            subtitlePanel.SetActive(true);

            // Fade in
            yield return StartCoroutine(FadeIn());

            // Show text (with or without typewriter effect)
            if (useTypewriterEffect)
            {
                typewriterCoroutine = StartCoroutine(TypewriterEffect(text));
                yield return typewriterCoroutine;
            }
            else
            {
                if (subtitleText != null)
                {
                    subtitleText.text = text;
                }
            }

            // Wait for duration if specified
            if (duration > 0)
            {
                // Calculate remaining time after typewriter
                float typewriterDuration = useTypewriterEffect ? text.Length / typewriterSpeed : 0;
                float remainingTime = duration - typewriterDuration;

                if (remainingTime > 0)
                {
                    yield return new WaitForSeconds(remainingTime);
                }

                // Auto hide after duration
                yield return StartCoroutine(FadeOut());
                HideImmediate();
            }

            isShowing = false;
        }

        IEnumerator TypewriterEffect(string text)
        {
            if (subtitleText == null) yield break;

            subtitleText.text = "";

            for (int i = 0; i <= text.Length; i++)
            {
                subtitleText.text = text.Substring(0, i);
                yield return new WaitForSeconds(1f / typewriterSpeed);
            }
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

        /// <summary>
        /// Hide subtitle with fade out
        /// </summary>
        public void HideSubtitle()
        {
            if (!isShowing) return;

            StopCurrentSubtitle();
            StartCoroutine(HideSubtitleCoroutine());
        }

        IEnumerator HideSubtitleCoroutine()
        {
            yield return StartCoroutine(FadeOut());
            HideImmediate();
        }

        /// <summary>
        /// Hide subtitle immediately without animation
        /// </summary>
        public void HideImmediate()
        {
            StopCurrentSubtitle();

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

            isShowing = false;
        }

        void StopCurrentSubtitle()
        {
            if (currentSubtitleCoroutine != null)
            {
                StopCoroutine(currentSubtitleCoroutine);
                currentSubtitleCoroutine = null;
            }

            if (typewriterCoroutine != null)
            {
                StopCoroutine(typewriterCoroutine);
                typewriterCoroutine = null;
            }
        }

        Color GetSpeakerColor(string speakerName)
        {
            switch (speakerName)
            {
                case "Aristotle":
                    return aristotleColor;
                case "Sartre":
                    return sartreColor;
                case "Wittgenstein":
                    return wittgensteinColor;
                case "Russell":
                    return russellColor;
                default:
                    return defaultSpeakerColor;
            }
        }

        /// <summary>
        /// Skip typewriter effect and show full text
        /// </summary>
        public void SkipTypewriter()
        {
            if (typewriterCoroutine != null)
            {
                StopCoroutine(typewriterCoroutine);
                typewriterCoroutine = null;
            }

            if (subtitleText != null && !string.IsNullOrEmpty(currentFullText))
            {
                subtitleText.text = currentFullText;
            }
        }

        public bool IsShowing => isShowing;
    }
}
