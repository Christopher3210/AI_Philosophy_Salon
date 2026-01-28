using UnityEngine;

/// <summary>
/// Static data class containing settings constants and configuration
/// </summary>
public static class SettingsData
{
    // Language models available for selection
    public static readonly string[] LanguageModels = new string[]
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

    // TTS voices available for selection
    public static readonly string[] TTSVoices = new string[]
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
    public static readonly string[] Philosophers = new string[]
    {
        "Aristotle",
        "Sartre",
        "Wittgenstein",
        "Russell"
    };

    // Default color theme
    public static readonly Color BackgroundColor = new Color(0.08f, 0.08f, 0.12f, 1f);
    public static readonly Color TitleColor = new Color(0.85f, 0.75f, 0.55f, 1f);
    public static readonly Color SubtitleColor = new Color(0.7f, 0.7f, 0.7f, 1f);
    public static readonly Color ButtonTextColor = new Color(0.9f, 0.9f, 0.9f, 1f);
    public static readonly Color ButtonHoverColor = new Color(0.85f, 0.75f, 0.55f, 0.3f);
    public static readonly Color PanelColor = new Color(0.12f, 0.12f, 0.18f, 0.98f);
    public static readonly Color DropdownColor = new Color(0.15f, 0.15f, 0.2f, 1f);

    // PlayerPrefs keys
    public const string KEY_MASTER_VOLUME = "MasterVolume";
    public const string KEY_SHOW_SUBTITLES = "ShowSubtitles";
    public const string KEY_DEBATE_SPEED = "DebateSpeed";
    public const string KEY_CONVIVIALITY = "Conviviality";

    // Default values
    public const float DEFAULT_VOLUME = 0.8f;
    public const bool DEFAULT_SUBTITLES = true;
    public const float DEFAULT_SPEED = 1f;
    public const float DEFAULT_CONVIVIALITY = 0.5f;

    // Get/Set Conviviality
    public static float Conviviality
    {
        get { return PlayerPrefs.GetFloat(KEY_CONVIVIALITY, DEFAULT_CONVIVIALITY); }
        set { PlayerPrefs.SetFloat(KEY_CONVIVIALITY, value); PlayerPrefs.Save(); }
    }
}
