using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using UnityEngine.Events;

/// <summary>
/// In-game pause menu - press ESC to open
/// Supports interrupting ongoing speech
/// </summary>
public class PauseMenu : MonoBehaviour
{
    [Header("Settings")]
    public string mainMenuSceneName = "MainMenu";
    public KeyCode pauseKey = KeyCode.Escape;

    [Header("Events")]
    public UnityEvent OnPause;
    public UnityEvent OnResume;
    public UnityEvent OnInterruptSpeech;

    private GameObject panel;
    private bool isPaused = false;
    private Canvas canvas;

    void Start()
    {
        CreateUI();
    }

    void Update()
    {
        if (Input.GetKeyDown(pauseKey))
        {
            if (isPaused)
                Resume();
            else
                Pause();
        }
    }

    private void CreateUI()
    {
        // Create Canvas
        GameObject canvasObj = new GameObject("PauseMenuCanvas");
        canvas = canvasObj.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 200; // Above other UI

        CanvasScaler scaler = canvasObj.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        scaler.matchWidthOrHeight = 0.5f;

        canvasObj.AddComponent<GraphicRaycaster>();

        // Panel
        panel = UIFactory.CreateElement("PausePanel", canvasObj);
        UIFactory.SetFullScreen(panel);

        // Dark overlay
        GameObject overlay = UIFactory.CreateElement("Overlay", panel);
        Image overlayImg = overlay.AddComponent<Image>();
        overlayImg.color = new Color(0, 0, 0, 0.75f);
        UIFactory.SetFullScreen(overlay);

        // Window
        GameObject window = UIFactory.CreateElement("Window", panel);
        Image windowBg = window.AddComponent<Image>();
        windowBg.color = SettingsData.PanelColor;
        UIFactory.SetRect(window, 0.5f, 0.5f, 400, 320);

        // Title
        Text title = UIFactory.CreateText(window, "Title", "Paused",
            42, SettingsData.TitleColor, TextAnchor.MiddleCenter, FontStyle.Bold);
        UIFactory.SetRect(title.gameObject, 0.5f, 0.85f, 300, 60);

        // Button container
        GameObject btnContainer = UIFactory.CreateElement("Buttons", window);
        UIFactory.SetRect(btnContainer, 0.5f, 0.45f, 280, 200);

        VerticalLayoutGroup layout = btnContainer.AddComponent<VerticalLayoutGroup>();
        layout.spacing = 15;
        layout.childAlignment = TextAnchor.MiddleCenter;
        layout.childControlWidth = true;
        layout.childControlHeight = false;
        layout.childForceExpandWidth = true;
        layout.childForceExpandHeight = false;

        // Buttons
        CreatePauseButton(btnContainer, "Continue", SettingsData.TitleColor, Resume);
        CreatePauseButton(btnContainer, "Exit to Menu", new Color(0.8f, 0.4f, 0.4f, 1f), ExitToMenu);

        panel.SetActive(false);
    }

    private void CreatePauseButton(GameObject parent, string text, Color bgColor, UnityAction onClick)
    {
        GameObject btnObj = UIFactory.CreateElement("Button_" + text, parent);

        Image btnImg = btnObj.AddComponent<Image>();
        btnImg.color = bgColor;

        Button btn = btnObj.AddComponent<Button>();
        btn.onClick.AddListener(onClick);

        ColorBlock colors = btn.colors;
        colors.normalColor = bgColor;
        colors.highlightedColor = new Color(bgColor.r + 0.1f, bgColor.g + 0.1f, bgColor.b + 0.1f, 1f);
        colors.pressedColor = new Color(bgColor.r - 0.1f, bgColor.g - 0.1f, bgColor.b - 0.1f, 1f);
        btn.colors = colors;

        LayoutElement le = btnObj.AddComponent<LayoutElement>();
        le.preferredHeight = 55;
        le.preferredWidth = 260;

        Text btnText = UIFactory.CreateText(btnObj, "Text", text,
            24, new Color(0.1f, 0.1f, 0.12f, 1f), TextAnchor.MiddleCenter, FontStyle.Bold);
        UIFactory.SetFullScreen(btnText.gameObject);
    }

    public void Pause()
    {
        isPaused = true;
        panel.SetActive(true);
        Time.timeScale = 0f; // Pause game time

        // Interrupt any ongoing speech
        OnInterruptSpeech?.Invoke();
        OnPause?.Invoke();
    }

    public void Resume()
    {
        isPaused = false;
        panel.SetActive(false);
        Time.timeScale = 1f; // Resume game time

        OnResume?.Invoke();
    }

    public void ExitToMenu()
    {
        Time.timeScale = 1f; // Reset time before loading
        OnInterruptSpeech?.Invoke();
        SceneManager.LoadScene(mainMenuSceneName);
    }

    public bool IsPaused => isPaused;

    void OnDestroy()
    {
        // Ensure time scale is reset
        Time.timeScale = 1f;
    }
}
