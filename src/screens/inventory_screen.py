import pygame

from src.screens.base_screen import BaseScreen
from src.ui.theme import UITheme
from src.ui.widgets import draw_panel, draw_text, draw_button


class InventoryScreen(BaseScreen):
    """
    Inventory UI screen.

    Now displays item quantities:
    - Rabbit Foot x3
    - Small Health Potion x2
    """

    def __init__(self, screen_manager):
        super().__init__(screen_manager)

        self.title_font = pygame.font.SysFont(None, UITheme.HEADER_SIZE)
        self.font = pygame.font.SysFont(None, UITheme.BODY_SIZE)
        self.small_font = pygame.font.SysFont(None, UITheme.SMALL_SIZE)

        self.inv_manager = self.screen_manager.game_session.inventory

        self.search_query = ""
        self.display_items = self.inv_manager.search_items("")

        self.selected_index = 0
        self.status_msg = "Type to search | TAB: Sort | ENTER: Use | ESC: Back"

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
            self.status_msg = f"{item.name} is a {item.item_type}, not a consumable item."

    def _refresh_display(self):
        self.display_items = self.inv_manager.search_items(self.search_query)

        if self.selected_index >= len(self.display_items):
            self.selected_index = max(0, len(self.display_items) - 1)

    def update(self):
        pass

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

        result_surf = self.small_font.render(result_text, True, UITheme.TEXT_DIM)

        surface.blit(
            result_surf,
            (
                search_rect.right - result_surf.get_width() - 20,
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

        draw_text(
            surface,
            self.status_msg,
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
                panel_rect.x + 25,
                panel_rect.y + 80
            )
            return

        row_height = 52
        visible_rows = 7

        start_index = max(0, self.selected_index - visible_rows + 1)
        end_index = min(len(self.display_items), start_index + visible_rows)

        y = panel_rect.y + 65

        for i in range(start_index, end_index):
            item = self.display_items[i]
            is_selected = i == self.selected_index
            count = self.inv_manager.get_item_count(item.item_id)

            row_rect = pygame.Rect(
                panel_rect.x + 18,
                y,
                panel_rect.width - 36,
                row_height - 8
            )

            if is_selected:
                draw_panel(
                    surface,
                    row_rect,
                    color=UITheme.PANEL_LIGHT,
                    border_color=UITheme.ACCENT
                )
                text_color = UITheme.TEXT
            else:
                draw_panel(
                    surface,
                    row_rect,
                    color=UITheme.PANEL_DARK,
                    border_color=(45, 55, 70)
                )
                text_color = UITheme.TEXT_DIM

            prefix = ">" if is_selected else " "
            item_name = f"{prefix} {item.name} x{count}"

            draw_text(
                surface,
                item_name,
                self.small_font,
                text_color,
                row_rect.x + 15,
                row_rect.y + 8
            )

            item_type = item.item_type.upper()
            type_surf = self.small_font.render(item_type, True, UITheme.ACCENT_GOLD)

            surface.blit(
                type_surf,
                (
                    row_rect.right - type_surf.get_width() - 15,
                    row_rect.y + 8
                )
            )

            y += row_height

        if len(self.display_items) > visible_rows:
            scroll_text = f"Showing {start_index + 1}-{end_index} of {len(self.display_items)}"

            draw_text(
                surface,
                scroll_text,
                self.small_font,
                UITheme.TEXT_DIM,
                panel_rect.x + 25,
                panel_rect.bottom - 35
            )

    def _draw_item_details(self, surface, panel_rect):
        if not self.display_items:
            draw_text(
                surface,
                "Select an item to view details.",
                self.small_font,
                UITheme.TEXT_DIM,
                panel_rect.x + 25,
                panel_rect.y + 80
            )
            return

        item = self.display_items[self.selected_index]
        count = self.inv_manager.get_item_count(item.item_id)

        x = panel_rect.x + 25
        y = panel_rect.y + 70

        draw_text(
            surface,
            f"{item.name} x{count}",
            self.font,
            UITheme.TEXT,
            x,
            y
        )

        y += 45

        type_rect = pygame.Rect(x, y, 170, 38)

        draw_panel(
            surface,
            type_rect,
            color=UITheme.PANEL_DARK,
            border_color=UITheme.ACCENT_DARK
        )

        draw_text(
            surface,
            item.item_type.upper(),
            self.small_font,
            UITheme.ACCENT_GOLD,
            type_rect.x + 15,
            type_rect.y + 9
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
            item.description,
            self.small_font,
            UITheme.TEXT_DIM,
            x,
            y,
            panel_rect.width - 50,
            26
        )

        y += 80

        draw_text(
            surface,
            "Effect",
            self.small_font,
            UITheme.ACCENT,
            x,
            y
        )

        y += 32

        if item.item_type == "potion":
            effect_text = f"Heals {item.heal_amount} HP."
            action_text = "Press ENTER to use one potion on Zac."
            can_use = True

        elif item.item_type == "material":
            effect_text = "Used as a mutation material."
            action_text = "Open Mutation Screen to use this material."
            can_use = False

        else:
            effect_text = "No direct effect."
            action_text = "This item cannot be consumed."
            can_use = False

        draw_text(
            surface,
            effect_text,
            self.small_font,
            UITheme.TEXT_DIM,
            x,
            y
        )

        session = self.screen_manager.game_session
        zac = session.party[0]

        stat_panel = pygame.Rect(
            x,
            panel_rect.bottom - 145,
            panel_rect.width - 50,
            75
        )

        draw_panel(
            surface,
            stat_panel,
            color=UITheme.PANEL_DARK,
            border_color=(45, 55, 70)
        )

        draw_text(
            surface,
            "Zac Status",
            self.small_font,
            UITheme.ACCENT_GOLD,
            stat_panel.x + 15,
            stat_panel.y + 10
        )

        draw_text(
            surface,
            f"HP {zac.current_hp}/{zac.max_hp}   ATK {zac.attack}   DEF {zac.defense}   SPD {zac.speed}",
            self.small_font,
            UITheme.TEXT_DIM,
            stat_panel.x + 15,
            stat_panel.y + 40
        )

        button_rect = pygame.Rect(
            x,
            panel_rect.bottom - 55,
            260,
            40
        )

        draw_button(
            surface,
            button_rect,
            "[ENTER] Use Item" if can_use else "Not Consumable",
            self.small_font,
            is_selected=can_use
        )

        draw_text(
            surface,
            action_text,
            self.small_font,
            UITheme.TEXT_DIM,
            button_rect.right + 25,
            button_rect.y + 10
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