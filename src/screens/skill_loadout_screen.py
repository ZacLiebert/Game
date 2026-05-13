"""Combat skill loadout screen."""

import pygame

from src.screens.base_screen import BaseScreen
from src.core.skill_library import SkillLibrary

from src.ui.theme import UITheme
from src.ui.fonts import get_font
from src.ui.widgets import draw_panel, draw_text, draw_button


class SkillLoadoutScreen(BaseScreen):
    """Screen for choosing Zac's equipped combat skills."""

    def __init__(self, screen_manager):
        """Set up initial state."""
        super().__init__(screen_manager)
        self.music_track = "map"

        self.title_font = get_font(UITheme.HEADER_SIZE, bold=True)
        self.font = get_font(UITheme.BODY_SIZE, bold=True)
        self.small_font = get_font(UITheme.SMALL_SIZE, bold=False)
        self.tiny_font = get_font(max(16, UITheme.SMALL_SIZE - 4), bold=False)

        self.session = self.screen_manager.game_session
        self.selected_index = 0
        self.status_msg = "Choose up to 4 skills for Zac before combat."

        self.available_skill_ids = []
        self._refresh()

    def _refresh(self):
        """Refresh the screen data from the current game state."""
        self.available_skill_ids = SkillLibrary.get_available_skill_ids(
            self.session.mutation_tree
        )

        self.session.skill_loadout = SkillLibrary.sanitize_loadout(
            self.session.skill_loadout,
            self.session.mutation_tree
        )

        if self.selected_index >= len(self.available_skill_ids):
            self.selected_index = max(0, len(self.available_skill_ids) - 1)

    # Input

    def handle_event(self, event):
        """Handle the event."""
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.play_sfx("click")
                self.screen_manager.pop()

            elif event.key == pygame.K_UP:
                self.play_sfx("click")
                self.selected_index = max(0, self.selected_index - 1)

            elif event.key == pygame.K_DOWN:
                self.play_sfx("click")
                if self.available_skill_ids:
                    self.selected_index = min(
                        len(self.available_skill_ids) - 1,
                        self.selected_index + 1
                    )

            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._toggle_selected_skill()

    def _toggle_selected_skill(self):
        """Equip or remove the selected skill."""
        if not self.available_skill_ids:
            return

        skill_id = self.available_skill_ids[self.selected_index]
        loadout = self.session.skill_loadout

        if skill_id == "basic_attack":
            self.play_sfx("error")
            self.status_msg = "Basic Attack is always equipped."
            return

        if skill_id in loadout:
            loadout.remove(skill_id)
            self.play_sfx("click")
            self.status_msg = f"Unequipped {SkillLibrary.get_skill_name(skill_id)}."

        else:
            if len(loadout) >= SkillLibrary.MAX_LOADOUT_SIZE:
                self.play_sfx("error")
                self.status_msg = "Loadout full. Unequip another skill first."
                return

            loadout.append(skill_id)
            self.play_sfx("success")
            self.status_msg = f"Equipped {SkillLibrary.get_skill_name(skill_id)}."

        self.session.skill_loadout = SkillLibrary.sanitize_loadout(
            loadout,
            self.session.mutation_tree
        )

        self._refresh()

    def update(self):
        """Update this screen for the current frame."""
        pass

    # Drawing

    def draw(self, surface):
        """Draw this screen."""
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        surface.fill(UITheme.BG)

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
        hint = self._fit_text_to_width(
            hint,
            self.small_font,
            header_rect.width - 470
        )

        draw_text(
            surface,
            hint,
            self.small_font,
            UITheme.TEXT_DIM,
            header_rect.x + 430,
            header_rect.y + 30
        )

        loadout_rect = pygame.Rect(30, 120, screen_w - 60, 55)

        draw_panel(
            surface,
            loadout_rect,
            color=UITheme.PANEL_DARK,
            border_color=UITheme.ACCENT_DARK
        )

        loadout_names = [
            SkillLibrary.get_skill_name(skill_id)
            for skill_id in self.session.skill_loadout
        ]

        loadout_text = (
            f"Equipped ({len(loadout_names)}/{SkillLibrary.MAX_LOADOUT_SIZE}): "
            + ", ".join(loadout_names)
        )

        loadout_text = self._fit_text_to_width(
            loadout_text,
            self.small_font,
            loadout_rect.width - 40
        )

        draw_text(
            surface,
            loadout_text,
            self.small_font,
            UITheme.TEXT,
            loadout_rect.x + 20,
            loadout_rect.y + 17
        )

        list_panel = pygame.Rect(30, 195, 560, screen_h - 240)
        detail_panel = pygame.Rect(615, 195, screen_w - 645, screen_h - 240)

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
            list_panel.x + 20,
            list_panel.y + 18
        )

        draw_text(
            surface,
            "Skill Details",
            self.font,
            UITheme.ACCENT_GOLD,
            detail_panel.x + 20,
            detail_panel.y + 18
        )

        self._draw_skill_list(surface, list_panel)
        self._draw_skill_details(surface, detail_panel)

        if "Equipped" in self.status_msg or "Unequipped" in self.status_msg:
            status_color = UITheme.SUCCESS
        elif "full" in self.status_msg.lower() or "always" in self.status_msg.lower():
            status_color = UITheme.WARNING
        else:
            status_color = UITheme.TEXT_DIM

        status_text = self._fit_text_to_width(
            self.status_msg,
            self.small_font,
            screen_w - 70
        )

        draw_text(
            surface,
            status_text,
            self.small_font,
            status_color,
            35,
            screen_h - 35
        )

    def _draw_skill_list(self, surface, panel_rect):
        """Draw the available skill list."""
        if not self.available_skill_ids:
            draw_text(
                surface,
                "No skills available.",
                self.small_font,
                UITheme.TEXT_DIM,
                panel_rect.x + 20,
                panel_rect.y + 70
            )
            return

        row_height = 46
        row_gap = 8
        top_y = panel_rect.y + 70
        bottom_limit = panel_rect.bottom - 22
        available_height = bottom_limit - top_y

        visible_rows = max(1, available_height // (row_height + row_gap))
        visible_rows = min(visible_rows, len(self.available_skill_ids))

        start_index = max(0, self.selected_index - visible_rows + 1)
        max_start = max(0, len(self.available_skill_ids) - visible_rows)
        start_index = min(start_index, max_start)
        end_index = min(len(self.available_skill_ids), start_index + visible_rows)

        y = top_y

        for i in range(start_index, end_index):
            skill_id = self.available_skill_ids[i]
            selected = i == self.selected_index
            equipped = skill_id in self.session.skill_loadout

            row_rect = pygame.Rect(
                panel_rect.x + 18,
                y,
                panel_rect.width - 36,
                row_height
            )

            if selected:
                draw_panel(
                    surface,
                    row_rect,
                    color=UITheme.PANEL_LIGHT,
                    border_color=UITheme.ACCENT
                )
            else:
                draw_panel(
                    surface,
                    row_rect,
                    color=UITheme.PANEL_DARK,
                    border_color=(55, 65, 80)
                )

            skill_name = SkillLibrary.get_skill_name(skill_id)
            skill_name = self._fit_text_to_width(
                skill_name,
                self.small_font,
                row_rect.width - 160
            )

            draw_text(
                surface,
                skill_name,
                self.small_font,
                UITheme.TEXT if selected else UITheme.TEXT_DIM,
                row_rect.x + 14,
                row_rect.y + 12
            )

            if equipped:
                status_text = "EQUIPPED"
                status_color = UITheme.SUCCESS
            else:
                status_text = "AVAILABLE"
                status_color = UITheme.TEXT_DIM

            status_surface = self.small_font.render(
                status_text,
                True,
                status_color
            )

            surface.blit(
                status_surface,
                (
                    row_rect.right - status_surface.get_width() - 14,
                    row_rect.y + 12
                )
            )

            y += row_height + row_gap

        if len(self.available_skill_ids) > visible_rows:
            scroll_text = f"Showing {start_index + 1}-{end_index} of {len(self.available_skill_ids)}"

            draw_text(
                surface,
                scroll_text,
                self.tiny_font,
                UITheme.TEXT_DIM,
                panel_rect.x + 20,
                panel_rect.bottom - 24
            )

    def _draw_skill_details(self, surface, panel_rect):
        """Draw details for the selected skill."""
        if not self.available_skill_ids:
            draw_text(
                surface,
                "Select a skill to view details.",
                self.small_font,
                UITheme.TEXT_DIM,
                panel_rect.x + 20,
                panel_rect.y + 70
            )
            return

        skill_id = self.available_skill_ids[self.selected_index]
        skill_name = SkillLibrary.get_skill_name(skill_id)
        skill_info = SkillLibrary.get_skill_info(skill_id)

        x = panel_rect.x + 24
        y = panel_rect.y + 70
        max_width = panel_rect.width - 48

        divider_y = panel_rect.bottom - 140
        button_y = panel_rect.bottom - 58
        content_bottom_limit = divider_y - 18

        title_text = self._fit_text_to_width(
            skill_name,
            self.font,
            max_width
        )

        draw_text(
            surface,
            title_text,
            self.font,
            UITheme.TEXT,
            x,
            y
        )

        y += 48

        if skill_id in self.session.skill_loadout:
            badge_text = "EQUIPPED"
            badge_color = UITheme.SUCCESS
        else:
            badge_text = "AVAILABLE"
            badge_color = UITheme.ACCENT_GOLD

        badge_rect = pygame.Rect(x, y, 180, 38)

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
            badge_rect.x + 18,
            badge_rect.y + 8
        )

        y += 58

        y = self._draw_detail_section(
            surface,
            title="Description",
            value=skill_info.get("description", "No description available."),
            value_color=UITheme.TEXT_DIM,
            x=x,
            y=y,
            max_width=max_width,
            max_bottom=content_bottom_limit
        )

        y = self._draw_detail_section(
            surface,
            title="Effect",
            value=skill_info.get("effect", "No effect information available."),
            value_color=UITheme.TEXT_DIM,
            x=x,
            y=y,
            max_width=max_width,
            max_bottom=content_bottom_limit
        )

        pygame.draw.line(
            surface,
            (55, 65, 80),
            (x, divider_y),
            (panel_rect.right - 24, divider_y),
            1
        )

        if skill_id == "basic_attack":
            button_text = "Basic Attack is always equipped"
            can_toggle = False
        elif skill_id in self.session.skill_loadout:
            button_text = "[ENTER] Unequip Skill"
            can_toggle = True
        else:
            button_text = "[ENTER] Equip Skill"
            can_toggle = len(self.session.skill_loadout) < SkillLibrary.MAX_LOADOUT_SIZE

        helper_text = "SPACE also toggles selected skill"
        helper_text = self._fit_text_to_width(
            helper_text,
            self.small_font,
            max_width
        )

        draw_text(
            surface,
            helper_text,
            self.small_font,
            UITheme.TEXT_DIM,
            x,
            divider_y + 18
        )

        button_rect = pygame.Rect(
            x,
            button_y,
            max_width,
            40
        )

        draw_button(
            surface,
            button_rect,
            button_text,
            self.small_font,
            is_selected=can_toggle
        )

    # Text helpers

    def _draw_detail_section(
        self,
        surface,
        title,
        value,
        value_color,
        x,
        y,
        max_width,
        max_bottom
    ):
        """Draw one titled detail section."""
        title_height = 24
        line_height = 23
        gap_after_title = 25
        gap_after_value = 18

        if y + title_height + line_height > max_bottom:
            return y

        draw_text(
            surface,
            title,
            self.small_font,
            UITheme.ACCENT,
            x,
            y
        )

        y += gap_after_title

        y = self._draw_wrapped_text_clamped(
            surface,
            value,
            self.small_font,
            value_color,
            x,
            y,
            max_width,
            line_height,
            max_bottom
        )

        y += gap_after_value

        return y

    def _draw_wrapped_text_clamped(
        self,
        surface,
        text,
        font,
        color,
        x,
        y,
        max_width,
        line_height,
        max_bottom
    ):
        """Draw wrapped text without passing the bottom limit."""
        words = str(text).split(" ")
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            test_surface = font.render(test_line, True, color)

            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    if y + line_height > max_bottom:
                        return y

                    line_surface = font.render(current_line, True, color)
                    surface.blit(line_surface, (x, y))
                    y += line_height

                current_line = word + " "

        if current_line and y + line_height <= max_bottom:
            line_surface = font.render(current_line, True, color)
            surface.blit(line_surface, (x, y))
            y += line_height

        return y

    def _fit_text_to_width(self, text, font, max_width):
        """Shorten text so it fits inside a width."""
        text = str(text)

        if font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."

        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]

        return text + ellipsis
