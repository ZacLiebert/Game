"""Exploration map screen."""

import math

import pygame
import random
from types import SimpleNamespace

from src.paths import resolve_asset_path
from src.screens.base_screen import BaseScreen
from src.entities.player import Player
from src.entities.npc import NPC
from src.graphics.clear_code_tmx_world import ClearCodeTmxWorld
from src.graphics.sprite_manager import SpriteManager
from src.graphics.camera import Camera
from src.screens.combat_screen import CombatScreen
from src.data_structures.sort_search import InventoryAlgorithms

from src.ui.theme import UITheme
from src.ui.fonts import get_font
from src.ui.widgets import draw_text


class MapScreen(BaseScreen):
    """Main exploration screen for movement, NPCs, quests, and encounters."""

    def __init__(self, screen_manager, map_id=None):
        """Set up initial state."""
        super().__init__(screen_manager)
        self.music_track = "map"

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

        # Outside-map background
        self.outside_bg_size = 256
        self.outside_bg_tile = SpriteManager.get_sprite(
            "outside_ocean.png",
            width=self.outside_bg_size,
            height=self.outside_bg_size
        )

        self.ocean_overlay_color = (0, 0, 0, 0)

        # Screen layout
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

        # Map data
        map_data = self.db.get_map_data(map_id)

        if not map_data or not map_data.get("tmx_file"):
            raise ValueError(f"Map '{map_id}' is missing a TMX file in assets/maps/maps.json")

        self.region_name = map_data.get("short_name", map_data.get("name", "Unknown Region"))

        # TMX map
        tmx_path = resolve_asset_path(map_data["tmx_file"])
        self.tmx_world = ClearCodeTmxWorld(tmx_path)
        self.map_pixel_width = self.tmx_world.width
        self.map_pixel_height = self.tmx_world.height

        player_position = session.player_position
        start_position = map_data.get("start_position")
        if start_position and tuple(player_position) == (128, 128):
            player_position = tuple(start_position)

        # Player setup
        self.player = Player(
            x=player_position[0],
            y=player_position[1],
            tile_size=self.tile_size
        )

        # NPC setup
        self.npcs = []

        if map_data:
            for n in map_data.get("npcs", []):
                new_npc = NPC(
                    name=n["name"],
                    x=n["x"],
                    y=n["y"],
                    enemy_ids=n.get("enemies", []),
                    sprite_filename=n.get("sprite", "sprites/npcs/story/sample_herbalist.png"),
                    npc_type=n.get("type", "farm"),
                    sprite_sheet=n.get("sprite_sheet", False),
                    dialogue=n.get("dialogue", []),
                    shop_items=n.get("shop_items", []),
                    sprite_rows=n.get("sprite_rows", 4),
                    sprite_cols=n.get("sprite_cols", 6),
                    sprite_width=n.get("sprite_width", 64),
                    sprite_height=n.get("sprite_height", 64)
                )
                new_npc.required_quest = n.get("required_quest")
                new_npc.battle_required_quest = n.get("battle_required_quest")
                new_npc.blocker = bool(n.get("blocker", False))
                new_npc.block_message_before_quest = n.get(
                    "block_message_before_quest",
                    f"{new_npc.name} blocks the way. Finish the current objective first."
                )

                blocker_rect = n.get("blocker_rect") or n.get("collision_rect")

                if blocker_rect and len(blocker_rect) == 4:
                    new_npc.custom_collision_rect = pygame.Rect(
                        int(blocker_rect[0]),
                        int(blocker_rect[1]),
                        int(blocker_rect[2]),
                        int(blocker_rect[3])
                    )
                    new_npc._sync_collision_rect()

                new_npc.defeated = session.is_npc_defeated(new_npc.name)
                self.npcs.append(new_npc)

        # Camera setup
        self.camera = Camera(
            self.play_area.width,
            self.play_area.height,
            self.map_pixel_width,
            self.map_pixel_height
        )

        # Random encounters
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

        self.status_message = "Talk to Dr. Biologist to learn what happened here."

        # Map animation state. Combat starts after a short transition so the
        # overworld does not cut instantly into the battle screen.
        self.pending_combat_npc = None
        self.combat_transition_start = 0
        self.combat_transition_duration = 520

    # Input

    def handle_event(self, event):
        """Handle the event."""
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                self.play_sfx("click")
                self.screen_manager.pop()

            elif event.key == pygame.K_i:
                self.play_sfx("click")
                from src.screens.inventory_screen import InventoryScreen
                self.screen_manager.push(InventoryScreen(self.screen_manager))

            elif event.key == pygame.K_m:
                self.play_sfx("click")
                from src.screens.mutation_screen import MutationScreen
                self.screen_manager.push(MutationScreen(self.screen_manager))

            elif event.key == pygame.K_k:
                self.play_sfx("click")
                from src.screens.skill_loadout_screen import SkillLoadoutScreen
                self.screen_manager.push(SkillLoadoutScreen(self.screen_manager))

            elif event.key == pygame.K_e:
                self._interact_with_nearby_npc()

    # Update

    def update(self):
        """Update this screen for the current frame."""
        if self._update_combat_transition():
            return

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
            if self._player_in_encounter_zone():
                self.status_message = "The grass rustles... unstable beasts may appear."
            else:
                self.status_message = self._get_contextual_status_message()

            if self._check_random_encounter():
                return

        nearby_npc = self._get_nearby_npc()

        if nearby_npc:
            self.status_message = f"Press E to interact with {nearby_npc.name}."


    def _get_contextual_status_message(self):
        """Return the contextual status message."""
        quest = self.screen_manager.game_session.quest_manager.get_current_quest()

        if not quest:
            return "The outbreak is contained. Return to camp or keep exploring."

        hint_by_quest = {
            "briefing": "Find Dr. Biologist at base camp for the emergency briefing.",
            "meet_team": "Speak with Mira and Kael so the whole team is ready.",
            "prepare_supplies": "Visit Quartermaster Rhea and review combat items.",
            "field_samples": "Enter tall grass to gather beast materials from wild mutants.",
            "first_evolution": "Open the Mutation screen and unlock two non-basic mutations.",
            "contain_bear": "Challenge the Mutant Bear blocking the eastern trail.",
            "final_boss": "Unlock four mutations, equip a skill, then defeat Alpha Chimera."
        }

        return hint_by_quest.get(quest["id"], "Follow the main quest marker.")

    # NPC interaction

    def _get_nearby_npc(self):
        """Return the nearby npc."""
        interaction_rect = self.player.rect.inflate(28, 28)

        for npc in self.npcs:
            if not self._is_npc_active(npc):
                continue

            target_rect = npc.rect

            if getattr(npc, "blocker", False) and hasattr(npc, "collision_rect"):
                target_rect = npc.collision_rect

            if interaction_rect.colliderect(target_rect.inflate(28, 28)):
                return npc

        return None

    def _interact_with_nearby_npc(self):
        """Start dialogue, shop, or combat with the nearby NPC."""
        npc = self._get_nearby_npc()

        if not npc:
            self.play_sfx("error")
            self.status_message = "No one nearby."
            return

        self.play_sfx("click")

        battle_required_quest = getattr(npc, "battle_required_quest", None)

        if battle_required_quest:
            quest_manager = self.screen_manager.game_session.quest_manager

            if not quest_manager.is_active(battle_required_quest):
                self.play_sfx("error")
                self.status_message = getattr(
                    npc,
                    "block_message_before_quest",
                    f"{npc.name} blocks the way. Finish the current objective first."
                )
                return

        if npc.npc_type == "final_boss":
            block_reason = self._get_final_boss_block_reason()

            if block_reason:
                self.play_sfx("error")
                self.status_message = block_reason
                return

        if npc.npc_type == "dialogue":
            from src.screens.dialogue_screen import DialogueScreen
            self.screen_manager.push(DialogueScreen(self.screen_manager, npc))

        elif npc.npc_type == "shop":
            self.screen_manager.game_session.quest_manager.record_talk(npc.name)
            from src.screens.shop_screen import ShopScreen
            self.screen_manager.push(ShopScreen(self.screen_manager, npc))

        else:
            self._start_combat_transition(npc)

    def _count_unlocked_non_basic_mutations(self):
        """Count unlocked mutations except Basic Form."""
        tree = self.screen_manager.game_session.mutation_tree

        if not tree:
            return 0

        return len([
            node_id for node_id in tree.get_unlocked_nodes()
            if node_id != "base"
        ])

    def _has_equipped_non_basic_skill(self):
        """Return whether Zac has a mutation skill equipped."""
        session = self.screen_manager.game_session
        session.skill_loadout = session.skill_loadout or ["basic_attack"]

        for skill_id in session.skill_loadout:
            if skill_id != "basic_attack":
                return True

        return False

    def _get_final_boss_block_reason(self):
        """Return the final boss block reason."""
        mutation_count = self._count_unlocked_non_basic_mutations()

        if mutation_count < 4:
            return (
                "Alpha Chimera is too unstable to approach. "
                f"Unlock 4 mutations first ({mutation_count}/4)."
            )

        if not self._has_equipped_non_basic_skill():
            return "Equip at least one non-basic skill with K before facing Alpha Chimera."

        return None

    # Map transitions

    def _start_combat_transition(self, npc, random_encounter=False):
        """Start the combat transition."""
        if self.pending_combat_npc is not None:
            return

        self.pending_combat_npc = npc
        self.combat_transition_start = pygame.time.get_ticks()

        if random_encounter:
            self.status_message = "The grass bursts open! A wild encounter begins!"
        elif getattr(npc, "blocker", False):
            self.status_message = f"{npc.name} roars and blocks the path!"
        else:
            self.status_message = f"{npc.name} challenges Zac!"

        self.play_sfx("alert")

    def _update_combat_transition(self):
        """Update the combat transition."""
        if self.pending_combat_npc is None:
            return False

        elapsed = pygame.time.get_ticks() - self.combat_transition_start

        if elapsed >= self.combat_transition_duration:
            npc = self.pending_combat_npc
            self.pending_combat_npc = None
            self.screen_manager.push(CombatScreen(self.screen_manager, npc))

        return True

    # Collision helpers

    def _get_static_collision_rects(self):
        """Return the static collision rects."""
        collision_rects = self.tmx_world.get_colliding_rects()
        collision_rects.extend(self._get_map_boundary_walls())
        return collision_rects

    def _get_active_npc_collision_rects(self):
        """Return the active npc collision rects."""
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
        """Return whether an NPC should appear on the map."""
        if npc.defeated:
            return False

        # Story blockers must remain visible before their battle quest becomes
        # active. Otherwise Zac can walk through the route before the story says
        # the pass is open. Interaction with the blocker decides whether combat
        # is allowed yet.
        if getattr(npc, "blocker", False):
            return True

        required_quest = getattr(npc, "required_quest", None)

        if not required_quest:
            return True

        quest_manager = self.screen_manager.game_session.quest_manager
        return quest_manager.is_active(required_quest)

    def _get_map_boundary_walls(self):
        """Return the map boundary walls."""
        thickness = self.tile_size

        return [
            pygame.Rect(
                -thickness,
                -thickness,
                self.map_pixel_width + thickness * 2,
                thickness
            ),
            pygame.Rect(
                -thickness,
                self.map_pixel_height,
                self.map_pixel_width + thickness * 2,
                thickness
            ),
            pygame.Rect(
                -thickness,
                0,
                thickness,
                self.map_pixel_height
            ),
            pygame.Rect(
                self.map_pixel_width,
                0,
                thickness,
                self.map_pixel_height
            )
        ]

    # Coordinate helpers

    def _world_to_screen(self, world_rect):
        """Convert a world position to screen coordinates."""
        screen_rect = self.camera.apply(world_rect)
        screen_rect.x += self.play_area.x
        screen_rect.y += self.play_area.y
        return screen_rect

    def _player_in_encounter_zone(self):
        """Return whether Zac is standing in an encounter zone."""
        return self.tmx_world.player_in_encounter_zone(self.player.collision_rect)

    def _get_weighted_encounter_pool(self):
        """Return the weighted encounter pool."""
        x = self.player.collision_rect.centerx
        y = self.player.collision_rect.centery
        session = self.screen_manager.game_session

        if x >= 2400:
            ids = ["e_tiger", "e_snake", "e_boar", "e_rabbit", "e_bat"]
            weights = [2, 2, 2, 1, 2]

            if session.is_npc_defeated("Mutant Bear"):
                ids.append("e_bear")
                weights.append(1)

            return ids, weights

        if y <= 1050:
            return ["e_bat", "e_snake", "e_rabbit", "e_tiger", "e_boar"], [4, 3, 2, 1, 1]

        if x <= 1850:
            return ["e_boar", "e_rabbit", "e_tiger", "e_snake", "e_bat"], [3, 3, 2, 1, 1]

        return self.random_enemy_ids, [1 for _ in self.random_enemy_ids]

    def _roll_random_enemy_team(self):
        """Choose a random enemy team from weighted encounters."""
        enemy_ids, weights = self._get_weighted_encounter_pool()
        return random.choices(enemy_ids, weights=weights, k=3)

    def _check_random_encounter(self):
        """Check random encounter."""
        if not self._player_in_encounter_zone():
            return False

        current_time = pygame.time.get_ticks()

        if current_time - self.last_encounter_time < self.encounter_cooldown_ms:
            return False

        if random.random() > self.encounter_chance:
            return False

        self.last_encounter_time = current_time

        enemy_ids = self._roll_random_enemy_team()

        encounter_npc = SimpleNamespace(
            name="Wild Encounter",
            enemy_ids=enemy_ids,
            npc_type="random",
            defeated=False
        )

        self._start_combat_transition(encounter_npc, random_encounter=True)
        return True

    # Drawing

    def draw(self, surface):
        """Draw this screen."""
        surface.fill((7, 10, 12))

        self._draw_background(surface)
        self._draw_top_hud(surface)
        self._draw_map_panel(surface)
        self._draw_world(surface)
        self._draw_combat_transition_overlay(surface)
        self._draw_bottom_hint(surface)

    def _draw_background(self, surface):
        """Draw the background."""
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

    def _get_hud_region_name(self):
        """Return the hud region name."""
        name = str(self.region_name or "Unknown")
        if " - " in name:
            name = name.split(" - ", 1)[0]
        if len(name) > 18:
            name = name[:17].rstrip() + "…"
        return name.upper()

    def _draw_top_hud(self, surface):
        """Draw the top hud."""
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
            self._get_hud_region_name(),
            self.small_font,
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
        item_count = session.inventory.get_total_item_count()

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
        """Draw the map panel."""
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
        """Draw the outside map background."""
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
        """Draw the world."""
        old_clip = surface.get_clip()
        surface.set_clip(self.play_area)

        self._draw_outside_map_background(surface)
        self.tmx_world.draw_background(surface, self.camera, self.play_area)
        self._draw_tmx_encounter_zone_effects(surface)

        draw_items = []

        for item in self.tmx_world.get_visible_main_items(self.camera):
            draw_items.append(("tmx", item, None, item.y_sort))

        for npc in self.npcs:
            if self._is_npc_active(npc):
                npc_screen_rect = self._world_to_screen(npc.rect)
                draw_items.append(("npc", npc, npc_screen_rect, npc.rect.bottom))

        player_screen_rect = self._world_to_screen(self.player.rect)
        draw_items.append(("player", self.player, player_screen_rect, self.player.rect.bottom))

        # Rendering order only: draw lower objects first based on y-sort value.
        # Uses custom QuickSort helper instead of Python list.sort() so DSA
        # requirements remain self-coded even in render ordering.
        draw_items = InventoryAlgorithms.quick_sort_by_key(
            draw_items,
            lambda item: item[3]
        )

        for item_type, obj, screen_rect, _ in draw_items:
            if item_type == "tmx":
                self.tmx_world.draw_item(surface, obj, self.camera, self.play_area)
            elif item_type == "npc":
                self._draw_npc(surface, obj, screen_rect)
            else:
                self._draw_player(surface, screen_rect)

        self.tmx_world.draw_foreground(surface, self.camera, self.play_area)

        self._draw_quest_tracker(surface)
        self._draw_map_status(surface)

        surface.set_clip(old_clip)

    def _is_boss_marker(self, npc):
        """Return whether an NPC should show a boss marker."""
        return getattr(npc, "npc_type", "") in ("boss", "final_boss")


    def _draw_boss_shadow_pulse(self, surface, npc, npc_screen_rect):
        """Draw the boss shadow pulse."""
        pulse = npc.get_attention_pulse() if hasattr(npc, "get_attention_pulse") else 0.5
        sprite_width = getattr(npc, "sprite_width", npc_screen_rect.width)
        width = int(max(72, sprite_width * (0.72 + 0.08 * pulse)))
        height = int(max(18, sprite_width * (0.16 + 0.03 * pulse)))
        shadow = pygame.Surface((width, height), pygame.SRCALPHA)
        alpha = 54 + int(35 * pulse)
        pygame.draw.ellipse(shadow, (10, 4, 16, alpha), shadow.get_rect())
        surface.blit(
            shadow,
            (
                npc_screen_rect.centerx - width // 2,
                npc_screen_rect.bottom - height // 2 + 8,
            ),
        )

    def _draw_npc(self, surface, npc, npc_screen_rect):
        """Draw the npc."""
        bob_y = 0
        if hasattr(npc, "get_idle_bob_offset"):
            bob_y = npc.get_idle_bob_offset()

        sprite_x = npc_screen_rect.x + getattr(npc, "draw_offset_x", 0)
        sprite_y = npc_screen_rect.y + getattr(npc, "draw_offset_y", 0) + bob_y

        if self._is_boss_marker(npc):
            self._draw_boss_shadow_pulse(surface, npc, npc_screen_rect)

        if getattr(npc, "blocker", False):
            self._draw_blocker_aura(surface, npc, npc_screen_rect)

        surface.blit(
            npc.sprite,
            (sprite_x, sprite_y)
        )

        if getattr(npc, "blocker", False) and self._player_close_to_npc(npc):
            self._draw_attention_marker(surface, npc_screen_rect, sprite_y)

        is_nearby = self._player_close_to_npc(npc)
        is_objective = self._is_current_objective_target(npc)

        if is_objective:
            self._draw_objective_marker(surface, npc_screen_rect, sprite_y)

        if is_nearby:
            self._draw_npc_name_tag(surface, npc, npc_screen_rect, sprite_y)


    def _get_current_objective_targets(self):
        """Return the current objective targets."""
        quest_manager = self.screen_manager.game_session.quest_manager
        quest = quest_manager.get_current_quest()

        if not quest:
            return set()

        target = quest.get("target")
        if not target:
            return set()

        if isinstance(target, str):
            return {target}

        return {str(name) for name in target}

    def _is_current_objective_target(self, npc):
        """Return whether an NPC is the current objective target."""
        return npc.name in self._get_current_objective_targets()

    def _draw_npc_name_tag(self, surface, npc, npc_screen_rect, sprite_y):
        """Draw the npc name tag."""
        name_surf = self.tiny_font.render(npc.name, True, UITheme.TEXT)
        pad_x = 12
        pad_y = 5
        name_x = npc_screen_rect.centerx - name_surf.get_width() // 2
        name_y = sprite_y - 28

        name_bg = pygame.Rect(
            name_x - pad_x,
            name_y - pad_y,
            name_surf.get_width() + pad_x * 2,
            name_surf.get_height() + pad_y * 2
        )

        bubble = pygame.Surface((name_bg.width, name_bg.height), pygame.SRCALPHA)
        pygame.draw.rect(bubble, (8, 8, 10, 205), bubble.get_rect(), border_radius=9)
        pygame.draw.rect(bubble, (255, 215, 110, 185), bubble.get_rect(), 2, border_radius=9)
        surface.blit(bubble, name_bg.topleft)
        surface.blit(name_surf, (name_x, name_y))

    def _draw_objective_marker(self, surface, npc_screen_rect, sprite_y):
        """Draw the objective marker."""
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 170.0)
        marker_y = sprite_y - 16 - int(4 * pulse)
        center_x = npc_screen_rect.centerx

        diamond = [
            (center_x, marker_y - 10),
            (center_x + 10, marker_y),
            (center_x, marker_y + 10),
            (center_x - 10, marker_y),
        ]
        pygame.draw.polygon(surface, (255, 215, 85), diamond)
        pygame.draw.polygon(surface, (85, 45, 10), diamond, 2)
        inner = [
            (center_x, marker_y - 4),
            (center_x + 4, marker_y),
            (center_x, marker_y + 4),
            (center_x - 4, marker_y),
        ]
        pygame.draw.polygon(surface, (255, 250, 220), inner)

    def _draw_player(self, surface, player_screen_rect):
        """Draw the player."""
        surface.blit(
            self.player.sprite,
            (
                player_screen_rect.x + self.player.draw_offset_x,
                player_screen_rect.y + self.player.draw_offset_y
            )
        )

    def _draw_encounter_tile_glow(self, surface, tile_rect):
        """Draw the encounter tile glow."""
        glow = pygame.Surface(
            (tile_rect.width, tile_rect.height),
            pygame.SRCALPHA
        )

        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 240.0)
        alpha_fill = 18 + int(24 * pulse)
        alpha_border = 30 + int(35 * pulse)

        pygame.draw.rect(
            glow,
            (0, 255, 150, alpha_fill),
            glow.get_rect(),
            border_radius=4
        )

        pygame.draw.rect(
            glow,
            (0, 255, 150, alpha_border),
            glow.get_rect(),
            1,
            border_radius=4
        )

        surface.blit(
            glow,
            tile_rect.topleft
        )

    def _draw_tmx_encounter_zone_effects(self, surface):
        """Draw the tmx encounter zone effects."""
        if not self.tmx_world:
            return

        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 260.0)
        player_inside = self._player_in_encounter_zone()

        for rect in getattr(self.tmx_world, "encounter_rects", []):
            screen_rect = self._world_to_screen(rect)

            if not screen_rect.colliderect(self.play_area):
                continue

            alpha = 14 + int(22 * pulse)
            if player_inside and rect.colliderect(self.player.collision_rect):
                alpha += 20

            shimmer = pygame.Surface((screen_rect.width, screen_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shimmer, (0, 255, 150, alpha), shimmer.get_rect(), border_radius=6)

            # Short diagonal strokes make the grass feel like it is rustling.
            stroke_alpha = min(95, alpha + 30)
            offset = int((pygame.time.get_ticks() / 65.0) % 24)
            for x in range(-24 + offset, screen_rect.width, 32):
                pygame.draw.line(
                    shimmer,
                    (170, 255, 200, stroke_alpha),
                    (x, screen_rect.height),
                    (x + 18, 0),
                    1
                )

            surface.blit(shimmer, screen_rect.topleft)

    def _draw_blocker_aura(self, surface, npc, npc_screen_rect):
        """Draw the blocker aura."""
        pulse = npc.get_attention_pulse() if hasattr(npc, "get_attention_pulse") else 0.5
        sprite_width = getattr(npc, "sprite_width", npc_screen_rect.width)
        width = max(72, int(sprite_width * (0.85 + 0.08 * pulse)))
        height = max(18, int(width * 0.24))
        aura = pygame.Surface((width, height), pygame.SRCALPHA)
        alpha = 34 + int(42 * pulse)

        if getattr(npc, "npc_type", "") == "final_boss":
            fill = (155, 70, 255, alpha)
            outline = (255, 85, 210, alpha // 2)
        else:
            fill = (255, 105, 85, alpha)
            outline = (150, 65, 255, alpha // 2)

        pygame.draw.ellipse(aura, fill, aura.get_rect())
        pygame.draw.ellipse(aura, outline, aura.get_rect(), 2)
        surface.blit(
            aura,
            (
                npc_screen_rect.centerx - width // 2,
                npc_screen_rect.bottom - 14,
            )
        )

    def _player_close_to_npc(self, npc):
        """Return whether Zac is close enough to interact."""
        interaction_rect = self.player.rect.inflate(160, 140)
        target = getattr(npc, "collision_rect", npc.rect)
        return interaction_rect.colliderect(target)

    def _draw_attention_marker(self, surface, npc_screen_rect, sprite_y):
        """Draw the attention marker."""
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 115.0)
        marker_y = sprite_y - 42 - int(5 * pulse)
        center_x = npc_screen_rect.centerx

        bubble_rect = pygame.Rect(center_x - 13, marker_y, 26, 30)
        pygame.draw.ellipse(surface, (255, 235, 80), bubble_rect)
        pygame.draw.ellipse(surface, (80, 35, 20), bubble_rect, 2)

        exclaim = self.small_font.render("!", True, (70, 28, 18))
        surface.blit(
            exclaim,
            (center_x - exclaim.get_width() // 2, marker_y + 1)
        )

    def _draw_combat_transition_overlay(self, surface):
        """Draw the combat transition overlay."""
        if self.pending_combat_npc is None:
            return

        elapsed = pygame.time.get_ticks() - self.combat_transition_start
        progress = max(0.0, min(1.0, elapsed / self.combat_transition_duration))
        flash = 0.5 + 0.5 * math.sin(progress * math.pi * 6)

        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((255, 245, 190, int(55 * flash)))
        surface.blit(overlay, (0, 0))

        # Closing letterbox bars make boss/random encounters feel intentional.
        bar_h = int(58 * progress)
        pygame.draw.rect(surface, (0, 0, 0), pygame.Rect(0, 0, surface.get_width(), bar_h))
        pygame.draw.rect(
            surface,
            (0, 0, 0),
            pygame.Rect(0, surface.get_height() - bar_h, surface.get_width(), bar_h)
        )

    def _draw_map_status(self, surface):
        """Draw the map status."""
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
        """Draw the quest tracker."""
        bg_rect = pygame.Rect(
            self.play_area.x + 14,
            self.play_area.y + 14,
            610,
            48
        )

        quest_summary = self.screen_manager.game_session.quest_manager.get_current_summary()
        quest_summary = self._fit_text_to_width(
            quest_summary,
            self.tiny_font,
            bg_rect.width - 20
        )

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

    def _fit_text_to_width(self, text, font, max_width):
        """Shorten text so it fits inside a width."""
        text = str(text)

        if font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."

        while text and font.size(text + ellipsis)[0] > max_width:
            text = text[:-1]

        return text + ellipsis

    def _draw_bottom_hint(self, surface):
        """Draw the bottom hint."""
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

    # UI helpers

    def _draw_small_hp_bar(self, surface, x, y, width, height, current_hp, max_hp):
        """Draw the small hp bar."""
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
        """Draw the soft panel."""
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
