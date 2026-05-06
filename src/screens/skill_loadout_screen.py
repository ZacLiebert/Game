import pygame

from src.screens.base_screen import BaseScreen
from src.core.skill_library import SkillLibrary

from src.ui.theme import UITheme
from src.ui.widgets import draw_panel, draw_text, draw_button


class SkillLoadoutScreen(BaseScreen):
    """
    Lets the player choose up to 4 combat skills before battle.

    Controls:
    - UP/DOWN: Select skill
    - ENTER/SPACE: Equip or unequip selected skill
    - ESC: Back to map
    """

    def __init__(self, screen_manager):
        super().__init__(screen_manager)

        self.title_font = pygame.font.SysFont(None, UITheme.HEADER_SIZE)
        self.font = pygame.font.SysFont(None, UITheme.BODY_SIZE)
        self.small_font = pygame.font.SysFont(None, UITheme.SMALL_SIZE)

        self.session = self.screen_manager.game_session
        self.selected_index = 0
        self.status_msg = "Choose up to 4 skills for Zac before combat."

        self.available_skill_ids = []
        self._refresh()

    def _refresh(self):
        """
        Refresh available skills and sanitize saved loadout.
        """
        self.available_skill_ids = SkillLibrary.get_available_skill_ids(
            self.session.mutation_tree
        )

        self.session.skill_loadout = SkillLibrary.sanitize_loadout(
            self.session.skill_loadout,
            self.session.mutation_tree
        )

        if self.selected_index >= len(self.available_skill_ids):
            self.selected_index = max(0, len(self.available_skill_ids) - 1)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.screen_manager.pop()

            elif event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)

            elif event.key == pygame.K_DOWN:
                if self.available_skill_ids:
                    self.selected_index = min(
                        len(self.available_skill_ids) - 1,
                        self.selected_index + 1
                    )

            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._toggle_selected_skill()

    def _toggle_selected_skill(self):
        if not self.available_skill_ids:
            return

        skill_id = self.available_skill_ids[self.selected_index]
        loadout = self.session.skill_loadout

        if skill_id == "basic_attack":
            self.status_msg = "Basic Attack is always equipped."
            return

        if skill_id in loadout:
            loadout.remove(skill_id)
            self.status_msg = f"Unequipped {SkillLibrary.get_skill_name(skill_id)}."

        else:
            if len(loadout) >= SkillLibrary.MAX_LOADOUT_SIZE:
                self.status_msg = "Loadout full. Unequip another skill first."
                return

            loadout.append(skill_id)
            self.status_msg = f"Equipped {SkillLibrary.get_skill_name(skill_id)}."

        self.session.skill_loadout = SkillLibrary.sanitize_loadout(
            loadout,
            self.session.mutation_tree
        )

        self._refresh()

    def update(self):
        pass

    def draw(self, surface):
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        surface.fill((10, 14, 22))

        header_rect = pygame.Rect(30, 25, screen_w - 60, 80)

        draw_panel(
            surface,
            header_rect,
            color=UITheme.PANEL_DARK,
            border_color=UITheme.ACCENT_DARK
        )

        draw_text(
            surface,
            "SKILL LOADOUT",
            self.title_font,
            UITheme.ACCENT,
            header_rect.x + 25,
            header_rect.y + 18
        )

        hint = "UP/DOWN: Select   ENTER/SPACE: Equip/Unequip   ESC: Back"

        draw_text(
            surface,
            hint,
            self.small_font,
            UITheme.TEXT_DIM,
            header_rect.x + 430,
            header_rect.y + 30
        )

        list_panel = pygame.Rect(30, 125, 600, screen_h - 180)
        detail_panel = pygame.Rect(660, 125, screen_w - 690, screen_h - 180)

        draw_panel(
            surface,
            list_panel,
            color=UITheme.PANEL,
            border_color=UITheme.ACCENT_DARK
        )

        draw_panel(
            surface,
            detail_panel,
            color=UITheme.PANEL,
            border_color=UITheme.ACCENT_DARK
        )

        draw_text(
            surface,
            "Available Skills",
            self.font,
            UITheme.ACCENT_GOLD,
            list_panel.x + 25,
            list_panel.y + 18
        )

        draw_text(
            surface,
            "Skill Details",
            self.font,
            UITheme.ACCENT_GOLD,
            detail_panel.x + 25,
            detail_panel.y + 18
        )

        self._draw_skill_list(surface, list_panel)
        self._draw_skill_details(surface, detail_panel)

        loadout_text = self._get_loadout_summary()

        draw_text(
            surface,
            loadout_text,
            self.small_font,
            UITheme.ACCENT_GOLD,
            35,
            screen_h - 60
        )

        if "full" in self.status_msg.lower():
            status_color = UITheme.WARNING
        elif "equipped" in self.status_msg.lower():
            status_color = UITheme.SUCCESS
        elif "unequipped" in self.status_msg.lower():
            status_color = UITheme.WARNING
        else:
            status_color = UITheme.TEXT_DIM

        draw_text(
            surface,
            self.status_msg,
            self.small_font,
            status_color,
            35,
            screen_h - 35
        )

    def _draw_skill_list(self, surface, panel_rect):
        if not self.available_skill_ids:
            draw_text(
                surface,
                "No skills available.",
                self.small_font,
                UITheme.TEXT_DIM,
                panel_rect.x + 25,
                panel_rect.y + 80
            )
            return

        row_height = 58
        y = panel_rect.y + 70

        for i, skill_id in enumerate(self.available_skill_ids):
            is_selected = i == self.selected_index
            is_equipped = skill_id in self.session.skill_loadout

            row_rect = pygame.Rect(
                panel_rect.x + 20,
                y,
                panel_rect.width - 40,
                row_height - 10
            )

            if is_selected:
                border_color = UITheme.ACCENT_GOLD
            elif is_equipped:
                border_color = UITheme.SUCCESS
            else:
                border_color = (55, 65, 80)

            if is_equipped:
                bg_color = (24, 50, 42)
                status_text = "EQUIPPED"
                status_color = UITheme.SUCCESS
            else:
                bg_color = UITheme.PANEL_DARK
                status_text = "AVAILABLE"
                status_color = UITheme.TEXT_DIM

            draw_panel(
                surface,
                row_rect,
                color=bg_color,
                border_color=border_color
            )

            prefix = ">" if is_selected else " "

            draw_text(
                surface,
                f"{prefix} {SkillLibrary.get_skill_name(skill_id)}",
                self.small_font,
                UITheme.TEXT,
                row_rect.x + 15,
                row_rect.y + 13
            )

            status_surf = self.small_font.render(
                status_text,
                True,
                status_color
            )

            surface.blit(
                status_surf,
                (
                    row_rect.right - status_surf.get_width() - 15,
                    row_rect.y + 13
                )
            )

            y += row_height

    def _draw_skill_details(self, surface, panel_rect):
        if not self.available_skill_ids:
            return

        skill_id = self.available_skill_ids[self.selected_index]
        skill_name = SkillLibrary.get_skill_name(skill_id)
        skill_info = SkillLibrary.get_skill_info(skill_id)
        is_equipped = skill_id in self.session.skill_loadout

        x = panel_rect.x + 25
        y = panel_rect.y + 75

        draw_text(
            surface,
            skill_name,
            self.font,
            UITheme.TEXT,
            x,
            y
        )

        y += 50

        badge_text = "EQUIPPED" if is_equipped else "NOT EQUIPPED"
        badge_color = UITheme.SUCCESS if is_equipped else UITheme.WARNING

        badge_rect = pygame.Rect(x, y, 210, 38)

        draw_panel(
            surface,
            badge_rect,
            color=UITheme.PANEL_DARK,
            border_color=badge_color
        )

        draw_text(
            surface,
            badge_text,
            self.small_font,
            badge_color,
            badge_rect.x + 15,
            badge_rect.y + 9
        )

        y += 65

        draw_text(
            surface,
            "Description",
            self.small_font,
            UITheme.ACCENT,
            x,
            y
        )

        y += 30

        self._draw_wrapped_text(
            surface,
            skill_info["description"],
            self.small_font,
            UITheme.TEXT_DIM,
            x,
            y,
            panel_rect.width - 50,
            26
        )

        y += 90

        draw_text(
            surface,
            "Effect",
            self.small_font,
            UITheme.ACCENT,
            x,
            y
        )

        y += 30

        self._draw_wrapped_text(
            surface,
            skill_info["effect"],
            self.small_font,
            UITheme.TEXT_DIM,
            x,
            y,
            panel_rect.width - 50,
            26
        )

        button_rect = pygame.Rect(
            x,
            panel_rect.bottom - 65,
            280,
            42
        )

        if skill_id == "basic_attack":
            button_text = "Always Equipped"
            can_select = False
        elif is_equipped:
            button_text = "[ENTER] Unequip"
            can_select = True
        else:
            button_text = "[ENTER] Equip"
            can_select = True

        draw_button(
            surface,
            button_rect,
            button_text,
            self.small_font,
            is_selected=can_select
        )

    def _get_loadout_summary(self):
        names = [
            SkillLibrary.get_skill_name(skill_id)
            for skill_id in self.session.skill_loadout
        ]

        return (
            f"Current Loadout "
            f"({len(self.session.skill_loadout)}/{SkillLibrary.MAX_LOADOUT_SIZE}): "
            + ", ".join(names)
        )

    def _draw_wrapped_text(self, surface, text, font, color, x, y, max_width, line_height):
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