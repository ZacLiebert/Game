import pygame

from src.screens.base_screen import BaseScreen
from src.ui.theme import UITheme
from src.ui.fonts import get_font
from src.ui.widgets import draw_panel, draw_text, draw_centered_text, draw_button


class GameOverScreen(BaseScreen):
    """
    Game Over screen displayed when the entire party is defeated.
    """

    def __init__(self, screen_manager):
        super().__init__(screen_manager)

        self.title_font = get_font(76)
        self.header_font = get_font(UITheme.HEADER_SIZE)
        self.font = get_font(UITheme.BODY_SIZE)
        self.small_font = get_font(UITheme.SMALL_SIZE)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                while self.screen_manager.size() > 1:
                    self.screen_manager.pop()

    def update(self):
        pass

    def draw(self, surface):
        screen_w = surface.get_width()
        screen_h = surface.get_height()
        center_x = screen_w // 2

        # Background
        surface.fill((18, 4, 8))
        self._draw_warning_background(surface)

        # Main panel
        panel_width = 760
        panel_height = 390
        panel_x = (screen_w - panel_width) // 2
        panel_y = (screen_h - panel_height) // 2

        main_panel = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        draw_panel(
            surface,
            main_panel,
            color=(35, 12, 18),
            border_color=UITheme.DANGER,
            border_width=3
        )

        # Title
        draw_centered_text(
            surface,
            "SYSTEM FAILURE",
            self.title_font,
            UITheme.DANGER,
            center_x,
            panel_y + 75
        )

        draw_centered_text(
            surface,
            "YOUR PARTY HAS BEEN WIPED OUT",
            self.header_font,
            UITheme.TEXT,
            center_x,
            panel_y + 135
        )

        # Description box
        desc_rect = pygame.Rect(panel_x + 70, panel_y + 180, panel_width - 140, 80)

        draw_panel(
            surface,
            desc_rect,
            color=(22, 8, 12),
            border_color=(100, 35, 45)
        )

        draw_centered_text(
            surface,
            "The mutation experiment has collapsed.",
            self.small_font,
            UITheme.TEXT_DIM,
            center_x,
            desc_rect.y + 25
        )

        draw_centered_text(
            surface,
            "Return stronger, evolve further, and try again.",
            self.small_font,
            UITheme.TEXT_DIM,
            center_x,
            desc_rect.y + 52
        )

        # Exit button
        button_rect = pygame.Rect(center_x - 160, panel_y + 295, 320, 52)

        draw_button(
            surface,
            button_rect,
            "[ENTER] Return to Menu",
            self.small_font,
            is_selected=True
        )

        # Bottom hint
        draw_centered_text(
            surface,
            "ESC also returns to menu",
            self.small_font,
            UITheme.TEXT_DIM,
            center_x,
            screen_h - 40
        )

    def _draw_warning_background(self, surface):
        """
        Draws simple red warning grid lines.
        """
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        grid_color = (35, 10, 14)

        for x in range(0, screen_w, 50):
            pygame.draw.line(surface, grid_color, (x, 0), (x, screen_h))

        for y in range(0, screen_h, 50):
            pygame.draw.line(surface, grid_color, (0, y), (screen_w, y))

        # Warning side bars
        pygame.draw.rect(surface, (60, 10, 15), (0, 0, 14, screen_h))
        pygame.draw.rect(surface, (60, 10, 15), (screen_w - 14, 0, 14, screen_h))
