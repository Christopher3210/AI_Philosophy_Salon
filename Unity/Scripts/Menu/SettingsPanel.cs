using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Events;

/// <summary>
/// Settings panel UI component
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

        // Window
        GameObject window = UIFactory.CreateElement("Window", panel);
        Image windowBg = window.AddComponent<Image>();
        windowBg.color = SettingsData.PanelColor;
        UIFactory.SetRect(window, 0.5f, 0.5f, 800, 700);

        // Title
        Text title = UIFactory.CreateText(window, "Title", "Settings",
            36, SettingsData.TitleColor, TextAnchor.MiddleCenter, FontStyle.Bold);
        UIFactory.SetRect(title.gameObject, 0.5f, 1f, 300, 60, new Vector2(0, -40));

        // Content area
        GameObject scrollArea = UIFactory.CreateElement("ScrollArea", window);
        UIFactory.SetRect(scrollArea, 0.5f, 0.5f, 750, 520, new Vector2(0, -20));

        GameObject content = UIFactory.CreateElement("Content", scrollArea);
        RectTransform contentRect = content.GetComponent<RectTransform>();
        contentRect.anchorMin = new Vector2(0, 1);
        contentRect.anchorMax = new Vector2(1, 1);
        contentRect.pivot = new Vector2(0.5f, 1);
        contentRect.sizeDelta = new Vector2(0, 950);
        contentRect.anchoredPosition = Vector2.zero;

        VerticalLayoutGroup layout = content.AddComponent<VerticalLayoutGroup>();
        layout.spacing = 25;
        layout.padding = new RectOffset(30, 30, 20, 20);
        layout.childAlignment = TextAnchor.UpperCenter;
        layout.childControlWidth = true;
        layout.childControlHeight = false;
        layout.childForceExpandWidth = true;
        layout.childForceExpandHeight = false;

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

        // Back button
        CreateBackButton(window);

        panel.SetActive(false);
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

        UIFactory.SetRect(backBtn, 0.5f, 0f, 150, 45, new Vector2(0, 40));

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
