using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Events;

/// <summary>
/// Settings panel UI component with scroll support
/// </summary>
public class SettingsPanel : MonoBehaviour
{
    private GameObject panel;
    private Slider volumeSlider;
    private Slider speedSlider;
    private Toggle subtitleToggle;

    public UnityAction OnBackClicked;

    /// <summary>
    /// Create and setup the settings panel
    /// </summary>
    public void Initialize(GameObject parent)
    {
        panel = UIFactory.CreateElement("SettingsPanel", parent);
        UIFactory.SetFullScreen(panel);

        // Dark overlay
        GameObject overlay = UIFactory.CreateElement("Overlay", panel);
        Image overlayImg = overlay.AddComponent<Image>();
        overlayImg.color = new Color(0, 0, 0, 0.7f);
        UIFactory.SetFullScreen(overlay);

        // Window - make it larger (90% of screen height)
        GameObject window = UIFactory.CreateElement("Window", panel);
        Image windowBg = window.AddComponent<Image>();
        windowBg.color = SettingsData.PanelColor;

        RectTransform windowRect = window.GetComponent<RectTransform>();
        windowRect.anchorMin = new Vector2(0.5f, 0.5f);
        windowRect.anchorMax = new Vector2(0.5f, 0.5f);
        windowRect.sizeDelta = new Vector2(850, 650);
        windowRect.anchoredPosition = Vector2.zero;

        // Title
        Text title = UIFactory.CreateText(window, "Title", "Settings",
            36, SettingsData.TitleColor, TextAnchor.MiddleCenter, FontStyle.Bold);
        UIFactory.SetRect(title.gameObject, 0.5f, 1f, 300, 60, new Vector2(0, -35));

        // Create scroll view
        CreateScrollView(window);

        // Back button
        CreateBackButton(window);

        panel.SetActive(false);
    }

    private void CreateScrollView(GameObject window)
    {
        // Scroll View container
        GameObject scrollView = UIFactory.CreateElement("ScrollView", window);
        RectTransform scrollViewRect = scrollView.GetComponent<RectTransform>();
        scrollViewRect.anchorMin = new Vector2(0, 0);
        scrollViewRect.anchorMax = new Vector2(1, 1);
        scrollViewRect.offsetMin = new Vector2(20, 70);  // Left, Bottom (space for back button)
        scrollViewRect.offsetMax = new Vector2(-20, -70); // Right, Top (space for title)

        ScrollRect scrollRect = scrollView.AddComponent<ScrollRect>();
        scrollRect.horizontal = false;
        scrollRect.vertical = true;
        scrollRect.movementType = ScrollRect.MovementType.Clamped;
        scrollRect.scrollSensitivity = 30f;

        // Viewport (masks content)
        GameObject viewport = UIFactory.CreateElement("Viewport", scrollView);
        RectTransform viewportRect = viewport.GetComponent<RectTransform>();
        viewportRect.anchorMin = Vector2.zero;
        viewportRect.anchorMax = Vector2.one;
        viewportRect.offsetMin = Vector2.zero;
        viewportRect.offsetMax = new Vector2(-15, 0); // Leave space for scrollbar

        Image viewportImage = viewport.AddComponent<Image>();
        viewportImage.color = new Color(1, 1, 1, 0);
        Mask mask = viewport.AddComponent<Mask>();
        mask.showMaskGraphic = false;

        scrollRect.viewport = viewportRect;

        // Content container
        GameObject content = UIFactory.CreateElement("Content", viewport);
        RectTransform contentRect = content.GetComponent<RectTransform>();
        contentRect.anchorMin = new Vector2(0, 1);
        contentRect.anchorMax = new Vector2(1, 1);
        contentRect.pivot = new Vector2(0.5f, 1);
        contentRect.anchoredPosition = Vector2.zero;

        // Content Size Fitter to auto-expand
        ContentSizeFitter fitter = content.AddComponent<ContentSizeFitter>();
        fitter.horizontalFit = ContentSizeFitter.FitMode.Unconstrained;
        fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

        VerticalLayoutGroup layout = content.AddComponent<VerticalLayoutGroup>();
        layout.spacing = 20;
        layout.padding = new RectOffset(25, 25, 15, 15);
        layout.childAlignment = TextAnchor.UpperCenter;
        layout.childControlWidth = true;
        layout.childControlHeight = false;
        layout.childForceExpandWidth = true;
        layout.childForceExpandHeight = false;

        scrollRect.content = contentRect;

        // Create scrollbar
        CreateScrollbar(scrollView, scrollRect);

        // Add settings content
        AddSettingsContent(content);
    }

    private void CreateScrollbar(GameObject scrollView, ScrollRect scrollRect)
    {
        GameObject scrollbarObj = UIFactory.CreateElement("Scrollbar", scrollView);
        RectTransform scrollbarRect = scrollbarObj.GetComponent<RectTransform>();
        scrollbarRect.anchorMin = new Vector2(1, 0);
        scrollbarRect.anchorMax = new Vector2(1, 1);
        scrollbarRect.pivot = new Vector2(1, 0.5f);
        scrollbarRect.sizeDelta = new Vector2(12, 0);
        scrollbarRect.anchoredPosition = Vector2.zero;

        Image scrollbarBg = scrollbarObj.AddComponent<Image>();
        scrollbarBg.color = new Color(0.15f, 0.15f, 0.2f, 1f);

        Scrollbar scrollbar = scrollbarObj.AddComponent<Scrollbar>();
        scrollbar.direction = Scrollbar.Direction.BottomToTop;

        // Handle
        GameObject handleArea = UIFactory.CreateElement("Handle Area", scrollbarObj);
        RectTransform handleAreaRect = handleArea.GetComponent<RectTransform>();
        handleAreaRect.anchorMin = Vector2.zero;
        handleAreaRect.anchorMax = Vector2.one;
        handleAreaRect.offsetMin = new Vector2(2, 2);
        handleAreaRect.offsetMax = new Vector2(-2, -2);

        GameObject handle = UIFactory.CreateElement("Handle", handleArea);
        RectTransform handleRect = handle.GetComponent<RectTransform>();
        handleRect.anchorMin = Vector2.zero;
        handleRect.anchorMax = Vector2.one;
        handleRect.offsetMin = Vector2.zero;
        handleRect.offsetMax = Vector2.zero;

        Image handleImage = handle.AddComponent<Image>();
        handleImage.color = SettingsData.TitleColor;

        scrollbar.targetGraphic = handleImage;
        scrollbar.handleRect = handleRect;

        scrollRect.verticalScrollbar = scrollbar;
        scrollRect.verticalScrollbarVisibility = ScrollRect.ScrollbarVisibility.AutoHideAndExpandViewport;
    }

    private void AddSettingsContent(GameObject content)
    {
        // Audio Settings
        UIFactory.CreateSectionHeader(content, "Audio Settings");
        volumeSlider = UIFactory.CreateSlider(content, "Master Volume",
            0f, 1f, PlayerPrefs.GetFloat(SettingsData.KEY_MASTER_VOLUME, SettingsData.DEFAULT_VOLUME),
            OnVolumeChanged);

        // Display Settings
        UIFactory.CreateSectionHeader(content, "Display Settings");
        subtitleToggle = UIFactory.CreateToggle(content, "Show Subtitles", SettingsData.DEFAULT_SUBTITLES);
        speedSlider = UIFactory.CreateSlider(content, "Debate Speed",
            0.5f, 2f, SettingsData.DEFAULT_SPEED, null);

        // AI Model Settings
        UIFactory.CreateSectionHeader(content, "AI Model Configuration");
        for (int i = 0; i < SettingsData.Philosophers.Length; i++)
        {
            UIFactory.CreateDropdown(content,
                SettingsData.Philosophers[i] + " - LLM",
                SettingsData.LanguageModels,
                i % SettingsData.LanguageModels.Length);
        }

        // Voice Settings
        UIFactory.CreateSectionHeader(content, "Voice Configuration");
        for (int i = 0; i < SettingsData.Philosophers.Length; i++)
        {
            UIFactory.CreateDropdown(content,
                SettingsData.Philosophers[i] + " - Voice",
                SettingsData.TTSVoices,
                i % SettingsData.TTSVoices.Length);
        }
    }

    private void CreateBackButton(GameObject parent)
    {
        GameObject backBtn = UIFactory.CreateElement("BackButton", parent);
        Image backBtnImg = backBtn.AddComponent<Image>();
        backBtnImg.color = new Color(0.85f, 0.75f, 0.55f, 0.9f);

        Button btn = backBtn.AddComponent<Button>();
        btn.onClick.AddListener(() => OnBackClicked?.Invoke());

        ColorBlock colors = btn.colors;
        colors.normalColor = new Color(0.85f, 0.75f, 0.55f, 0.9f);
        colors.highlightedColor = new Color(0.95f, 0.85f, 0.65f, 1f);
        colors.pressedColor = new Color(0.75f, 0.65f, 0.45f, 1f);
        btn.colors = colors;

        UIFactory.SetRect(backBtn, 0.5f, 0f, 150, 45, new Vector2(0, 15));

        Text btnText = UIFactory.CreateText(backBtn, "Text", "Back",
            22, new Color(0.1f, 0.1f, 0.15f, 1f), TextAnchor.MiddleCenter, FontStyle.Bold);
        UIFactory.SetFullScreen(btnText.gameObject);
    }

    private void OnVolumeChanged(float value)
    {
        AudioListener.volume = value;
        PlayerPrefs.SetFloat(SettingsData.KEY_MASTER_VOLUME, value);
    }

    public void Show()
    {
        panel.SetActive(true);
    }

    public void Hide()
    {
        panel.SetActive(false);
    }

    public bool IsVisible => panel.activeSelf;
}
