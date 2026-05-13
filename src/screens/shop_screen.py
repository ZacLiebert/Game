"""Shop screen."""

import pygame

from src.screens.base_screen import BaseScreen
from src.ui.theme import UITheme
from src.ui.fonts import get_font
from src.ui.widgets import draw_panel, draw_text, draw_button


class ShopScreen(BaseScreen):
    """Shop screen for buying and selling items."""

    MODE_BUY = "BUY"
    MODE_SELL = "SELL"

    def __init__(self, screen_manager, npc):
        """Set up initial state."""
        super().__init__(screen_manager)
        self.music_track = "map"

        self.npc = npc
        self.session = self.screen_manager.game_session
        self.db = self.session.db
        self.inventory = self.session.inventory

        self.title_font = get_font(UITheme.HEADER_SIZE, bold=True)
        self.font = get_font(UITheme.BODY_SIZE, bold=True)
        self.small_font = get_font(UITheme.SMALL_SIZE)
        self.tiny_font = get_font(max(16, UITheme.SMALL_SIZE - 4))

        self.mode = self.MODE_BUY
        self.selected_index = 0
        self.status_msg = (
            "Rhea: Med Kits heal, Serums boost stats, Revive Shots restore fallen allies."
        )

        self.shop_items = self._load_shop_items()
        self.display_items = []
        self._refresh_display_items()

    # Data helpers

    def _load_shop_items(self):
        """Load the shop items."""
        items = []

        for item_id in getattr(self.npc, "shop_items", []):
            item = self.db.get_item(item_id)

            if item:
                items.append(item)

        return items

    def _refresh_display_items(self):
        """Refresh the item list for the current shop mode."""
        if self.mode == self.MODE_BUY:
            self.display_items = self.shop_items
        else:
            self.display_items = self.inventory.get_unique_items()

        if self.selected_index >= len(self.display_items):
            self.selected_index = max(0, len(self.display_items) - 1)

    def _get_selected_item(self):
        """Return the currently selected item."""
        if not self.display_items:
            return None

        if self.selected_index < 0 or self.selected_index >= len(self.display_items):
            return None

        return self.display_items[self.selected_index]

    def _switch_mode(self):
        """Switch between buy and sell mode."""
        if self.mode == self.MODE_BUY:
            self.mode = self.MODE_SELL
            self.status_msg = "Sell mode: choose an item from inventory."
        else:
            self.mode = self.MODE_BUY
            self.status_msg = "Buy mode: choose an item from the merchant."

        self.selected_index = 0
        self._refresh_display_items()

    # Input

    def handle_event(self, event):
        """Handle the event."""
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            self.play_sfx("click")
            self.screen_manager.pop()
            return

        elif event.key in (pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT):
            self.play_sfx("click")
            self._switch_mode()
            return

        elif event.key == pygame.K_UP:
            self.play_sfx("click")
            self.selected_index = max(0, self.selected_index - 1)

        elif event.key == pygame.K_DOWN:
            self.play_sfx("click")
            if self.display_items:
                self.selected_index = min(
                    len(self.display_items) - 1,
                    self.selected_index + 1
                )

        elif event.key == pygame.K_RETURN:
            if self.mode == self.MODE_BUY:
                self._buy_selected_item()
            else:
                self._sell_selected_item()

    # Shop actions

    def _buy_selected_item(self):
        """Buy the selected shop item if possible."""
        item = self._get_selected_item()

        if not item:
            self.play_sfx("error")
            self.status_msg = "No item selected."
            return

        price = getattr(item, "buy_price", 0)

        if price <= 0:
            self.play_sfx("error")
            self.status_msg = f"{item.name} cannot be bought."
            return

        if self.session.gold < price:
            self.play_sfx("error")
            self.status_msg = f"Not enough gold. Need {price}G."
            return

        self.session.gold -= price
        self.inventory.add_item(item)

        self.play_sfx("success")
        self.status_msg = f"Bought {item.name} for {price}G."

    def _sell_selected_item(self):
        """Sell the selected inventory item if possible."""
        item = self._get_selected_item()

        if not item:
            self.play_sfx("error")
            self.status_msg = "No item selected."
            return

        price = getattr(item, "sell_price", 0)

        if price <= 0:
            self.play_sfx("error")
            self.status_msg = f"{item.name} cannot be sold."
            return

        removed = self.inventory.remove_item_by_id(item.item_id)

        if not removed:
            self.play_sfx("error")
            self.status_msg = f"You do not have {item.name}."
            self._refresh_display_items()
            return

        self.session.gold += price
        self.play_sfx("success")
        self.status_msg = f"Sold {item.name} for {price}G."

        self._refresh_display_items()

    # Update

    def update(self):
        """Update this screen for the current frame."""
        pass

    # Drawing

    def draw(self, surface):
        """Draw this screen."""
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        surface.fill(UITheme.BG)

        header_rect = pygame.Rect(30, 25, screen_w - 60, 82)
        tab_rect = pygame.Rect(30, 122, screen_w - 60, 62)

        list_panel = pygame.Rect(30, 205, 560, screen_h - 265)
        detail_panel = pygame.Rect(615, 205, screen_w - 645, screen_h - 265)

        status_rect = pygame.Rect(30, screen_h - 48, screen_w - 60, 34)

        # Header
        draw_panel(
            surface,
            header_rect,
            color=UITheme.PANEL_DARK,
            border_color=UITheme.ACCENT
        )

        draw_text(
            surface,
            f"{self.npc.name.upper()} SHOP",
            self.title_font,
            UITheme.ACCENT_GOLD,
            header_rect.x + 24,
            header_rect.y + 18
        )

        gold_text = f"Gold: {self.session.gold}G"
        gold_surface = self.font.render(gold_text, True, UITheme.ACCENT_GOLD)

        surface.blit(
            gold_surface,
            (
                header_rect.right - gold_surface.get_width() - 28,
                header_rect.y + 26
            )
        )

        # Mode tabs
        draw_panel(
            surface,
            tab_rect,
            color=UITheme.PANEL,
            border_color=UITheme.ACCENT_DARK
        )

        buy_button = pygame.Rect(tab_rect.x + 20, tab_rect.y + 12, 180, 38)
        sell_button = pygame.Rect(tab_rect.x + 215, tab_rect.y + 12, 180, 38)

        draw_button(
            surface,
            buy_button,
            "BUY",
            self.small_font,
            is_selected=self.mode == self.MODE_BUY
        )

        draw_button(
            surface,
            sell_button,
            "SELL",
            self.small_font,
            is_selected=self.mode == self.MODE_SELL
        )

        hint = "TAB / LEFT / RIGHT: Switch mode    UP / DOWN: Select    ENTER: Confirm    ESC: Back"
        hint = self._fit_text_to_width(hint, self.small_font, tab_rect.width - 430)

        draw_text(
            surface,
            hint,
            self.small_font,
            UITheme.TEXT_DIM,
            tab_rect.x + 420,
            tab_rect.y + 19
        )

        # Panels
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

        list_title = "Merchant Items" if self.mode == self.MODE_BUY else "Your Inventory"

        draw_text(
            surface,
            list_title,
            self.font,
            UITheme.ACCENT,
            list_panel.x + 22,
            list_panel.y + 20
        )

        draw_text(
            surface,
            "Details",
            self.font,
            UITheme.ACCENT,
            detail_panel.x + 22,
            detail_panel.y + 20
        )

        self._draw_item_list(surface, list_panel)
        self._draw_item_details(surface, detail_panel)

        # Status
        draw_panel(
            surface,
            status_rect,
            color=UITheme.PANEL_DARK,
            border_color=UITheme.ACCENT_DARK
        )

        status_color = UITheme.TEXT_DIM

        if "bought" in self.status_msg.lower() or "sold" in self.status_msg.lower():
            status_color = UITheme.SUCCESS
        elif "not enough" in self.status_msg.lower() or "cannot" in self.status_msg.lower():
            status_color = UITheme.WARNING

        draw_text(
            surface,
            self._fit_text_to_width(self.status_msg, self.small_font, status_rect.width - 24),
            self.small_font,
            status_color,
            status_rect.x + 12,
            status_rect.y + 7
        )

    def _draw_item_list(self, surface, panel_rect):
        """Draw the item list panel."""
        x = panel_rect.x + 22
        y = panel_rect.y + 70
        row_h = 42
        max_rows = max(1, (panel_rect.height - 95) // row_h)

        if not self.display_items:
            empty_text = "No items available." if self.mode == self.MODE_BUY else "Inventory is empty."

            draw_text(
                surface,
                empty_text,
                self.small_font,
                UITheme.TEXT_DIM,
                x,
                y
            )
            return

        start_index = 0

        if self.selected_index >= max_rows:
            start_index = self.selected_index - max_rows + 1

        visible_items = self.display_items[start_index:start_index + max_rows]

        for offset, item in enumerate(visible_items):
            index = start_index + offset
            row_rect = pygame.Rect(
                panel_rect.x + 14,
                y + offset * row_h,
                panel_rect.width - 28,
                row_h - 6
            )

            is_selected = index == self.selected_index

            if is_selected:
                pygame.draw.rect(
                    surface,
                    UITheme.PANEL_LIGHT,
                    row_rect,
                    border_radius=8
                )

                pygame.draw.rect(
                    surface,
                    UITheme.ACCENT_GOLD,
                    row_rect,
                    2,
                    border_radius=8
                )

            name = self._fit_text_to_width(item.name, self.small_font, 280)

            if self.mode == self.MODE_BUY:
                price = getattr(item, "buy_price", 0)
                price_text = f"{price}G"
            else:
                count = self.inventory.get_item_count(item.item_id)
                price = getattr(item, "sell_price", 0)
                price_text = f"x{count} | {price}G"

            draw_text(
                surface,
                name,
                self.small_font,
                UITheme.TEXT,
                row_rect.x + 12,
                row_rect.y + 7
            )

            price_surface = self.small_font.render(
                price_text,
                True,
                UITheme.ACCENT_GOLD
            )

            surface.blit(
                price_surface,
                (
                    row_rect.right - price_surface.get_width() - 12,
                    row_rect.y + 8
                )
            )

    def _draw_item_details(self, surface, panel_rect):
        """Draw details for the selected item."""
        item = self._get_selected_item()

        x = panel_rect.x + 24
        y = panel_rect.y + 70
        max_width = panel_rect.width - 48

        if not item:
            draw_text(
                surface,
                "Select an item to view details.",
                self.small_font,
                UITheme.TEXT_DIM,
                x,
                y
            )
            return

        draw_text(
            surface,
            item.name,
            self.font,
            UITheme.ACCENT_GOLD,
            x,
            y
        )

        y += 48

        item_type = getattr(item, "item_type", "unknown")
        draw_text(
            surface,
            f"Type: {item_type}",
            self.small_font,
            UITheme.TEXT,
            x,
            y
        )

        y += 34

        if self.mode == self.MODE_BUY:
            price_text = f"Buy Price: {getattr(item, 'buy_price', 0)}G"
        else:
            count = self.inventory.get_item_count(item.item_id)
            price_text = f"Owned: {count}    Sell Price: {getattr(item, 'sell_price', 0)}G"

        draw_text(
            surface,
            price_text,
            self.small_font,
            UITheme.ACCENT_GOLD,
            x,
            y
        )

        y += 42

        draw_text(
            surface,
            "Description:",
            self.small_font,
            UITheme.ACCENT,
            x,
            y
        )

        y += 30

        y = self._draw_wrapped_text(
            surface,
            getattr(item, "description", "No description."),
            self.small_font,
            UITheme.TEXT_DIM,
            x,
            y,
            max_width,
            26
        )

        if getattr(item, "item_type", "") == "potion" and hasattr(item, "get_effect_summary"):
            y += 15
            draw_text(
                surface,
                "Effect:",
                self.small_font,
                UITheme.ACCENT,
                x,
                y
            )
            y += 28
            y = self._draw_wrapped_text(
                surface,
                item.get_effect_summary(),
                self.small_font,
                UITheme.TEXT_DIM,
                x,
                y,
                max_width,
                24
            )

        y += 25

        action_rect = pygame.Rect(
            x,
            panel_rect.bottom - 70,
            max_width,
            45
        )

        if self.mode == self.MODE_BUY:
            action_text = "[ENTER] Buy Item"
        else:
            action_text = "[ENTER] Sell Item"

        draw_button(
            surface,
            action_rect,
            action_text,
            self.small_font,
            is_selected=True
        )

    # Text helpers

    def _draw_wrapped_text(self, surface, text, font, color, x, y, max_width, line_height):
        """Draw text across multiple lines."""
        words = str(text).split(" ")
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            test_surface = font.render(test_line, True, color)

            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    line_surface = font.render(current_line, True, color)
                    surface.blit(line_surface, (x, y))
                    y += line_height

                current_line = word + " "

        if current_line:
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
