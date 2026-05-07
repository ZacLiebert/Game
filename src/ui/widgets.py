import pygame
from src.ui.theme import UITheme


def draw_panel(surface, rect, color=None, border_color=None, border_width=2):
    """
    Draws a rounded rectangle panel.
    """
    panel_color = color if color else UITheme.PANEL

    pygame.draw.rect(
        surface,
        panel_color,
        rect,
        border_radius=UITheme.BORDER_RADIUS
    )

    if border_color:
        pygame.draw.rect(
            surface,
            border_color,
            rect,
            border_width,
            border_radius=UITheme.BORDER_RADIUS
        )


def _draw_text_surface(surface, text_surface, pos):
    """
    Draws text with:
    - dark shadow for contrast
    - a very subtle extra pass for thicker text

    This makes UI text clearer without changing layout sizes.
    """
    x, y = pos

    # Dark shadow
    shadow = text_surface.copy()
    shadow.fill(
        (0, 0, 0),
        special_flags=pygame.BLEND_RGB_MULT
    )
    shadow.set_alpha(150)

    surface.blit(shadow, (x + 2, y + 2))

    # Subtle thickness pass
    thick_pass = text_surface.copy()
    thick_pass.set_alpha(85)
    surface.blit(thick_pass, (x + 1, y))

    # Main text
    surface.blit(text_surface, (x, y))


def draw_text(surface, text, font, color, x, y):
    """
    Draws text at a fixed position with improved readability.
    """
    text_surface = font.render(str(text), True, color)

    _draw_text_surface(
        surface,
        text_surface,
        (x, y)
    )

    return text_surface.get_rect(topleft=(x, y))


def draw_centered_text(surface, text, font, color, center_x, y):
    """
    Draws text centered horizontally with improved readability.
    """
    text_surface = font.render(str(text), True, color)
    text_rect = text_surface.get_rect(center=(center_x, y))

    _draw_text_surface(
        surface,
        text_surface,
        text_rect.topleft
    )

    return text_rect


def draw_button(surface, rect, text, font, is_selected=False):
    """
    Draws a simple selectable button.
    """
    if is_selected:
        bg_color = UITheme.PANEL_LIGHT
        border_color = UITheme.ACCENT
        text_color = UITheme.TEXT
    else:
        bg_color = UITheme.PANEL
        border_color = UITheme.ACCENT_DARK
        text_color = UITheme.TEXT_DIM

    draw_panel(
        surface,
        rect,
        bg_color,
        border_color,
        2
    )

    text_surface = font.render(str(text), True, text_color)
    text_rect = text_surface.get_rect(center=rect.center)

    _draw_text_surface(
        surface,
        text_surface,
        text_rect.topleft
    )

    return text_rect


def draw_health_bar(surface, x, y, width, height, current_hp, max_hp):
    """
    Draws a health bar with current HP ratio.
    """
    bg_rect = pygame.Rect(x, y, width, height)

    pygame.draw.rect(
        surface,
        UITheme.HP_BG,
        bg_rect,
        border_radius=6
    )

    if max_hp > 0:
        ratio = max(0, min(1, current_hp / max_hp))
        fill_width = int(width * ratio)

        fill_rect = pygame.Rect(
            x,
            y,
            fill_width,
            height
        )

        pygame.draw.rect(
            surface,
            UITheme.HP_FILL,
            fill_rect,
            border_radius=6
        )

    pygame.draw.rect(
        surface,
        UITheme.TEXT_DIM,
        bg_rect,
        1,
        border_radius=6
    )


def draw_shadow_panel(surface, rect):
    """
    Draws a panel with a simple fake shadow effect.
    """
    shadow_rect = pygame.Rect(
        rect.x + 5,
        rect.y + 5,
        rect.width,
        rect.height
    )

    pygame.draw.rect(
        surface,
        (0, 0, 0),
        shadow_rect,
        border_radius=UITheme.BORDER_RADIUS
    )

    draw_panel(
        surface,
        rect,
        UITheme.PANEL,
        UITheme.ACCENT_DARK,
        2
    )