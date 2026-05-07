import pygame

from src.screens.base_screen import BaseScreen
from src.ui.theme import UITheme
from src.ui.widgets import draw_panel, draw_text, draw_button

try:
    from src.ui.fonts import get_font
except ImportError:
    def get_font(size, bold=False, italic=False):
        return pygame.font.SysFont(None, size, bold=bold, italic=italic)


class MutationScreen(BaseScreen):
    """
    Mutation UI screen.
    Uses the Mutation Tree to display and unlock biological evolutions.

    Fixed:
    - Header title and controls no longer overlap.
    - Mutation tree is drawn as connected nodes instead of a flat list.
    - Details panel reserves bottom area for Zac status and button.
    - Long text is clamped / shortened to avoid overlap.
    - Supports mouse click on mutation nodes.
    """

    NODE_WIDTH = 132
    NODE_HEIGHT = 48

    def __init__(self, screen_manager):
        super().__init__(screen_manager)

        self.title_font = get_font(UITheme.HEADER_SIZE, bold=True)
        self.font = get_font(UITheme.BODY_SIZE, bold=True)
        self.small_font = get_font(UITheme.SMALL_SIZE, bold=False)
        self.tiny_font = get_font(max(18, UITheme.SMALL_SIZE - 5), bold=False)

        self.session = self.screen_manager.game_session
        self.tree = self.session.mutation_tree
        self.db = self.session.db

        self.status_msg = "UP/DOWN: Select | ENTER/E: Evolve | ESC: Back"

        self.selected_index = 0
        self.nodes_list = []
        self.node_click_rects = []

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
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            for rect, index in self.node_click_rects:
                if rect.collidepoint(mouse_pos):
                    self.selected_index = index
                    return

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

        skill_name = self._get_skill_display_name(
            getattr(node, "unlock_skill", None)
        )

        if skill_name:
            self.status_msg = (
                f"Evolution success: {node.name} unlocked! "
                f"Skill gained: {skill_name}"
            )
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

        self._draw_header(surface, header_rect)

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

        self._draw_tree_graph(surface, tree_panel)
        self._draw_selected_details(surface, detail_panel)

        if "success" in self.status_msg.lower():
            status_color = UITheme.SUCCESS
        elif "cannot" in self.status_msg.lower() or "locked" in self.status_msg.lower():
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

    # ============================================================
    # HEADER
    # ============================================================

    def _draw_header(self, surface, header_rect):
        """
        Draws title and control hint on separate lines.

        This fixes the overlap caused by drawing the hint at a fixed x position
        while the title uses a large / thick font.
        """
        title_text = "BIOLOGICAL MUTATION CHAMBER"
        hint_text = "UP/DOWN: Select   ENTER/E: Evolve   ESC: Back"

        title_text = self._fit_text_to_width(
            title_text,
            self.title_font,
            header_rect.width - 50
        )

        draw_text(
            surface,
            title_text,
            self.title_font,
            UITheme.ACCENT,
            header_rect.x + 25,
            header_rect.y + 8
        )

        hint_text = self._fit_text_to_width(
            hint_text,
            self.small_font,
            header_rect.width - 50
        )

        hint_surface = self.small_font.render(
            hint_text,
            True,
            UITheme.TEXT_DIM
        )

        surface.blit(
            hint_surface,
            (
                header_rect.right - hint_surface.get_width() - 25,
                header_rect.y + 52
            )
        )

    # ============================================================
    # MUTATION TREE GRAPH
    # ============================================================

    def _draw_tree_graph(self, surface, panel_rect):
        if not self.nodes_list or not self.tree or not self.tree.root:
            draw_text(
                surface,
                "No mutations available.",
                self.small_font,
                UITheme.TEXT_DIM,
                panel_rect.x + 25,
                panel_rect.y + 80
            )
            return

        self.node_click_rects = []

        layout = self._build_tree_layout(panel_rect)
        selected_node = self.nodes_list[self.selected_index]["node"]

        self._draw_tree_connections(surface, self.tree.root, layout)

        for index, item in enumerate(self.nodes_list):
            node = item["node"]
            parent = self.tree.find_parent(node.node_id)

            center_x, center_y = layout[node.node_id]

            node_rect = pygame.Rect(
                center_x - self.NODE_WIDTH // 2,
                center_y - self.NODE_HEIGHT // 2,
                self.NODE_WIDTH,
                self.NODE_HEIGHT
            )

            self.node_click_rects.append((node_rect, index))

            if node.is_unlocked:
                bg_color = (24, 50, 42)
                border_color = UITheme.SUCCESS
                title_color = UITheme.TEXT
                sub_color = UITheme.SUCCESS
                status_text = "ACTIVE"
            else:
                can_unlock_now = False

                if parent is None or parent.is_unlocked:
                    can_unlock_now, _ = node.can_unlock(self.session.inventory)

                if can_unlock_now:
                    bg_color = (38, 44, 22)
                    border_color = UITheme.ACCENT_GOLD
                    title_color = UITheme.TEXT
                    sub_color = UITheme.ACCENT_GOLD
                    status_text = "READY"
                elif parent and parent.is_unlocked:
                    bg_color = UITheme.PANEL_DARK
                    border_color = (90, 110, 128)
                    title_color = UITheme.TEXT
                    sub_color = UITheme.TEXT_DIM
                    status_text = "OPEN"
                else:
                    bg_color = UITheme.PANEL_DARK
                    border_color = (55, 65, 80)
                    title_color = UITheme.TEXT_DIM
                    sub_color = UITheme.TEXT_DIM
                    status_text = "LOCKED"

            if node.node_id == selected_node.node_id:
                glow_rect = node_rect.inflate(12, 12)

                pygame.draw.rect(
                    surface,
                    UITheme.ACCENT_GOLD,
                    glow_rect,
                    2,
                    border_radius=12
                )

                border_color = UITheme.ACCENT_GOLD

            draw_panel(
                surface,
                node_rect,
                color=bg_color,
                border_color=border_color
            )

            node_name = self._fit_text_to_width(
                node.name,
                self.tiny_font,
                self.NODE_WIDTH - 14
            )

            name_surface = self.tiny_font.render(
                node_name,
                True,
                title_color
            )

            name_rect = name_surface.get_rect(
                center=(node_rect.centerx, node_rect.y + 15)
            )

            surface.blit(name_surface, name_rect)

            sub_text = self._get_tree_node_subtext(node)
            sub_text = self._fit_text_to_width(
                sub_text,
                self.tiny_font,
                self.NODE_WIDTH - 14
            )

            sub_surface = self.tiny_font.render(
                sub_text,
                True,
                sub_color
            )

            sub_rect = sub_surface.get_rect(
                center=(node_rect.centerx, node_rect.y + 32)
            )

            surface.blit(sub_surface, sub_rect)

            tag_surface = self.tiny_font.render(
                status_text,
                True,
                sub_color
            )

            tag_rect = tag_surface.get_rect(
                center=(node_rect.centerx, node_rect.bottom + 12)
            )

            surface.blit(tag_surface, tag_rect)

        legend_text = "Green: Active   Gold: Selected/Ready   Gray: Locked"
        legend_text = self._fit_text_to_width(
            legend_text,
            self.tiny_font,
            panel_rect.width - 48
        )

        draw_text(
            surface,
            legend_text,
            self.tiny_font,
            UITheme.TEXT_DIM,
            panel_rect.x + 24,
            panel_rect.bottom - 28
        )

    def _build_tree_layout(self, panel_rect):
        """
        Calculates graph positions for each mutation node.

        X position depends on depth.
        Y position depends on subtree leaf placement so parent nodes sit roughly
        between their children.
        """
        layout = {}

        top_y = panel_rect.y + 92
        bottom_y = panel_rect.bottom - 58
        left_x = panel_rect.x + 78
        right_x = panel_rect.right - 78

        max_depth = self._get_max_depth(self.tree.root)
        usable_width = max(1, right_x - left_x)
        x_gap = usable_width / max(1, max_depth)

        leaf_count = self._count_leaf_nodes(self.tree.root)
        usable_height = max(1, bottom_y - top_y)
        y_gap = usable_height / max(1, leaf_count)
        next_leaf_y = top_y + y_gap / 2

        def place_node(node, depth):
            nonlocal next_leaf_y

            x = int(left_x + depth * x_gap)

            if not node.children:
                y = int(next_leaf_y)
                next_leaf_y += y_gap
            else:
                child_ys = []

                for child in node.children:
                    place_node(child, depth + 1)
                    child_ys.append(layout[child.node_id][1])

                if child_ys:
                    y = int(sum(child_ys) / len(child_ys))
                else:
                    y = int(next_leaf_y)

            layout[node.node_id] = (x, y)

        place_node(self.tree.root, 0)

        return layout

    def _draw_tree_connections(self, surface, node, layout):
        parent_center = layout[node.node_id]

        parent_rect = pygame.Rect(
            parent_center[0] - self.NODE_WIDTH // 2,
            parent_center[1] - self.NODE_HEIGHT // 2,
            self.NODE_WIDTH,
            self.NODE_HEIGHT
        )

        for child in node.children:
            child_center = layout[child.node_id]

            child_rect = pygame.Rect(
                child_center[0] - self.NODE_WIDTH // 2,
                child_center[1] - self.NODE_HEIGHT // 2,
                self.NODE_WIDTH,
                self.NODE_HEIGHT
            )

            if node.is_unlocked and child.is_unlocked:
                line_color = UITheme.SUCCESS
            elif node.is_unlocked:
                line_color = UITheme.ACCENT_GOLD
            else:
                line_color = (70, 80, 95)

            start = (parent_rect.right, parent_rect.centery)
            end = (child_rect.left, child_rect.centery)
            mid_x = (start[0] + end[0]) // 2

            pygame.draw.line(
                surface,
                line_color,
                start,
                (mid_x, start[1]),
                2
            )

            pygame.draw.line(
                surface,
                line_color,
                (mid_x, start[1]),
                (mid_x, end[1]),
                2
            )

            pygame.draw.line(
                surface,
                line_color,
                (mid_x, end[1]),
                end,
                2
            )

            self._draw_tree_connections(surface, child, layout)

    def _count_leaf_nodes(self, node):
        if not node.children:
            return 1

        total = 0

        for child in node.children:
            total += self._count_leaf_nodes(child)

        return total

    def _get_max_depth(self, node, current_depth=0):
        if not node.children:
            return current_depth

        return max(
            self._get_max_depth(child, current_depth + 1)
            for child in node.children
        )

    def _get_tree_node_subtext(self, node):
        if node.required_item_id is None:
            return "Free"

        item = self.db.get_item(node.required_item_id)
        item_name = item.name if item else node.required_item_id

        if len(item_name) > 10:
            short_name = item_name[:10] + "..."
        else:
            short_name = item_name

        owned = self.session.inventory.get_item_count(node.required_item_id)
        needed = node.required_count

        return f"{short_name} {owned}/{needed}"

    # ============================================================
    # DETAILS PANEL
    # ============================================================

    def _draw_selected_details(self, surface, panel_rect):
        if not self.nodes_list:
            return

        node = self.nodes_list[self.selected_index]["node"]

        x = panel_rect.x + 25
        y = panel_rect.y + 62

        divider_y = panel_rect.bottom - 135
        zac_y = divider_y + 28
        button_y = panel_rect.bottom - 58

        content_bottom_limit = divider_y - 18
        max_width = panel_rect.width - 50

        node_name = self._fit_text_to_width(
            node.name,
            self.font,
            max_width
        )

        draw_text(
            surface,
            node_name,
            self.font,
            UITheme.TEXT,
            x,
            y
        )

        y += 42

        if node.is_unlocked:
            badge_text = "ACTIVE"
            badge_color = UITheme.SUCCESS
        else:
            badge_text = "LOCKED"
            badge_color = UITheme.WARNING

        badge_rect = pygame.Rect(x, y, 160, 34)

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
            badge_rect.y + 7
        )

        y += 50

        y = self._draw_detail_section(
            surface,
            title="Description",
            value=node.description,
            value_color=UITheme.TEXT_DIM,
            x=x,
            y=y,
            max_width=max_width,
            max_bottom=content_bottom_limit
        )

        y = self._draw_detail_section(
            surface,
            title="Requirement",
            value=self._get_requirement_detail(node),
            value_color=UITheme.TEXT_DIM,
            x=x,
            y=y,
            max_width=max_width,
            max_bottom=content_bottom_limit
        )

        y = self._draw_detail_section(
            surface,
            title="Stat Bonus",
            value=self._get_stat_text(node),
            value_color=UITheme.TEXT_DIM,
            x=x,
            y=y,
            max_width=max_width,
            max_bottom=content_bottom_limit
        )

        skill_name = self._get_skill_display_name(
            getattr(node, "unlock_skill", None)
        )

        if skill_name:
            skill_text = skill_name
            skill_color = UITheme.ACCENT_GOLD
        else:
            skill_text = "None"
            skill_color = UITheme.TEXT_DIM

        self._draw_detail_section(
            surface,
            title="Unlock Skill",
            value=skill_text,
            value_color=skill_color,
            x=x,
            y=y,
            max_width=max_width,
            max_bottom=content_bottom_limit
        )

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

        zac = self.session.party[0]

        zac_text = (
            f"Zac: HP {zac.current_hp}/{zac.max_hp}   "
            f"ATK {zac.attack}   DEF {zac.defense}   SPD {zac.speed}"
        )

        zac_text = self._fit_text_to_width(
            zac_text,
            self.small_font,
            max_width
        )

        pygame.draw.line(
            surface,
            (55, 65, 80),
            (x, divider_y),
            (panel_rect.right - 25, divider_y),
            1
        )

        draw_text(
            surface,
            zac_text,
            self.small_font,
            UITheme.TEXT_DIM,
            x,
            zac_y
        )

        button_width = min(max_width, 520)

        button_rect = pygame.Rect(
            x,
            button_y,
            button_width,
            40
        )

        button_text = self._fit_text_to_width(
            button_text,
            self.small_font,
            button_rect.width - 20
        )

        draw_button(
            surface,
            button_rect,
            button_text,
            self.small_font,
            is_selected=can_evolve
        )

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
        """
        Draws one detail section only if it fits above the fixed bottom area.
        This prevents text from overlapping Zac stats and the evolve button.
        """
        title_height = 24
        gap_after_title = 22
        gap_after_value = 14
        line_height = 22

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

    # ============================================================
    # TEXT / DATA HELPERS
    # ============================================================

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
            "toxic_bite": "Toxic Bite",
            "sonic_pulse": "Sonic Pulse",
            "sonic_pulse_plus": "Sonic Pulse+",
            "beast_focus": "Beast Focus"
        }

        return skill_names.get(skill_id, skill_id.replace("_", " ").title())

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
        """
        Draws wrapped text but stops before max_bottom.
        If there is no more room, it silently stops to avoid overlap.
        """
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
        """
        Shortens text with ... so it fits inside a given width.
        """
        text = str(text)

        if font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."

        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]

        return text + ellipsis