"""Ending screen."""

import pygame

from src.screens.base_screen import BaseScreen
from src.ui.theme import UITheme
from src.ui.fonts import get_font
from src.ui.widgets import draw_button, draw_centered_text, draw_panel


class EndingScreen(BaseScreen):
    """Final story screen shown after the last quest."""

    def __init__(self, screen_manager):
        """Set up initial state."""
        super().__init__(screen_manager)
        self.music_track = "forest"
        self.play_sfx("success")

        self.title_font = get_font(78)
        self.header_font = get_font(UITheme.HEADER_SIZE)
        self.font = get_font(UITheme.BODY_SIZE)
        self.small_font = get_font(UITheme.SMALL_SIZE)

    def handle_event(self, event):
        """Handle the event."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                self.play_sfx("click")
                while self.screen_manager.size() > 1:
                    self.screen_manager.pop()

    def update(self):
        """Update this screen for the current frame."""
        pass

    def draw(self, surface):
        """Draw this screen."""
        screen_w = surface.get_width()
        screen_h = surface.get_height()
        center_x = screen_w // 2

        surface.fill((6, 18, 18))
        self._draw_background(surface)

        panel_width = 820
        panel_height = 430
        panel_x = (screen_w - panel_width) // 2
        panel_y = (screen_h - panel_height) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        draw_panel(
            surface,
            panel_rect,
            color=(10, 28, 26),
            border_color=UITheme.ACCENT,
            border_width=3
        )

        draw_centered_text(
            surface,
            "OUTBREAK CONTAINED",
            self.title_font,
            UITheme.ACCENT,
            center_x,
            panel_y + 80
        )

        draw_centered_text(
            surface,
            "Zac's mutation stabilized the island.",
            self.header_font,
            UITheme.TEXT,
            center_x,
            panel_y + 145
        )

        lines = [
            "The field samples, evolutions, and final battle proved the cure pathway.",
            "The remaining beasts retreat into the forest as the lab signal goes silent.",
            "Main Quest Complete"
        ]

        for i, line in enumerate(lines):
            draw_centered_text(
                surface,
                line,
                self.small_font,
                UITheme.TEXT_DIM if i < len(lines) - 1 else UITheme.ACCENT_GOLD,
                center_x,
                panel_y + 205 + i * 34
            )

        button_rect = pygame.Rect(center_x - 175, panel_y + 335, 350, 52)

        draw_button(
            surface,
            button_rect,
            "[ENTER] Return to Menu",
            self.small_font,
            is_selected=True
        )

    def _draw_background(self, surface):
        """Draw the background."""
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        grid_color = (11, 34, 33)

        for x in range(0, screen_w, 56):
            pygame.draw.line(surface, grid_color, (x, 0), (x, screen_h))

        for y in range(0, screen_h, 56):
            pygame.draw.line(surface, grid_color, (0, y), (screen_w, y))
