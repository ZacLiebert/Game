import pygame

from src.screens.base_screen import BaseScreen
from src.ui.theme import UITheme
from src.ui.fonts import get_font
from src.ui.widgets import draw_panel, draw_text, draw_button


class InventoryScreen(BaseScreen):
    """
    Inventory UI screen.

    Fixed:
    - No text beside button.
    - Detail content cannot overlap Zac status / button.
    - Long text is shortened or clamped.
    - Item list scrolls safely based on panel height.
    """

    def __init__(self, screen_manager):
        super().__init__(screen_manager)

        self.title_font = get_font(UITheme.HEADER_SIZE, bold=True)
        self.font = get_font(UITheme.BODY_SIZE, bold=True)
        self.small_font = get_font(UITheme.SMALL_SIZE, bold=False)
        self.tiny_font = get_font(max(16, UITheme.SMALL_SIZE - 4), bold=False)

        self.inv_manager = self.screen_manager.game_session.inventory

        self.search_query = ""
        self.display_items = self.inv_manager.search_items("")

        self.selected_index = 0
        self.status_msg = "Type to search | TAB: Sort | ENTER: Use | ESC: Back"

    # ============================================================
    # INPUT
    # ============================================================

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.screen_manager.pop()

            elif event.key == pygame.K_TAB:
                self.inv_manager.sort_by_name()
                self._refresh_display()
                self.status_msg = "Inventory sorted by item name using Quick Sort."

            elif event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)

            elif event.key == pygame.K_DOWN:
                if self.display_items:
                    self.selected_index = min(
                        len(self.display_items) - 1,
                        self.selected_index + 1
                    )

            elif event.key == pygame.K_RETURN:
                self._use_selected_item()

            elif event.key == pygame.K_BACKSPACE:
                self.search_query = self.search_query[:-1]
                self._refresh_display()

            elif event.key == pygame.K_DELETE:
                self.search_query = ""
                self._refresh_display()
                self.status_msg = "Search cleared."

            elif event.unicode and event.unicode.isprintable():
                self.search_query += event.unicode
                self._refresh_display()

    def _use_selected_item(self):
        """
        Uses the selected item if it is a consumable potion.
        """
        if not self.display_items:
            self.status_msg = "No item selected."
            return

        item = self.display_items[self.selected_index]
        session = self.screen_manager.game_session
        zac = session.party[0]

        if item.item_type == "potion":
            item.apply_effect(zac)

            if hasattr(zac, "max_hp"):
                zac.current_hp = min(zac.current_hp, zac.max_hp)

            self.inv_manager.remove_item_by_id(item.item_id)
            self._refresh_display()

            self.status_msg = f"Used {item.name}. Zac HP: {zac.current_hp}/{zac.max_hp}"
        else:
            self.status_msg = f"{item.name} is a {item.item_type}, not a usable item."

    def _refresh_display(self):
        self.display_items = self.inv_manager.search_items(self.search_query)

        if self.selected_index >= len(self.display_items):
            self.selected_index = max(0, len(self.display_items) - 1)

    def update(self):
        pass

    # ============================================================
    # DRAW
    # ============================================================

    def draw(self, surface):
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
            "INVENTORY",
            self.title_font,
            UITheme.ACCENT,
            header_rect.x + 25,
            header_rect.y + 18
        )

        hint = "UP/DOWN: Select   ENTER: Use   TAB: Sort   DELETE: Clear Search   ESC: Back"
        hint = self._fit_text_to_width(
            hint,
            self.small_font,
            header_rect.width - 360
        )

        draw_text(
            surface,
            hint,
            self.small_font,
            UITheme.TEXT_DIM,
            header_rect.x + 270,
            header_rect.y + 28
        )

        search_rect = pygame.Rect(30, 120, screen_w - 60, 55)

        draw_panel(
            surface,
            search_rect,
            color=(20, 26, 36),
            border_color=UITheme.ACCENT_DARK
        )

        search_text = f"Search: {self.search_query}_"
        search_text = self._fit_text_to_width(
            search_text,
            self.font,
            search_rect.width - 330
        )

        draw_text(
            surface,
            search_text,
            self.font,
            UITheme.TEXT,
            search_rect.x + 20,
            search_rect.y + 14
        )

        result_text = (
            f"{len(self.display_items)} type(s), "
            f"{self.inv_manager.get_total_item_count()} total item(s)"
        )

        result_text = self._fit_text_to_width(
            result_text,
            self.small_font,
            300
        )

        result_surface = self.small_font.render(
            result_text,
            True,
            UITheme.TEXT_DIM
        )

        surface.blit(
            result_surface,
            (
                search_rect.right - result_surface.get_width() - 20,
                search_rect.y + 18
            )
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
            "Item List",
            self.font,
            UITheme.ACCENT_GOLD,
            list_panel.x + 20,
            list_panel.y + 18
        )

        draw_text(
            surface,
            "Item Details",
            self.font,
            UITheme.ACCENT_GOLD,
            detail_panel.x + 20,
            detail_panel.y + 18
        )

        self._draw_item_list(surface, list_panel)
        self._draw_item_details(surface, detail_panel)

        status_rect = pygame.Rect(30, screen_h - 35, screen_w - 60, 25)

        if "Used" in self.status_msg or "sorted" in self.status_msg:
            status_color = UITheme.SUCCESS
        elif "not" in self.status_msg or "No item" in self.status_msg:
            status_color = UITheme.WARNING
        else:
            status_color = UITheme.TEXT_DIM

        status_text = self._fit_text_to_width(
            self.status_msg,
            self.small_font,
            status_rect.width
        )

        draw_text(
            surface,
            status_text,
            self.small_font,
            status_color,
            status_rect.x,
            status_rect.y
        )

    def _draw_item_list(self, surface, panel_rect):
        if not self.display_items:
            draw_text(
                surface,
                "No items match your search.",
                self.small_font,
                UITheme.TEXT_DIM,
                panel_rect.x + 20,
                panel_rect.y + 70
            )
            return

        row_height = 42
        row_gap = 8
        top_y = panel_rect.y + 70
        bottom_limit = panel_rect.bottom - 22
        available_height = bottom_limit - top_y

        visible_rows = max(1, available_height // (row_height + row_gap))
        visible_rows = min(visible_rows, len(self.display_items))

        start_index = max(0, self.selected_index - visible_rows + 1)
        max_start = max(0, len(self.display_items) - visible_rows)
        start_index = min(start_index, max_start)

        end_index = min(len(self.display_items), start_index + visible_rows)

        y = top_y

        for i in range(start_index, end_index):
            item = self.display_items[i]
            selected = i == self.selected_index
            count = self.inv_manager.get_item_count(item.item_id)

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

            item_label = f"> {item.name} x{count}"
            item_label = self._fit_text_to_width(
                item_label,
                self.small_font,
                row_rect.width - 145
            )

            draw_text(
                surface,
                item_label,
                self.small_font,
                UITheme.TEXT if selected else UITheme.TEXT_DIM,
                row_rect.x + 14,
                row_rect.y + 10
            )

            type_text = str(item.item_type).upper()
            type_text = self._fit_text_to_width(
                type_text,
                self.small_font,
                110
            )

            type_surface = self.small_font.render(
                type_text,
                True,
                UITheme.ACCENT_GOLD
            )

            surface.blit(
                type_surface,
                (
                    row_rect.right - type_surface.get_width() - 14,
                    row_rect.y + 10
                )
            )

            y += row_height + row_gap

        if len(self.display_items) > visible_rows:
            scroll_text = f"Showing {start_index + 1}-{end_index} of {len(self.display_items)}"

            draw_text(
                surface,
                scroll_text,
                self.tiny_font,
                UITheme.TEXT_DIM,
                panel_rect.x + 20,
                panel_rect.bottom - 24
            )

    def _draw_item_details(self, surface, panel_rect):
        if not self.display_items:
            draw_text(
                surface,
                "Select an item to view details.",
                self.small_font,
                UITheme.TEXT_DIM,
                panel_rect.x + 20,
                panel_rect.y + 70
            )
            return

        item = self.display_items[self.selected_index]
        count = self.inv_manager.get_item_count(item.item_id)
        session = self.screen_manager.game_session
        zac = session.party[0]

        x = panel_rect.x + 24
        y = panel_rect.y + 70
        max_width = panel_rect.width - 48

        divider_y = panel_rect.bottom - 160
        zac_box_y = divider_y + 16
        button_y = panel_rect.bottom - 64
        content_bottom_limit = divider_y - 18

        name_text = f"{item.name} x{count}"
        name_text = self._fit_text_to_width(
            name_text,
            self.font,
            max_width
        )

        draw_text(
            surface,
            name_text,
            self.font,
            UITheme.TEXT,
            x,
            y
        )

        y += 52

        type_rect = pygame.Rect(x, y, 170, 38)

        draw_panel(
            surface,
            type_rect,
            color=UITheme.PANEL_DARK,
            border_color=UITheme.ACCENT_DARK
        )

        draw_text(
            surface,
            str(item.item_type).upper(),
            self.small_font,
            UITheme.ACCENT_GOLD,
            type_rect.x + 18,
            type_rect.y + 8
        )

        y += 58

        y = self._draw_detail_section(
            surface,
            title="Description",
            value=item.description,
            value_color=UITheme.TEXT_DIM,
            x=x,
            y=y,
            max_width=max_width,
            max_bottom=content_bottom_limit
        )

        if item.item_type == "potion":
            heal_amount = getattr(item, "heal_amount", 0)

            if heal_amount > 0:
                effect = f"Heals {heal_amount} HP."
            else:
                effect = "Consumable item."
        elif item.item_type == "material":
            effect = "Used as mutation material."
        else:
            effect = "No direct effect."

        self._draw_detail_section(
            surface,
            title="Effect",
            value=effect,
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

        zac_box_rect = pygame.Rect(
            x,
            zac_box_y,
            max_width,
            74
        )

        draw_panel(
            surface,
            zac_box_rect,
            color=UITheme.PANEL_DARK,
            border_color=(55, 65, 80)
        )

        draw_text(
            surface,
            "Zac Status",
            self.small_font,
            UITheme.ACCENT_GOLD,
            zac_box_rect.x + 16,
            zac_box_rect.y + 10
        )

        zac_text = (
            f"HP {zac.current_hp}/{zac.max_hp}   "
            f"ATK {zac.attack}   DEF {zac.defense}   SPD {zac.speed}"
        )

        zac_text = self._fit_text_to_width(
            zac_text,
            self.small_font,
            zac_box_rect.width - 32
        )

        draw_text(
            surface,
            zac_text,
            self.small_font,
            UITheme.TEXT,
            zac_box_rect.x + 16,
            zac_box_rect.y + 40
        )

        button_rect = pygame.Rect(
            x,
            button_y,
            max_width,
            42
        )

        if item.item_type == "potion":
            button_text = "[ENTER] Use Item"
            can_use = True
        else:
            button_text = "Materials cannot be used here"
            can_use = False

        draw_button(
            surface,
            button_rect,
            button_text,
            self.small_font,
            is_selected=can_use
        )

    # ============================================================
    # TEXT HELPERS
    # ============================================================

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
        text = str(text)

        if font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."

        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]

        return text + ellipsis