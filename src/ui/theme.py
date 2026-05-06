class UITheme:
    """
    Stores shared colors and font sizes for the whole game UI.
    This helps all screens follow the same visual style.
    """

    # Main colors
    BG = (14, 18, 26)
    BG_DARK = (8, 10, 16)

    PANEL = (28, 34, 48)
    PANEL_DARK = (18, 22, 32)
    PANEL_LIGHT = (42, 50, 68)

    # Accent colors
    ACCENT = (0, 220, 150)
    ACCENT_DARK = (0, 140, 100)
    ACCENT_GOLD = (255, 210, 80)

    # Text colors
    TEXT = (235, 240, 245)
    TEXT_DIM = (160, 170, 180)
    TEXT_DARK = (80, 90, 100)

    # Status colors
    SUCCESS = (100, 230, 130)
    WARNING = (255, 190, 80)
    DANGER = (230, 80, 80)

    # Combat colors
    HP_BG = (90, 30, 30)
    HP_FILL = (70, 220, 110)
    MANA_FILL = (80, 160, 255)

    # UI sizes
    BORDER_RADIUS = 12
    PANEL_BORDER_WIDTH = 2

    TITLE_SIZE = 64
    HEADER_SIZE = 40
    BODY_SIZE = 28
    SMALL_SIZE = 22