import pygame

from src.screens.base_screen import BaseScreen
from src.ui.theme import UITheme
from src.ui.widgets import draw_panel, draw_text, draw_button


class ShopScreen(BaseScreen):
    """
    Buy / Sell shop screen.

    Controls:
    - TAB: switch BUY / SELL mode
    - UP / DOWN: select item
    - ENTER: buy or sell selected item
    - ESC: close shop
    """

    def __init__(self, screen_manager, npc):
        super().__init__(screen_manager)

        self.npc = npc
        self.session = self.screen_manager.game_session
        self.db = self.session.db
        self.inventory = self.session.inventory

        self.mode = "BUY"
        self.selected_index = 0
        self.status_msg = "Welcome to the shop."

        self.title_font = pygame.font.SysFont(None, UITheme.HEADER_SIZE)
        self.font = pygame.font.SysFont(None, UITheme.BODY_SIZE)
        self.small_font = pygame.font.SysFont(None, UITheme.SMALL_SIZE)

    # ============================================================
    # INPUT
    # ============================================================

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.screen_manager.pop()

            elif event.key == pygame.K_TAB:
                self._switch_mode()

            elif event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)

            elif event.key == pygame.K_DOWN:
                items = self._get_display_items()

                if items:
                    self.selected_index = min(
                        len(items) - 1,
                        self.selected_index + 1
                    )

            elif event.key == pygame.K_RETURN:
                if self.mode == "BUY":
                    self._buy_selected_item()
                else:
                    self._sell_selected_item()

    def update(self):
        pass

    # ============================================================
    # SHOP LOGIC
    # ============================================================

    def _switch_mode(self):
        self.mode = "SELL" if self.mode == "BUY" else "BUY"
        self.selected_index = 0
        self.status_msg = f"Switched to {self.mode} mode."

    def _get_display_items(self):
        """
        BUY mode:
            Show items listed in npc.shop_items.

        SELL mode:
            Show unique items in player's inventory.
        """
        if self.mode == "BUY":
            items = []

            for item_id in self.npc.shop_items:
                item = self.db.get_item(item_id)

                if item:
                    items.append(item)

            return items

        return self.inventory.get_unique_items()

    def _buy_selected_item(self):
        items = self._get_display_items()

        if not items:
            self.status_msg = "Nothing to buy."
            return

        item = items[self.selected_index]
        price = getattr(item, "buy_price", 0)

        if price <= 0:
            self.status_msg = f"{item.name} is not for sale."
            return

        if self.session.gold < price:
            self.status_msg = "Not enough gold."
            return

        self.session.gold -= price
        self.inventory.add_item(item)

        self.status_msg = f"Bought {item.name} for {price} gold."

    def _sell_selected_item(self):
        items = self._get_display_items()

        if not items:
            self.status_msg = "You have nothing to sell."
            return

        item = items[self.selected_index]
        price = getattr(item, "sell_price", 0)

        if price <= 0:
            self.status_msg = f"{item.name} cannot be sold."
            return

        removed = self.inventory.remove_item_by_id(item.item_id)

        if removed:
            self.session.gold += price
            self.status_msg = f"Sold {item.name} for {price} gold."
        else:
            self.status_msg = "Item not found."

        items = self._get_display_items()

        if self.selected_index >= len(items):
            self.selected_index = max(0, len(items) - 1)

    # ============================================================
    # DRAW
    # ============================================================

    def draw(self, surface):
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

        panel_rect = pygame.Rect(
            130,
            80,
            screen_w - 260,
            screen_h - 160
        )

        draw_panel(
            surface,
            panel_rect,
            color=UITheme.PANEL_DARK,
            border_color=UITheme.ACCENT
        )

        draw_text(
            surface,
            f"{self.npc.name} - SHOP",
            self.title_font,
            UITheme.ACCENT,
            panel_rect.x + 30,
            panel_rect.y + 25
        )

        draw_text(
            surface,
            f"Gold: {self.session.gold}",
            self.font,
            UITheme.ACCENT_GOLD,
            panel_rect.right - 180,
            panel_rect.y + 32
        )

        mode_rect = pygame.Rect(
            panel_rect.x + 30,
            panel_rect.y + 80,
            240,
            42
        )

        draw_button(
            surface,
            mode_rect,
            f"Mode: {self.mode} [TAB]",
            self.small_font,
            is_selected=True
        )

        self._draw_item_list(surface, panel_rect)
        self._draw_item_details(surface, panel_rect)

        draw_text(
            surface,
            self.status_msg,
            self.small_font,
            UITheme.TEXT_DIM,
            panel_rect.x + 30,
            panel_rect.bottom - 38
        )

    def _draw_item_list(self, surface, panel_rect):
        items = self._get_display_items()

        list_rect = pygame.Rect(
            panel_rect.x + 30,
            panel_rect.y + 145,
            430,
            panel_rect.height - 210
        )

        draw_panel(
            surface,
            list_rect,
            color=UITheme.PANEL,
            border_color=UITheme.ACCENT_DARK
        )

        draw_text(
            surface,
            "Items",
            self.font,
            UITheme.ACCENT_GOLD,
            list_rect.x + 20,
            list_rect.y + 16
        )

        if not items:
            draw_text(
                surface,
                "No items.",
                self.small_font,
                UITheme.TEXT_DIM,
                list_rect.x + 20,
                list_rect.y + 65
            )
            return

        y = list_rect.y + 60

        for i, item in enumerate(items[:8]):
            selected = i == self.selected_index

            row_rect = pygame.Rect(
                list_rect.x + 15,
                y,
                list_rect.width - 30,
                38
            )

            if selected:
                draw_panel(
                    surface,
                    row_rect,
                    color=UITheme.PANEL_LIGHT,
                    border_color=UITheme.ACCENT
                )

            if self.mode == "BUY":
                price = getattr(item, "buy_price", 0)
                label = f"{item.name} - {price}G"
            else:
                count = self.inventory.get_item_count(item.item_id)
                price = getattr(item, "sell_price", 0)
                label = f"{item.name} x{count} - {price}G"

            draw_text(
                surface,
                label,
                self.small_font,
                UITheme.TEXT if selected else UITheme.TEXT_DIM,
                row_rect.x + 12,
                row_rect.y + 8
            )

            y += 44

    def _draw_item_details(self, surface, panel_rect):
        items = self._get_display_items()

        detail_rect = pygame.Rect(
            panel_rect.x + 490,
            panel_rect.y + 145,
            panel_rect.width - 520,
            panel_rect.height - 210
        )

        draw_panel(
            surface,
            detail_rect,
            color=UITheme.PANEL,
            border_color=UITheme.ACCENT_DARK
        )

        draw_text(
            surface,
            "Details",
            self.font,
            UITheme.ACCENT_GOLD,
            detail_rect.x + 20,
            detail_rect.y + 16
        )

        if not items:
            draw_text(
                surface,
                "Select an item to view details.",
                self.small_font,
                UITheme.TEXT_DIM,
                detail_rect.x + 20,
                detail_rect.y + 65
            )
            return

        item = items[self.selected_index]

        y = detail_rect.y + 65

        draw_text(
            surface,
            item.name,
            self.font,
            UITheme.TEXT,
            detail_rect.x + 20,
            y
        )

        y += 42

        self._draw_wrapped_text(
            surface,
            item.description,
            self.small_font,
            UITheme.TEXT_DIM,
            detail_rect.x + 20,
            y,
            detail_rect.width - 40,
            24
        )

        y += 90

        if item.item_type == "potion":
            effect = f"Heals {item.heal_amount} HP."
        elif item.item_type == "material":
            effect = "Used as mutation material."
        else:
            effect = "No direct effect."

        draw_text(
            surface,
            effect,
            self.small_font,
            UITheme.ACCENT,
            detail_rect.x + 20,
            y
        )

        draw_text(
            surface,
            "ENTER: Buy/Sell    TAB: Switch Mode    ESC: Close",
            self.small_font,
            UITheme.TEXT_DIM,
            detail_rect.x + 20,
            detail_rect.bottom - 35
        )

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