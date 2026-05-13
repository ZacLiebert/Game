"""Font loading helper."""

import pygame


FONT_CANDIDATES = [
    "bahnschrift",
    "segoe ui",
    "verdana",
    "consolas",
    "cascadia mono",
    "dejavu sans mono",
    "courier new",
    "arial",
]


def get_font(size, bold=False, italic=False):
    """Return the font."""
    font_name = None

    for candidate in FONT_CANDIDATES:
        matched = pygame.font.match_font(candidate)

        if matched:
            font_name = candidate
            break

    safe_size = max(12, int(size * 0.90))

    return pygame.font.SysFont(
        font_name,
        safe_size,
        bold=bold,
        italic=italic
    )
