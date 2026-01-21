using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using UnityEngine.EventSystems;
using System.Collections;
using System.Collections.Generic;

/// <summary>
/// AI Philosophy Salon - Main Menu with Settings Panel
/// Usage: Create an empty GameObject and attach this script
/// </summary>
public class MainMenuGenerator : MonoBehaviour
{
    [Header("Scene Settings")]
    public string gameSceneName = "SalonScene";

    [Header("Color Theme")]
    public Color backgroundColor = new Color(0.08f, 0.08f, 0.12f, 1f);
    public Color titleColor = new Color(0.85f, 0.75f, 0.55f, 1f);
    public Color subtitleColor = new Color(0.7f, 0.7f, 0.7f, 1f);
    public Color buttonTextColor = new Color(0.9f, 0.9f, 0.9f, 1f);
    public Color buttonHoverColor = new Color(0.85f, 0.75f, 0.55f, 0.3f);
    public Color panelColor = new Color(0.12f, 0.12f, 0.18f, 0.98f);
    public Color dropdownColor = new Color(0.15f, 0.15f, 0.2f, 1f);

    // Language models list (for display)
    private string[] languageModels = new string[]
    {
        "GPT-4o",
        "GPT-4 Turbo",
        "Claude 3.5 Sonnet",
        "Claude 3 Opus",
        "Gemini 1.5 Pro",
        "Gemini Ultra",
        "LLaMA 3.1 405B",
        "Mistral Large",
        "Qwen 2.5 72B",
        "DeepSeek V3"
    };

    // TTS voices list (for display)
    private string[] ttsVoices = new string[]
    {
        "David (Deep Male)",
        "James (British Male)",
        "Michael (American Male)",
        "Robert (Elderly Male)",
        "William (Classical Male)",
        "Alexander (European Male)",
        "Benjamin (Warm Male)",
        "Charles (Formal Male)",
        "Edward (Scholarly Male)",
        "Frederick (Authoritative Male)"
    };

    // Philosopher names
    private string[] philosophers = new string[]
    {
        "Aristotle",
        "Sartre",
        "Wittgenstein",
        "Russell"
    };

    // Private variables
    private Canvas canvas;
    private CanvasGroup fadeOverlay;
    private GameObject mainMenuPanel;
    private GameObject settingsPanel;
    private Slider volumeSlider;
    private Slider speedSlider;
    private Toggle subtitleToggle;
    private float fadeSpeed = 1.5f;
    private Font uiFont;

    // Settings storage
    private Dictionary<string, int> philosopherModelIndex = new Dictionary<string, int>();
    private Dictionary<string, int> philosopherVoiceIndex = new Dictionary<string, int>();

    void Start()
    {
        // Initialize default settings
        for (int i = 0; i < philosophers.Length; i++)
        {
            philosopherModelIndex[philosophers[i]] = i % languageModels.Length;
            philosopherVoiceIndex[philosophers[i]] = i % ttsVoices.Length;
        }

        uiFont = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        CreateUI();
        StartCoroutine(FadeIn());
    }

    void CreateUI()
    {
        // Create EventSystem
        if (FindObjectOfType<EventSystem>() == null)
        {
            GameObject eventSystem = new GameObject("EventSystem");
            eventSystem.AddComponent<EventSystem>();
            eventSystem.AddComponent<StandaloneInputModule>();
        }

        // Create Canvas
        GameObject canvasObj = new GameObject("MainMenuCanvas");
        canvas = canvasObj.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 100;
        CanvasScaler scaler = canvasObj.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        scaler.matchWidthOrHeight = 0.5f;
        canvasObj.AddComponent<GraphicRaycaster>();

        // Create background
        CreateBackground(canvasObj);

        // Create main menu
        CreateMainMenu(canvasObj);

        // Create settings panel
        CreateSettingsPanel(canvasObj);

        // Create fade overlay
        CreateFadeOverlay(canvasObj);
    }

    void CreateBackground(GameObject parent)
    {
        GameObject bg = CreateUIElement("Background", parent);
        Image bgImage = bg.AddComponent<Image>();
        bgImage.color = backgroundColor;
        SetFullScreen(bg);
    }

    void CreateMainMenu(GameObject parent)
    {
        mainMenuPanel = CreateUIElement("MainMenuPanel", parent);
        SetFullScreen(mainMenuPanel);

        // Title
        GameObject titleObj = CreateUIElement("Title", mainMenuPanel);
        Text title = titleObj.AddComponent<Text>();
        title.text = "AI Philosophy Salon";
        title.font = uiFont;
        title.fontSize = 72;
        title.fontStyle = FontStyle.Bold;
        title.color = titleColor;
        title.alignment = TextAnchor.MiddleCenter;
        SetRect(titleObj, 0.5f, 0.7f, 900, 100);

        // Subtitle
        GameObject subtitleObj = CreateUIElement("Subtitle", mainMenuPanel);
        Text subtitle = subtitleObj.AddComponent<Text>();
        subtitle.text = "— Philosophical Debate with AI Agents —";
        subtitle.font = uiFont;
        subtitle.fontSize = 24;
        subtitle.fontStyle = FontStyle.Italic;
        subtitle.color = subtitleColor;
        subtitle.alignment = TextAnchor.MiddleCenter;
        SetRect(subtitleObj, 0.5f, 0.62f, 600, 40);

        // Button container
        GameObject buttonContainer = CreateUIElement("ButtonContainer", mainMenuPanel);
        SetRect(buttonContainer, 0.5f, 0.38f, 300, 220);
        VerticalLayoutGroup layout = buttonContainer.AddComponent<VerticalLayoutGroup>();
        layout.spacing = 15;
        layout.childAlignment = TextAnchor.MiddleCenter;
        layout.childControlWidth = true;
        layout.childControlHeight = false;
        layout.childForceExpandWidth = true;
        layout.childForceExpandHeight = false;

        CreateMenuButton(buttonContainer, "Start Debate", OnStartClick);
        CreateMenuButton(buttonContainer, "Settings", OnSettingsClick);
        CreateMenuButton(buttonContainer, "Exit", OnExitClick);

        // Footer
        GameObject footerObj = CreateUIElement("Footer", mainMenuPanel);
        Text footer = footerObj.AddComponent<Text>();
        footer.text = "Graduation Project 2025 · Jinwei Zhang";
        footer.font = uiFont;
        footer.fontSize = 16;
        footer.color = new Color(0.4f, 0.4f, 0.4f, 1f);
        footer.alignment = TextAnchor.MiddleCenter;
        SetRect(footerObj, 0.5f, 0.05f, 400, 30);
    }

    void CreateMenuButton(GameObject parent, string text, UnityEngine.Events.UnityAction onClick)
    {
        GameObject btnObj = CreateUIElement("Button_" + text, parent);
        Image btnImage = btnObj.AddComponent<Image>();
        btnImage.color = new Color(1, 1, 1, 0.08f);

        Button btn = btnObj.AddComponent<Button>();
        btn.onClick.AddListener(onClick);

        ColorBlock colors = btn.colors;
        colors.normalColor = new Color(1, 1, 1, 0.08f);
        colors.highlightedColor = buttonHoverColor;
        colors.pressedColor = new Color(0.85f, 0.75f, 0.55f, 0.5f);
        colors.selectedColor = buttonHoverColor;
        btn.colors = colors;

        LayoutElement layoutElement = btnObj.AddComponent<LayoutElement>();
        layoutElement.preferredHeight = 55;
        layoutElement.preferredWidth = 280;

        GameObject textObj = CreateUIElement("Text", btnObj);
        Text btnText = textObj.AddComponent<Text>();
        btnText.text = text;
        btnText.font = uiFont;
        btnText.fontSize = 26;
        btnText.color = buttonTextColor;
        btnText.alignment = TextAnchor.MiddleCenter;
        SetFullScreen(textObj);
    }

    void CreateSettingsPanel(GameObject parent)
    {
        settingsPanel = CreateUIElement("SettingsPanel", parent);
        SetFullScreen(settingsPanel);

        // Dark overlay
        GameObject overlay = CreateUIElement("Overlay", settingsPanel);
        Image overlayImg = overlay.AddComponent<Image>();
        overlayImg.color = new Color(0, 0, 0, 0.7f);
        SetFullScreen(overlay);

        // Settings window
        GameObject window = CreateUIElement("Window", settingsPanel);
        Image windowBg = window.AddComponent<Image>();
        windowBg.color = panelColor;
        SetRect(window, 0.5f, 0.5f, 800, 700);

        // Title
        GameObject titleObj = CreateUIElement("Title", window);
        Text title = titleObj.AddComponent<Text>();
        title.text = "Settings";
        title.font = uiFont;
        title.fontSize = 36;
        title.fontStyle = FontStyle.Bold;
        title.color = titleColor;
        title.alignment = TextAnchor.MiddleCenter;
        SetRect(titleObj, 0.5f, 1f, 300, 60, new Vector2(0, -40));

        // Scroll view for settings
        GameObject scrollArea = CreateUIElement("ScrollArea", window);
        SetRect(scrollArea, 0.5f, 0.5f, 750, 520, new Vector2(0, -20));

        // Content container
        GameObject content = CreateUIElement("Content", scrollArea);
        RectTransform contentRect = content.GetComponent<RectTransform>();
        contentRect.anchorMin = new Vector2(0, 1);
        contentRect.anchorMax = new Vector2(1, 1);
        contentRect.pivot = new Vector2(0.5f, 1);
        contentRect.sizeDelta = new Vector2(0, 900);
        contentRect.anchoredPosition = Vector2.zero;

        VerticalLayoutGroup contentLayout = content.AddComponent<VerticalLayoutGroup>();
        contentLayout.spacing = 25;
        contentLayout.padding = new RectOffset(30, 30, 20, 20);
        contentLayout.childAlignment = TextAnchor.UpperCenter;
        contentLayout.childControlWidth = true;
        contentLayout.childControlHeight = false;
        contentLayout.childForceExpandWidth = true;
        contentLayout.childForceExpandHeight = false;

        // === Audio Settings Section ===
        CreateSectionHeader(content, "Audio Settings");
        volumeSlider = CreateSliderSetting(content, "Master Volume", 0f, 1f,
            PlayerPrefs.GetFloat("MasterVolume", 0.8f), OnVolumeChanged);

        // === Display Settings Section ===
        CreateSectionHeader(content, "Display Settings");
        subtitleToggle = CreateToggleSetting(content, "Show Subtitles", true);
        speedSlider = CreateSliderSetting(content, "Debate Speed", 0.5f, 2f, 1f, null);

        // === AI Model Settings Section ===
        CreateSectionHeader(content, "AI Model Configuration");
        foreach (string philosopher in philosophers)
        {
            CreateDropdownSetting(content, philosopher + " - LLM", languageModels,
                philosopherModelIndex[philosopher]);
        }

        // === Voice Settings Section ===
        CreateSectionHeader(content, "Voice Configuration");
        foreach (string philosopher in philosophers)
        {
            CreateDropdownSetting(content, philosopher + " - Voice", ttsVoices,
                philosopherVoiceIndex[philosopher]);
        }

        // Back button
        GameObject backBtn = CreateUIElement("BackButton", window);
        Image backBtnImg = backBtn.AddComponent<Image>();
        backBtnImg.color = new Color(0.85f, 0.75f, 0.55f, 0.9f);

        Button btn = backBtn.AddComponent<Button>();
        btn.onClick.AddListener(OnBackClick);

        ColorBlock colors = btn.colors;
        colors.normalColor = new Color(0.85f, 0.75f, 0.55f, 0.9f);
        colors.highlightedColor = new Color(0.95f, 0.85f, 0.65f, 1f);
        colors.pressedColor = new Color(0.75f, 0.65f, 0.45f, 1f);
        btn.colors = colors;

        SetRect(backBtn, 0.5f, 0f, 150, 45, new Vector2(0, 40));

        GameObject backText = CreateUIElement("Text", backBtn);
        Text btnText = backText.AddComponent<Text>();
        btnText.text = "Back";
        btnText.font = uiFont;
        btnText.fontSize = 22;
        btnText.fontStyle = FontStyle.Bold;
        btnText.color = new Color(0.1f, 0.1f, 0.15f, 1f);
        btnText.alignment = TextAnchor.MiddleCenter;
        SetFullScreen(backText);

        settingsPanel.SetActive(false);
    }

    void CreateSectionHeader(GameObject parent, string text)
    {
        GameObject header = CreateUIElement("Header_" + text, parent);
        LayoutElement le = header.AddComponent<LayoutElement>();
        le.preferredHeight = 40;
        le.preferredWidth = 700;

        Text headerText = header.AddComponent<Text>();
        headerText.text = "— " + text + " —";
        headerText.font = uiFont;
        headerText.fontSize = 22;
        headerText.fontStyle = FontStyle.Bold;
        headerText.color = titleColor;
        headerText.alignment = TextAnchor.MiddleLeft;
    }

    Slider CreateSliderSetting(GameObject parent, string label, float min, float max,
        float defaultValue, UnityEngine.Events.UnityAction<float> callback)
    {
        GameObject container = CreateUIElement("Setting_" + label, parent);
        LayoutElement le = container.AddComponent<LayoutElement>();
        le.preferredHeight = 50;
        le.preferredWidth = 700;

        // Label
        GameObject labelObj = CreateUIElement("Label", container);
        Text labelText = labelObj.AddComponent<Text>();
        labelText.text = label;
        labelText.font = uiFont;
        labelText.fontSize = 20;
        labelText.color = buttonTextColor;
        labelText.alignment = TextAnchor.MiddleLeft;
        RectTransform labelRect = labelObj.GetComponent<RectTransform>();
        labelRect.anchorMin = new Vector2(0, 0);
        labelRect.anchorMax = new Vector2(0.4f, 1);
        labelRect.offsetMin = Vector2.zero;
        labelRect.offsetMax = Vector2.zero;

        // Slider background
        GameObject sliderObj = CreateUIElement("Slider", container);
        RectTransform sliderRect = sliderObj.GetComponent<RectTransform>();
        sliderRect.anchorMin = new Vector2(0.42f, 0.3f);
        sliderRect.anchorMax = new Vector2(0.88f, 0.7f);
        sliderRect.offsetMin = Vector2.zero;
        sliderRect.offsetMax = Vector2.zero;

        // Background
        GameObject bgObj = CreateUIElement("Background", sliderObj);
        Image bgImage = bgObj.AddComponent<Image>();
        bgImage.color = new Color(0.2f, 0.2f, 0.25f, 1f);
        SetFullScreen(bgObj);

        // Fill area
        GameObject fillArea = CreateUIElement("Fill Area", sliderObj);
        RectTransform fillAreaRect = fillArea.GetComponent<RectTransform>();
        fillAreaRect.anchorMin = new Vector2(0, 0.25f);
        fillAreaRect.anchorMax = new Vector2(1, 0.75f);
        fillAreaRect.offsetMin = new Vector2(5, 0);
        fillAreaRect.offsetMax = new Vector2(-5, 0);

        GameObject fill = CreateUIElement("Fill", fillArea);
        Image fillImage = fill.AddComponent<Image>();
        fillImage.color = titleColor;
        RectTransform fillRect = fill.GetComponent<RectTransform>();
        fillRect.anchorMin = Vector2.zero;
        fillRect.anchorMax = Vector2.one;
        fillRect.offsetMin = Vector2.zero;
        fillRect.offsetMax = Vector2.zero;

        // Handle area
        GameObject handleArea = CreateUIElement("Handle Slide Area", sliderObj);
        RectTransform handleAreaRect = handleArea.GetComponent<RectTransform>();
        handleAreaRect.anchorMin = Vector2.zero;
        handleAreaRect.anchorMax = Vector2.one;
        handleAreaRect.offsetMin = new Vector2(10, 0);
        handleAreaRect.offsetMax = new Vector2(-10, 0);

        GameObject handle = CreateUIElement("Handle", handleArea);
        Image handleImage = handle.AddComponent<Image>();
        handleImage.color = Color.white;
        RectTransform handleRect = handle.GetComponent<RectTransform>();
        handleRect.sizeDelta = new Vector2(20, 30);

        // Slider component
        Slider slider = sliderObj.AddComponent<Slider>();
        slider.fillRect = fillRect;
        slider.handleRect = handleRect;
        slider.targetGraphic = handleImage;
        slider.direction = Slider.Direction.LeftToRight;
        slider.minValue = min;
        slider.maxValue = max;
        slider.value = defaultValue;
        if (callback != null)
            slider.onValueChanged.AddListener(callback);

        // Value display
        GameObject valueObj = CreateUIElement("Value", container);
        Text valueText = valueObj.AddComponent<Text>();
        valueText.text = Mathf.RoundToInt(defaultValue * 100) + "%";
        valueText.font = uiFont;
        valueText.fontSize = 18;
        valueText.color = subtitleColor;
        valueText.alignment = TextAnchor.MiddleCenter;
        RectTransform valueRect = valueObj.GetComponent<RectTransform>();
        valueRect.anchorMin = new Vector2(0.9f, 0);
        valueRect.anchorMax = new Vector2(1f, 1);
        valueRect.offsetMin = Vector2.zero;
        valueRect.offsetMax = Vector2.zero;

        // Update value text on change
        slider.onValueChanged.AddListener((val) => {
            valueText.text = Mathf.RoundToInt(val * 100) + "%";
        });

        return slider;
    }

    Toggle CreateToggleSetting(GameObject parent, string label, bool defaultValue)
    {
        GameObject container = CreateUIElement("Setting_" + label, parent);
        LayoutElement le = container.AddComponent<LayoutElement>();
        le.preferredHeight = 50;
        le.preferredWidth = 700;

        // Label
        GameObject labelObj = CreateUIElement("Label", container);
        Text labelText = labelObj.AddComponent<Text>();
        labelText.text = label;
        labelText.font = uiFont;
        labelText.fontSize = 20;
        labelText.color = buttonTextColor;
        labelText.alignment = TextAnchor.MiddleLeft;
        RectTransform labelRect = labelObj.GetComponent<RectTransform>();
        labelRect.anchorMin = new Vector2(0, 0);
        labelRect.anchorMax = new Vector2(0.4f, 1);
        labelRect.offsetMin = Vector2.zero;
        labelRect.offsetMax = Vector2.zero;

        // Toggle
        GameObject toggleObj = CreateUIElement("Toggle", container);
        RectTransform toggleRect = toggleObj.GetComponent<RectTransform>();
        toggleRect.anchorMin = new Vector2(0.42f, 0.2f);
        toggleRect.anchorMax = new Vector2(0.5f, 0.8f);
        toggleRect.offsetMin = Vector2.zero;
        toggleRect.offsetMax = Vector2.zero;

        // Background
        GameObject bgObj = CreateUIElement("Background", toggleObj);
        Image bgImage = bgObj.AddComponent<Image>();
        bgImage.color = new Color(0.2f, 0.2f, 0.25f, 1f);
        SetFullScreen(bgObj);

        // Checkmark
        GameObject checkmark = CreateUIElement("Checkmark", toggleObj);
        Image checkImage = checkmark.AddComponent<Image>();
        checkImage.color = titleColor;
        RectTransform checkRect = checkmark.GetComponent<RectTransform>();
        checkRect.anchorMin = new Vector2(0.15f, 0.15f);
        checkRect.anchorMax = new Vector2(0.85f, 0.85f);
        checkRect.offsetMin = Vector2.zero;
        checkRect.offsetMax = Vector2.zero;

        Toggle toggle = toggleObj.AddComponent<Toggle>();
        toggle.targetGraphic = bgImage;
        toggle.graphic = checkImage;
        toggle.isOn = defaultValue;

        return toggle;
    }

    void CreateDropdownSetting(GameObject parent, string label, string[] options, int defaultIndex)
    {
        GameObject container = CreateUIElement("Setting_" + label, parent);
        LayoutElement le = container.AddComponent<LayoutElement>();
        le.preferredHeight = 50;
        le.preferredWidth = 700;

        // Label
        GameObject labelObj = CreateUIElement("Label", container);
        Text labelText = labelObj.AddComponent<Text>();
        labelText.text = label;
        labelText.font = uiFont;
        labelText.fontSize = 20;
        labelText.color = buttonTextColor;
        labelText.alignment = TextAnchor.MiddleLeft;
        RectTransform labelRect = labelObj.GetComponent<RectTransform>();
        labelRect.anchorMin = new Vector2(0, 0);
        labelRect.anchorMax = new Vector2(0.4f, 1);
        labelRect.offsetMin = Vector2.zero;
        labelRect.offsetMax = Vector2.zero;

        // Dropdown container
        GameObject dropdownObj = CreateUIElement("Dropdown", container);
        RectTransform dropdownRect = dropdownObj.GetComponent<RectTransform>();
        dropdownRect.anchorMin = new Vector2(0.42f, 0.15f);
        dropdownRect.anchorMax = new Vector2(0.98f, 0.85f);
        dropdownRect.offsetMin = Vector2.zero;
        dropdownRect.offsetMax = Vector2.zero;

        Image dropdownBg = dropdownObj.AddComponent<Image>();
        dropdownBg.color = dropdownColor;

        Dropdown dropdown = dropdownObj.AddComponent<Dropdown>();
        dropdown.targetGraphic = dropdownBg;

        // Caption text
        GameObject captionObj = CreateUIElement("Label", dropdownObj);
        Text captionText = captionObj.AddComponent<Text>();
        captionText.font = uiFont;
        captionText.fontSize = 18;
        captionText.color = buttonTextColor;
        captionText.alignment = TextAnchor.MiddleLeft;
        RectTransform captionRect = captionObj.GetComponent<RectTransform>();
        captionRect.anchorMin = Vector2.zero;
        captionRect.anchorMax = Vector2.one;
        captionRect.offsetMin = new Vector2(10, 0);
        captionRect.offsetMax = new Vector2(-30, 0);
        dropdown.captionText = captionText;

        // Arrow
        GameObject arrowObj = CreateUIElement("Arrow", dropdownObj);
        Text arrowText = arrowObj.AddComponent<Text>();
        arrowText.text = "▼";
        arrowText.font = uiFont;
        arrowText.fontSize = 14;
        arrowText.color = subtitleColor;
        arrowText.alignment = TextAnchor.MiddleCenter;
        RectTransform arrowRect = arrowObj.GetComponent<RectTransform>();
        arrowRect.anchorMin = new Vector2(1, 0);
        arrowRect.anchorMax = new Vector2(1, 1);
        arrowRect.sizeDelta = new Vector2(30, 0);
        arrowRect.anchoredPosition = new Vector2(-15, 0);

        // Template
        GameObject templateObj = CreateUIElement("Template", dropdownObj);
        RectTransform templateRect = templateObj.GetComponent<RectTransform>();
        templateRect.anchorMin = new Vector2(0, 0);
        templateRect.anchorMax = new Vector2(1, 0);
        templateRect.pivot = new Vector2(0.5f, 1);
        templateRect.sizeDelta = new Vector2(0, 200);
        templateRect.anchoredPosition = Vector2.zero;

        Image templateBg = templateObj.AddComponent<Image>();
        templateBg.color = dropdownColor;

        ScrollRect scrollRect = templateObj.AddComponent<ScrollRect>();

        // Viewport
        GameObject viewportObj = CreateUIElement("Viewport", templateObj);
        RectTransform viewportRect = viewportObj.GetComponent<RectTransform>();
        viewportRect.anchorMin = Vector2.zero;
        viewportRect.anchorMax = Vector2.one;
        viewportRect.offsetMin = Vector2.zero;
        viewportRect.offsetMax = Vector2.zero;

        Mask mask = viewportObj.AddComponent<Mask>();
        mask.showMaskGraphic = false;
        Image viewportImg = viewportObj.AddComponent<Image>();
        viewportImg.color = Color.white;

        // Content
        GameObject contentObj = CreateUIElement("Content", viewportObj);
        RectTransform contentRect = contentObj.GetComponent<RectTransform>();
        contentRect.anchorMin = new Vector2(0, 1);
        contentRect.anchorMax = new Vector2(1, 1);
        contentRect.pivot = new Vector2(0.5f, 1);
        contentRect.sizeDelta = new Vector2(0, 0);

        scrollRect.viewport = viewportRect;
        scrollRect.content = contentRect;

        // Item template
        GameObject itemObj = CreateUIElement("Item", contentObj);
        RectTransform itemRect = itemObj.GetComponent<RectTransform>();
        itemRect.anchorMin = new Vector2(0, 0.5f);
        itemRect.anchorMax = new Vector2(1, 0.5f);
        itemRect.sizeDelta = new Vector2(0, 35);

        Toggle itemToggle = itemObj.AddComponent<Toggle>();

        // Item background
        GameObject itemBgObj = CreateUIElement("Item Background", itemObj);
        Image itemBgImg = itemBgObj.AddComponent<Image>();
        itemBgImg.color = new Color(0.85f, 0.75f, 0.55f, 0.3f);
        SetFullScreen(itemBgObj);
        itemToggle.targetGraphic = itemBgImg;

        // Item checkmark (hidden)
        GameObject itemCheckObj = CreateUIElement("Item Checkmark", itemObj);
        Image itemCheckImg = itemCheckObj.AddComponent<Image>();
        itemCheckImg.color = titleColor;
        RectTransform itemCheckRect = itemCheckObj.GetComponent<RectTransform>();
        itemCheckRect.anchorMin = new Vector2(0, 0.2f);
        itemCheckRect.anchorMax = new Vector2(0, 0.8f);
        itemCheckRect.sizeDelta = new Vector2(20, 0);
        itemCheckRect.anchoredPosition = new Vector2(15, 0);
        itemToggle.graphic = itemCheckImg;

        // Item label
        GameObject itemLabelObj = CreateUIElement("Item Label", itemObj);
        Text itemLabelText = itemLabelObj.AddComponent<Text>();
        itemLabelText.font = uiFont;
        itemLabelText.fontSize = 18;
        itemLabelText.color = buttonTextColor;
        itemLabelText.alignment = TextAnchor.MiddleLeft;
        RectTransform itemLabelRect = itemLabelObj.GetComponent<RectTransform>();
        itemLabelRect.anchorMin = Vector2.zero;
        itemLabelRect.anchorMax = Vector2.one;
        itemLabelRect.offsetMin = new Vector2(35, 0);
        itemLabelRect.offsetMax = new Vector2(-10, 0);

        dropdown.template = templateRect;
        dropdown.itemText = itemLabelText;
        templateObj.SetActive(false);

        // Add options
        dropdown.ClearOptions();
        dropdown.AddOptions(new List<string>(options));
        dropdown.value = defaultIndex;
        dropdown.RefreshShownValue();
    }

    void CreateFadeOverlay(GameObject parent)
    {
        GameObject fadeObj = CreateUIElement("FadeOverlay", parent);
        Image fadeImage = fadeObj.AddComponent<Image>();
        fadeImage.color = Color.black;
        fadeOverlay = fadeObj.AddComponent<CanvasGroup>();
        fadeOverlay.alpha = 1f;
        fadeOverlay.blocksRaycasts = true;
        SetFullScreen(fadeObj);
        fadeObj.transform.SetAsLastSibling();
    }

    // === Utility Methods ===

    GameObject CreateUIElement(string name, GameObject parent)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(parent.transform, false);
        obj.AddComponent<RectTransform>();
        return obj;
    }

    void SetFullScreen(GameObject obj)
    {
        RectTransform rect = obj.GetComponent<RectTransform>();
        rect.anchorMin = Vector2.zero;
        rect.anchorMax = Vector2.one;
        rect.sizeDelta = Vector2.zero;
        rect.anchoredPosition = Vector2.zero;
    }

    void SetRect(GameObject obj, float anchorX, float anchorY, float width, float height, Vector2 offset = default)
    {
        RectTransform rect = obj.GetComponent<RectTransform>();
        rect.anchorMin = new Vector2(anchorX, anchorY);
        rect.anchorMax = new Vector2(anchorX, anchorY);
        rect.sizeDelta = new Vector2(width, height);
        rect.anchoredPosition = offset;
    }

    // === Button Callbacks ===

    void OnStartClick()
    {
        StartCoroutine(FadeOutAndLoad(gameSceneName));
    }

    void OnSettingsClick()
    {
        mainMenuPanel.SetActive(false);
        settingsPanel.SetActive(true);
    }

    void OnBackClick()
    {
        settingsPanel.SetActive(false);
        mainMenuPanel.SetActive(true);
    }

    void OnExitClick()
    {
        #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
        #else
            Application.Quit();
        #endif
    }

    void OnVolumeChanged(float value)
    {
        AudioListener.volume = value;
        PlayerPrefs.SetFloat("MasterVolume", value);
    }

    // === Fade Effects ===

    IEnumerator FadeIn()
    {
        while (fadeOverlay.alpha > 0)
        {
            fadeOverlay.alpha -= Time.deltaTime * fadeSpeed;
            yield return null;
        }
        fadeOverlay.blocksRaycasts = false;
        fadeOverlay.gameObject.SetActive(false);
    }

    IEnumerator FadeOutAndLoad(string sceneName)
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
