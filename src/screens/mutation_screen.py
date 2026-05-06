import pygame

from src.screens.base_screen import BaseScreen
from src.ui.theme import UITheme
from src.ui.widgets import draw_panel, draw_text, draw_button


class MutationScreen(BaseScreen):
    """
    Mutation UI screen.
    Uses the Mutation Tree to display and unlock biological evolutions.
    """

    def __init__(self, screen_manager):
        super().__init__(screen_manager)

        self.title_font = pygame.font.SysFont(None, UITheme.HEADER_SIZE)
        self.font = pygame.font.SysFont(None, UITheme.BODY_SIZE)
        self.small_font = pygame.font.SysFont(None, UITheme.SMALL_SIZE)

        self.session = self.screen_manager.game_session
        self.tree = self.session.mutation_tree
        self.db = self.session.db

        self.status_msg = "UP/DOWN: Select | ENTER/E: Evolve | ESC: Back"

        self.selected_index = 0
        self.nodes_list = []

        if self.tree:
            self._refresh_node_list()

    def _refresh_node_list(self):
        """
        Flattens the mutation tree into a list for keyboard navigation.
        """
        self.nodes_list = []

        def traverse(node, depth):
            self.nodes_list.append({
                "node": node,
                "depth": depth
            })

            for child in node.children:
                traverse(child, depth + 1)

        traverse(self.tree.root, 0)

        if self.selected_index >= len(self.nodes_list):
            self.selected_index = max(0, len(self.nodes_list) - 1)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.screen_manager.pop()

            elif event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)

            elif event.key == pygame.K_DOWN:
                if self.nodes_list:
                    self.selected_index = min(
                        len(self.nodes_list) - 1,
                        self.selected_index + 1
                    )

            elif event.key == pygame.K_RETURN or event.key == pygame.K_e:
                self._attempt_unlock()

    def _attempt_unlock(self):
        """
        Attempts to unlock the selected mutation.

        Checks:
        - Already unlocked
        - Parent unlocked
        - Enough required material count

        Then:
        - Consumes required materials
        - Unlocks node
        - Applies stat bonus
        """
        if not self.tree or not self.nodes_list:
            self.status_msg = "Mutation Tree is not available."
            return

        target_data = self.nodes_list[self.selected_index]
        node = target_data["node"]
        inventory = self.session.inventory

        if node.is_unlocked:
            self.status_msg = f"{node.name} is already active."
            return

        parent = self.tree.find_parent(node.node_id)

        if parent and not parent.is_unlocked:
            self.status_msg = f"Locked. Unlock {parent.name} first."
            return

        can_afford, msg = node.can_unlock(inventory)

        if not can_afford:
            self.status_msg = f"Cannot evolve: {msg}"
            return

        if node.required_item_id:
            removed = inventory.remove_item_count(
                node.required_item_id,
                node.required_count
            )

            if not removed:
                self.status_msg = "Cannot evolve: material count changed."
                return

        node.is_unlocked = True
        self._apply_stat_modifier(node)
        self.session.quest_manager.record_mutation(node.node_id)

        skill_name = self._get_skill_display_name(getattr(node, "unlock_skill", None))

        if skill_name:
            self.status_msg = f"Evolution success: {node.name} unlocked! Skill gained: {skill_name}"
        else:
            self.status_msg = f"Evolution success: {node.name} unlocked!"

    def _apply_stat_modifier(self, node):
        """
        Applies mutation stat bonuses to Zac.
        """
        stats_modifier = getattr(node, "stats_modifier", {})

        if not stats_modifier:
            return

        zac = self.session.party[0]

        zac.attack += stats_modifier.get("attack", 0)
        zac.defense += stats_modifier.get("defense", 0)
        zac.speed += stats_modifier.get("speed", 0)

        if "hp" in stats_modifier:
            zac.max_hp += stats_modifier["hp"]
            zac.current_hp += stats_modifier["hp"]

    def update(self):
        pass

    def draw(self, surface):
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        surface.fill((10, 16, 22))

        header_rect = pygame.Rect(30, 25, screen_w - 60, 80)

        draw_panel(
            surface,
            header_rect,
            color=UITheme.PANEL_DARK,
            border_color=UITheme.ACCENT_DARK
        )

        draw_text(
            surface,
            "BIOLOGICAL MUTATION CHAMBER",
            self.title_font,
            UITheme.ACCENT,
            header_rect.x + 25,
            header_rect.y + 18
        )

        hint = "UP/DOWN: Select   ENTER/E: Evolve   ESC: Back"
        draw_text(
            surface,
            hint,
            self.small_font,
            UITheme.TEXT_DIM,
            header_rect.x + 560,
            header_rect.y + 30
        )

        tree_panel = pygame.Rect(30, 125, 640, screen_h - 180)
        detail_panel = pygame.Rect(700, 125, screen_w - 730, screen_h - 180)

        draw_panel(
            surface,
            tree_panel,
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
            "Mutation Tree",
            self.font,
            UITheme.ACCENT_GOLD,
            tree_panel.x + 25,
            tree_panel.y + 18
        )

        draw_text(
            surface,
            "Mutation Details",
            self.font,
            UITheme.ACCENT_GOLD,
            detail_panel.x + 25,
            detail_panel.y + 18
        )

        if not self.tree:
            draw_text(
                surface,
                "Mutation Tree failed to load.",
                self.small_font,
                UITheme.DANGER,
                tree_panel.x + 25,
                tree_panel.y + 80
            )
            return

        self._draw_tree_list(surface, tree_panel)
        self._draw_selected_details(surface, detail_panel)

        if "success" in self.status_msg.lower():
            status_color = UITheme.SUCCESS
        elif "cannot" in self.status_msg.lower() or "locked" in self.status_msg.lower():
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

    def _draw_tree_list(self, surface, panel_rect):
        if not self.nodes_list:
            draw_text(
                surface,
                "No mutations available.",
                self.small_font,
                UITheme.TEXT_DIM,
                panel_rect.x + 25,
                panel_rect.y + 80
            )
            return

        row_height = 70
        visible_rows = 7

        start_index = max(0, self.selected_index - visible_rows + 1)
        end_index = min(len(self.nodes_list), start_index + visible_rows)

        y = panel_rect.y + 70

        for i in range(start_index, end_index):
            item = self.nodes_list[i]
            node = item["node"]
            depth = item["depth"]
            is_selected = i == self.selected_index

            indent = depth * 35

            row_rect = pygame.Rect(
                panel_rect.x + 20 + indent,
                y,
                panel_rect.width - 40 - indent,
                row_height - 12
            )

            if node.is_unlocked:
                bg_color = (24, 50, 42)
                border_color = UITheme.SUCCESS
                status_text = "ACTIVE"
                status_color = UITheme.SUCCESS
            else:
                bg_color = UITheme.PANEL_DARK
                border_color = (55, 65, 80)
                status_text = "LOCKED"
                status_color = UITheme.TEXT_DIM

            if is_selected:
                border_color = UITheme.ACCENT_GOLD

            draw_panel(
                surface,
                row_rect,
                color=bg_color,
                border_color=border_color
            )

            connector = "ROOT" if depth == 0 else "+-"

            draw_text(
                surface,
                connector,
                self.small_font,
                UITheme.TEXT_DIM,
                row_rect.x + 12,
                row_rect.y + 18
            )

            draw_text(
                surface,
                node.name,
                self.small_font,
                UITheme.TEXT,
                row_rect.x + 65,
                row_rect.y + 10
            )

            cost_text = self._get_cost_text(node)

            draw_text(
                surface,
                cost_text,
                self.small_font,
                UITheme.TEXT_DIM,
                row_rect.x + 65,
                row_rect.y + 34
            )

            status_surf = self.small_font.render(status_text, True, status_color)

            surface.blit(
                status_surf,
                (
                    row_rect.right - status_surf.get_width() - 15,
                    row_rect.y + 19
                )
            )

            y += row_height

        if len(self.nodes_list) > visible_rows:
            scroll_text = f"Showing {start_index + 1}-{end_index} of {len(self.nodes_list)}"

            draw_text(
                surface,
                scroll_text,
                self.small_font,
                UITheme.TEXT_DIM,
                panel_rect.x + 25,
                panel_rect.bottom - 35
            )

    def _draw_selected_details(self, surface, panel_rect):
        if not self.nodes_list:
            return

        node = self.nodes_list[self.selected_index]["node"]

        x = panel_rect.x + 25
        y = panel_rect.y + 75

        draw_text(
            surface,
            node.name,
            self.font,
            UITheme.TEXT,
            x,
            y
        )

        y += 50

        if node.is_unlocked:
            badge_text = "ACTIVE"
            badge_color = UITheme.SUCCESS
        else:
            badge_text = "LOCKED"
            badge_color = UITheme.WARNING

        badge_rect = pygame.Rect(x, y, 160, 38)

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
            node.description,
            self.small_font,
            UITheme.TEXT_DIM,
            x,
            y,
            panel_rect.width - 50,
            26
        )

        y += 105

        draw_text(
            surface,
            "Requirement",
            self.small_font,
            UITheme.ACCENT,
            x,
            y
        )

        y += 32

        requirement_text = self._get_requirement_detail(node)

        draw_text(
            surface,
            requirement_text,
            self.small_font,
            UITheme.TEXT_DIM,
            x,
            y
        )

        y += 55

        draw_text(
            surface,
            "Stat Bonus",
            self.small_font,
            UITheme.ACCENT,
            x,
            y
        )

        y += 32

        stat_text = self._get_stat_text(node)

        draw_text(
            surface,
            stat_text,
            self.small_font,
            UITheme.TEXT_DIM,
            x,
            y
        )

        y += 55

        draw_text(
            surface,
            "Unlock Skill",
            self.small_font,
            UITheme.ACCENT,
            x,
            y
        )

        y += 32

        skill_name = self._get_skill_display_name(getattr(node, "unlock_skill", None))

        if skill_name:
            skill_color = UITheme.ACCENT_GOLD
            skill_text = skill_name
        else:
            skill_color = UITheme.TEXT_DIM
            skill_text = "None"

        draw_text(
            surface,
            skill_text,
            self.small_font,
            skill_color,
            x,
            y
        )

        y += 65

        parent = self.tree.find_parent(node.node_id)

        if node.is_unlocked:
            button_text = "Already Active"
            can_evolve = False
        elif parent and not parent.is_unlocked:
            button_text = f"Requires {parent.name}"
            can_evolve = False
        else:
            can_afford, _ = node.can_unlock(self.session.inventory)

            if can_afford:
                button_text = "[ENTER/E] Evolve"
                can_evolve = True
            else:
                button_text = "Not Enough Materials"
                can_evolve = False

        button_rect = pygame.Rect(
            x,
            panel_rect.bottom - 65,
            260,
            42
        )

        draw_button(
            surface,
            button_rect,
            button_text,
            self.small_font,
            is_selected=can_evolve
        )

        zac = self.session.party[0]

        zac_text = (
            f"Zac: HP {zac.current_hp}/{zac.max_hp}   "
            f"ATK {zac.attack}   DEF {zac.defense}   SPD {zac.speed}"
        )

        draw_text(
            surface,
            zac_text,
            self.small_font,
            UITheme.TEXT_DIM,
            x,
            panel_rect.bottom - 105
        )

    def _get_cost_text(self, node):
        """
        Short cost text for the tree list.
        """
        if node.required_item_id is None:
            return "Cost: Free"

        item = self.db.get_item(node.required_item_id)
        item_name = item.name if item else node.required_item_id

        owned = self.session.inventory.get_item_count(node.required_item_id)
        needed = node.required_count

        return f"Cost: {item_name} {owned}/{needed}"

    def _get_requirement_detail(self, node):
        """
        Detailed requirement text for selected mutation.
        """
        if node.required_item_id is None:
            return "Free mutation. No material required."

        item = self.db.get_item(node.required_item_id)
        item_name = item.name if item else node.required_item_id

        owned = self.session.inventory.get_item_count(node.required_item_id)
        needed = node.required_count

        return f"{item_name}: Owned {owned}/{needed}"

    def _get_stat_text(self, node):
        """
        Converts stat modifier dictionary into readable text.
        """
        stats_modifier = getattr(node, "stats_modifier", {})

        if not stats_modifier:
            return "No stat bonus."

        parts = []

        if "hp" in stats_modifier:
            parts.append(f"HP +{stats_modifier['hp']}")

        if "attack" in stats_modifier:
            parts.append(f"ATK +{stats_modifier['attack']}")

        if "defense" in stats_modifier:
            parts.append(f"DEF +{stats_modifier['defense']}")

        if "speed" in stats_modifier:
            parts.append(f"SPD +{stats_modifier['speed']}")

        return "   ".join(parts)

    def _get_skill_display_name(self, skill_id):
        """
        Converts skill id from JSON into readable combat skill name.
        """
        if not skill_id:
            return None

        skill_names = {
            "venom_bite": "Venom Bite",
            "sonic_pulse": "Sonic Pulse",
            "beast_focus": "Beast Focus"
        }

        return skill_names.get(skill_id, skill_id.replace("_", " ").title())

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
