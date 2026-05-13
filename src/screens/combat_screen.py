"""Turn-based combat screen."""

import pygame
import random
import math

from src.paths import resolve_asset_path
from src.screens.base_screen import BaseScreen
from src.core.combat_manager import CombatManager
from src.core.enemy_skill_library import EnemySkillLibrary
from src.core.skill_library import SkillLibrary
from src.graphics.sprite_manager import SpriteManager
from src.data_structures.sort_search import InventoryAlgorithms

from src.ui.theme import UITheme
from src.ui.widgets import draw_button, draw_text


class CombatScreen(BaseScreen):
    """Turn-based battle screen."""

    def __init__(self, screen_manager, npc):
        """Set up initial state."""
        super().__init__(screen_manager)

        npc_type = getattr(npc, "npc_type", "farm")
        self.music_track = (
            "boss" if npc_type in ("boss", "final_boss") else "battle"
        )

        self.font = pygame.font.SysFont(None, UITheme.HEADER_SIZE)
        self.small_font = pygame.font.SysFont(None, UITheme.SMALL_SIZE)
        self.action_font = pygame.font.SysFont(None, UITheme.BODY_SIZE)

        self.npc = npc
        session = self.screen_manager.game_session
        self.db = session.db

        players = session.party

        enemies = [
            self.db.create_entity(eid, is_enemy=True)
            for eid in self.npc.enemy_ids
        ]
        enemies = [e for e in enemies if e is not None]

        self.combat_manager = CombatManager(players, enemies)
        self.combat_manager.prepare_round()

        self.combat_log = ["Battle Started! Determining first turn..."]

        self.state = "NEXT_TURN"
        self.current_actor = None
        self.selected_action = None
        self.selected_item = None
        self.target_idx = 0
        self.item_idx = 0
        self.ally_target_idx = 0
        self.pending_ending = False

        self.delay_timer = pygame.time.get_ticks()
        self.base_delay = 1200
        self.fast_delay = 200
        self.current_delay = self.base_delay
        self.is_fast_forward = False

        self.skill_button_rects = []
        self.item_button_rects = []

        # Stores clickable target areas:
        # [(rect, entity), ...]
        self.enemy_card_rects = []
        self.ally_card_rects = []

        self.sprite_cache = {}

        self.battle_bg = self._load_optional_background("battle_forest.png")

        self.flip_enemy_sprites = False

        # Lightweight combat animation state. These are visual-only effects;
        # battle logic still resolves immediately so the turn system stays simple.
        self.entity_screen_positions = {}
        self.sprite_effects = {}
        self.combat_popups = []
        self.screen_shake_until = 0
        self.screen_shake_strength = 0

    # Setup and asset helpers

    def _load_optional_background(self, filename):
        """Load the optional background."""
        path = resolve_asset_path(filename)

        if not path.exists():
            return None

        try:
            return pygame.image.load(str(path)).convert()
        except Exception:
            return None

    def _trim_transparent_padding(self, image):
        """Trim transparent padding."""
        rect = image.get_bounding_rect()

        if rect.width <= 0 or rect.height <= 0:
            return image

        return image.subsurface(rect).copy()

    def _get_entity_sprite(self, entity, max_width=130, max_height=130):
        """Return the entity sprite."""
        sprite_name = getattr(entity, "sprite_name", "zac_battle.png")
        cache_key = (sprite_name, max_width, max_height)

        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]

        path = resolve_asset_path(sprite_name)

        if path.exists():
            try:
                image = pygame.image.load(str(path)).convert_alpha()
                image = self._trim_transparent_padding(image)
            except Exception:
                image = SpriteManager.get_sprite(
                    sprite_name,
                    width=max_width,
                    height=max_height
                )
                self.sprite_cache[cache_key] = image
                return image

            original_w = image.get_width()
            original_h = image.get_height()

            if original_w <= 0 or original_h <= 0:
                image = SpriteManager.get_sprite(
                    sprite_name,
                    width=max_width,
                    height=max_height
                )
                self.sprite_cache[cache_key] = image
                return image

            scale = min(
                max_width / original_w,
                max_height / original_h
            )

            new_w = max(1, int(original_w * scale))
            new_h = max(1, int(original_h * scale))

            sprite = pygame.transform.smoothscale(
                image,
                (new_w, new_h)
            )

            self.sprite_cache[cache_key] = sprite
            return sprite

        sprite = SpriteManager.get_sprite(
            sprite_name,
            width=max_width,
            height=max_height
        )

        self.sprite_cache[cache_key] = sprite
        return sprite

    # Action definitions

    def _get_player_actions(self):
        """Return the player actions."""
        actor = self.current_actor
        actor_id = getattr(actor, "entity_id", None)
        is_zac = actor_id == "p1"

        if not is_zac:
            skill_ids = SkillLibrary.get_ally_skill_ids(actor_id)
            actions = [SkillLibrary.build_action(skill_id) for skill_id in skill_ids]
            actions = actions[:SkillLibrary.MAX_LOADOUT_SIZE]

            for i, action in enumerate(actions):
                action["label"] = f"[{i + 1}] {action['name']}"

            return actions

        session = self.screen_manager.game_session
        tree = session.mutation_tree

        session.skill_loadout = SkillLibrary.sanitize_loadout(
            session.skill_loadout,
            tree
        )

        available_skill_ids = SkillLibrary.get_available_skill_ids(tree)
        available_set = set(available_skill_ids)

        selected_skill_ids = []

        for skill_id in session.skill_loadout:
            if skill_id in available_set and skill_id not in selected_skill_ids:
                selected_skill_ids.append(skill_id)

        if "basic_attack" not in selected_skill_ids:
            selected_skill_ids.insert(0, "basic_attack")

        selected_skill_ids = selected_skill_ids[:SkillLibrary.MAX_LOADOUT_SIZE]

        actions = [
            SkillLibrary.build_action(skill_id)
            for skill_id in selected_skill_ids
        ]

        if self._get_usable_combat_items():
            if len(actions) >= SkillLibrary.MAX_LOADOUT_SIZE:
                actions = actions[:SkillLibrary.MAX_LOADOUT_SIZE - 1]

            actions.append({
                "name": "Items",
                "mult": 0,
                "target": "item_menu",
                "is_item_menu": True
            })

        for i, action in enumerate(actions):
            action["label"] = f"[{i + 1}] {action['name']}"

        return actions

    def _get_item_target_candidates(self, item):
        """Return the item target candidates."""
        if item is None:
            return []

        party = self.combat_manager.player_team

        if getattr(item, "needs_defeated_target", lambda: False)():
            candidates = [member for member in party if not member.is_alive()]
        else:
            candidates = [member for member in party if member.is_alive()]

        return [
            member for member in candidates
            if getattr(item, "can_use_on", lambda _target: False)(member)
        ]

    def _get_ally_action_targets(self, action):
        """Return the ally action targets."""
        if action is None:
            return []

        target_type = action.get("target")

        if target_type == "self":
            return [self.current_actor] if self.current_actor and self.current_actor.is_alive() else []

        if target_type != "ally":
            return []

        targets = [
            member for member in self.combat_manager.player_team
            if member.is_alive()
        ]

        clear_statuses = action.get("clear_statuses", [])

        if action.get("heal_amount", 0) > 0 or clear_statuses:
            useful_targets = []

            for member in targets:
                is_wounded = member.current_hp < member.max_hp
                has_clearable_status = any(
                    effect.get("type") in clear_statuses
                    for effect in getattr(member, "status_effects", [])
                )

                if is_wounded or has_clearable_status:
                    useful_targets.append(member)

            if useful_targets:
                return useful_targets

        return targets

    def _get_current_ally_targets(self):
        """Return the current ally targets."""
        if self.selected_item is not None:
            return self._get_item_target_candidates(self.selected_item)

        return self._get_ally_action_targets(self.selected_action)

    def _start_ally_targeting(self):
        """Start the ally targeting."""
        targets = self._get_ally_action_targets(self.selected_action)

        if not targets:
            self.play_sfx("error")
            action_name = self.selected_action.get("name", "support skill")
            self.combat_log.append(f"No valid ally target for {action_name}.")
            self._trim_log()
            return

        self.selected_item = None
        self.ally_target_idx = 0
        self.state = "PLAYER_ALLY_TARGET"
        self.combat_log.append(f"Select ally target for {self.selected_action['name']}.")
        self._trim_log()

    def _execute_selected_ally_action_on_target(self, target):
        """Execute the selected ally action on target."""
        if self.selected_action is None or target is None:
            return

        self._execute_action(self.current_actor, target, self.selected_action)

    def _get_usable_combat_items(self):
        """Return the usable combat items."""
        session = self.screen_manager.game_session
        items = []

        for item in session.inventory.get_unique_items():
            if getattr(item, "item_type", "") != "potion":
                continue

            if session.inventory.get_item_count(item.item_id) <= 0:
                continue

            if self._get_item_target_candidates(item):
                items.append(item)

        return items

    def _open_item_menu(self):
        """Open the combat item menu."""
        items = self._get_usable_combat_items()

        if not items:
            self.play_sfx("error")
            self.combat_log.append("No usable combat items are available.")
            self._trim_log()
            return

        self.item_idx = min(self.item_idx, len(items) - 1)
        self.item_idx = max(0, self.item_idx)
        self.state = "PLAYER_ITEM"
        self.combat_log.append("Choose a consumable item.")
        self._trim_log()

    def _get_visible_item_window(self, window_size=4):
        """Return the visible item window."""
        items = self._get_usable_combat_items()

        if not items:
            return [], 0

        self.item_idx = max(0, min(self.item_idx, len(items) - 1))
        start = max(0, self.item_idx - window_size + 1)
        max_start = max(0, len(items) - window_size)
        start = min(start, max_start)

        return items[start:start + window_size], start

    def _choose_combat_item(self, absolute_index=None):
        """Choose combat item."""
        items = self._get_usable_combat_items()

        if not items:
            self.play_sfx("error")
            self.state = "PLAYER_ACTION"
            self.combat_log.append("No usable combat items are available.")
            self._trim_log()
            return

        if absolute_index is None:
            absolute_index = self.item_idx

        if absolute_index < 0 or absolute_index >= len(items):
            return

        self.item_idx = absolute_index
        self.selected_item = items[self.item_idx]
        self.selected_action = None
        targets = self._get_item_target_candidates(self.selected_item)

        if not targets:
            self.play_sfx("error")
            self.combat_log.append(f"No valid target for {self.selected_item.name}.")
            self._trim_log()
            return

        self.ally_target_idx = 0
        self.state = "PLAYER_ALLY_TARGET"
        self.combat_log.append(f"Select ally target for {self.selected_item.name}.")
        self._trim_log()

    def _execute_selected_item_on_target(self, target):
        """Execute the selected item on target."""
        if self.selected_item is None or target is None:
            return

        action = {
            "name": self.selected_item.name,
            "mult": 0,
            "target": "ally",
            "item_id": self.selected_item.item_id,
            "item": self.selected_item
        }

        self._execute_action(self.current_actor, target, action)

    def _choose_player_action(self, index):
        """Choose player action."""
        actions = self._get_player_actions()

        if index < 0 or index >= len(actions):
            return

        self.selected_action = actions[index]

        if self.selected_action.get("is_item_menu"):
            self._open_item_menu()
        elif self.selected_action.get("target") == "self":
            self._execute_action(
                self.current_actor,
                self.current_actor,
                self.selected_action
            )
        elif self.selected_action.get("target") == "ally":
            self._start_ally_targeting()
        else:
            self._start_targeting()

    # Input

    def handle_event(self, event):
        """Handle the event."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            if self.state == "PLAYER_ACTION":
                for i, rect in enumerate(self.skill_button_rects):
                    if rect.collidepoint(mouse_pos):
                        self._choose_player_action(i)
                        break

            elif self.state == "PLAYER_ITEM":
                _visible_items, start_index = self._get_visible_item_window()

                for offset, rect in enumerate(self.item_button_rects):
                    if rect.collidepoint(mouse_pos):
                        self._choose_combat_item(start_index + offset)
                        break

            elif self.state == "PLAYER_ALLY_TARGET":
                targets = self._get_current_ally_targets()

                for rect, ally in self.ally_card_rects:
                    if rect.collidepoint(mouse_pos) and ally in targets:
                        if self.selected_item is not None:
                            self._execute_selected_item_on_target(ally)
                        else:
                            self._execute_selected_ally_action_on_target(ally)
                        break

            elif self.state == "PLAYER_TARGET":
                alive_enemies = self._get_alive_enemies()

                for rect, enemy in self.enemy_card_rects:
                    if rect.collidepoint(mouse_pos) and enemy in alive_enemies:
                        self.target_idx = alive_enemies.index(enemy)

                        self._execute_action(
                            self.current_actor,
                            enemy,
                            self.selected_action
                        )
                        break

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._handle_escape_key()
                return

            elif event.key == pygame.K_f:
                self.play_sfx("click")
                self.is_fast_forward = not self.is_fast_forward
                self.current_delay = (
                    self.fast_delay
                    if self.is_fast_forward
                    else self.base_delay
                )

            if self.state == "GAME_OVER":
                if event.key == pygame.K_RETURN:
                    self.play_sfx("click")
                    if self.pending_ending:
                        self.screen_manager.pop()

                        from src.screens.ending_screen import EndingScreen
                        self.screen_manager.push(EndingScreen(self.screen_manager))
                        return

                    self.screen_manager.pop()
                return

            elif self.state == "PLAYER_ACTION":
                if event.key == pygame.K_1:
                    self.play_sfx("click")
                    self._choose_player_action(0)

                elif event.key == pygame.K_2:
                    self.play_sfx("click")
                    self._choose_player_action(1)

                elif event.key == pygame.K_3:
                    self.play_sfx("click")
                    self._choose_player_action(2)

                elif event.key == pygame.K_4:
                    self.play_sfx("click")
                    self._choose_player_action(3)

            elif self.state == "PLAYER_ITEM":
                items = self._get_usable_combat_items()

                if not items:
                    self.state = "PLAYER_ACTION"
                    return

                if event.key == pygame.K_UP:
                    self.play_sfx("click")
                    self.item_idx = max(0, self.item_idx - 1)

                elif event.key == pygame.K_DOWN:
                    self.play_sfx("click")
                    self.item_idx = min(len(items) - 1, self.item_idx + 1)

                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    visible_items, start_index = self._get_visible_item_window()
                    key_to_offset = {
                        pygame.K_1: 0,
                        pygame.K_2: 1,
                        pygame.K_3: 2,
                        pygame.K_4: 3
                    }
                    offset = key_to_offset.get(event.key, 0)
                    absolute_index = start_index + offset

                    if 0 <= offset < len(visible_items):
                        self.play_sfx("click")
                        self._choose_combat_item(absolute_index)

                elif event.key == pygame.K_RETURN:
                    self.play_sfx("click")
                    self._choose_combat_item(self.item_idx)

            elif self.state == "PLAYER_ALLY_TARGET":
                targets = self._get_current_ally_targets()

                if not targets:
                    self.state = "PLAYER_ITEM" if self.selected_item is not None else "PLAYER_ACTION"
                    return

                if event.key in (pygame.K_UP, pygame.K_LEFT):
                    self.play_sfx("click")
                    self.ally_target_idx = (self.ally_target_idx - 1) % len(targets)

                elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                    self.play_sfx("click")
                    self.ally_target_idx = (self.ally_target_idx + 1) % len(targets)

                elif event.key == pygame.K_RETURN:
                    self.play_sfx("click")
                    target = targets[self.ally_target_idx]
                    if self.selected_item is not None:
                        self._execute_selected_item_on_target(target)
                    else:
                        self._execute_selected_ally_action_on_target(target)

            elif self.state == "PLAYER_TARGET":
                alive_enemies = self._get_alive_enemies()

                if not alive_enemies:
                    return

                if event.key == pygame.K_UP or event.key == pygame.K_LEFT:
                    self.play_sfx("click")
                    self.target_idx = (self.target_idx - 1) % len(alive_enemies)

                elif event.key == pygame.K_DOWN or event.key == pygame.K_RIGHT:
                    self.play_sfx("click")
                    self.target_idx = (self.target_idx + 1) % len(alive_enemies)

                elif event.key == pygame.K_RETURN:
                    self.play_sfx("click")
                    if self.target_idx >= len(alive_enemies):
                        self.target_idx = 0

                    target = alive_enemies[self.target_idx]

                    self._execute_action(
                        self.current_actor,
                        target,
                        self.selected_action
                    )

    def _handle_escape_key(self):
        """Handle the escape key."""
        if self.state == "PLAYER_ALLY_TARGET":
            self.play_sfx("click")
            self.state = "PLAYER_ITEM" if self.selected_item is not None else "PLAYER_ACTION"
            return

        if self.state == "PLAYER_ITEM":
            self.play_sfx("click")
            self.state = "PLAYER_ACTION"
            return

        if self.state == "GAME_OVER":
            if self.pending_ending:
                self.play_sfx("error")
                self.combat_log.append("Press [ENTER] to finish the story.")
                self._trim_log()
                return

            self.screen_manager.pop()
            return

        npc_type = getattr(self.npc, "npc_type", "farm")

        if npc_type in ("boss", "final_boss"):
            self.play_sfx("error")
            self.combat_log.append("You cannot escape from this battle!")
            self._trim_log()
            return

        self.screen_manager.pop()

    # Update and turn flow

    def update(self):
        """Update this screen for the current frame."""
        current_time = pygame.time.get_ticks()
        self._update_combat_animations(current_time)

        if self.state == "NEXT_TURN":
            if current_time - self.delay_timer > self.current_delay:
                self._start_turn()

        elif self.state == "ENEMY_TURN":
            if current_time - self.delay_timer > self.current_delay:
                self._execute_enemy_turn()

    def _start_turn(self):
        """Start the turn."""
        self.current_actor = self.combat_manager.get_next_in_line()

        if not self.current_actor:
            self.combat_log.append("--- Round over! Rebuilding turn order... ---")
            self.combat_manager.prepare_round()
            self.state = "NEXT_TURN"
            self.delay_timer = pygame.time.get_ticks()
            self._trim_log()
            return

        if hasattr(self.current_actor, "process_start_turn_status"):
            status_messages, skip_turn = self.current_actor.process_start_turn_status()
        else:
            status_messages, skip_turn = [], False

        for msg in status_messages:
            self.combat_log.append(msg)

        if not self.current_actor.is_alive():
            self._check_end_condition()

            if self.state != "GAME_OVER":
                self.state = "NEXT_TURN"
                self.delay_timer = pygame.time.get_ticks()

            self._trim_log()
            return

        if skip_turn:
            self.combat_log.append(
                f"{self.current_actor.name}'s turn was skipped."
            )
            self.state = "NEXT_TURN"
            self.delay_timer = pygame.time.get_ticks()
            self._trim_log()
            return

        if self.current_actor in self.combat_manager.player_team:
            self.state = "PLAYER_ACTION"
            self.combat_log.append(
                f"> {self.current_actor.name}'s turn! Choose an action."
            )
        else:
            self.state = "ENEMY_TURN"
            self.combat_log.append(
                f"> {self.current_actor.name} is preparing to attack..."
            )
            self.delay_timer = pygame.time.get_ticks()

        self._trim_log()

    def _start_targeting(self):
        """Start the targeting."""
        alive_enemies = self._get_alive_enemies()

        if not alive_enemies:
            return

        self.state = "PLAYER_TARGET"
        self.target_idx = 0

        self.combat_log.append(
            f"Select target for {self.selected_action['name']}."
        )
        self._trim_log()

    # Combat animation helpers

    def _update_combat_animations(self, current_time):
        """Update the combat animations."""
        self.combat_popups = [
            popup for popup in self.combat_popups
            if current_time - popup["start"] <= popup["duration"]
        ]

        for entity_id, effect in list(self.sprite_effects.items()):
            for key in list(effect.keys()):
                if key.endswith("_until") and current_time > effect[key]:
                    del effect[key]

            if not effect:
                del self.sprite_effects[entity_id]

        if current_time > self.screen_shake_until:
            self.screen_shake_strength = 0

    def _remember_entity_position(self, entity, center_x, ground_y, sprite_rect):
        """Remember entity position."""
        self.entity_screen_positions[id(entity)] = {
            "center": (center_x, ground_y),
            "popup": (center_x, sprite_rect.y + 12),
            "sprite_rect": sprite_rect.copy()
        }

    def _get_entity_position(self, entity):
        """Return the entity position."""
        if entity is None:
            return (640, 320)

        info = self.entity_screen_positions.get(id(entity))

        if info:
            return info.get("center", (640, 320))

        return (640, 320)

    def _spawn_popup(self, entity, text, color, duration=900):
        """Spawn popup."""
        info = self.entity_screen_positions.get(id(entity), {})
        x, y = info.get("popup", self._get_entity_position(entity))

        self.combat_popups.append({
            "text": str(text),
            "x": x,
            "y": y,
            "color": color,
            "start": pygame.time.get_ticks(),
            "duration": duration
        })

    def _start_attack_animation(self, actor, target=None, did_hit=False):
        """Start the attack animation."""
        now = pygame.time.get_ticks()
        actor_id = id(actor)
        effect = self.sprite_effects.setdefault(actor_id, {})
        effect["attack_start"] = now
        effect["attack_until"] = now + 320
        effect["attack_dir"] = self._get_attack_direction(actor, target)

        if did_hit and target is not None and target is not actor:
            target_effect = self.sprite_effects.setdefault(id(target), {})
            target_effect["hit_until"] = now + 360
            target_effect["hit_start"] = now

            self.screen_shake_until = now + 220
            self.screen_shake_strength = 5

    def _get_attack_direction(self, actor, target):
        """Return the attack direction."""
        if actor is None or target is None:
            return 1

        actor_x, _ = self._get_entity_position(actor)
        target_x, _ = self._get_entity_position(target)

        if actor_x == target_x:
            return 1 if actor in self.combat_manager.player_team else -1

        return 1 if target_x > actor_x else -1

    def _get_entity_animation_offset(self, entity):
        """Return the entity animation offset."""
        effect = self.sprite_effects.get(id(entity), {})
        now = pygame.time.get_ticks()
        offset_x = 0
        offset_y = 0

        if "attack_until" in effect:
            duration = max(1, effect["attack_until"] - effect.get("attack_start", now))
            elapsed = max(0, now - effect.get("attack_start", now))
            progress = min(1.0, elapsed / duration)
            lunge = math.sin(progress * math.pi) * 24
            offset_x += int(lunge * effect.get("attack_dir", 1))
            offset_y -= int(math.sin(progress * math.pi) * 4)

        if "hit_until" in effect:
            duration = max(1, effect["hit_until"] - effect.get("hit_start", now))
            elapsed = max(0, now - effect.get("hit_start", now))
            progress = min(1.0, elapsed / duration)
            shake = int((1.0 - progress) * 7)
            if shake > 0:
                offset_x += shake if (now // 45) % 2 == 0 else -shake

        return offset_x, offset_y

    def _get_screen_shake_offset(self):
        """Return the screen shake offset."""
        now = pygame.time.get_ticks()

        if now > self.screen_shake_until or self.screen_shake_strength <= 0:
            return (0, 0)

        strength = self.screen_shake_strength
        return (
            random.randint(-strength, strength),
            random.randint(-strength, strength)
        )

    def _is_hit_flashing(self, entity):
        """Return whether a unit is currently flashing from a hit."""
        effect = self.sprite_effects.get(id(entity), {})
        return pygame.time.get_ticks() <= effect.get("hit_until", 0)

    def _flash_sprite(self, sprite):
        """Flash sprite."""
        flash = sprite.copy()
        flash.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
        return flash

    def _draw_combat_popups(self, surface):
        """Draw the combat popups."""
        now = pygame.time.get_ticks()

        for popup in self.combat_popups:
            age = now - popup["start"]
            duration = max(1, popup["duration"])
            progress = min(1.0, age / duration)
            alpha = max(0, int(255 * (1.0 - progress)))
            y = popup["y"] - int(46 * progress)

            text_surface = self.action_font.render(
                popup["text"],
                True,
                popup["color"]
            ).convert_alpha()
            text_surface.set_alpha(alpha)

            rect = text_surface.get_rect(center=(popup["x"], y))

            shadow = text_surface.copy()
            shadow.fill((0, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_MULT)

            surface.blit(shadow, (rect.x + 2, rect.y + 2))
            surface.blit(text_surface, rect.topleft)

    # Action execution

    def _execute_action(self, actor, target, action):
        """Run the selected menu or combat action."""
        if actor is None or action is None:
            return

        action_name = action.get("name", "Unknown Action")
        damage_mult = action.get("mult", 1.0)

        if action.get("item_id"):
            item_id = action.get("item_id")
            item = action.get("item") or self.db.get_item(item_id)
            session = self.screen_manager.game_session

            if item is None or not getattr(item, "can_use_on", lambda _target: False)(target):
                self.play_sfx("error")
                self._spawn_popup(actor, "BAD TARGET", UITheme.WARNING)
                self.combat_log.append(f"* {action_name} has no valid target.")
                self.state = "PLAYER_ACTION"
                self._trim_log()
                return

            old_speed = target.speed if target is not None else None

            if session.inventory.remove_item_by_id(item_id):
                self.play_sfx("success")
                messages = item.apply_effect(target)

                popup_text = "ITEM"
                if getattr(item, "revive_amount", 0) > 0:
                    popup_text = "REVIVE"
                elif getattr(item, "heal_amount", 0) > 0:
                    popup_text = f"+{getattr(item, 'heal_amount', 0)} HP"
                elif getattr(item, "stat_stage_changes", []):
                    popup_text = "BUFF"

                self._spawn_popup(target, popup_text, UITheme.SUCCESS)
                self.combat_log.append(f"* {actor.name} used {item.name} on {target.name}.")

                for msg in messages:
                    self.combat_log.append(msg)

                if old_speed is not None and target.speed != old_speed:
                    self.combat_manager.refresh_turn_order()
            else:
                self.play_sfx("error")
                self._spawn_popup(actor, "NO ITEM", UITheme.WARNING)
                self.combat_log.append(f"* No {action_name} item remains.")

            self._check_end_condition()
            return

        if target is not None and damage_mult > 0:
            raw_damage = int(actor.attack * damage_mult)
            damage_dealt = target.take_damage(raw_damage)
            self.play_sfx("hit")
            self._start_attack_animation(actor, target, did_hit=True)
            self._spawn_popup(target, f"-{damage_dealt}", UITheme.DANGER)

            self.combat_log.append(
                f"* {actor.name} used {action_name} on {target.name} for {damage_dealt} DMG!"
            )
        else:
            self._start_attack_animation(actor, target, did_hit=False)
            if target is not None and target is not actor:
                self.combat_log.append(
                    f"* {actor.name} used {action_name} on {target.name}!"
                )
            else:
                self.combat_log.append(
                    f"* {actor.name} used {action_name}!"
                )

        heal_amount = action.get("heal_amount", 0)

        if target is not None and heal_amount > 0 and target.is_alive():
            before_hp = target.current_hp
            target.heal(heal_amount)
            restored = target.current_hp - before_hp

            if restored > 0:
                self.play_sfx("success")
                self._spawn_popup(target, f"+{restored} HP", UITheme.SUCCESS)
                self.combat_log.append(
                    f"{target.name} recovered {restored} HP."
                )
            else:
                self._spawn_popup(target, "FULL HP", UITheme.TEXT_DIM)
                self.combat_log.append(f"{target.name} is already at full HP.")

        clear_statuses = action.get("clear_statuses", [])

        if target is not None and clear_statuses and hasattr(target, "status_effects"):
            old_count = len(target.status_effects)
            target.status_effects = [
                effect for effect in target.status_effects
                if effect.get("type") not in clear_statuses
            ]
            cleared_count = old_count - len(target.status_effects)

            if cleared_count > 0:
                self._spawn_popup(target, "CLEANSE", UITheme.SUCCESS)
                self.combat_log.append(
                    f"{target.name} was cleansed of harmful effects."
                )

        status = action.get("status")

        if status:
            status_target = actor if status.get("target") == "self" else target

            if status_target is not None and status_target.is_alive():
                apply_chance = status.get("apply_chance", 1.0)

                if random.random() <= apply_chance:
                    status_target.add_status(
                        status_type=status.get("type"),
                        duration=status.get("duration", 1),
                        power=status.get("power", 0),
                        chance=status.get("chance", 1.0)
                    )

                    status_name = str(status.get('type')).upper()
                    self._spawn_popup(status_target, status_name, UITheme.ACCENT_GOLD)
                    self.combat_log.append(
                        f"{status_target.name} is affected by {status.get('type')}!"
                    )
                else:
                    self._spawn_popup(status_target, "RESIST", UITheme.TEXT_DIM)
                    self.combat_log.append(
                        f"{status_target.name} resisted the effect!"
                    )

        stage_changes = action.get("stage_changes")

        if stage_changes is None:
            single_change = action.get("stage_change")
            stage_changes = [single_change] if single_change else []

        speed_changed = False

        for change in stage_changes:
            stage_target = actor if change.get("target") == "self" else target

            if stage_target is not None and stage_target.is_alive():
                stat_name = change.get("stat")
                amount = change.get("amount", 0)
                old_speed = stage_target.speed

                msg = stage_target.change_stat_stage(
                    stat_name,
                    amount
                )
                self.combat_log.append(msg)

                if "rose" in msg or "fell" in msg:
                    arrow = "+" if amount > 0 else "-"
                    color = UITheme.SUCCESS if amount > 0 else UITheme.WARNING
                    self._spawn_popup(
                        stage_target,
                        f"{stat_name.upper()} {arrow}",
                        color
                    )

                new_speed = stage_target.speed

                if stat_name == "speed" and new_speed != old_speed:
                    speed_changed = True

        if speed_changed:
            self.combat_manager.refresh_turn_order()

        self._check_end_condition()

    def _execute_enemy_turn(self):
        """Execute the enemy turn."""
        alive_players = [
            p for p in self.combat_manager.player_team
            if p.is_alive()
        ]

        if not alive_players:
            self._check_end_condition()
            return

        action, target = EnemySkillLibrary.choose_action_and_target(
            self.current_actor,
            alive_players
        )

        self._execute_action(self.current_actor, target, action)

    def _check_end_condition(self):
        """Check end condition."""
        status = self.combat_manager.check_battle_status()

        if status == "VICTORY":
            self.play_sfx("success")
            self.state = "GAME_OVER"
            self.combat_log.append("=== VICTORY! ===")

            session = self.screen_manager.game_session
            npc_type = getattr(self.npc, "npc_type", "farm")

            if npc_type in ("boss", "final_boss"):
                self.npc.defeated = True
                session.mark_npc_defeated(self.npc.name)

            session.quest_manager.record_defeated_npc(getattr(self.npc, "name", ""))

            gold_reward = sum(
                getattr(enemy, "gold_reward", 0)
                for enemy in self.combat_manager.enemy_team
            )

            if gold_reward > 0:
                session.gold += gold_reward
                self.combat_log.append(f"Earned {gold_reward} gold.")

            for enemy in self.combat_manager.enemy_team:
                if enemy.loot_id:
                    loot_chance = getattr(enemy, "loot_chance", 1.0)
                    loot_amount = getattr(enemy, "loot_amount", 1)

                    roll = random.random()

                    if roll <= loot_chance:
                        item = self.db.get_item(enemy.loot_id)

                        if item:
                            for _ in range(loot_amount):
                                session.inventory.add_item(item)

                            if getattr(item, "item_type", "") == "material":
                                session.quest_manager.record_loot(loot_amount)

                            percent = int(loot_chance * 100)

                            if loot_amount > 1:
                                self.combat_log.append(
                                    f"Found: {item.name} x{loot_amount} from {enemy.name} ({percent}%)"
                                )
                            else:
                                self.combat_log.append(
                                    f"Found: {item.name} from {enemy.name} ({percent}%)"
                                )
                    else:
                        percent = int(loot_chance * 100)
                        self.combat_log.append(
                            f"No drop from {enemy.name}. Drop chance was {percent}%."
                        )

            self._clear_temporary_combat_effects()

            if npc_type == "final_boss" and session.is_story_complete():
                self.pending_ending = True
                self.combat_log.append("Press [ENTER] to finish the story.")
            else:
                self.combat_log.append("Press [ENTER] to return to map.")

        elif status == "DEFEAT":
            self.state = "GAME_OVER"
            self.combat_log.append("=== DEFEAT! Your team was wiped out. ===")
            self.combat_log.append("Press [ENTER] to continue.")

            self._clear_temporary_combat_effects()

            from src.screens.game_over_screen import GameOverScreen
            self.screen_manager.push(GameOverScreen(self.screen_manager))

        else:
            self.state = "NEXT_TURN"
            self.delay_timer = pygame.time.get_ticks()

        self._trim_log()

    def _clear_temporary_combat_effects(self):
        """Clear temporary combat effects."""
        all_entities = (
            self.combat_manager.player_team
            + self.combat_manager.enemy_team
        )

        for entity in all_entities:
            if hasattr(entity, "status_effects"):
                entity.status_effects = []

            if hasattr(entity, "reset_stat_stages"):
                entity.reset_stat_stages()

    def _get_alive_enemies(self):
        """Return the alive enemies."""
        return [
            e for e in self.combat_manager.enemy_team
            if e.is_alive()
        ]

    def _trim_log(self):
        """Trim log."""
        if len(self.combat_log) > 4:
            self.combat_log = self.combat_log[-4:]

    # Drawing

    def draw(self, surface):
        """Draw this screen."""
        screen_w = surface.get_width()
        screen_h = surface.get_height()

        surface.fill((8, 10, 12))

        header_rect = pygame.Rect(
            35,
            18,
            screen_w - 70,
            54
        )

        self._draw_soft_panel(
            surface,
            header_rect,
            fill=(8, 12, 18, 145),
            border=(45, 90, 110),
            radius=8
        )

        title = (
            f"COMBAT SYSTEM | ROUND {self.combat_manager.round_count} | STATE: {self.state}"
        )

        draw_text(
            surface,
            title,
            self.small_font,
            UITheme.TEXT,
            header_rect.x + 18,
            header_rect.y + 15
        )

        ff_color = UITheme.ACCENT_GOLD if self.is_fast_forward else UITheme.TEXT_DIM

        draw_text(
            surface,
            f"[F] Fast Forward: {'ON' if self.is_fast_forward else 'OFF'}",
            self.small_font,
            ff_color,
            header_rect.right - 255,
            header_rect.y + 15
        )

        battlefield_rect = pygame.Rect(
            30,
            84,
            screen_w - 60,
            screen_h - 205
        )

        shake_x, shake_y = self._get_screen_shake_offset()
        animated_battlefield_rect = battlefield_rect.move(shake_x, shake_y)

        self._draw_battlefield_background(surface, animated_battlefield_rect)
        self._draw_battlefield(surface, animated_battlefield_rect)
        self._draw_combat_popups(surface)

        bottom_panel = pygame.Rect(
            35,
            screen_h - 108,
            screen_w - 70,
            82
        )

        self._draw_soft_panel(
            surface,
            bottom_panel,
            fill=(8, 10, 16, 145),
            border=(45, 60, 80),
            radius=8
        )

        self._draw_action_panel(surface, bottom_panel)
        self._draw_combat_log(surface, bottom_panel)

    def _draw_battlefield_background(self, surface, rect):
        """Draw the battlefield background."""
        if self.battle_bg:
            bg = pygame.transform.smoothscale(
                self.battle_bg,
                (rect.width, rect.height)
            )
            surface.blit(bg, rect)
        else:
            for i in range(rect.height):
                t = i / max(1, rect.height)
                r = int(12 + 10 * t)
                g = int(30 + 30 * t)
                b = int(28 + 12 * t)

                pygame.draw.line(
                    surface,
                    (r, g, b),
                    (rect.x, rect.y + i),
                    (rect.right, rect.y + i)
                )

            ground_rect = pygame.Rect(
                rect.x,
                rect.bottom - 130,
                rect.width,
                130
            )

            pygame.draw.rect(
                surface,
                (34, 56, 38),
                ground_rect
            )

        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 8))
        surface.blit(overlay, rect.topleft)

    def _draw_battlefield(self, surface, rect):
        """Draw the battlefield."""
        self.enemy_card_rects = []
        self.ally_card_rects = []

        draw_text(
            surface,
            "ALLY TEAM",
            self.small_font,
            UITheme.ACCENT,
            rect.x + 18,
            rect.y + 10
        )

        draw_text(
            surface,
            "ENEMY TEAM",
            self.small_font,
            UITheme.DANGER,
            rect.right - 150,
            rect.y + 10
        )

        ally_positions = self._get_formation_positions(
            rect,
            side="left",
            count=min(3, len(self.combat_manager.player_team))
        )

        enemy_positions = self._get_formation_positions(
            rect,
            side="right",
            count=min(3, len(self.combat_manager.enemy_team))
        )

        ally_units = list(zip(self.combat_manager.player_team[:3], ally_positions))
        enemy_units = list(zip(self.combat_manager.enemy_team[:3], enemy_positions))

        all_draw_items = []

        for entity, pos in ally_units:
            all_draw_items.append((entity, pos, False))

        for entity, pos in enemy_units:
            all_draw_items.append((entity, pos, True))

        # Rendering order only: draw units with lower Y first.
        # Uses custom QuickSort helper instead of Python list.sort() so DSA
        # requirements remain self-coded even in render ordering.
        all_draw_items = InventoryAlgorithms.quick_sort_by_key(
            all_draw_items,
            lambda item: item[1][1]
        )

        alive_enemies = self._get_alive_enemies()
        ally_targets = self._get_current_ally_targets() if self.state == "PLAYER_ALLY_TARGET" else []

        for entity, pos, is_enemy in all_draw_items:
            center_x, ground_y = pos

            is_selected_target = (
                (
                    is_enemy
                    and self.state == "PLAYER_TARGET"
                    and entity in alive_enemies
                    and alive_enemies.index(entity) == self.target_idx
                )
                or (
                    not is_enemy
                    and self.state == "PLAYER_ALLY_TARGET"
                    and entity in ally_targets
                    and ally_targets.index(entity) == self.ally_target_idx
                )
            )

            click_rect = self._draw_ground_unit(
                surface,
                entity=entity,
                center_x=center_x,
                ground_y=ground_y,
                is_enemy=is_enemy,
                is_target_selected=is_selected_target
            )

            if is_enemy and entity.is_alive():
                self.enemy_card_rects.append((click_rect, entity))
            elif not is_enemy and entity in ally_targets:
                self.ally_card_rects.append((click_rect, entity))

    def _get_formation_positions(self, rect, side, count):
        """Return the formation positions."""
        ground_front = rect.bottom - 92
        ground_back = rect.bottom - 185

        if side == "left":
            positions = [
                (rect.x + 150, ground_front),
                (rect.x + 290, ground_back),
                (rect.x + 430, ground_front),
            ]
        else:
            positions = [
                (rect.right - 150, ground_front),
                (rect.right - 290, ground_back),
                (rect.right - 430, ground_front),
            ]

        return positions[:count]

    def _draw_ground_unit(self, surface, entity, center_x, ground_y, is_enemy=False, is_target_selected=False):
        """Draw the ground unit."""
        is_current = entity == self.current_actor

        if is_enemy:
            sprite = self._get_entity_sprite(
                entity,
                max_width=165,
                max_height=135
            )

            if self.flip_enemy_sprites:
                sprite = pygame.transform.flip(sprite, True, False)

        else:
            # Party sprites use role-aware bounds so the three allies read as
            # members of the same combat scene. Mira's original asset is more
            # zoomed-in than Zac/Kael, so give her a smaller render box.
            entity_id = getattr(entity, "entity_id", None)

            if entity_id == "p2":
                # Mira: compact healer/support silhouette.
                sprite = self._get_entity_sprite(
                    entity,
                    max_width=95,
                    max_height=110
                )
            elif entity_id == "p3":
                # Kael: slightly larger because he is the tank/frontliner.
                sprite = self._get_entity_sprite(
                    entity,
                    max_width=145,
                    max_height=165
                )
            else:
                # Zac: baseline party scale.
                sprite = self._get_entity_sprite(
                    entity,
                    max_width=120,
                    max_height=145
                )

        if entity.is_alive():
            enemy_y_offset = 8 if is_enemy else 0
            unit_ground_y = ground_y + enemy_y_offset

            ring_w = max(52, int(sprite.get_width() * 0.82))
            ring_h = max(14, int(sprite.get_height() * 0.16))

            if is_current or is_target_selected:
                glow_w = ring_w + 30
                glow_h = ring_h + 12

                glow_surface = pygame.Surface(
                    (glow_w, glow_h),
                    pygame.SRCALPHA
                )

                glow_color = UITheme.ACCENT_GOLD

                pygame.draw.ellipse(
                    glow_surface,
                    (*glow_color[:3], 110),
                    glow_surface.get_rect(),
                    3
                )

                glow_rect = glow_surface.get_rect(
                    center=(center_x, unit_ground_y - 8)
                )

                surface.blit(
                    glow_surface,
                    glow_rect.topleft
                )

            idle_bob = int(
                math.sin(
                    pygame.time.get_ticks() / 260
                    + (id(entity) % 97) * 0.07
                ) * 3
            )
            anim_x, anim_y = self._get_entity_animation_offset(entity)

            sprite_rect = sprite.get_rect()
            sprite_rect.midbottom = (
                center_x + anim_x,
                unit_ground_y + idle_bob + anim_y
            )

            draw_sprite = sprite

            if self._is_hit_flashing(entity) and (pygame.time.get_ticks() // 70) % 2 == 0:
                draw_sprite = self._flash_sprite(sprite)

            surface.blit(
                draw_sprite,
                sprite_rect
            )

            self._remember_entity_position(entity, center_x, unit_ground_y, sprite_rect)

            # UI is lifted upward so labels stay closer to the unit.
            # Increase ui_lift if the label still looks too low.
            ui_lift = 34
            info_y = unit_ground_y - ui_lift

            name_surface = self.small_font.render(
                entity.name,
                True,
                UITheme.TEXT
            )
            name_rect = name_surface.get_rect(
                center=(center_x, info_y)
            )
            self._draw_text_shadow(surface, name_surface, name_rect)

            hp_text = f"HP {entity.current_hp}/{entity.max_hp}"
            hp_surface = self.small_font.render(
                hp_text,
                True,
                UITheme.TEXT
            )
            hp_rect = hp_surface.get_rect(
                center=(center_x, info_y + 24)
            )
            self._draw_text_shadow(surface, hp_surface, hp_rect)

            bar_w = 130
            bar_x = center_x - bar_w // 2
            bar_y = info_y + 42

            self._draw_health_bar(
                surface,
                entity,
                bar_x,
                bar_y,
                width=bar_w,
                height=10
            )

            status_text = self._get_status_text(entity)

            if status_text != "Normal":
                status_surface = self.small_font.render(
                    status_text,
                    True,
                    UITheme.ACCENT_GOLD
                )
                status_rect = status_surface.get_rect(
                    center=(center_x, sprite_rect.y - 12)
                )
                self._draw_text_shadow(surface, status_surface, status_rect)

            click_rect = pygame.Rect(
                center_x - 95,
                sprite_rect.y - 12,
                190,
                (bar_y + 18) - (sprite_rect.y - 12)
            )

            return click_rect

        down_surface = self.small_font.render(
            f"{entity.name} - DEFEATED",
            True,
            UITheme.TEXT_DIM
        )
        down_rect = down_surface.get_rect(
            center=(center_x, ground_y - 10)
        )
        self._draw_text_shadow(surface, down_surface, down_rect)

        return pygame.Rect(
            center_x - 80,
            ground_y - 50,
            160,
            100
        )

    def _draw_action_panel(self, surface, bottom_panel):
        """Draw the action panel."""
        self.skill_button_rects = []

        left_area = pygame.Rect(
            bottom_panel.x + 14,
            bottom_panel.y + 12,
            350,
            bottom_panel.height - 24
        )

        if self.state == "PLAYER_ACTION":
            actions = self._get_player_actions()

            button_w = 165
            button_h = 32
            gap_x = 10
            gap_y = 6

            positions = [
                (left_area.x, left_area.y),
                (left_area.x + button_w + gap_x, left_area.y),
                (left_area.x, left_area.y + button_h + gap_y),
                (left_area.x + button_w + gap_x, left_area.y + button_h + gap_y),
            ]

            for i, action in enumerate(actions):
                if i >= len(positions):
                    break

                rect = pygame.Rect(
                    positions[i][0],
                    positions[i][1],
                    button_w,
                    button_h
                )

                self.skill_button_rects.append(rect)

                draw_button(
                    surface,
                    rect,
                    action.get("label", action.get("name", "Skill")),
                    self.small_font,
                    is_selected=True
                )

        elif self.state == "PLAYER_ITEM":
            self.item_button_rects = []
            visible_items, start_index = self._get_visible_item_window()

            button_w = 165
            button_h = 32
            gap_x = 10
            gap_y = 6
            positions = [
                (left_area.x, left_area.y),
                (left_area.x + button_w + gap_x, left_area.y),
                (left_area.x, left_area.y + button_h + gap_y),
                (left_area.x + button_w + gap_x, left_area.y + button_h + gap_y),
            ]

            for offset, item in enumerate(visible_items):
                rect = pygame.Rect(positions[offset][0], positions[offset][1], button_w, button_h)
                self.item_button_rects.append(rect)
                count = self.screen_manager.game_session.inventory.get_item_count(item.item_id)
                label = f"[{offset + 1}] {item.name} x{count}"

                draw_button(
                    surface,
                    rect,
                    label,
                    self.small_font,
                    is_selected=(start_index + offset == self.item_idx)
                )

            if not visible_items:
                draw_text(
                    surface,
                    "No usable combat items.",
                    self.small_font,
                    UITheme.WARNING,
                    left_area.x,
                    left_area.y + 8
                )

        elif self.state == "PLAYER_ALLY_TARGET":
            item_name = (
                self.selected_item.name
                if self.selected_item
                else self.selected_action.get("name", "skill")
            )
            draw_text(
                surface,
                f"Select ally for {item_name}: arrows + ENTER",
                self.small_font,
                UITheme.ACCENT_GOLD,
                left_area.x,
                left_area.y + 8
            )

        elif self.state == "PLAYER_TARGET":
            draw_text(
                surface,
                "Click enemy or use UP/DOWN + ENTER",
                self.small_font,
                UITheme.ACCENT_GOLD,
                left_area.x,
                left_area.y + 8
            )

        elif self.state == "GAME_OVER":
            if self.pending_ending:
                text = "Press ENTER to finish the story"
            else:
                text = "Press ENTER to return"

            draw_text(
                surface,
                text,
                self.small_font,
                UITheme.ACCENT_GOLD,
                left_area.x,
                left_area.y + 8
            )

        else:
            draw_text(
                surface,
                "Waiting for next turn...",
                self.small_font,
                UITheme.TEXT_DIM,
                left_area.x,
                left_area.y + 8
            )

    def _draw_combat_log(self, surface, bottom_panel):
        """Draw the combat log."""
        log_x = bottom_panel.x + 385
        log_y = bottom_panel.y + 10

        draw_text(
            surface,
            "Battle Log",
            self.small_font,
            UITheme.ACCENT,
            log_x,
            log_y
        )

        for i, msg in enumerate(self.combat_log):
            color = UITheme.TEXT

            if msg.startswith(">"):
                color = UITheme.ACCENT
            elif "VICTORY" in msg or "Found:" in msg:
                color = UITheme.SUCCESS
            elif "DEFEAT" in msg or "No drop" in msg:
                color = UITheme.WARNING
            elif "cannot escape" in msg:
                color = UITheme.WARNING

            log_text = self.small_font.render(
                msg,
                True,
                color
            )

            surface.blit(
                log_text,
                (log_x, log_y + 20 + i * 16)
            )

    def _draw_health_bar(self, surface, entity, x, y, width=120, height=10):
        """Draw the health bar."""
        hp_bg = pygame.Rect(x, y, width, height)

        pygame.draw.rect(
            surface,
            (30, 36, 42),
            hp_bg,
            border_radius=5
        )

        if entity.max_hp > 0:
            health_ratio = max(0, entity.current_hp / entity.max_hp)
            fill_width = int(width * health_ratio)

            hp_fill = pygame.Rect(
                x,
                y,
                fill_width,
                height
            )

            pygame.draw.rect(
                surface,
                UITheme.HP_FILL,
                hp_fill,
                border_radius=5
            )

        pygame.draw.rect(
            surface,
            UITheme.TEXT_DIM,
            hp_bg,
            1,
            border_radius=5
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

    def _draw_text_shadow(self, surface, text_surface, rect):
        """Draw the text shadow."""
        shadow = text_surface.copy()
        shadow.fill(
            (0, 0, 0),
            special_flags=pygame.BLEND_RGB_MULT
        )

        surface.blit(
            shadow,
            (rect.x + 2, rect.y + 2)
        )

        surface.blit(
            text_surface,
            rect.topleft
        )

    def _get_status_text(self, entity):
        """Return the status text."""
        if hasattr(entity, "get_status_summary"):
            return entity.get_status_summary()

        return "Normal"
