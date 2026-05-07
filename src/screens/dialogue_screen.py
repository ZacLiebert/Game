import pygame

from src.screens.base_screen import BaseScreen
from src.ui.theme import UITheme
from src.ui.fonts import get_font
from src.ui.widgets import draw_panel, draw_text


class DialogueScreen(BaseScreen):
    """
    Pokemon-style dialogue screen.

    The map remains visible behind the dialogue box.
    Controls:
    - ENTER / SPACE: next line
    - ESC: close dialogue
    """

    def __init__(self, screen_manager, npc):
        super().__init__(screen_manager)

        self.npc = npc
        self.lines = npc.dialogue if npc.dialogue else ["..."]
        self.current_line = 0

        self.name_font = get_font(UITheme.BODY_SIZE)
        self.text_font = get_font(UITheme.SMALL_SIZE)
        self.hint_font = get_font(22)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.screen_manager.pop()
                return

            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self.current_line += 1

                if self.current_line >= len(self.lines):
                    self.screen_manager.pop()
                    return

    def update(self):
        pass

    def draw(self, surface):
        """
        Draws the map behind the dialogue, then draws a Pokemon-style
        dialogue box at the bottom.
        """
        if not self.lines:
            self.lines = ["..."]

        if self.current_line >= len(self.lines):
            return

        # Draw MapScreen underneath first.
        self._draw_previous_screen(surface)

        screen_w = surface.get_width()
        screen_h = surface.get_height()

        # Dialogue box at bottom, Pokemon-style.
        box_rect = pygame.Rect(
            60,
            screen_h - 185,
            screen_w - 120,
            135
        )

        draw_panel(
            surface,
            box_rect,
            color=UITheme.PANEL_DARK,
            border_color=UITheme.ACCENT,
            border_width=3
        )

        # NPC name plate.
        name_rect = pygame.Rect(
            box_rect.x + 24,
            box_rect.y - 34,
            260,
            38
        )

        draw_panel(
            surface,
            name_rect,
            color=UITheme.PANEL,
            border_color=UITheme.ACCENT_GOLD,
            border_width=2
        )

        draw_text(
            surface,
            self.npc.name,
            self.name_font,
            UITheme.ACCENT_GOLD,
            name_rect.x + 15,
            name_rect.y + 8
        )

        # Dialogue text.
        line = self.lines[self.current_line]

        self._draw_wrapped_text(
            surface,
            line,
            self.text_font,
            UITheme.TEXT,
            box_rect.x + 28,
            box_rect.y + 32,
            box_rect.width - 70,
            28
        )

        # Continue indicator.
        draw_text(
            surface,
            "ENTER / SPACE",
            self.hint_font,
            UITheme.TEXT_DIM,
            box_rect.right - 165,
            box_rect.bottom - 30
        )

        # Small arrow indicator.
        pygame.draw.polygon(
            surface,
            UITheme.ACCENT_GOLD,
            [
                (box_rect.right - 35, box_rect.bottom - 24),
                (box_rect.right - 20, box_rect.bottom - 24),
                (box_rect.right - 27, box_rect.bottom - 14)
            ]
        )

    def _draw_previous_screen(self, surface):
        """
        Draws the screen underneath this dialogue screen.
        Usually this is MapScreen.

        This keeps the map visible like Pokemon-style dialogue.
        """
        stack = getattr(self.screen_manager, "stack", [])

        if len(stack) >= 2:
            previous_screen = stack[-2]
            previous_screen.draw(surface)
        else:
            surface.fill(UITheme.BG_DARK)

    def _draw_wrapped_text(
        self,
        surface,
        text,
        font,
        color,
        x,
        y,
        max_width,
        line_height
    ):
        words = text.split(" ")
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            test_surface = font.render(test_line, True, color)

            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                line_surface = font.render(current_line, True, color)
                surface.blit(line_surface, (x, y))

                y += line_height
                current_line = word + " "

        if current_line:
            line_surface = font.render(current_line, True, color)
            surface.blit(line_surface, (x, y))