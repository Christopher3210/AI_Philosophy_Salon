// SubtitleManager.cs
// Simple subtitle display - shows full text

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

        [Header("Colors")]
        public Color aristotleColor = new Color(0.4f, 0.6f, 1f);
        public Color sartreColor = new Color(1f, 0.4f, 0.4f);
        public Color wittgensteinColor = new Color(0.4f, 0.9f, 0.5f);
        public Color russellColor = new Color(1f, 0.7f, 0.3f);
        public Color defaultColor = Color.yellow;

        private CanvasGroup canvasGroup;
        private bool isShowing = false;

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
            HideImmediate();
        }

        public void ShowSubtitle(string speakerName, string text, float duration = 0f)
        {
            if (subtitlePanel == null) return;

            if (speakerNameText != null)
            {
                speakerNameText.text = speakerName + ":";
                speakerNameText.color = GetSpeakerColor(speakerName);
            }

            if (subtitleText != null)
            {
                subtitleText.text = text;
            }

            subtitlePanel.SetActive(true);
            if (canvasGroup != null) canvasGroup.alpha = 1f;
            isShowing = true;
        }

        public void ShowSubtitleWithAudio(string speakerName, string text, float audioDuration)
        {
            ShowSubtitle(speakerName, text, audioDuration);
        }

        public void HideSubtitle()
        {
            HideImmediate();
        }

        public void HideImmediate()
        {
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

        Color GetSpeakerColor(string speakerName)
        {
            switch (speakerName)
            {
                case "Aristotle": return aristotleColor;
                case "Sartre": return sartreColor;
                case "Wittgenstein": return wittgensteinColor;
                case "Russell": return russellColor;
                default: return defaultColor;
            }
        }

        public bool IsShowing => isShowing;
    }
}
