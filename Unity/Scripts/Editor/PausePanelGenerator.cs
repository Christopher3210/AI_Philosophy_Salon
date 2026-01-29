// PausePanelGenerator.cs
// Editor tool to generate the pause panel UI

using UnityEngine;
using UnityEditor;
using UnityEngine.UI;
using TMPro;

namespace PhilosophySalon.Editor
{
    public class PausePanelGenerator : EditorWindow
    {
        [MenuItem("Philosophy Salon/Generate Pause Panel UI")]
        public static void GeneratePausePanel()
        {
            // Find or create Canvas
            Canvas canvas = FindObjectOfType<Canvas>();
            if (canvas == null)
            {
                Debug.LogError("No Canvas found in scene. Please create a Canvas first.");
                return;
            }

            // Create pause panel
            GameObject pausePanel = CreatePanel(canvas.transform, "PausePanel");

            // Create semi-transparent background
            Image bgImage = pausePanel.GetComponent<Image>();
            bgImage.color = new Color(0, 0, 0, 0.7f);

            // Create center panel
            GameObject centerPanel = CreateElement("CenterPanel", pausePanel.transform);
            RectTransform centerRect = centerPanel.GetComponent<RectTransform>();
            centerRect.anchorMin = new Vector2(0.3f, 0.25f);
            centerRect.anchorMax = new Vector2(0.7f, 0.75f);
            centerRect.offsetMin = Vector2.zero;
            centerRect.offsetMax = Vector2.zero;

            Image centerBg = centerPanel.AddComponent<Image>();
            centerBg.color = new Color(0.15f, 0.15f, 0.2f, 0.95f);

            // Title
            GameObject titleObj = CreateElement("Title", centerPanel.transform);
            RectTransform titleRect = titleObj.GetComponent<RectTransform>();
            titleRect.anchorMin = new Vector2(0, 0.85f);
            titleRect.anchorMax = new Vector2(1, 0.95f);
            titleRect.offsetMin = new Vector2(10, 0);
            titleRect.offsetMax = new Vector2(-10, 0);

            TextMeshProUGUI titleText = titleObj.AddComponent<TextMeshProUGUI>();
            titleText.text = "Debate Paused";
            titleText.fontSize = 28;
            titleText.alignment = TextAlignmentOptions.Center;
            titleText.color = new Color(0.85f, 0.75f, 0.55f);

            // Question section
            GameObject questionSection = CreateElement("QuestionSection", centerPanel.transform);
            RectTransform qsRect = questionSection.GetComponent<RectTransform>();
            qsRect.anchorMin = new Vector2(0.05f, 0.45f);
            qsRect.anchorMax = new Vector2(0.95f, 0.80f);
            qsRect.offsetMin = Vector2.zero;
            qsRect.offsetMax = Vector2.zero;

            // Question label
            GameObject qLabelObj = CreateElement("QuestionLabel", questionSection.transform);
            RectTransform qlRect = qLabelObj.GetComponent<RectTransform>();
            qlRect.anchorMin = new Vector2(0, 0.75f);
            qlRect.anchorMax = new Vector2(1, 1f);
            qlRect.offsetMin = Vector2.zero;
            qlRect.offsetMax = Vector2.zero;

            TextMeshProUGUI qLabelText = qLabelObj.AddComponent<TextMeshProUGUI>();
            qLabelText.text = "Ask a Question:";
            qLabelText.fontSize = 18;
            qLabelText.alignment = TextAlignmentOptions.Left;
            qLabelText.color = Color.white;

            // Question input (full width now)
            GameObject inputObj = CreateInputField(questionSection.transform, "QuestionInput");
            RectTransform inputRect = inputObj.GetComponent<RectTransform>();
            inputRect.anchorMin = new Vector2(0, 0.5f);
            inputRect.anchorMax = new Vector2(1f, 0.75f);
            inputRect.offsetMin = Vector2.zero;
            inputRect.offsetMax = Vector2.zero;

            // Ask button
            GameObject askBtnObj = CreateButton(questionSection.transform, "AskButton", "Ask Question");
            RectTransform askRect = askBtnObj.GetComponent<RectTransform>();
            askRect.anchorMin = new Vector2(0.3f, 0.1f);
            askRect.anchorMax = new Vector2(0.7f, 0.35f);
            askRect.offsetMin = Vector2.zero;
            askRect.offsetMax = Vector2.zero;

            // Button section
            GameObject buttonSection = CreateElement("ButtonSection", centerPanel.transform);
            RectTransform bsRect = buttonSection.GetComponent<RectTransform>();
            bsRect.anchorMin = new Vector2(0.05f, 0.05f);
            bsRect.anchorMax = new Vector2(0.95f, 0.40f);
            bsRect.offsetMin = Vector2.zero;
            bsRect.offsetMax = Vector2.zero;

            // Resume button
            GameObject resumeBtn = CreateButton(buttonSection.transform, "ResumeButton", "Continue Debate");
            RectTransform resumeRect = resumeBtn.GetComponent<RectTransform>();
            resumeRect.anchorMin = new Vector2(0.05f, 0.55f);
            resumeRect.anchorMax = new Vector2(0.45f, 0.9f);
            resumeRect.offsetMin = Vector2.zero;
            resumeRect.offsetMax = Vector2.zero;
            SetButtonColor(resumeBtn, new Color(0.2f, 0.5f, 0.3f));

            // Exit button
            GameObject exitBtn = CreateButton(buttonSection.transform, "ExitButton", "Exit to Menu");
            RectTransform exitRect = exitBtn.GetComponent<RectTransform>();
            exitRect.anchorMin = new Vector2(0.55f, 0.55f);
            exitRect.anchorMax = new Vector2(0.95f, 0.9f);
            exitRect.offsetMin = Vector2.zero;
            exitRect.offsetMax = Vector2.zero;
            SetButtonColor(exitBtn, new Color(0.5f, 0.2f, 0.2f));

            // Pause button (outside the panel, in the main UI)
            GameObject pauseBtn = CreateButton(canvas.transform, "PauseButton", "Pause");
            RectTransform pauseRect = pauseBtn.GetComponent<RectTransform>();
            pauseRect.anchorMin = new Vector2(0.9f, 0.9f);
            pauseRect.anchorMax = new Vector2(0.98f, 0.98f);
            pauseRect.offsetMin = Vector2.zero;
            pauseRect.offsetMax = Vector2.zero;
            SetButtonColor(pauseBtn, new Color(0.4f, 0.4f, 0.5f));

            // Hide pause panel initially
            pausePanel.SetActive(false);

            // Try to connect to UIManager
            UIManager uiManager = FindObjectOfType<UIManager>();
            if (uiManager != null)
            {
                uiManager.pausePanel = pausePanel;
                uiManager.pauseButton = pauseBtn.GetComponent<Button>();
                uiManager.resumeButton = resumeBtn.GetComponent<Button>();
                uiManager.exitButton = exitBtn.GetComponent<Button>();
                uiManager.askInPauseButton = askBtnObj.GetComponent<Button>();

                TMP_InputField input = inputObj.GetComponent<TMP_InputField>();
                if (uiManager.questionInput == null)
                    uiManager.questionInput = input;

                EditorUtility.SetDirty(uiManager);
                Debug.Log("UIManager references connected!");
            }

            Selection.activeGameObject = pausePanel;
            Debug.Log("Pause Panel UI generated successfully!");
        }

        static GameObject CreatePanel(Transform parent, string name)
        {
            GameObject panel = new GameObject(name);
            panel.transform.SetParent(parent, false);

            RectTransform rect = panel.AddComponent<RectTransform>();
            rect.anchorMin = Vector2.zero;
            rect.anchorMax = Vector2.one;
            rect.offsetMin = Vector2.zero;
            rect.offsetMax = Vector2.zero;

            panel.AddComponent<Image>();
            return panel;
        }

        static GameObject CreateElement(string name, Transform parent)
        {
            GameObject obj = new GameObject(name);
            obj.transform.SetParent(parent, false);
            obj.AddComponent<RectTransform>();
            return obj;
        }

        static GameObject CreateButton(Transform parent, string name, string text)
        {
            GameObject btnObj = new GameObject(name);
            btnObj.transform.SetParent(parent, false);
            btnObj.AddComponent<RectTransform>();

            Image img = btnObj.AddComponent<Image>();
            img.color = new Color(0.25f, 0.25f, 0.3f);

            Button btn = btnObj.AddComponent<Button>();
            btn.targetGraphic = img;

            ColorBlock colors = btn.colors;
            colors.highlightedColor = new Color(0.35f, 0.35f, 0.4f);
            colors.pressedColor = new Color(0.2f, 0.2f, 0.25f);
            btn.colors = colors;

            GameObject textObj = new GameObject("Text");
            textObj.transform.SetParent(btnObj.transform, false);

            RectTransform textRect = textObj.AddComponent<RectTransform>();
            textRect.anchorMin = Vector2.zero;
            textRect.anchorMax = Vector2.one;
            textRect.offsetMin = new Vector2(5, 2);
            textRect.offsetMax = new Vector2(-5, -2);

            TextMeshProUGUI btnText = textObj.AddComponent<TextMeshProUGUI>();
            btnText.text = text;
            btnText.fontSize = 16;
            btnText.alignment = TextAlignmentOptions.Center;
            btnText.color = Color.white;

            return btnObj;
        }

        static void SetButtonColor(GameObject btnObj, Color color)
        {
            Image img = btnObj.GetComponent<Image>();
            if (img != null)
            {
                img.color = color;
            }

            Button btn = btnObj.GetComponent<Button>();
            if (btn != null)
            {
                ColorBlock colors = btn.colors;
                colors.normalColor = color;
                colors.highlightedColor = color * 1.2f;
                colors.pressedColor = color * 0.8f;
                btn.colors = colors;
            }
        }

        static GameObject CreateDropdown(Transform parent, string name)
        {
            GameObject ddObj = new GameObject(name);
            ddObj.transform.SetParent(parent, false);
            ddObj.AddComponent<RectTransform>();

            Image bgImg = ddObj.AddComponent<Image>();
            bgImg.color = new Color(0.2f, 0.2f, 0.25f);

            TMP_Dropdown dropdown = ddObj.AddComponent<TMP_Dropdown>();

            // Label
            GameObject labelObj = new GameObject("Label");
            labelObj.transform.SetParent(ddObj.transform, false);
            RectTransform labelRect = labelObj.AddComponent<RectTransform>();
            labelRect.anchorMin = Vector2.zero;
            labelRect.anchorMax = Vector2.one;
            labelRect.offsetMin = new Vector2(10, 2);
            labelRect.offsetMax = new Vector2(-25, -2);

            TextMeshProUGUI labelText = labelObj.AddComponent<TextMeshProUGUI>();
            labelText.text = "Aristotle";
            labelText.fontSize = 14;
            labelText.alignment = TextAlignmentOptions.Left;
            labelText.color = Color.white;

            dropdown.captionText = labelText;

            // Add default options
            dropdown.ClearOptions();
            dropdown.AddOptions(new System.Collections.Generic.List<string> { "Aristotle", "Sartre", "Wittgenstein", "Russell" });

            // Template (simplified)
            GameObject template = new GameObject("Template");
            template.transform.SetParent(ddObj.transform, false);
            RectTransform templateRect = template.AddComponent<RectTransform>();
            templateRect.anchorMin = new Vector2(0, 0);
            templateRect.anchorMax = new Vector2(1, 0);
            templateRect.pivot = new Vector2(0.5f, 1);
            templateRect.sizeDelta = new Vector2(0, 120);

            Image templateImg = template.AddComponent<Image>();
            templateImg.color = new Color(0.15f, 0.15f, 0.2f);

            ScrollRect scroll = template.AddComponent<ScrollRect>();

            // Viewport
            GameObject viewport = new GameObject("Viewport");
            viewport.transform.SetParent(template.transform, false);
            RectTransform vpRect = viewport.AddComponent<RectTransform>();
            vpRect.anchorMin = Vector2.zero;
            vpRect.anchorMax = Vector2.one;
            vpRect.offsetMin = Vector2.zero;
            vpRect.offsetMax = Vector2.zero;

            viewport.AddComponent<Mask>();
            viewport.AddComponent<Image>().color = Color.white;

            // Content
            GameObject content = new GameObject("Content");
            content.transform.SetParent(viewport.transform, false);
            RectTransform contentRect = content.AddComponent<RectTransform>();
            contentRect.anchorMin = new Vector2(0, 1);
            contentRect.anchorMax = new Vector2(1, 1);
            contentRect.pivot = new Vector2(0.5f, 1);
            contentRect.sizeDelta = new Vector2(0, 28);

            scroll.viewport = vpRect;
            scroll.content = contentRect;

            // Item
            GameObject item = new GameObject("Item");
            item.transform.SetParent(content.transform, false);
            RectTransform itemRect = item.AddComponent<RectTransform>();
            itemRect.anchorMin = new Vector2(0, 0.5f);
            itemRect.anchorMax = new Vector2(1, 0.5f);
            itemRect.sizeDelta = new Vector2(0, 28);

            Toggle toggle = item.AddComponent<Toggle>();

            // Item label
            GameObject itemLabelObj = new GameObject("Item Label");
            itemLabelObj.transform.SetParent(item.transform, false);
            RectTransform itemLabelRect = itemLabelObj.AddComponent<RectTransform>();
            itemLabelRect.anchorMin = Vector2.zero;
            itemLabelRect.anchorMax = Vector2.one;
            itemLabelRect.offsetMin = new Vector2(10, 0);
            itemLabelRect.offsetMax = new Vector2(-10, 0);

            TextMeshProUGUI itemLabel = itemLabelObj.AddComponent<TextMeshProUGUI>();
            itemLabel.fontSize = 14;
            itemLabel.alignment = TextAlignmentOptions.Left;
            itemLabel.color = Color.white;

            dropdown.template = templateRect;
            dropdown.itemText = itemLabel;

            template.SetActive(false);

            return ddObj;
        }

        static GameObject CreateInputField(Transform parent, string name)
        {
            GameObject inputObj = new GameObject(name);
            inputObj.transform.SetParent(parent, false);
            inputObj.AddComponent<RectTransform>();

            Image bgImg = inputObj.AddComponent<Image>();
            bgImg.color = new Color(0.1f, 0.1f, 0.15f);

            TMP_InputField input = inputObj.AddComponent<TMP_InputField>();

            // Text Area
            GameObject textArea = new GameObject("Text Area");
            textArea.transform.SetParent(inputObj.transform, false);
            RectTransform taRect = textArea.AddComponent<RectTransform>();
            taRect.anchorMin = Vector2.zero;
            taRect.anchorMax = Vector2.one;
            taRect.offsetMin = new Vector2(10, 5);
            taRect.offsetMax = new Vector2(-10, -5);

            // Placeholder
            GameObject placeholderObj = new GameObject("Placeholder");
            placeholderObj.transform.SetParent(textArea.transform, false);
            RectTransform phRect = placeholderObj.AddComponent<RectTransform>();
            phRect.anchorMin = Vector2.zero;
            phRect.anchorMax = Vector2.one;
            phRect.offsetMin = Vector2.zero;
            phRect.offsetMax = Vector2.zero;

            TextMeshProUGUI placeholder = placeholderObj.AddComponent<TextMeshProUGUI>();
            placeholder.text = "Enter your question...";
            placeholder.fontSize = 14;
            placeholder.fontStyle = FontStyles.Italic;
            placeholder.color = new Color(0.5f, 0.5f, 0.5f);
            placeholder.alignment = TextAlignmentOptions.Left;

            // Text
            GameObject textObj = new GameObject("Text");
            textObj.transform.SetParent(textArea.transform, false);
            RectTransform txtRect = textObj.AddComponent<RectTransform>();
            txtRect.anchorMin = Vector2.zero;
            txtRect.anchorMax = Vector2.one;
            txtRect.offsetMin = Vector2.zero;
            txtRect.offsetMax = Vector2.zero;

            TextMeshProUGUI inputText = textObj.AddComponent<TextMeshProUGUI>();
            inputText.fontSize = 14;
            inputText.color = Color.white;
            inputText.alignment = TextAlignmentOptions.Left;

            input.textViewport = taRect;
            input.textComponent = inputText;
            input.placeholder = placeholder;

            return inputObj;
        }
    }
}
