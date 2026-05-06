import pygame
from src.paths import DEFAULT_SAVE_FILE
from src.core.game_session import GameSession
from src.screens.base_screen import BaseScreen
from src.data_structures.cryptography import SaveEncryption

from src.ui.theme import UITheme
from src.ui.widgets import draw_shadow_panel, draw_button, draw_centered_text


class MainMenuScreen(BaseScreen):
    """
    The title screen of the game.

    Handles:
    - Starting a new game
    - Loading an HMAC-verified save file
    - Saving the current game session
    - Quitting the game
    """

    def __init__(self, screen_manager):
        super().__init__(screen_manager)

        self.title_font = pygame.font.SysFont(None, UITheme.TITLE_SIZE)
        self.header_font = pygame.font.SysFont(None, UITheme.HEADER_SIZE)
        self.menu_font = pygame.font.SysFont(None, UITheme.BODY_SIZE)
        self.small_font = pygame.font.SysFont(None, UITheme.SMALL_SIZE)

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
        """
        Handles menu selection via keyboard.
        Supports both old hotkeys and UP/DOWN/ENTER navigation.
        """
        if event.type == pygame.KEYDOWN:

            # Navigate menu
            if event.key == pygame.K_UP:
                self.selected_option = (
                    self.selected_option - 1
                ) % len(self.options)

            elif event.key == pygame.K_DOWN:
                self.selected_option = (
                    self.selected_option + 1
                ) % len(self.options)

            elif event.key == pygame.K_RETURN:
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
        """
        Executes the selected menu action.
        """
        if action == "new":
            self.screen_manager.game_session = GameSession()

            from src.screens.map_screen import MapScreen
            self.screen_manager.push(MapScreen(self.screen_manager))

        elif action == "load":
            self._load_verified_save()

        elif action == "save":
            self._save_current_game()

        elif action == "quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _load_verified_save(self):
        """
        Loads a save file only if its HMAC signature is valid.
        """
        if not self.save_file_path.exists():
            self.status_message = "No save file found. Start a New Game first."
            return

        save_data = SaveEncryption.load_game(self.save_file_path)

        if save_data:
            print("Save file verified and loaded successfully!")

            # Reset session first, then import save data.
            # This avoids old runtime state leaking into loaded data.
            self.screen_manager.game_session = GameSession()
            self.screen_manager.game_session.import_save_data(save_data)

            from src.screens.map_screen import MapScreen
            self.screen_manager.push(MapScreen(self.screen_manager))

        else:
            self.status_message = "ERROR: Save file modified or corrupted!"

    def _save_current_game(self):
        """
        Saves the current game session with HMAC protection.
        """
        save_data = self.screen_manager.game_session.export_save_data()

        success = SaveEncryption.save_game(
            save_data,
            self.save_file_path
        )

        if success:
            self.status_message = "Game Session Saved with HMAC!"
        else:
            self.status_message = "ERROR: Failed to save game!"

    def update(self):
        """
        Static menu, no update logic needed.
        """
        pass

    def draw(self, surface):
        """
        Renders the title screen UI.
        """
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
        """
        Draws a simple background grid to make the menu feel less empty.
        """
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