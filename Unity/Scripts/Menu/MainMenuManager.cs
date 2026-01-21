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

        // Button container
        GameObject buttonContainer = UIFactory.CreateElement("ButtonContainer", mainMenuPanel);
        UIFactory.SetRect(buttonContainer, 0.5f, 0.38f, 300, 220);

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
