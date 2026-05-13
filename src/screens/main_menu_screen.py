"""Main menu screen."""

import pygame
from src.paths import DEFAULT_SAVE_FILE
from src.core.game_session import GameSession
from src.screens.base_screen import BaseScreen
from src.core.save_integrity import SaveEncryption

from src.ui.theme import UITheme
from src.ui.fonts import get_font
from src.ui.widgets import draw_shadow_panel, draw_button, draw_centered_text


class MainMenuScreen(BaseScreen):
    """Main menu for starting, loading, and exiting the game."""

    def __init__(self, screen_manager):
        """Set up initial state."""
        super().__init__(screen_manager)
        self.music_track = "forest"

        self.title_font = get_font(UITheme.TITLE_SIZE)
        self.header_font = get_font(UITheme.HEADER_SIZE)
        self.menu_font = get_font(UITheme.BODY_SIZE)
        self.small_font = get_font(UITheme.SMALL_SIZE)

        self.save_file_path = DEFAULT_SAVE_FILE
        self.status_message = ""

        # Menu options
        self.options = [
            {"label": "New Game", "action": "new"},
            {"label": "Load Verified Save", "action": "load"},
            {"label": "Save Game", "action": "save"},
            {"label": "Quit", "action": "quit"}
        ]

        self.selected_option = 0

    def handle_event(self, event):
        """Handle the event."""
        if event.type == pygame.KEYDOWN:

            # Navigate menu
            if event.key == pygame.K_UP:
                self.selected_option = (
                    self.selected_option - 1
                ) % len(self.options)
                self.play_sfx("click")

            elif event.key == pygame.K_DOWN:
                self.selected_option = (
                    self.selected_option + 1
                ) % len(self.options)
                self.play_sfx("click")

            elif event.key == pygame.K_RETURN:
                self.play_sfx("click")
                selected_action = self.options[self.selected_option]["action"]
                self._execute_action(selected_action)

            # Shortcut keys
            elif event.key == pygame.K_n:
                self._execute_action("new")

            elif event.key == pygame.K_l:
                self._execute_action("load")

            elif event.key == pygame.K_s:
                self._execute_action("save")

            elif event.key == pygame.K_ESCAPE:
                self._execute_action("quit")


    def _execute_action(self, action):
        """Run the selected menu or combat action."""
        if action == "new":
            self.play_sfx("success")
            self.screen_manager.game_session = GameSession()

            from src.screens.intro_screen import IntroScreen

            self.screen_manager.push(IntroScreen(self.screen_manager))

        elif action == "load":
            self._load_verified_save()

        elif action == "save":
            self._save_current_game()

        elif action == "quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _load_verified_save(self):
        """Load save data after integrity checking."""
        if not self.save_file_path.exists():
            self.play_sfx("error")
            self.status_message = "No save file found. Start a New Game first."
            return

        save_data = SaveEncryption.load_game(self.save_file_path)

        if save_data:
            self.play_sfx("success")
            print("Save file verified and loaded successfully!")

            # Reset session first, then import save data.
            # This avoids old runtime state leaking into loaded data.
            self.screen_manager.game_session = GameSession()
            self.screen_manager.game_session.import_save_data(save_data)

            from src.screens.map_screen import MapScreen
            self.screen_manager.push(MapScreen(self.screen_manager))

        else:
            self.play_sfx("error")
            self.status_message = "ERROR: Save file modified or corrupted!"

    def _save_current_game(self):
        """Save the current game session."""
        save_data = self.screen_manager.game_session.export_save_data()

        success = SaveEncryption.save_game(
            save_data,
            self.save_file_path
        )

        if success:
            self.play_sfx("success")
            self.status_message = "Game Session Saved with HMAC!"
        else:
            self.play_sfx("error")
            self.status_message = "ERROR: Failed to save game!"

    def update(self):
        """Update this screen for the current frame."""
        pass

    def draw(self, surface):
        """Draw this screen."""
        screen_w = surface.get_width()
        screen_h = surface.get_height()
        center_x = screen_w // 2

        # Background
        surface.fill(UITheme.BG_DARK)

        # Simple sci-fi grid background
        self._draw_background_grid(surface)

        # Main panel
        panel_width = 620
        panel_height = 470
        panel_x = (screen_w - panel_width) // 2
        panel_y = 100

        main_panel = pygame.Rect(
            panel_x,
            panel_y,
            panel_width,
            panel_height
        )

        draw_shadow_panel(surface, main_panel)

        # Title
        draw_centered_text(
            surface,
            "MUTATION RPG",
            self.title_font,
            UITheme.ACCENT,
            center_x,
            panel_y + 70
        )

        draw_centered_text(
            surface,
            "Biological Evolution Warfare",
            self.small_font,
            UITheme.TEXT_DIM,
            center_x,
            panel_y + 115
        )

        # Menu buttons
        button_width = 420
        button_height = 48
        button_x = center_x - button_width // 2
        start_y = panel_y + 165

        for i, option in enumerate(self.options):
            button_rect = pygame.Rect(
                button_x,
                start_y + i * 65,
                button_width,
                button_height
            )

            draw_button(
                surface,
                button_rect,
                option["label"],
                self.menu_font,
                is_selected=(i == self.selected_option)
            )

        # Status message
        if self.status_message:
            if (
                "ERROR" in self.status_message
                or "No save" in self.status_message
                or "Failed" in self.status_message
            ):
                status_color = UITheme.DANGER
            else:
                status_color = UITheme.SUCCESS

            draw_centered_text(
                surface,
                self.status_message,
                self.small_font,
                status_color,
                center_x,
                panel_y + panel_height - 45
            )

        # Controls hint
        hint_text = "UP/DOWN: Select   ENTER: Confirm   ESC: Quit"

        draw_centered_text(
            surface,
            hint_text,
            self.small_font,
            UITheme.TEXT_DIM,
            center_x,
            screen_h - 40
        )

    def _draw_background_grid(self, surface):
        """Draw the animated menu grid."""
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        grid_color = (22, 30, 42)

        for x in range(0, screen_w, 40):
            pygame.draw.line(
                surface,
                grid_color,
                (x, 0),
                (x, screen_h)
            )

        for y in range(0, screen_h, 40):
            pygame.draw.line(
                surface,
                grid_color,
                (0, y),
                (screen_w, y)
            )
