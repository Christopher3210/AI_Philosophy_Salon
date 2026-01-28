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

                CanvasScaler scaler = canvasObj.AddComponent<CanvasScaler>();
                scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
                scaler.referenceResolution = new Vector2(1920, 1080);

                canvasObj.AddComponent<GraphicRaycaster>();
            }

            // Delete existing SubtitlePanel if any
            Transform existingPanel = canvas.transform.Find("SubtitlePanel");
            if (existingPanel != null)
            {
                DestroyImmediate(existingPanel.gameObject);
            }

            // Create Subtitle Panel
            GameObject subtitlePanel = new GameObject("SubtitlePanel");
            subtitlePanel.transform.SetParent(canvas.transform, false);

            RectTransform panelRect = subtitlePanel.AddComponent<RectTransform>();
            panelRect.anchorMin = new Vector2(0.02f, 0f);
            panelRect.anchorMax = new Vector2(0.98f, 0f);
            panelRect.pivot = new Vector2(0.5f, 0f);
            panelRect.anchoredPosition = new Vector2(0, 5);
            panelRect.sizeDelta = new Vector2(0, 55);

            Image bgImage = subtitlePanel.AddComponent<Image>();
            bgImage.color = new Color(0, 0, 0, 0.8f);

            subtitlePanel.AddComponent<CanvasGroup>();

            GameObject speakerObj = new GameObject("SpeakerName");
            speakerObj.transform.SetParent(subtitlePanel.transform, false);

            RectTransform speakerRect = speakerObj.AddComponent<RectTransform>();
            speakerRect.anchorMin = new Vector2(0, 0);
            speakerRect.anchorMax = new Vector2(0, 1);
            speakerRect.pivot = new Vector2(0, 0.5f);
            speakerRect.anchoredPosition = new Vector2(6, 0);
            speakerRect.sizeDelta = new Vector2(65, 0);

            TextMeshProUGUI speakerText = speakerObj.AddComponent<TextMeshProUGUI>();
            speakerText.text = "";
            speakerText.fontSize = 10;
            speakerText.fontStyle = FontStyles.Bold;
            speakerText.color = Color.yellow;
            speakerText.alignment = TextAlignmentOptions.Left;
            speakerText.verticalAlignment = VerticalAlignmentOptions.Middle;
            speakerText.enableWordWrapping = false;

            GameObject subtitleObj = new GameObject("SubtitleText");
            subtitleObj.transform.SetParent(subtitlePanel.transform, false);

            RectTransform subtitleRect = subtitleObj.AddComponent<RectTransform>();
            subtitleRect.anchorMin = Vector2.zero;
            subtitleRect.anchorMax = Vector2.one;
            subtitleRect.pivot = new Vector2(0, 0.5f);
            subtitleRect.offsetMin = new Vector2(70, 2);
            subtitleRect.offsetMax = new Vector2(-5, -2);

            TextMeshProUGUI subtitleText = subtitleObj.AddComponent<TextMeshProUGUI>();
            subtitleText.text = "";
            subtitleText.fontSize = 10;
            subtitleText.color = Color.white;
            subtitleText.alignment = TextAlignmentOptions.TopLeft;
            subtitleText.enableWordWrapping = true;
            subtitleText.overflowMode = TextOverflowModes.Ellipsis;

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

            // Mark scene dirty
            UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(
                UnityEditor.SceneManagement.EditorSceneManager.GetActiveScene());

            // Select the panel
            Selection.activeGameObject = subtitlePanel;

            Debug.Log("[SubtitleUIGenerator] Subtitle UI created successfully!");
            Debug.Log("SubtitleManager references have been auto-assigned.");
        }
    }
}
