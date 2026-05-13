"""Opening briefing screen."""

import math
import pygame

from src.screens.base_screen import BaseScreen
from src.ui.theme import UITheme
from src.ui.fonts import get_font
from src.ui.widgets import draw_panel, draw_text, draw_centered_text


class IntroScreen(BaseScreen):
    """Opening briefing screen shown before the map."""

    def __init__(self, screen_manager):
        """Set up initial state."""
        super().__init__(screen_manager)
        self.music_track = "forest"

        self.title_font = get_font(UITheme.HEADER_SIZE)
        self.header_font = get_font(UITheme.BODY_SIZE)
        self.body_font = get_font(UITheme.SMALL_SIZE)
        self.small_font = get_font(18)

        self.lines = [
            "BIOHAZARD ALERT: Quarantine Woods has been sealed after a mutation outbreak escaped from the research lab.",
            "Containment alarms are still active. Unknown samples are changing every living creature they touch.",
            "Your first objective is to reach the base camp scientist and receive the emergency briefing from Dr. Biologist."
        ]
        self.current_line = 0

        self.started_at = pygame.time.get_ticks()
        self.reveal_delay_ms = 18
        self.visible_chars = 0
        self.last_reveal_time = self.started_at
        self.line_finished = False
        self.blink_anchor = self.started_at

    def handle_event(self, event):
        """Handle the event."""
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.play_sfx("click")
            self._start_game_map()
            return

        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.play_sfx("click")

            if not self.line_finished:
                self._reveal_current_line_immediately()
                return

            self.current_line += 1
            if self.current_line >= len(self.lines):
                self._start_game_map()
                return

            self._reset_line_animation()

    def update(self):
        """Update this screen for the current frame."""
        if self.current_line >= len(self.lines) or self.line_finished:
            return

        line = self.lines[self.current_line]
        now = pygame.time.get_ticks()

        while self.visible_chars < len(line):
            if now - self.last_reveal_time < self.reveal_delay_ms:
                break
            self.visible_chars += 1
            self.last_reveal_time += self.reveal_delay_ms

        if self.visible_chars >= len(line):
            self._reveal_current_line_immediately()

    def draw(self, surface):
        """Draw this screen."""
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        surface.fill(UITheme.BG_DARK)
        self._draw_scan_background(surface)

        center_x = screen_w // 2
        main_rect = pygame.Rect(120, 88, screen_w - 240, screen_h - 176)
        draw_panel(
            surface,
            main_rect,
            color=UITheme.PANEL_DARK,
            border_color=UITheme.ACCENT,
            border_width=3
        )

        draw_centered_text(
            surface,
            "CONTAINMENT BREACH",
            self.title_font,
            UITheme.DANGER,
            center_x,
            main_rect.y + 64
        )
        draw_centered_text(
            surface,
            "OPENING FIELD BRIEFING",
            self.small_font,
            UITheme.ACCENT_GOLD,
            center_x,
            main_rect.y + 106
        )

        self._draw_status_block(surface, main_rect)
        self._draw_briefing_text(surface, main_rect)
        self._draw_progress(surface, main_rect)
        self._draw_hint(surface, main_rect)

    def _start_game_map(self):
        """Create the map screen after the intro."""
        from src.screens.map_screen import MapScreen

        self.screen_manager.pop()
        self.screen_manager.push(MapScreen(self.screen_manager))

    def _reset_line_animation(self):
        """Restart the typewriter animation for the current line."""
        self.visible_chars = 0
        self.last_reveal_time = pygame.time.get_ticks()
        self.line_finished = False
        self.blink_anchor = self.last_reveal_time

    def _reveal_current_line_immediately(self):
        """Show the full current line at once."""
        line = self.lines[self.current_line] if self.lines else ""
        self.visible_chars = len(line)
        self.line_finished = True
        self.blink_anchor = pygame.time.get_ticks()

    def _draw_scan_background(self, surface):
        """Draw the animated intro background."""
        screen_w = surface.get_width()
        screen_h = surface.get_height()
        now = pygame.time.get_ticks()

        grid_color = (18, 30, 38)
        for x in range(0, screen_w, 48):
            pygame.draw.line(surface, grid_color, (x, 0), (x, screen_h))
        for y in range(0, screen_h, 48):
            pygame.draw.line(surface, grid_color, (0, y), (screen_w, y))

        scan_y = int((now / 6) % max(1, screen_h))
        pygame.draw.line(
            surface,
            UITheme.ACCENT_DARK,
            (0, scan_y),
            (screen_w, scan_y),
            2
        )

        for y in range(0, screen_h, 8):
            pygame.draw.line(surface, (5, 8, 12), (0, y), (screen_w, y))

    def _draw_status_block(self, surface, main_rect):
        """Draw the intro mission status card."""
        block_rect = pygame.Rect(main_rect.x + 38, main_rect.y + 150, 330, 230)
        draw_panel(
            surface,
            block_rect,
            color=UITheme.PANEL,
            border_color=UITheme.ACCENT_DARK,
            border_width=2
        )

        rows = [
            ("REGION", "QUARANTINE WOODS", UITheme.ACCENT),
            ("THREAT", "MUTATION OUTBREAK", UITheme.DANGER),
            ("STATUS", "BASE CAMP SIGNAL FOUND", UITheme.ACCENT_GOLD),
            ("OBJECTIVE", "CONTACT DR. BIOLOGIST", UITheme.TEXT),
        ]

        y = block_rect.y + 26
        for label, value, color in rows:
            draw_text(surface, label, self.small_font, UITheme.TEXT_DIM, block_rect.x + 24, y)
            draw_text(surface, value, self.small_font, color, block_rect.x + 24, y + 24)
            y += 50

    def _draw_briefing_text(self, surface, main_rect):
        """Draw the current briefing message."""
        text_rect = pygame.Rect(main_rect.x + 398, main_rect.y + 150, main_rect.width - 436, 230)
        draw_panel(
            surface,
            text_rect,
            color=(12, 16, 24),
            border_color=UITheme.ACCENT_GOLD,
            border_width=2
        )

        page_text = f"TRANSMISSION {self.current_line + 1}/{len(self.lines)}"
        draw_text(surface, page_text, self.small_font, UITheme.ACCENT_GOLD, text_rect.x + 24, text_rect.y + 24)

        active_line = ""
        if self.current_line < len(self.lines):
            active_line = self.lines[self.current_line][:self.visible_chars]

        self._draw_wrapped_text(
            surface,
            active_line,
            self.body_font,
            UITheme.TEXT,
            text_rect.x + 24,
            text_rect.y + 78,
            text_rect.width - 48,
            34
        )

        if not self.line_finished:
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 120.0)
            pygame.draw.circle(
                surface,
                UITheme.ACCENT_GOLD,
                (text_rect.right - 34, text_rect.bottom - 30),
                4 + int(pulse * 3)
            )

    def _draw_progress(self, surface, main_rect):
        """Draw the intro page progress."""
        progress_rect = pygame.Rect(main_rect.x + 38, main_rect.bottom - 126, main_rect.width - 76, 34)
        draw_panel(
            surface,
            progress_rect,
            color=(8, 12, 18),
            border_color=UITheme.ACCENT_DARK,
            border_width=2
        )

        line_progress = (self.current_line + (1 if self.line_finished else 0)) / len(self.lines)
        time_progress = min(1.0, (pygame.time.get_ticks() - self.started_at) / 2600.0)
        progress = max(line_progress, time_progress * 0.35)
        fill_width = int((progress_rect.width - 8) * min(1.0, progress))

        fill_rect = pygame.Rect(progress_rect.x + 4, progress_rect.y + 4, fill_width, progress_rect.height - 8)
        if fill_width > 0:
            pygame.draw.rect(surface, UITheme.ACCENT, fill_rect, border_radius=8)

        pct_text = f"LOADING INTRO SEQUENCE  {int(progress * 100):03d}%"
        draw_text(surface, pct_text, self.small_font, UITheme.TEXT_DIM, progress_rect.x + 12, progress_rect.y + 6)

    def _draw_hint(self, surface, main_rect):
        """Draw the bottom control hint."""
        if self.line_finished:
            if self.current_line == len(self.lines) - 1:
                hint = "SPACE / ENTER  START MISSION"
            else:
                hint = "SPACE / ENTER  NEXT TRANSMISSION"
            blink_on = ((pygame.time.get_ticks() - self.blink_anchor) // 320) % 2 == 0
            color = UITheme.TEXT if blink_on else UITheme.TEXT_DIM
        else:
            hint = "SPACE / ENTER  COMPLETE TEXT     ESC  SKIP INTRO"
            color = UITheme.TEXT_DIM

        draw_centered_text(
            surface,
            hint,
            self.small_font,
            color,
            surface.get_width() // 2,
            main_rect.bottom - 52
        )

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
                if current_line:
                    surface.blit(font.render(current_line, True, color), (x, y))
                    y += line_height
                current_line = word + " "

        if current_line:
            surface.blit(font.render(current_line, True, color), (x, y))
