// SubtitleUIGenerator.cs
// Editor script to generate subtitle UI

using UnityEngine;
using UnityEditor;
using UnityEngine.UI;
using TMPro;

namespace PhilosophySalon
{
    public class SubtitleUIGenerator : EditorWindow
    {
        [MenuItem("Tools/Generate Subtitle UI")]
        public static void GenerateSubtitleUI()
        {
            // Find or create Canvas
            Canvas canvas = FindObjectOfType<Canvas>();
            if (canvas == null)
            {
                GameObject canvasObj = new GameObject("Canvas");
                canvas = canvasObj.AddComponent<Canvas>();
                canvas.renderMode = RenderMode.ScreenSpaceOverlay;
                canvasObj.AddComponent<CanvasScaler>();
                canvasObj.AddComponent<GraphicRaycaster>();
            }

            // Create Subtitle Panel
            GameObject subtitlePanel = new GameObject("SubtitlePanel");
            subtitlePanel.transform.SetParent(canvas.transform, false);

            RectTransform panelRect = subtitlePanel.AddComponent<RectTransform>();
            panelRect.anchorMin = new Vector2(0.1f, 0.05f);
            panelRect.anchorMax = new Vector2(0.9f, 0.2f);
            panelRect.offsetMin = Vector2.zero;
            panelRect.offsetMax = Vector2.zero;

            // Background
            Image bgImage = subtitlePanel.AddComponent<Image>();
            bgImage.color = new Color(0, 0, 0, 0.7f);

            // Add CanvasGroup for fading
            subtitlePanel.AddComponent<CanvasGroup>();

            // Horizontal Layout
            HorizontalLayoutGroup layout = subtitlePanel.AddComponent<HorizontalLayoutGroup>();
            layout.padding = new RectOffset(20, 20, 10, 10);
            layout.spacing = 15;
            layout.childAlignment = TextAnchor.MiddleLeft;
            layout.childControlWidth = false;
            layout.childControlHeight = true;
            layout.childForceExpandWidth = false;
            layout.childForceExpandHeight = true;

            // Speaker Name Text
            GameObject speakerObj = new GameObject("SpeakerName");
            speakerObj.transform.SetParent(subtitlePanel.transform, false);

            RectTransform speakerRect = speakerObj.AddComponent<RectTransform>();
            speakerRect.sizeDelta = new Vector2(200, 50);

            TextMeshProUGUI speakerText = speakerObj.AddComponent<TextMeshProUGUI>();
            speakerText.text = "Speaker:";
            speakerText.fontSize = 28;
            speakerText.fontStyle = FontStyles.Bold;
            speakerText.color = Color.yellow;
            speakerText.alignment = TextAlignmentOptions.MidlineLeft;

            LayoutElement speakerLayout = speakerObj.AddComponent<LayoutElement>();
            speakerLayout.minWidth = 150;
            speakerLayout.preferredWidth = 200;

            // Subtitle Text
            GameObject subtitleObj = new GameObject("SubtitleText");
            subtitleObj.transform.SetParent(subtitlePanel.transform, false);

            RectTransform subtitleRect = subtitleObj.AddComponent<RectTransform>();

            TextMeshProUGUI subtitleText = subtitleObj.AddComponent<TextMeshProUGUI>();
            subtitleText.text = "Subtitle text will appear here...";
            subtitleText.fontSize = 24;
            subtitleText.color = Color.white;
            subtitleText.alignment = TextAlignmentOptions.MidlineLeft;
            subtitleText.enableWordWrapping = true;

            LayoutElement subtitleLayout = subtitleObj.AddComponent<LayoutElement>();
            subtitleLayout.flexibleWidth = 1;

            // Create or find SubtitleManager
            SubtitleManager manager = FindObjectOfType<SubtitleManager>();
            if (manager == null)
            {
                GameObject managerObj = new GameObject("SubtitleManager");
                manager = managerObj.AddComponent<SubtitleManager>();
            }

            // Assign references
            manager.subtitlePanel = subtitlePanel;
            manager.speakerNameText = speakerText;
            manager.subtitleText = subtitleText;
            manager.backgroundImage = bgImage;

            // Select the panel
            Selection.activeGameObject = subtitlePanel;

            Debug.Log("[SubtitleUIGenerator] Subtitle UI created successfully!");
            Debug.Log("Remember to assign SubtitleManager to DialogueManager!");
        }
    }
}
