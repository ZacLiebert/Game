import pygame
from src.screens.base_screen import BaseScreen

class MutationScreen(BaseScreen):
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self.font = pygame.font.SysFont(None, 40)
        self.small_font = pygame.font.SysFont(None, 24)
        
        # Pull the REAL tree and database from the session
        self.session = self.screen_manager.game_session
        self.tree = self.session.mutation_tree
        self.db = self.session.db
        
        self.status_msg = "Arrows to navigate, [ENTER] to Evolve, [ESC] to exit."
        
        # UI State
        self.selected_index = 0
        self.nodes_list = [] # We will flatten the tree into this list for easy selection
        self._refresh_node_list()

    def _refresh_node_list(self):
        """Flattens the tree into a list so we can navigate with Up/Down keys."""
        self.nodes_list = []
        def traverse(node, depth):
            self.nodes_list.append({"node": node, "depth": depth})
            for child in node.children:
                traverse(child, depth + 1)
        traverse(self.tree.root, 0)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.screen_manager.pop()
            
            # Navigation
            elif event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.nodes_list) - 1, self.selected_index + 1)
                
            # Evolution Action
            elif event.key == pygame.K_RETURN or event.key == pygame.K_e:
                self._attempt_unlock()

    def _attempt_unlock(self):
        """Logic to consume items and unlock the selected node."""
        target_data = self.nodes_list[self.selected_index]
        node = target_data["node"]
        inventory = self.session.inventory

        # 1. Check if already unlocked
        if node.is_unlocked:
            self.status_msg = f"{node.name} is already active!"
            return

        # 2. Check Parent (using the find_parent helper in MutationTree)
        parent = self.tree.find_parent(node.node_id)
        if parent and not parent.is_unlocked:
            self.status_msg = f"Locked! Must unlock {parent.name} first."
            return

        # 3. Check Item Requirements
        # We use the method we added to the Node class earlier
        can_afford, msg = node.can_unlock(inventory)
        
        if can_afford:
            # SUCCESS: Consume the item
            if node.required_item_id:
                inventory.remove_item_by_id(node.required_item_id)
            
            node.is_unlocked = True
            self.status_msg = f"EVOLUTION SUCCESS: {node.name} unlocked!"
            
            # (Optional) Apply stat boost to Zac instantly
            if hasattr(node, 'stats_modifier') and node.stats_modifier:
                self.session.party[0].attack += node.stats_modifier.get("attack", 0)
        else:
            self.status_msg = f"INSUFFICIENT RESOURCES: {msg}"

    def draw(self, surface):
        surface.fill((25, 25, 35)) # Sci-fi dark background
        
        # Header
        header = self.font.render("BIOLOGICAL MUTATION CHAMBER", True, (0, 255, 150))
        surface.blit(header, (50, 30))
        
        # Status Bar
        status_color = (255, 200, 0) if "ERROR" in self.status_msg or "FAILED" in self.status_msg else (100, 200, 255)
        status_surf = self.small_font.render(self.status_msg, True, status_color)
        surface.blit(status_surf, (50, 75))

        # Draw the Tree List
        start_y = 150
        for i, item in enumerate(self.nodes_list):
            node = item["node"]
            depth = item["depth"]
            
            # Visual logic for selection
            is_selected = (i == self.selected_index)
            prefix = " > " if is_selected else "   "
            indent = "    " * depth
            
            # Color logic
            if node.is_unlocked:
                text_color = (100, 255, 100) # Green for active
                status_text = "[ACTIVE]"
            else:
                text_color = (255, 255, 255) if is_selected else (150, 150, 150)
                status_text = f"[Cost: {node.required_item_id}]" if node.required_item_id else "[FREE]"

            # Render the line
            display_text = f"{prefix}{indent}└─ {node.name} {status_text}"
            node_surf = self.small_font.render(display_text, True, text_color)
            
            # Draw a highlight box for selection
            if is_selected:
                pygame.draw.rect(surface, (40, 60, 80), (45, start_y + (i * 30) - 5, 600, 30))
            
            surface.blit(node_surf, (50, start_y + (i * 30)))

        # Bottom Info Box for Selected Node
        sel_node = self.nodes_list[self.selected_index]["node"]
        desc_title = self.small_font.render(f"Description: {sel_node.description}", True, (200, 200, 200))
        surface.blit(desc_title, (50, surface.get_height() - 80))