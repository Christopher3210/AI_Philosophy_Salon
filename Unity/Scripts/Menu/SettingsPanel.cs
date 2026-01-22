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

    public void Initialize(GameObject parent)
    {
        panel = UIFactory.CreateElement("SettingsPanel", parent);
        UIFactory.SetFullScreen(panel);

        // Dark overlay
        GameObject overlay = UIFactory.CreateElement("Overlay", panel);
        Image overlayImg = overlay.AddComponent<Image>();
        overlayImg.color = new Color(0, 0, 0, 0.7f);
        UIFactory.SetFullScreen(overlay);

        // Window
        GameObject window = UIFactory.CreateElement("Window", panel);
        Image windowBg = window.AddComponent<Image>();
        windowBg.color = SettingsData.PanelColor;
        UIFactory.SetRect(window, 0.5f, 0.5f, 850, 650);

        // Title
        Text title = UIFactory.CreateText(window, "Title", "Settings",
            36, SettingsData.TitleColor, TextAnchor.MiddleCenter, FontStyle.Bold);
        UIFactory.SetRect(title.gameObject, 0.5f, 1f, 300, 60, new Vector2(0, -35));

        // Scroll View
        GameObject scrollView = UIFactory.CreateElement("ScrollView", window);
        RectTransform svRect = scrollView.GetComponent<RectTransform>();
        svRect.anchorMin = new Vector2(0, 0);
        svRect.anchorMax = new Vector2(1, 1);
        svRect.offsetMin = new Vector2(15, 65);
        svRect.offsetMax = new Vector2(-15, -70);

        ScrollRect scrollRect = scrollView.AddComponent<ScrollRect>();
        scrollRect.horizontal = false;
        scrollRect.vertical = true;
        scrollRect.movementType = ScrollRect.MovementType.Elastic;
        scrollRect.elasticity = 0.1f;
        scrollRect.scrollSensitivity = 25f;

        // Viewport - use RectMask2D for better performance
        GameObject viewport = UIFactory.CreateElement("Viewport", scrollView);
        UIFactory.SetFullScreen(viewport);
        viewport.AddComponent<RectMask2D>();
        scrollRect.viewport = viewport.GetComponent<RectTransform>();

        // Content - fixed height based on number of items
        GameObject content = UIFactory.CreateElement("Content", viewport);
        RectTransform contentRect = content.GetComponent<RectTransform>();
        contentRect.anchorMin = new Vector2(0, 1);
        contentRect.anchorMax = new Vector2(1, 1);
        contentRect.pivot = new Vector2(0.5f, 1);
        contentRect.sizeDelta = new Vector2(-30, 950); // Fixed height for all content
        contentRect.anchoredPosition = Vector2.zero;

        scrollRect.content = contentRect;

        // Layout
        VerticalLayoutGroup layout = content.AddComponent<VerticalLayoutGroup>();
        layout.spacing = 18;
        layout.padding = new RectOffset(20, 20, 10, 10);
        layout.childAlignment = TextAnchor.UpperCenter;
        layout.childControlWidth = true;
        layout.childControlHeight = false;
        layout.childForceExpandWidth = true;
        layout.childForceExpandHeight = false;

        // Add all settings
        AddSettingsContent(content);

        // Scrollbar
        CreateScrollbar(scrollView, scrollRect);

        // Back button
        CreateBackButton(window);

        panel.SetActive(false);
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

    private void CreateScrollbar(GameObject scrollView, ScrollRect scrollRect)
    {
        GameObject scrollbarObj = UIFactory.CreateElement("Scrollbar", scrollView);
        RectTransform sbRect = scrollbarObj.GetComponent<RectTransform>();
        sbRect.anchorMin = new Vector2(1, 0);
        sbRect.anchorMax = new Vector2(1, 1);
        sbRect.pivot = new Vector2(1, 0.5f);
        sbRect.sizeDelta = new Vector2(10, 0);
        sbRect.anchoredPosition = new Vector2(5, 0);

        Image sbBg = scrollbarObj.AddComponent<Image>();
        sbBg.color = new Color(0.2f, 0.2f, 0.25f, 0.5f);

        Scrollbar scrollbar = scrollbarObj.AddComponent<Scrollbar>();
        scrollbar.direction = Scrollbar.Direction.BottomToTop;

        // Handle
        GameObject handle = UIFactory.CreateElement("Handle", scrollbarObj);
        RectTransform handleRect = handle.GetComponent<RectTransform>();
        handleRect.anchorMin = Vector2.zero;
        handleRect.anchorMax = Vector2.one;
        handleRect.offsetMin = new Vector2(1, 0);
        handleRect.offsetMax = new Vector2(-1, 0);

        Image handleImg = handle.AddComponent<Image>();
        handleImg.color = SettingsData.TitleColor;

        scrollbar.handleRect = handleRect;
        scrollbar.targetGraphic = handleImg;

        scrollRect.verticalScrollbar = scrollbar;
        scrollRect.verticalScrollbarVisibility = ScrollRect.ScrollbarVisibility.AutoHide;
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

        UIFactory.SetRect(backBtn, 0.5f, 0f, 150, 45, new Vector2(0, 12));

        Text btnText = UIFactory.CreateText(backBtn, "Text", "Back",
            22, new Color(0.1f, 0.1f, 0.15f, 1f), TextAnchor.MiddleCenter, FontStyle.Bold);
        UIFactory.SetFullScreen(btnText.gameObject);
    }

    private void OnVolumeChanged(float value)
    {
        AudioListener.volume = value;
        PlayerPrefs.SetFloat(SettingsData.KEY_MASTER_VOLUME, value);
    }

    public void Show() => panel.SetActive(true);
    public void Hide() => panel.SetActive(false);
    public bool IsVisible => panel.activeSelf;
}
