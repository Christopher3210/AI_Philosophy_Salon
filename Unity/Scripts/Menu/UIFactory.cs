using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Events;
using System.Collections.Generic;

/// <summary>
/// Factory class for creating UI elements programmatically
/// </summary>
public static class UIFactory
{
    private static Font _cachedFont;

    public static Font DefaultFont
    {
        get
        {
            if (_cachedFont == null)
                _cachedFont = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            return _cachedFont;
        }
    }

    /// <summary>
    /// Create a basic UI element with RectTransform
    /// </summary>
    public static GameObject CreateElement(string name, GameObject parent)
    {
        GameObject obj = new GameObject(name);
        obj.transform.SetParent(parent.transform, false);
        obj.AddComponent<RectTransform>();
        return obj;
    }

    /// <summary>
    /// Set RectTransform to fill parent
    /// </summary>
    public static void SetFullScreen(GameObject obj)
    {
        RectTransform rect = obj.GetComponent<RectTransform>();
        rect.anchorMin = Vector2.zero;
        rect.anchorMax = Vector2.one;
        rect.sizeDelta = Vector2.zero;
        rect.anchoredPosition = Vector2.zero;
    }

    /// <summary>
    /// Set RectTransform with anchor point and size
    /// </summary>
    public static void SetRect(GameObject obj, float anchorX, float anchorY,
        float width, float height, Vector2 offset = default)
    {
        RectTransform rect = obj.GetComponent<RectTransform>();
        rect.anchorMin = new Vector2(anchorX, anchorY);
        rect.anchorMax = new Vector2(anchorX, anchorY);
        rect.sizeDelta = new Vector2(width, height);
        rect.anchoredPosition = offset;
    }

    /// <summary>
    /// Create a text element
    /// </summary>
    public static Text CreateText(GameObject parent, string name, string content,
        int fontSize, Color color, TextAnchor alignment = TextAnchor.MiddleCenter,
        FontStyle style = FontStyle.Normal)
    {
        GameObject obj = CreateElement(name, parent);
        Text text = obj.AddComponent<Text>();
        text.text = content;
        text.font = DefaultFont;
        text.fontSize = fontSize;
        text.fontStyle = style;
        text.color = color;
        text.alignment = alignment;
        return text;
    }

    /// <summary>
    /// Create a button with text
    /// </summary>
    public static Button CreateButton(GameObject parent, string name, string text,
        UnityAction onClick, float width = 280, float height = 55)
    {
        GameObject btnObj = CreateElement("Button_" + name, parent);

        Image btnImage = btnObj.AddComponent<Image>();
        btnImage.color = new Color(1, 1, 1, 0.08f);

        Button btn = btnObj.AddComponent<Button>();
        btn.onClick.AddListener(onClick);

        ColorBlock colors = btn.colors;
        colors.normalColor = new Color(1, 1, 1, 0.08f);
        colors.highlightedColor = SettingsData.ButtonHoverColor;
        colors.pressedColor = new Color(0.85f, 0.75f, 0.55f, 0.5f);
        colors.selectedColor = SettingsData.ButtonHoverColor;
        btn.colors = colors;

        LayoutElement layoutElement = btnObj.AddComponent<LayoutElement>();
        layoutElement.preferredHeight = height;
        layoutElement.preferredWidth = width;

        GameObject textObj = CreateElement("Text", btnObj);
        Text btnText = textObj.AddComponent<Text>();
        btnText.text = text;
        btnText.font = DefaultFont;
        btnText.fontSize = 26;
        btnText.color = SettingsData.ButtonTextColor;
        btnText.alignment = TextAnchor.MiddleCenter;
        SetFullScreen(textObj);

        return btn;
    }

    /// <summary>
    /// Create a slider with label and value display
    /// </summary>
    public static Slider CreateSlider(GameObject parent, string label,
        float min, float max, float defaultValue, UnityAction<float> callback)
    {
        GameObject container = CreateElement("Setting_" + label, parent);
        LayoutElement le = container.AddComponent<LayoutElement>();
        le.preferredHeight = 50;
        le.preferredWidth = 700;

        // Label
        GameObject labelObj = CreateElement("Label", container);
        Text labelText = labelObj.AddComponent<Text>();
        labelText.text = label;
        labelText.font = DefaultFont;
        labelText.fontSize = 20;
        labelText.color = SettingsData.ButtonTextColor;
        labelText.alignment = TextAnchor.MiddleLeft;
        RectTransform labelRect = labelObj.GetComponent<RectTransform>();
        labelRect.anchorMin = new Vector2(0, 0);
        labelRect.anchorMax = new Vector2(0.4f, 1);
        labelRect.offsetMin = Vector2.zero;
        labelRect.offsetMax = Vector2.zero;

        // Slider
        GameObject sliderObj = CreateElement("Slider", container);
        RectTransform sliderRect = sliderObj.GetComponent<RectTransform>();
        sliderRect.anchorMin = new Vector2(0.42f, 0.3f);
        sliderRect.anchorMax = new Vector2(0.88f, 0.7f);
        sliderRect.offsetMin = Vector2.zero;
        sliderRect.offsetMax = Vector2.zero;

        // Background
        GameObject bgObj = CreateElement("Background", sliderObj);
        Image bgImage = bgObj.AddComponent<Image>();
        bgImage.color = new Color(0.2f, 0.2f, 0.25f, 1f);
        SetFullScreen(bgObj);

        // Fill area
        GameObject fillArea = CreateElement("Fill Area", sliderObj);
        RectTransform fillAreaRect = fillArea.GetComponent<RectTransform>();
        fillAreaRect.anchorMin = new Vector2(0, 0.25f);
        fillAreaRect.anchorMax = new Vector2(1, 0.75f);
        fillAreaRect.offsetMin = new Vector2(5, 0);
        fillAreaRect.offsetMax = new Vector2(-5, 0);

        GameObject fill = CreateElement("Fill", fillArea);
        Image fillImage = fill.AddComponent<Image>();
        fillImage.color = SettingsData.TitleColor;
        RectTransform fillRect = fill.GetComponent<RectTransform>();
        fillRect.anchorMin = Vector2.zero;
        fillRect.anchorMax = Vector2.one;
        fillRect.offsetMin = Vector2.zero;
        fillRect.offsetMax = Vector2.zero;

        // Handle
        GameObject handleArea = CreateElement("Handle Slide Area", sliderObj);
        RectTransform handleAreaRect = handleArea.GetComponent<RectTransform>();
        handleAreaRect.anchorMin = Vector2.zero;
        handleAreaRect.anchorMax = Vector2.one;
        handleAreaRect.offsetMin = new Vector2(10, 0);
        handleAreaRect.offsetMax = new Vector2(-10, 0);

        GameObject handle = CreateElement("Handle", handleArea);
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
        GameObject valueObj = CreateElement("Value", container);
        Text valueText = valueObj.AddComponent<Text>();
        valueText.text = Mathf.RoundToInt(defaultValue * 100) + "%";
        valueText.font = DefaultFont;
        valueText.fontSize = 18;
        valueText.color = SettingsData.SubtitleColor;
        valueText.alignment = TextAnchor.MiddleCenter;
        RectTransform valueRect = valueObj.GetComponent<RectTransform>();
        valueRect.anchorMin = new Vector2(0.9f, 0);
        valueRect.anchorMax = new Vector2(1f, 1);
        valueRect.offsetMin = Vector2.zero;
        valueRect.offsetMax = Vector2.zero;

        slider.onValueChanged.AddListener((val) => {
            valueText.text = Mathf.RoundToInt(val * 100) + "%";
        });

        return slider;
    }

    /// <summary>
    /// Create a toggle with label
    /// </summary>
    public static Toggle CreateToggle(GameObject parent, string label, bool defaultValue)
    {
        GameObject container = CreateElement("Setting_" + label, parent);
        LayoutElement le = container.AddComponent<LayoutElement>();
        le.preferredHeight = 50;
        le.preferredWidth = 700;

        // Label
        GameObject labelObj = CreateElement("Label", container);
        Text labelText = labelObj.AddComponent<Text>();
        labelText.text = label;
        labelText.font = DefaultFont;
        labelText.fontSize = 20;
        labelText.color = SettingsData.ButtonTextColor;
        labelText.alignment = TextAnchor.MiddleLeft;
        RectTransform labelRect = labelObj.GetComponent<RectTransform>();
        labelRect.anchorMin = new Vector2(0, 0);
        labelRect.anchorMax = new Vector2(0.4f, 1);
        labelRect.offsetMin = Vector2.zero;
        labelRect.offsetMax = Vector2.zero;

        // Toggle
        GameObject toggleObj = CreateElement("Toggle", container);
        RectTransform toggleRect = toggleObj.GetComponent<RectTransform>();
        toggleRect.anchorMin = new Vector2(0.42f, 0.2f);
        toggleRect.anchorMax = new Vector2(0.5f, 0.8f);
        toggleRect.offsetMin = Vector2.zero;
        toggleRect.offsetMax = Vector2.zero;

        GameObject bgObj = CreateElement("Background", toggleObj);
        Image bgImage = bgObj.AddComponent<Image>();
        bgImage.color = new Color(0.2f, 0.2f, 0.25f, 1f);
        SetFullScreen(bgObj);

        GameObject checkmark = CreateElement("Checkmark", toggleObj);
        Image checkImage = checkmark.AddComponent<Image>();
        checkImage.color = SettingsData.TitleColor;
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

    /// <summary>
    /// Create a dropdown with label
    /// </summary>
    public static Dropdown CreateDropdown(GameObject parent, string label,
        string[] options, int defaultIndex)
    {
        GameObject container = CreateElement("Setting_" + label, parent);
        LayoutElement le = container.AddComponent<LayoutElement>();
        le.preferredHeight = 50;
        le.preferredWidth = 700;

        // Label
        GameObject labelObj = CreateElement("Label", container);
        Text labelText = labelObj.AddComponent<Text>();
        labelText.text = label;
        labelText.font = DefaultFont;
        labelText.fontSize = 20;
        labelText.color = SettingsData.ButtonTextColor;
        labelText.alignment = TextAnchor.MiddleLeft;
        RectTransform labelRect = labelObj.GetComponent<RectTransform>();
        labelRect.anchorMin = new Vector2(0, 0);
        labelRect.anchorMax = new Vector2(0.4f, 1);
        labelRect.offsetMin = Vector2.zero;
        labelRect.offsetMax = Vector2.zero;

        // Dropdown
        GameObject dropdownObj = CreateElement("Dropdown", container);
        RectTransform dropdownRect = dropdownObj.GetComponent<RectTransform>();
        dropdownRect.anchorMin = new Vector2(0.42f, 0.15f);
        dropdownRect.anchorMax = new Vector2(0.98f, 0.85f);
        dropdownRect.offsetMin = Vector2.zero;
        dropdownRect.offsetMax = Vector2.zero;

        Image dropdownBg = dropdownObj.AddComponent<Image>();
        dropdownBg.color = SettingsData.DropdownColor;

        Dropdown dropdown = dropdownObj.AddComponent<Dropdown>();
        dropdown.targetGraphic = dropdownBg;

        // Caption
        GameObject captionObj = CreateElement("Label", dropdownObj);
        Text captionText = captionObj.AddComponent<Text>();
        captionText.font = DefaultFont;
        captionText.fontSize = 18;
        captionText.color = SettingsData.ButtonTextColor;
        captionText.alignment = TextAnchor.MiddleLeft;
        RectTransform captionRect = captionObj.GetComponent<RectTransform>();
        captionRect.anchorMin = Vector2.zero;
        captionRect.anchorMax = Vector2.one;
        captionRect.offsetMin = new Vector2(10, 0);
        captionRect.offsetMax = new Vector2(-30, 0);
        dropdown.captionText = captionText;

        // Arrow
        GameObject arrowObj = CreateElement("Arrow", dropdownObj);
        Text arrowText = arrowObj.AddComponent<Text>();
        arrowText.text = "▼";
        arrowText.font = DefaultFont;
        arrowText.fontSize = 14;
        arrowText.color = SettingsData.SubtitleColor;
        arrowText.alignment = TextAnchor.MiddleCenter;
        RectTransform arrowRect = arrowObj.GetComponent<RectTransform>();
        arrowRect.anchorMin = new Vector2(1, 0);
        arrowRect.anchorMax = new Vector2(1, 1);
        arrowRect.sizeDelta = new Vector2(30, 0);
        arrowRect.anchoredPosition = new Vector2(-15, 0);

        // Template
        GameObject templateObj = CreateElement("Template", dropdownObj);
        RectTransform templateRect = templateObj.GetComponent<RectTransform>();
        templateRect.anchorMin = new Vector2(0, 0);
        templateRect.anchorMax = new Vector2(1, 0);
        templateRect.pivot = new Vector2(0.5f, 1);
        templateRect.sizeDelta = new Vector2(0, 200);
        templateRect.anchoredPosition = Vector2.zero;

        Image templateBg = templateObj.AddComponent<Image>();
        templateBg.color = SettingsData.DropdownColor;

        ScrollRect scrollRect = templateObj.AddComponent<ScrollRect>();
        scrollRect.horizontal = false;
        scrollRect.vertical = true;
        scrollRect.movementType = ScrollRect.MovementType.Clamped;
        scrollRect.scrollSensitivity = 30f;

        // Viewport
        GameObject viewportObj = CreateElement("Viewport", templateObj);
        RectTransform viewportRect = viewportObj.GetComponent<RectTransform>();
        viewportRect.anchorMin = Vector2.zero;
        viewportRect.anchorMax = Vector2.one;
        viewportRect.offsetMin = new Vector2(0, 0);
        viewportRect.offsetMax = new Vector2(-12, 0); // Leave space for scrollbar

        Image viewportImg = viewportObj.AddComponent<Image>();
        viewportImg.color = Color.clear;
        Mask mask = viewportObj.AddComponent<Mask>();
        mask.showMaskGraphic = false;

        // Dropdown scrollbar
        GameObject scrollbarObj = CreateElement("Scrollbar", templateObj);
        RectTransform sbRect = scrollbarObj.GetComponent<RectTransform>();
        sbRect.anchorMin = new Vector2(1, 0);
        sbRect.anchorMax = new Vector2(1, 1);
        sbRect.pivot = new Vector2(1, 0.5f);
        sbRect.sizeDelta = new Vector2(10, 0);
        sbRect.anchoredPosition = Vector2.zero;

        Image sbBg = scrollbarObj.AddComponent<Image>();
        sbBg.color = new Color(0.2f, 0.2f, 0.25f, 0.8f);

        Scrollbar scrollbar = scrollbarObj.AddComponent<Scrollbar>();
        scrollbar.direction = Scrollbar.Direction.BottomToTop;

        GameObject sbHandle = CreateElement("Handle", scrollbarObj);
        RectTransform sbHandleRect = sbHandle.GetComponent<RectTransform>();
        sbHandleRect.anchorMin = Vector2.zero;
        sbHandleRect.anchorMax = Vector2.one;
        sbHandleRect.offsetMin = new Vector2(2, 2);
        sbHandleRect.offsetMax = new Vector2(-2, -2);

        Image sbHandleImg = sbHandle.AddComponent<Image>();
        sbHandleImg.color = SettingsData.TitleColor;

        scrollbar.handleRect = sbHandleRect;
        scrollbar.targetGraphic = sbHandleImg;

        scrollRect.verticalScrollbar = scrollbar;
        scrollRect.verticalScrollbarVisibility = ScrollRect.ScrollbarVisibility.AutoHide;

        // Content
        GameObject contentObj = CreateElement("Content", viewportObj);
        RectTransform contentRect = contentObj.GetComponent<RectTransform>();
        contentRect.anchorMin = new Vector2(0, 1);
        contentRect.anchorMax = new Vector2(1, 1);
        contentRect.pivot = new Vector2(0.5f, 1);
        contentRect.sizeDelta = new Vector2(0, 0);

        scrollRect.viewport = viewportRect;
        scrollRect.content = contentRect;

        // Item template
        GameObject itemObj = CreateElement("Item", contentObj);
        RectTransform itemRect = itemObj.GetComponent<RectTransform>();
        itemRect.anchorMin = new Vector2(0, 0.5f);
        itemRect.anchorMax = new Vector2(1, 0.5f);
        itemRect.sizeDelta = new Vector2(0, 35);

        Toggle itemToggle = itemObj.AddComponent<Toggle>();

        GameObject itemBgObj = CreateElement("Item Background", itemObj);
        Image itemBgImg = itemBgObj.AddComponent<Image>();
        itemBgImg.color = new Color(0.85f, 0.75f, 0.55f, 0.3f);
        SetFullScreen(itemBgObj);
        itemToggle.targetGraphic = itemBgImg;

        GameObject itemCheckObj = CreateElement("Item Checkmark", itemObj);
        Image itemCheckImg = itemCheckObj.AddComponent<Image>();
        itemCheckImg.color = SettingsData.TitleColor;
        RectTransform itemCheckRect = itemCheckObj.GetComponent<RectTransform>();
        itemCheckRect.anchorMin = new Vector2(0, 0.2f);
        itemCheckRect.anchorMax = new Vector2(0, 0.8f);
        itemCheckRect.sizeDelta = new Vector2(20, 0);
        itemCheckRect.anchoredPosition = new Vector2(15, 0);
        itemToggle.graphic = itemCheckImg;

        GameObject itemLabelObj = CreateElement("Item Label", itemObj);
        Text itemLabelText = itemLabelObj.AddComponent<Text>();
        itemLabelText.font = DefaultFont;
        itemLabelText.fontSize = 18;
        itemLabelText.color = SettingsData.ButtonTextColor;
        itemLabelText.alignment = TextAnchor.MiddleLeft;
        RectTransform itemLabelRect = itemLabelObj.GetComponent<RectTransform>();
        itemLabelRect.anchorMin = Vector2.zero;
        itemLabelRect.anchorMax = Vector2.one;
        itemLabelRect.offsetMin = new Vector2(35, 0);
        itemLabelRect.offsetMax = new Vector2(-10, 0);

        dropdown.template = templateRect;
        dropdown.itemText = itemLabelText;
        templateObj.SetActive(false);

        dropdown.ClearOptions();
        dropdown.AddOptions(new List<string>(options));
        dropdown.value = defaultIndex;
        dropdown.RefreshShownValue();

        return dropdown;
    }

    /// <summary>
    /// Create a section header
    /// </summary>
    public static void CreateSectionHeader(GameObject parent, string text)
    {
        GameObject header = CreateElement("Header_" + text, parent);
        LayoutElement le = header.AddComponent<LayoutElement>();
        le.preferredHeight = 40;
        le.preferredWidth = 700;

        Text headerText = header.AddComponent<Text>();
        headerText.text = "— " + text + " —";
        headerText.font = DefaultFont;
        headerText.fontSize = 22;
        headerText.fontStyle = FontStyle.Bold;
        headerText.color = SettingsData.TitleColor;
        headerText.alignment = TextAnchor.MiddleLeft;
    }
}
