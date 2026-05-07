import pygame
import random
from types import SimpleNamespace

from src.paths import resolve_map_path
from src.screens.base_screen import BaseScreen
from src.entities.player import Player
from src.entities.npc import NPC
from src.graphics.tilemap import TileMap
from src.graphics.sprite_manager import SpriteManager
from src.graphics.camera import Camera
from src.screens.combat_screen import CombatScreen

from src.ui.theme import UITheme
from src.ui.fonts import get_font
from src.ui.widgets import draw_text


class MapScreen(BaseScreen):
    """
    Main overworld map screen.

    Handles:
    - Player grid movement
    - Tile collision
    - Random encounters in bush tiles
    - NPC / boss encounters
    - Dialogue NPCs
    - Shop NPCs
    - Inventory, Mutation, and Skill Loadout shortcuts
    """

    def __init__(self, screen_manager, map_id=None):
        super().__init__(screen_manager)

        self.font = get_font(UITheme.HEADER_SIZE)
        self.small_font = get_font(UITheme.SMALL_SIZE)
        self.tiny_font = get_font(20)

        session = self.screen_manager.game_session

        if map_id is None:
            map_id = session.current_map_id

        self.map_id = map_id
        self.db = self.screen_manager.game_session.db

        self.screen_width = 1280
        self.screen_height = 720

        self.tile_size = 64

        # =========================
        # OUTSIDE-MAP BACKGROUND
        # =========================
        self.outside_bg_size = 256
        self.outside_bg_tile = SpriteManager.get_sprite(
            "outside_ocean.png",
            width=self.outside_bg_size,
            height=self.outside_bg_size
        )

        self.ocean_overlay_color = (0, 20, 30, 35)

        # =========================
        # SCREEN LAYOUT
        # =========================
        self.top_panel = pygame.Rect(
            24,
            18,
            self.screen_width - 48,
            76
        )

        self.play_area = pygame.Rect(
            28,
            112,
            self.screen_width - 56,
            self.screen_height - 190
        )

        self.bottom_panel = pygame.Rect(
            24,
            self.screen_height - 58,
            self.screen_width - 48,
            42
        )

        # =========================
        # MAP DATA
        # =========================
        map_data = self.db.get_map_data(map_id)

        self.region_name = "Unknown Region"
        self.level_data = [
            list("#####"),
            list("#...#"),
            list("#.B.#"),
            list("#...#"),
            list("#####"),
        ]

        # =========================
        # PLAYER
        # =========================
        self.player = Player(
            x=session.player_position[0],
            y=session.player_position[1],
            tile_size=self.tile_size
        )

        # =========================
        # NPCS
        # =========================
        self.npcs = []

        if map_data:
            self.region_name = map_data.get("name", "Unknown Region")

            for n in map_data.get("npcs", []):
                new_npc = NPC(
                    name=n["name"],
                    x=n["x"],
                    y=n["y"],
                    enemy_ids=n.get("enemies", []),
                    sprite_filename=n.get("sprite", "slime.png"),
                    npc_type=n.get("type", "farm"),
                    sprite_sheet=n.get("sprite_sheet", False),
                    dialogue=n.get("dialogue", []),
                    shop_items=n.get("shop_items", [])
                )
                new_npc.required_quest = n.get("required_quest")
                new_npc.defeated = session.is_npc_defeated(new_npc.name)
                self.npcs.append(new_npc)

        # =========================
        # TILE MAP
        # =========================
        self.world_map = TileMap(tile_size=self.tile_size)

        if map_data:
            solid_tiles = map_data.get("solid_tiles", [])

            for tile_id, sprite_file in map_data.get("tile_sprites", {}).items():
                is_wall = tile_id in solid_tiles

                self.world_map.add_tile(
                    tile_id,
                    SpriteManager.get_sprite(
                        sprite_file,
                        width=self.tile_size,
                        height=self.tile_size
                    ),
                    is_wall
                )

            map_filename = map_data.get("map_file", "forest_01.txt")
            self.level_data = self.load_map_from_file(map_filename)

        else:
            grass = pygame.Surface((self.tile_size, self.tile_size))
            grass.fill((40, 120, 50))

            wall = pygame.Surface((self.tile_size, self.tile_size))
            wall.fill((40, 60, 40))

            bush = pygame.Surface((self.tile_size, self.tile_size))
            bush.fill((35, 140, 45))

            sand = pygame.Surface((self.tile_size, self.tile_size))
            sand.fill((230, 200, 120))

            self.world_map.add_tile(".", grass, False)
            self.world_map.add_tile("#", wall, True)
            self.world_map.add_tile("B", bush, False)
            self.world_map.add_tile("S", sand, False)

        self.world_map.load_map(self.level_data)

        # =========================
        # CAMERA
        # =========================
        map_pixel_width = len(self.level_data[0]) * self.tile_size
        map_pixel_height = len(self.level_data) * self.tile_size

        self.camera = Camera(
            self.play_area.width,
            self.play_area.height,
            map_pixel_width,
            map_pixel_height
        )

        # =========================
        # RANDOM ENCOUNTER
        # =========================
        self.encounter_tiles = {"B"}

        self.random_enemy_ids = [
            "e_tiger",
            "e_snake",
            "e_boar",
            "e_rabbit",
            "e_bat"
        ]

        self.encounter_chance = 0.15
        self.encounter_cooldown_ms = 1200
        self.last_encounter_time = 0

        self.status_message = "Explore the forest. Step into bushes to find mutated beasts."

    # ============================================================
    # MAP LOADING
    # ============================================================

    def load_map_from_file(self, filename):
        """
        Reads a .txt file containing ASCII map data.
        """
        path = resolve_map_path(filename)
        grid = []

        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    clean_line = line.strip()

                    if clean_line:
                        grid.append(list(clean_line))

            return grid

        except FileNotFoundError:
            print(f"ERROR: Could not find {path}.")
            return [
                list("#####"),
                list("#...#"),
                list("#.B.#"),
                list("#...#"),
                list("#####"),
            ]

    # ============================================================
    # INPUT
    # ============================================================

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.screen_manager.pop()

            elif event.key == pygame.K_i:
                from src.screens.inventory_screen import InventoryScreen
                self.screen_manager.push(InventoryScreen(self.screen_manager))

            elif event.key == pygame.K_m:
                from src.screens.mutation_screen import MutationScreen
                self.screen_manager.push(MutationScreen(self.screen_manager))

            elif event.key == pygame.K_k:
                from src.screens.skill_loadout_screen import SkillLoadoutScreen
                self.screen_manager.push(SkillLoadoutScreen(self.screen_manager))

            elif event.key == pygame.K_e:
                self._interact_with_nearby_npc()

    # ============================================================
    # UPDATE
    # ============================================================

    def update(self):
        keys = pygame.key.get_pressed()

        static_collision_rects = self._get_static_collision_rects()
        player_collision_rects = (
            static_collision_rects
            + self._get_active_npc_collision_rects()
        )

        player_moved = self.player.handle_movement(keys, player_collision_rects)

        for npc in self.npcs:
            if self._is_npc_active(npc):
                npc.update_ai(self.player.rect, static_collision_rects)

        self.camera.update(self.player.rect)
        self.screen_manager.game_session.remember_map_position(
            self.map_id,
            self.player.rect
        )

        if player_moved:
            current_tile = self._get_player_tile()

            if current_tile in self.encounter_tiles:
                self.status_message = "The bushes rustle... something may appear."
            else:
                self.status_message = "Explore the forest. Step into bushes to find mutated beasts."

            if self._check_random_encounter():
                return

        nearby_npc = self._get_nearby_npc()

        if nearby_npc:
            self.status_message = f"Press E to interact with {nearby_npc.name}."

    # ============================================================
    # NPC INTERACTION
    # ============================================================

    def _get_nearby_npc(self):
        """
        Finds an NPC close enough to interact with.
        """
        interaction_rect = self.player.rect.inflate(28, 28)

        for npc in self.npcs:
            if self._is_npc_active(npc) and interaction_rect.colliderect(npc.rect):
                return npc

        return None

    def _interact_with_nearby_npc(self):
        """
        Interacts with nearby NPC based on npc_type.
        """
        npc = self._get_nearby_npc()

        if not npc:
            self.status_message = "No one nearby."
            return

        if npc.npc_type == "dialogue":
            from src.screens.dialogue_screen import DialogueScreen
            self.screen_manager.push(DialogueScreen(self.screen_manager, npc))

        elif npc.npc_type == "shop":
            from src.screens.shop_screen import ShopScreen
            self.screen_manager.push(ShopScreen(self.screen_manager, npc))

        else:
            self.screen_manager.push(CombatScreen(self.screen_manager, npc))

    # ============================================================
    # COLLISION HELPERS
    # ============================================================

    def _get_static_collision_rects(self):
        """
        Returns map collision rectangles that do not depend on NPC state.
        """
        collision_rects = self.world_map.get_colliding_rects()
        collision_rects.extend(self._get_map_boundary_walls())
        return collision_rects

    def _get_active_npc_collision_rects(self):
        """
        Returns collision rectangles for visible NPCs.

        Important:
        - Player movement checks against Player.collision_rect.
        - NPC has its own smaller foot hitbox named collision_rect.
        - Using npc.collision_rect prevents Zac from walking through NPCs
          without creating a large invisible wall around the full sprite/name.
        """
        rects = []

        for npc in self.npcs:
            if self._is_npc_active(npc):
                if hasattr(npc, "_sync_collision_rect"):
                    npc._sync_collision_rect()

                if hasattr(npc, "collision_rect"):
                    rects.append(npc.collision_rect.copy())
                else:
                    rects.append(npc.rect.copy())

        return rects

    def _is_npc_active(self, npc):
        if npc.defeated:
            return False

        required_quest = getattr(npc, "required_quest", None)

        if not required_quest:
            return True

        quest_manager = self.screen_manager.game_session.quest_manager
        return quest_manager.is_active(required_quest)

    def _get_map_boundary_walls(self):
        """
        Creates invisible walls around the playable map.

        The ocean is only a background layer outside the map.
        These boundary walls prevent the player from walking into it.
        """
        map_pixel_width = len(self.level_data[0]) * self.tile_size
        map_pixel_height = len(self.level_data) * self.tile_size
        thickness = self.tile_size

        return [
            pygame.Rect(
                -thickness,
                -thickness,
                map_pixel_width + thickness * 2,
                thickness
            ),
            pygame.Rect(
                -thickness,
                map_pixel_height,
                map_pixel_width + thickness * 2,
                thickness
            ),
            pygame.Rect(
                -thickness,
                0,
                thickness,
                map_pixel_height
            ),
            pygame.Rect(
                map_pixel_width,
                0,
                thickness,
                map_pixel_height
            )
        ]

    # ============================================================
    # COORDINATE HELPERS
    # ============================================================

    def _world_to_screen(self, world_rect):
        """
        Converts a world rect into a screen rect inside the play area.
        """
        screen_rect = self.camera.apply(world_rect)
        screen_rect.x += self.play_area.x
        screen_rect.y += self.play_area.y
        return screen_rect

    def _get_player_tile(self):
        """
        Returns the tile character under the player's center position.
        """
        center_x = self.player.rect.centerx
        center_y = self.player.rect.centery

        col = center_x // self.tile_size
        row = center_y // self.tile_size

        if row < 0 or row >= len(self.level_data):
            return None

        if col < 0 or col >= len(self.level_data[row]):
            return None

        return self.level_data[row][col]

    def _check_random_encounter(self):
        """
        Starts a random combat encounter when Zac steps onto bush tiles.
        """
        current_tile = self._get_player_tile()

        if current_tile not in self.encounter_tiles:
            return False

        current_time = pygame.time.get_ticks()

        if current_time - self.last_encounter_time < self.encounter_cooldown_ms:
            return False

        if random.random() > self.encounter_chance:
            return False

        self.last_encounter_time = current_time

        enemy_ids = random.choices(
            self.random_enemy_ids,
            k=3
        )

        encounter_npc = SimpleNamespace(
            name="Wild Encounter",
            enemy_ids=enemy_ids,
            npc_type="random",
            defeated=False
        )

        self.screen_manager.push(CombatScreen(self.screen_manager, encounter_npc))
        return True

    # ============================================================
    # DRAW
    # ============================================================

    def draw(self, surface):
        surface.fill((7, 10, 12))

        self._draw_background(surface)
        self._draw_top_hud(surface)
        self._draw_map_panel(surface)
        self._draw_world(surface)
        self._draw_bottom_hint(surface)

    def _draw_background(self, surface):
        """
        Draws subtle dark background behind the map panel.
        """
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        surface.fill((7, 10, 12))

        grid_color = (12, 20, 24)

        for x in range(0, screen_w, 48):
            pygame.draw.line(
                surface,
                grid_color,
                (x, 0),
                (x, screen_h)
            )

        for y in range(0, screen_h, 48):
            pygame.draw.line(
                surface,
                grid_color,
                (0, y),
                (screen_w, y)
            )

        vignette = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        pygame.draw.rect(
            vignette,
            (0, 0, 0, 45),
            pygame.Rect(0, 0, screen_w, screen_h)
        )
        surface.blit(vignette, (0, 0))

    def _draw_top_hud(self, surface):
        """
        Draws region, player status, gold, and inventory count.
        """
        session = self.screen_manager.game_session
        zac = session.party[0]

        self._draw_soft_panel(
            surface,
            self.top_panel,
            fill=(12, 18, 23, 210),
            border=(0, 170, 130),
            radius=10
        )

        region_x = self.top_panel.x + 25

        draw_text(
            surface,
            "REGION",
            self.small_font,
            UITheme.TEXT_DIM,
            region_x,
            self.top_panel.y + 12
        )

        draw_text(
            surface,
            self.region_name.upper(),
            self.font,
            UITheme.ACCENT,
            region_x,
            self.top_panel.y + 38
        )

        status_x = self.top_panel.x + 385

        draw_text(
            surface,
            "ZAC STATUS",
            self.small_font,
            UITheme.TEXT_DIM,
            status_x,
            self.top_panel.y + 12
        )

        stat_text = (
            f"HP {zac.current_hp}/{zac.max_hp}   "
            f"ATK {zac.attack}   DEF {zac.defense}   SPD {zac.speed}"
        )

        draw_text(
            surface,
            stat_text,
            self.small_font,
            UITheme.TEXT,
            status_x,
            self.top_panel.y + 39
        )

        self._draw_small_hp_bar(
            surface,
            status_x,
            self.top_panel.y + 63,
            285,
            8,
            zac.current_hp,
            zac.max_hp
        )

        inv_x = self.top_panel.right - 300
        item_count = len(session.inventory.items)

        draw_text(
            surface,
            "INVENTORY / GOLD",
            self.small_font,
            UITheme.TEXT_DIM,
            inv_x,
            self.top_panel.y + 12
        )

        draw_text(
            surface,
            f"{item_count} item(s)   {session.gold}G",
            self.small_font,
            UITheme.ACCENT_GOLD,
            inv_x,
            self.top_panel.y + 40
        )

    def _draw_map_panel(self, surface):
        """
        Draws the main map container.
        """
        outer_rect = self.play_area.inflate(8, 8)

        self._draw_soft_panel(
            surface,
            outer_rect,
            fill=(8, 15, 16, 180),
            border=(25, 90, 80),
            radius=8
        )

        inner_overlay = pygame.Surface(
            (self.play_area.width, self.play_area.height),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            inner_overlay,
            (0, 0, 0, 18),
            inner_overlay.get_rect()
        )

        surface.blit(
            inner_overlay,
            self.play_area.topleft
        )

    def _draw_outside_map_background(self, surface):
        """
        Draws repeated ocean background behind the real tile map.
        """
        bg_size = self.outside_bg_size

        start_x = self.play_area.x + (self.camera.camera.x % bg_size) - bg_size
        start_y = self.play_area.y + (self.camera.camera.y % bg_size) - bg_size

        end_x = self.play_area.right + bg_size
        end_y = self.play_area.bottom + bg_size

        overlay = pygame.Surface((bg_size, bg_size), pygame.SRCALPHA)
        overlay.fill(self.ocean_overlay_color)

        for y in range(start_y, end_y, bg_size):
            for x in range(start_x, end_x, bg_size):
                surface.blit(self.outside_bg_tile, (x, y))
                surface.blit(overlay, (x, y))

    def _draw_world(self, surface):
        """
        Draws the tilemap, NPCs, player, and small map effects.
        """
        old_clip = surface.get_clip()
        surface.set_clip(self.play_area)

        self._draw_outside_map_background(surface)

        # =========================
        # TILE LAYERS
        # =========================
        for row_idx, row in enumerate(self.world_map.map_grid):
            for col_idx, tile_id in enumerate(row):
                tile_rect = pygame.Rect(
                    col_idx * self.tile_size,
                    row_idx * self.tile_size,
                    self.tile_size,
                    self.tile_size
                )

                screen_tile_rect = self._world_to_screen(tile_rect)

                # Draw grass base first.
                if "." in self.world_map.tiles:
                    surface.blit(
                        self.world_map.tiles["."],
                        screen_tile_rect
                    )

                # Draw special tile on top.
                if tile_id != "." and tile_id in self.world_map.tiles:
                    surface.blit(
                        self.world_map.tiles[tile_id],
                        screen_tile_rect
                    )

                    if tile_id in self.encounter_tiles:
                        self._draw_encounter_tile_glow(
                            surface,
                            screen_tile_rect
                        )

        # =========================
        # NPCS + PLAYER DRAW ORDER
        # =========================
        draw_items = []

        for npc in self.npcs:
            if self._is_npc_active(npc):
                npc_screen_rect = self._world_to_screen(npc.rect)
                draw_items.append(
                    ("npc", npc, npc_screen_rect, npc_screen_rect.bottom)
                )

        player_screen_rect = self._world_to_screen(self.player.rect)
        draw_items.append(
            ("player", self.player, player_screen_rect, player_screen_rect.bottom)
        )

        draw_items.sort(key=lambda item: item[3])

        for item_type, obj, screen_rect, _ in draw_items:
            if item_type == "npc":
                self._draw_npc(surface, obj, screen_rect)
            else:
                self._draw_player(surface, screen_rect)

        self._draw_quest_tracker(surface)
        self._draw_map_status(surface)

        surface.set_clip(old_clip)

    def _draw_npc(self, surface, npc, npc_screen_rect):
        """
        Draws NPC sprite and name tag.
        """
        sprite_x = npc_screen_rect.x + getattr(npc, "draw_offset_x", 0)
        sprite_y = npc_screen_rect.y + getattr(npc, "draw_offset_y", 0)

        surface.blit(
            npc.sprite,
            (sprite_x, sprite_y)
        )

        name_surf = self.tiny_font.render(
            npc.name,
            True,
            UITheme.TEXT
        )

        name_x = npc_screen_rect.centerx - name_surf.get_width() // 2
        name_y = sprite_y - 22

        name_bg = pygame.Rect(
            name_x - 5,
            name_y - 2,
            name_surf.get_width() + 10,
            20
        )

        pygame.draw.rect(
            surface,
            (0, 0, 0),
            name_bg,
            border_radius=6
        )

        surface.blit(
            name_surf,
            (name_x, name_y)
        )

    def _draw_player(self, surface, player_screen_rect):
        """
        Draws the player sprite.
        """
        surface.blit(
            self.player.sprite,
            (
                player_screen_rect.x + self.player.draw_offset_x,
                player_screen_rect.y + self.player.draw_offset_y
            )
        )

    def _draw_encounter_tile_glow(self, surface, tile_rect):
        """
        Adds a subtle overlay to bush encounter tiles.
        """
        glow = pygame.Surface(
            (tile_rect.width, tile_rect.height),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            glow,
            (0, 255, 150, 20),
            glow.get_rect(),
            border_radius=4
        )

        pygame.draw.rect(
            glow,
            (0, 255, 150, 35),
            glow.get_rect(),
            1,
            border_radius=4
        )

        surface.blit(
            glow,
            tile_rect.topleft
        )

    def _draw_map_status(self, surface):
        """
        Small status text inside the map panel.
        """
        status_surface = self.tiny_font.render(
            self.status_message,
            True,
            UITheme.TEXT_DIM
        )

        bg_rect = pygame.Rect(
            self.play_area.x + 14,
            self.play_area.bottom - 32,
            status_surface.get_width() + 20,
            24
        )

        status_bg = pygame.Surface(
            (bg_rect.width, bg_rect.height),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            status_bg,
            (0, 0, 0, 120),
            status_bg.get_rect(),
            border_radius=6
        )

        surface.blit(
            status_bg,
            bg_rect.topleft
        )

        surface.blit(
            status_surface,
            (
                bg_rect.x + 10,
                bg_rect.y + 5
            )
        )

    def _draw_quest_tracker(self, surface):
        """
        Draws the current main objective inside the map panel.
        """
        quest_summary = self.screen_manager.game_session.quest_manager.get_current_summary()
        max_chars = 86

        if len(quest_summary) > max_chars:
            quest_summary = quest_summary[:max_chars - 3] + "..."

        title_surface = self.tiny_font.render(
            "MAIN QUEST",
            True,
            UITheme.ACCENT_GOLD
        )

        quest_surface = self.tiny_font.render(
            quest_summary,
            True,
            UITheme.TEXT
        )

        bg_rect = pygame.Rect(
            self.play_area.x + 14,
            self.play_area.y + 14,
            610,
            48
        )

        quest_bg = pygame.Surface(
            (bg_rect.width, bg_rect.height),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            quest_bg,
            (0, 0, 0, 125),
            quest_bg.get_rect(),
            border_radius=6
        )

        surface.blit(quest_bg, bg_rect.topleft)
        surface.blit(title_surface, (bg_rect.x + 10, bg_rect.y + 6))
        surface.blit(quest_surface, (bg_rect.x + 10, bg_rect.y + 25))

    def _draw_bottom_hint(self, surface):
        """
        Draws bottom control hint bar.
        """
        self._draw_soft_panel(
            surface,
            self.bottom_panel,
            fill=(12, 18, 23, 210),
            border=(45, 65, 75),
            radius=8
        )

        hint = (
            "WASD / ARROWS: Move    "
            "E: Interact    "
            "I: Inventory    "
            "M: Mutations    "
            "K: Skills    "
            "ESC: Menu"
        )

        draw_text(
            surface,
            hint,
            self.small_font,
            UITheme.TEXT_DIM,
            self.bottom_panel.x + 24,
            self.bottom_panel.y + 12
        )

    # ============================================================
    # UI HELPERS
    # ============================================================

    def _draw_small_hp_bar(self, surface, x, y, width, height, current_hp, max_hp):
        """
        Draws compact HP bar.
        """
        bg_rect = pygame.Rect(x, y, width, height)

        pygame.draw.rect(
            surface,
            UITheme.HP_BG,
            bg_rect,
            border_radius=4
        )

        if max_hp > 0:
            ratio = max(0, min(1, current_hp / max_hp))

            fill_rect = pygame.Rect(
                x,
                y,
                int(width * ratio),
                height
            )

            pygame.draw.rect(
                surface,
                UITheme.HP_FILL,
                fill_rect,
                border_radius=4
            )

        pygame.draw.rect(
            surface,
            (15, 25, 25),
            bg_rect,
            1,
            border_radius=4
        )

    def _draw_soft_panel(self, surface, rect, fill, border, radius=8):
        """
        Draws translucent panel with border.
        """
        panel_surface = pygame.Surface(
            (rect.width, rect.height),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            panel_surface,
            fill,
            pygame.Rect(0, 0, rect.width, rect.height),
            border_radius=radius
        )

        surface.blit(
            panel_surface,
            rect.topleft
        )

        pygame.draw.rect(
            surface,
            border,
            rect,
            2,
            border_radius=radius
        )