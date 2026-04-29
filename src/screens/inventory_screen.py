import pygame
from src.screens.base_screen import BaseScreen
from src.core.inventory_manager import InventoryManager
from src.entities.item import Item

class InventoryScreen(BaseScreen):
    """
    The UI interface for the player's inventory.
    Demonstrates KMP String Matching (Search) and Quick Sort (Organization).
    Now features Item Consumption logic.
    """
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self.font = pygame.font.SysFont(None, 40)
        self.small_font = pygame.font.SysFont(None, 28)

        self.inv_manager = self.screen_manager.game_session.inventory

        self.search_query = ""
        self.display_items = self.inv_manager.items
        
        # --- NEW: UI State for Selection ---
        self.selected_index = 0
        self.status_msg = "Arrows to Select | ENTER to Use | Type to Search"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.screen_manager.pop()
                
            elif event.key == pygame.K_TAB:
                self.inv_manager.sort_by_name()
                self._refresh_display()
                
            # --- NEW: Cursor Navigation ---
            elif event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
            elif event.key == pygame.K_DOWN:
                if self.display_items:
                    self.selected_index = min(len(self.display_items) - 1, self.selected_index + 1)
                    
            # --- NEW: Use Item ---
            elif event.key == pygame.K_RETURN:
                self._use_selected_item()
                
            elif event.key == pygame.K_BACKSPACE:
                self.search_query = self.search_query[:-1]
                self._refresh_display()
                
            elif event.unicode.isprintable():
                self.search_query += event.unicode
                self._refresh_display()

    def _use_selected_item(self):
        """Logic to consume potions and apply them to the player."""
        if not self.display_items:
            return

        item = self.display_items[self.selected_index]
        session = self.screen_manager.game_session
        zac = session.party[0] # Apply the item to your main character (Zac)

        # Check if the item is consumable
        if item.item_type == "potion":
            item.apply_effect(zac) # This calls the logic we wrote in item.py!
            
            # Prevent overhealing past Max HP (assuming you have a max_hp variable)
            zac.current_hp = min(zac.current_hp, zac.max_hp) if hasattr(zac, 'max_hp') else zac.current_hp
            
            self.status_msg = f"SUCCESS: Used {item.name}! Zac HP: {zac.current_hp}"
            
            # Remove the item from the inventory after use
            self.inv_manager.remove_item_by_id(item.item_id)
            self._refresh_display() # Update the UI list
        else:
            self.status_msg = f"ERROR: You cannot consume a {item.item_type}!"

    def _refresh_display(self):
        """Updates the visual list using KMP search filtering."""
        self.display_items = self.inv_manager.search_items(self.search_query)
        
        # Safety check: If filtering makes the list shorter, adjust the cursor
        if self.selected_index >= len(self.display_items):
            self.selected_index = max(0, len(self.display_items) - 1)

    def update(self):
        pass

    def draw(self, surface):
        surface.fill((40, 44, 52))
        center_x = surface.get_width() // 2

        # Header
        header = self.font.render("INVENTORY [Press ESC to close]", True, (255, 215, 0))
        header_rect = header.get_rect(center=(center_x, 40))
        surface.blit(header, header_rect)

        # Status & Search Bar
        controls_text = f"Search: {self.search_query}_"
        controls_surf = self.small_font.render(controls_text, True, (152, 195, 121))
        surface.blit(controls_surf, (50, 80))
        
        status_surf = self.small_font.render(self.status_msg, True, (100, 200, 255))
        surface.blit(status_surf, (50, 115))

        # Draw the filtered/sorted Item List with Selection Highlight
        y_offset = 160
        for i, item in enumerate(self.display_items):
            is_selected = (i == self.selected_index)
            
            # Highlight the background if selected
            if is_selected:
                pygame.draw.rect(surface, (70, 80, 95), (45, y_offset - 5, 600, 35))
                prefix = " > "
                text_color = (255, 255, 255)
            else:
                prefix = "   "
                text_color = (180, 180, 180)

            item_text = f"{prefix}{item.name} ({item.item_type.upper()}) - {item.description}"
            item_surf = self.small_font.render(item_text, True, text_color)
            surface.blit(item_surf, (50, y_offset))
            y_offset += 40