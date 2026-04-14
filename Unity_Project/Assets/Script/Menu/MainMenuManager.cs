using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using UnityEngine.EventSystems;
using System.Collections;

/// <summary>
/// Main menu controller - handles menu display and navigation
/// Usage: Create an empty GameObject and attach this script
/// </summary>
public class MainMenuManager : MonoBehaviour
{
    [Header("Scene Settings")]
    public string gameSceneName = "SalonScene";

    [Header("Animation")]
    public float fadeSpeed = 1.5f;

    // UI Components
    private Canvas canvas;
    private GameObject mainMenuPanel;
    private SettingsPanel settingsPanel;
    private CanvasGroup fadeOverlay;
    private Slider convivialitySlider;
    private Text convivialityValueText;
    private Slider durationSlider;
    private Text durationValueText;
    private InputField topicInputField;

    void Start()
    {
        CreateEventSystem();
        CreateCanvas();
        CreateBackground();
        CreateMainMenu();
        CreateSettingsPanel();
        CreateFadeOverlay();

        StartCoroutine(FadeIn());
    }

    private void CreateEventSystem()
    {
        if (FindObjectOfType<EventSystem>() == null)
        {
            GameObject eventSystem = new GameObject("EventSystem");
            eventSystem.AddComponent<EventSystem>();
            eventSystem.AddComponent<StandaloneInputModule>();
        }
    }

    private void CreateCanvas()
    {
        GameObject canvasObj = new GameObject("MainMenuCanvas");
        canvas = canvasObj.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 100;

        CanvasScaler scaler = canvasObj.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        scaler.matchWidthOrHeight = 0.5f;

        canvasObj.AddComponent<GraphicRaycaster>();
    }

    private void CreateBackground()
    {
        GameObject bg = UIFactory.CreateElement("Background", canvas.gameObject);
        Image bgImage = bg.AddComponent<Image>();
        bgImage.color = SettingsData.BackgroundColor;
        UIFactory.SetFullScreen(bg);
    }

    private void CreateMainMenu()
    {
        mainMenuPanel = UIFactory.CreateElement("MainMenuPanel", canvas.gameObject);
        UIFactory.SetFullScreen(mainMenuPanel);

        // Title
        Text title = UIFactory.CreateText(mainMenuPanel, "Title", "AI Philosophy Salon",
            72, SettingsData.TitleColor, TextAnchor.MiddleCenter, FontStyle.Bold);
        UIFactory.SetRect(title.gameObject, 0.5f, 0.7f, 900, 100);

        // Subtitle
        Text subtitle = UIFactory.CreateText(mainMenuPanel, "Subtitle",
            "— Philosophical Debate with AI Agents —",
            24, SettingsData.SubtitleColor, TextAnchor.MiddleCenter, FontStyle.Italic);
        UIFactory.SetRect(subtitle.gameObject, 0.5f, 0.62f, 600, 40);

        // Topic input section
        GameObject topicSection = UIFactory.CreateElement("TopicSection", mainMenuPanel);
        UIFactory.SetRect(topicSection, 0.5f, 0.52f, 600, 70);

        Text topicLabel = UIFactory.CreateText(topicSection, "Label", "Debate Topic",
            20, SettingsData.SubtitleColor, TextAnchor.MiddleCenter);
        RectTransform topicLabelRect = topicLabel.GetComponent<RectTransform>();
        topicLabelRect.anchorMin = new Vector2(0, 0.65f);
        topicLabelRect.anchorMax = new Vector2(1, 1f);
        topicLabelRect.offsetMin = Vector2.zero;
        topicLabelRect.offsetMax = Vector2.zero;

        topicInputField = CreateTopicInputField(topicSection);

        // Conviviality slider section
        GameObject sliderSection = UIFactory.CreateElement("ConvivialitySection", mainMenuPanel);
        UIFactory.SetRect(sliderSection, 0.5f, 0.40f, 400, 80);

        Text sliderLabel = UIFactory.CreateText(sliderSection, "Label", "Conviviality",
            20, SettingsData.SubtitleColor, TextAnchor.MiddleCenter);
        RectTransform labelRect = sliderLabel.GetComponent<RectTransform>();
        labelRect.anchorMin = new Vector2(0, 0.6f);
        labelRect.anchorMax = new Vector2(1, 1f);
        labelRect.offsetMin = Vector2.zero;
        labelRect.offsetMax = Vector2.zero;

        convivialitySlider = CreateConvivialitySlider(sliderSection);

        convivialityValueText = UIFactory.CreateText(sliderSection, "Value", GetConvivialityLabel(SettingsData.Conviviality),
            16, SettingsData.TitleColor, TextAnchor.MiddleCenter);
        RectTransform valueRect = convivialityValueText.GetComponent<RectTransform>();
        valueRect.anchorMin = new Vector2(0, 0f);
        valueRect.anchorMax = new Vector2(1, 0.25f);
        valueRect.offsetMin = Vector2.zero;
        valueRect.offsetMax = Vector2.zero;

        // Duration slider section
        GameObject durationSection = UIFactory.CreateElement("DurationSection", mainMenuPanel);
        UIFactory.SetRect(durationSection, 0.5f, 0.32f, 500, 80);

        Text durationLabel = UIFactory.CreateText(durationSection, "DurationLabel", "Debate Duration",
            18, SettingsData.SubtitleColor, TextAnchor.MiddleCenter);
        RectTransform durLabelRect = durationLabel.GetComponent<RectTransform>();
        durLabelRect.anchorMin = new Vector2(0, 0.6f);
        durLabelRect.anchorMax = new Vector2(1, 1f);
        durLabelRect.offsetMin = Vector2.zero;
        durLabelRect.offsetMax = Vector2.zero;

        durationSlider = CreateDurationSlider(durationSection);

        durationValueText = UIFactory.CreateText(durationSection, "DurationValue", GetDurationLabel(SettingsData.DebateDuration),
            16, SettingsData.TitleColor, TextAnchor.MiddleCenter);
        RectTransform durValueRect = durationValueText.GetComponent<RectTransform>();
        durValueRect.anchorMin = new Vector2(0, 0f);
        durValueRect.anchorMax = new Vector2(1, 0.25f);
        durValueRect.offsetMin = Vector2.zero;
        durValueRect.offsetMax = Vector2.zero;

        // Button container
        GameObject buttonContainer = UIFactory.CreateElement("ButtonContainer", mainMenuPanel);
        UIFactory.SetRect(buttonContainer, 0.5f, 0.22f, 300, 180);

        VerticalLayoutGroup layout = buttonContainer.AddComponent<VerticalLayoutGroup>();
        layout.spacing = 15;
        layout.childAlignment = TextAnchor.MiddleCenter;
        layout.childControlWidth = true;
        layout.childControlHeight = false;
        layout.childForceExpandWidth = true;
        layout.childForceExpandHeight = false;

        UIFactory.CreateButton(buttonContainer, "StartDebate", "Start Debate", OnStartClick);
        UIFactory.CreateButton(buttonContainer, "Settings", "Settings", OnSettingsClick);
        UIFactory.CreateButton(buttonContainer, "Exit", "Exit", OnExitClick);

        // Footer
        Text footer = UIFactory.CreateText(mainMenuPanel, "Footer",
            "Graduation Project 2025 · Jinwei Zhang",
            16, new Color(0.4f, 0.4f, 0.4f, 1f));
        UIFactory.SetRect(footer.gameObject, 0.5f, 0.05f, 400, 30);
    }

    private void CreateSettingsPanel()
    {
        settingsPanel = canvas.gameObject.AddComponent<SettingsPanel>();
        settingsPanel.Initialize(canvas.gameObject);
        settingsPanel.OnBackClicked = OnBackClick;
    }

    private void CreateFadeOverlay()
    {
        GameObject fadeObj = UIFactory.CreateElement("FadeOverlay", canvas.gameObject);
        Image fadeImage = fadeObj.AddComponent<Image>();
        fadeImage.color = Color.black;
        fadeOverlay = fadeObj.AddComponent<CanvasGroup>();
        fadeOverlay.alpha = 1f;
        fadeOverlay.blocksRaycasts = true;
        UIFactory.SetFullScreen(fadeObj);
        fadeObj.transform.SetAsLastSibling();
    }

    private Slider CreateConvivialitySlider(GameObject parent)
    {
        GameObject sliderObj = UIFactory.CreateElement("Slider", parent);
        RectTransform sliderRect = sliderObj.GetComponent<RectTransform>();
        sliderRect.anchorMin = new Vector2(0.1f, 0.25f);
        sliderRect.anchorMax = new Vector2(0.9f, 0.55f);
        sliderRect.offsetMin = Vector2.zero;
        sliderRect.offsetMax = Vector2.zero;

        GameObject bgObj = UIFactory.CreateElement("Background", sliderObj);
        Image bgImage = bgObj.AddComponent<Image>();
        bgImage.color = new Color(0.2f, 0.2f, 0.25f, 1f);
        UIFactory.SetFullScreen(bgObj);

        GameObject fillArea = UIFactory.CreateElement("FillArea", sliderObj);
        RectTransform fillAreaRect = fillArea.GetComponent<RectTransform>();
        fillAreaRect.anchorMin = new Vector2(0, 0.25f);
        fillAreaRect.anchorMax = new Vector2(1, 0.75f);
        fillAreaRect.offsetMin = new Vector2(5, 0);
        fillAreaRect.offsetMax = new Vector2(-5, 0);

        GameObject fill = UIFactory.CreateElement("Fill", fillArea);
        Image fillImage = fill.AddComponent<Image>();
        fillImage.color = SettingsData.TitleColor;
        RectTransform fillRect = fill.GetComponent<RectTransform>();
        fillRect.anchorMin = Vector2.zero;
        fillRect.anchorMax = Vector2.one;
        fillRect.offsetMin = Vector2.zero;
        fillRect.offsetMax = Vector2.zero;

        GameObject handleArea = UIFactory.CreateElement("HandleArea", sliderObj);
        RectTransform handleAreaRect = handleArea.GetComponent<RectTransform>();
        handleAreaRect.anchorMin = Vector2.zero;
        handleAreaRect.anchorMax = Vector2.one;
        handleAreaRect.offsetMin = new Vector2(10, 0);
        handleAreaRect.offsetMax = new Vector2(-10, 0);

        GameObject handle = UIFactory.CreateElement("Handle", handleArea);
        Image handleImage = handle.AddComponent<Image>();
        handleImage.color = Color.white;
        RectTransform handleRect = handle.GetComponent<RectTransform>();
        handleRect.sizeDelta = new Vector2(20, 0);

        Slider slider = sliderObj.AddComponent<Slider>();
        slider.fillRect = fillRect;
        slider.handleRect = handleRect;
        slider.targetGraphic = handleImage;
        slider.direction = Slider.Direction.LeftToRight;
        slider.minValue = 0f;
        slider.maxValue = 1f;
        slider.value = SettingsData.Conviviality;
        slider.onValueChanged.AddListener(OnConvivialityChanged);

        return slider;
    }

    private InputField CreateTopicInputField(GameObject parent)
    {
        GameObject inputObj = UIFactory.CreateElement("TopicInput", parent);
        RectTransform inputRect = inputObj.GetComponent<RectTransform>();
        inputRect.anchorMin = new Vector2(0.05f, 0.1f);
        inputRect.anchorMax = new Vector2(0.95f, 0.6f);
        inputRect.offsetMin = Vector2.zero;
        inputRect.offsetMax = Vector2.zero;

        Image bgImage = inputObj.AddComponent<Image>();
        bgImage.color = new Color(0.15f, 0.15f, 0.2f, 1f);

        GameObject textArea = UIFactory.CreateElement("TextArea", inputObj);
        RectTransform textAreaRect = textArea.GetComponent<RectTransform>();
        textAreaRect.anchorMin = Vector2.zero;
        textAreaRect.anchorMax = Vector2.one;
        textAreaRect.offsetMin = new Vector2(10, 5);
        textAreaRect.offsetMax = new Vector2(-10, -5);

        GameObject textObj = UIFactory.CreateElement("Text", textArea);
        RectTransform textObjRect = textObj.GetComponent<RectTransform>();
        textObjRect.anchorMin = Vector2.zero;
        textObjRect.anchorMax = Vector2.one;
        textObjRect.offsetMin = Vector2.zero;
        textObjRect.offsetMax = Vector2.zero;

        Text inputText = textObj.AddComponent<Text>();
        inputText.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        inputText.fontSize = 18;
        inputText.color = Color.white;
        inputText.alignment = TextAnchor.MiddleLeft;
        inputText.supportRichText = false;

        GameObject placeholderObj = UIFactory.CreateElement("Placeholder", textArea);
        RectTransform placeholderRect = placeholderObj.GetComponent<RectTransform>();
        placeholderRect.anchorMin = Vector2.zero;
        placeholderRect.anchorMax = Vector2.one;
        placeholderRect.offsetMin = Vector2.zero;
        placeholderRect.offsetMax = Vector2.zero;

        Text placeholderText = placeholderObj.AddComponent<Text>();
        placeholderText.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        placeholderText.fontSize = 18;
        placeholderText.fontStyle = FontStyle.Italic;
        placeholderText.color = new Color(0.5f, 0.5f, 0.5f, 0.8f);
        placeholderText.alignment = TextAnchor.MiddleLeft;
        placeholderText.text = "Enter debate topic...";

        InputField input = inputObj.AddComponent<InputField>();
        input.textComponent = inputText;
        input.placeholder = placeholderText;
        input.text = SettingsData.Topic;
        input.onEndEdit.AddListener(OnTopicChanged);

        return input;
    }

    private void OnTopicChanged(string value)
    {
        if (!string.IsNullOrWhiteSpace(value))
        {
            SettingsData.Topic = value;
        }
    }

    private string GetConvivialityLabel(float value)
    {
        if (value < 0.33f) return "Heated Debate";
        if (value < 0.66f) return "Balanced Discussion";
        return "Friendly Exchange";
    }

    private void OnConvivialityChanged(float value)
    {
        SettingsData.Conviviality = value;
        if (convivialityValueText != null)
        {
            convivialityValueText.text = GetConvivialityLabel(value);
        }
    }

    private Slider CreateDurationSlider(GameObject parent)
    {
        GameObject sliderObj = UIFactory.CreateElement("DurationSlider", parent);
        RectTransform sliderRect = sliderObj.GetComponent<RectTransform>();
        sliderRect.anchorMin = new Vector2(0.1f, 0.25f);
        sliderRect.anchorMax = new Vector2(0.9f, 0.55f);
        sliderRect.offsetMin = Vector2.zero;
        sliderRect.offsetMax = Vector2.zero;

        GameObject bgObj = UIFactory.CreateElement("Background", sliderObj);
        Image bgImage = bgObj.AddComponent<Image>();
        bgImage.color = new Color(0.2f, 0.2f, 0.25f, 1f);
        UIFactory.SetFullScreen(bgObj);

        GameObject fillArea = UIFactory.CreateElement("FillArea", sliderObj);
        RectTransform fillAreaRect = fillArea.GetComponent<RectTransform>();
        fillAreaRect.anchorMin = new Vector2(0, 0.25f);
        fillAreaRect.anchorMax = new Vector2(1, 0.75f);
        fillAreaRect.offsetMin = new Vector2(5, 0);
        fillAreaRect.offsetMax = new Vector2(-5, 0);

        GameObject fill = UIFactory.CreateElement("Fill", fillArea);
        Image fillImage = fill.AddComponent<Image>();
        fillImage.color = SettingsData.TitleColor;
        RectTransform fillRect = fill.GetComponent<RectTransform>();
        fillRect.anchorMin = Vector2.zero;
        fillRect.anchorMax = Vector2.one;
        fillRect.offsetMin = Vector2.zero;
        fillRect.offsetMax = Vector2.zero;

        GameObject handleArea = UIFactory.CreateElement("HandleArea", sliderObj);
        RectTransform handleAreaRect = handleArea.GetComponent<RectTransform>();
        handleAreaRect.anchorMin = Vector2.zero;
        handleAreaRect.anchorMax = Vector2.one;
        handleAreaRect.offsetMin = new Vector2(10, 0);
        handleAreaRect.offsetMax = new Vector2(-10, 0);

        GameObject handle = UIFactory.CreateElement("Handle", handleArea);
        Image handleImage = handle.AddComponent<Image>();
        handleImage.color = Color.white;
        RectTransform handleRect = handle.GetComponent<RectTransform>();
        handleRect.sizeDelta = new Vector2(20, 0);

        Slider slider = sliderObj.AddComponent<Slider>();
        slider.fillRect = fillRect;
        slider.handleRect = handleRect;
        slider.targetGraphic = handleImage;
        slider.direction = Slider.Direction.LeftToRight;
        slider.wholeNumbers = true;
        slider.minValue = 0f;
        slider.maxValue = 30f;
        slider.value = SettingsData.DebateDuration;
        slider.onValueChanged.AddListener(OnDurationChanged);

        return slider;
    }

    private string GetDurationLabel(float minutes)
    {
        if (minutes <= 0) return "Unlimited";
        return $"{(int)minutes} minutes";
    }

    private void OnDurationChanged(float value)
    {
        SettingsData.DebateDuration = value;
        if (durationValueText != null)
        {
            durationValueText.text = GetDurationLabel(value);
        }
    }

    // === Button Callbacks ===

    private void OnStartClick()
    {
        StartCoroutine(FadeOutAndLoad(gameSceneName));
    }

    private void OnSettingsClick()
    {
        mainMenuPanel.SetActive(false);
        settingsPanel.Show();
    }

    private void OnBackClick()
    {
        settingsPanel.Hide();
        mainMenuPanel.SetActive(true);
    }

    private void OnExitClick()
    {
        #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
        #else
            Application.Quit();
        #endif
    }

    // === Fade Effects ===

    private IEnumerator FadeIn()
    {
        while (fadeOverlay.alpha > 0)
        {
            fadeOverlay.alpha -= Time.deltaTime * fadeSpeed;
            yield return null;
        }
        fadeOverlay.blocksRaycasts = false;
        fadeOverlay.gameObject.SetActive(false);
    }

    private IEnumerator FadeOutAndLoad(string sceneName)
    {
        fadeOverlay.gameObject.SetActive(true);
        fadeOverlay.blocksRaycasts = true;
        fadeOverlay.alpha = 0f;

        while (fadeOverlay.alpha < 1)
        {
            fadeOverlay.alpha += Time.deltaTime * fadeSpeed;
            yield return null;
        }

        SceneManager.LoadScene(sceneName);
    }
}
