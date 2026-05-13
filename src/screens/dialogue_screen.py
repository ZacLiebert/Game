"""Animated dialogue screen."""

import pygame

from src.screens.base_screen import BaseScreen
from src.ui.theme import UITheme
from src.ui.fonts import get_font
from src.ui.widgets import draw_panel, draw_text


class DialogueScreen(BaseScreen):
    """Dialogue overlay shown above the previous screen."""

    def __init__(self, screen_manager, npc):
        """Set up initial state."""
        super().__init__(screen_manager)
        self.music_track = "map"

        self.npc = npc
        self.lines = npc.dialogue if npc.dialogue else ["..."]
        self.current_line = 0

        self.name_font = get_font(UITheme.BODY_SIZE)
        self.text_font = get_font(UITheme.SMALL_SIZE)
        self.hint_font = get_font(20)

        self.reveal_delay_ms = 22
        self.long_pause_ms = 90
        self.visible_chars = 0
        self.last_reveal_time = pygame.time.get_ticks()
        self._line_finished = False
        self._blink_anchor = self.last_reveal_time

    def handle_event(self, event):
        """Handle the event."""
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.play_sfx("click")
            self.screen_manager.pop()
            return

        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.play_sfx("click")

            if not self._line_finished:
                self._reveal_current_line_immediately()
                return

            self.current_line += 1
            if self.current_line >= len(self.lines):
                self._finish_dialogue()
                return

            self._reset_line_animation()

    def _finish_dialogue(self):
        """Close the dialogue and run its callback."""
        session = self.screen_manager.game_session
        quest_manager = getattr(session, "quest_manager", None)

        if quest_manager and hasattr(self.npc, "name"):
            quest_manager.record_talk(self.npc.name)

        self.screen_manager.pop()

    def update(self):
        """Update this screen for the current frame."""
        self._update_typewriter()

    def _reset_line_animation(self):
        """Restart the typewriter animation for the current line."""
        self.visible_chars = 0
        self.last_reveal_time = pygame.time.get_ticks()
        self._line_finished = False
        self._blink_anchor = self.last_reveal_time

    def _reveal_current_line_immediately(self):
        """Show the full current line at once."""
        line = self.lines[self.current_line] if self.lines else ""
        self.visible_chars = len(line)
        self._line_finished = True
        self._blink_anchor = pygame.time.get_ticks()

    def _update_typewriter(self):
        """Update the typewriter."""
        if not self.lines or self.current_line >= len(self.lines):
            return

        line = self.lines[self.current_line]
        if self._line_finished or self.visible_chars >= len(line):
            self.visible_chars = len(line)
            self._line_finished = True
            return

        now = pygame.time.get_ticks()

        while self.visible_chars < len(line):
            delay = self._get_delay_after_character(line[self.visible_chars - 1]) if self.visible_chars > 0 else self.reveal_delay_ms
            if now - self.last_reveal_time < delay:
                break

            self.visible_chars += 1
            self.last_reveal_time += delay

        if self.visible_chars >= len(line):
            self.visible_chars = len(line)
            self._line_finished = True
            self._blink_anchor = now

    def _get_delay_after_character(self, character):
        """Return the delay after character."""
        if character in ".!?":
            return self.long_pause_ms
        if character in ",;:":
            return 45
        return self.reveal_delay_ms

    def _get_visible_line_text(self):
        """Return the visible line text."""
        if not self.lines or self.current_line >= len(self.lines):
            return ""

        line = self.lines[self.current_line]
        return line[:self.visible_chars]

    def draw(self, surface):
        """Draw this screen."""
        if not self.lines:
            self.lines = ["..."]

        if self.current_line >= len(self.lines):
            return

        self._draw_previous_screen(surface)

        screen_w = surface.get_width()
        screen_h = surface.get_height()

        box_rect = pygame.Rect(52, screen_h - 198, screen_w - 104, 148)

        draw_panel(
            surface,
            box_rect,
            color=UITheme.PANEL_DARK,
            border_color=UITheme.ACCENT,
            border_width=3
        )

        name_rect = pygame.Rect(box_rect.x + 22, box_rect.y - 34, 300, 38)
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

        line = self._get_visible_line_text()
        self._draw_wrapped_text(
            surface,
            line,
            self.text_font,
            UITheme.TEXT,
            box_rect.x + 28,
            box_rect.y + 28,
            box_rect.width - 70,
            28
        )

        if self._line_finished:
            hint_text = "SPACE / ENTER  NEXT"
            blink_on = ((pygame.time.get_ticks() - self._blink_anchor) // 320) % 2 == 0
            hint_color = UITheme.TEXT if blink_on else UITheme.TEXT_DIM
            draw_text(
                surface,
                hint_text,
                self.hint_font,
                hint_color,
                box_rect.right - 230,
                box_rect.bottom - 32
            )
            if blink_on:
                pygame.draw.polygon(
                    surface,
                    UITheme.ACCENT_GOLD,
                    [
                        (box_rect.right - 35, box_rect.bottom - 24),
                        (box_rect.right - 20, box_rect.bottom - 24),
                        (box_rect.right - 27, box_rect.bottom - 14)
                    ]
                )
        else:
            draw_text(
                surface,
                "SPACE / ENTER  COMPLETE",
                self.hint_font,
                UITheme.TEXT_DIM,
                box_rect.right - 275,
                box_rect.bottom - 32
            )
            pulse = 0.5 + 0.5 * __import__("math").sin(pygame.time.get_ticks() / 140.0)
            pygame.draw.circle(
                surface,
                UITheme.ACCENT_GOLD,
                (box_rect.right - 26, box_rect.bottom - 22),
                3 + int(pulse * 2)
            )

    def _draw_previous_screen(self, surface):
        """Draw the previous screen."""
        previous_screen = self.screen_manager.previous()

        if previous_screen:
            previous_screen.draw(surface)
        else:
            surface.fill(UITheme.BG_DARK)

    def _draw_wrapped_text(self, surface, text, font, color, x, y, max_width, line_height):
        """Draw text across multiple lines."""
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
