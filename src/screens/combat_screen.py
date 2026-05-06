import pygame
import random

from src.paths import resolve_asset_path
from src.screens.base_screen import BaseScreen
from src.core.combat_manager import CombatManager
from src.core.enemy_skill_library import EnemySkillLibrary
from src.core.skill_library import SkillLibrary
from src.graphics.sprite_manager import SpriteManager

from src.ui.theme import UITheme
from src.ui.widgets import draw_button, draw_text


class CombatScreen(BaseScreen):
    """
    Turn-based combat screen.

    Layout:
    - Forest battle background.
    - Allies stand on the left side.
    - Enemies stand on the right side.
    - Units face each other in a 3 vs 3 formation.
    - No unit cards/frames.
    - No dark shadow under units.
    - Only sprite, highlight ring, name, HP text, and HP bar.
    """

    SPRITE_SHEET_FILES = {
        "zac.png"
    }

    def __init__(self, screen_manager, npc):
        super().__init__(screen_manager)

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
        self.target_idx = 0
        self.pending_ending = False

        self.delay_timer = pygame.time.get_ticks()
        self.base_delay = 1200
        self.fast_delay = 200
        self.current_delay = self.base_delay
        self.is_fast_forward = False

        self.skill_button_rects = []

        # Stores clickable enemy target areas:
        # [(rect, enemy_entity), ...]
        self.enemy_card_rects = []

        self.sprite_cache = {}

        # Put generated background here:
        # assets/backgrounds/battle_forest.png
        self.battle_bg = self._load_optional_background("battle_forest.png")

        # Change to True if enemy sprites face the wrong direction.
        self.flip_enemy_sprites = False

    # ============================================================
    # SETUP / ASSET HELPERS
    # ============================================================

    def _load_optional_background(self, filename):
        path = resolve_asset_path(filename)

        if not path.exists():
            return None

        try:
            return pygame.image.load(str(path)).convert()
        except Exception:
            return None

    def _trim_transparent_padding(self, image):
        """
        Removes transparent padding around a sprite.
        """
        rect = image.get_bounding_rect()

        if rect.width <= 0 or rect.height <= 0:
            return image

        return image.subsurface(rect).copy()

    def _get_entity_sprite(self, entity, max_width=130, max_height=130):
        """
        Loads and scales a combat sprite while preserving aspect ratio.
        """
        sprite_name = getattr(entity, "sprite_name", "placeholder.png")
        cache_key = (sprite_name, max_width, max_height)

        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]

        if sprite_name in self.SPRITE_SHEET_FILES:
            sheet = SpriteManager.load_sprite_sheet(
                sprite_name,
                rows=4,
                cols=6,
                target_width=max_width,
                target_height=max_height
            )
            sprite = sheet[0][0]
            self.sprite_cache[cache_key] = sprite
            return sprite

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

    # ============================================================
    # ACTION DEFINITIONS
    # ============================================================

    def _get_player_actions(self):
        """
        Returns combat actions based on Zac's selected skill loadout.

        Rules:
        - Basic Attack is always available.
        - Zac uses the selected skill_loadout from GameSession.
        - Tanker and Rogue only use Basic Attack.
        - Combat displays maximum 4 skills.
        """
        actor = self.current_actor
        is_zac = actor is not None and getattr(actor, "entity_id", None) == "p1"

        if not is_zac:
            actions = [
                SkillLibrary.build_action("basic_attack")
            ]

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

        if (
            session.inventory.get_item_count("pot_hp_small") > 0
            and len(actions) < SkillLibrary.MAX_LOADOUT_SIZE
        ):
            potion = self.db.get_item("pot_hp_small")
            heal_amount = getattr(potion, "heal_amount", 20)

            actions.append({
                "name": "Use Potion",
                "mult": 0,
                "target": "self",
                "item_id": "pot_hp_small",
                "heal": heal_amount
            })

        for i, action in enumerate(actions):
            action["label"] = f"[{i + 1}] {action['name']}"

        return actions

    def _choose_player_action(self, index):
        actions = self._get_player_actions()

        if index < 0 or index >= len(actions):
            return

        self.selected_action = actions[index]

        if self.selected_action.get("target") == "self":
            self._execute_action(
                self.current_actor,
                self.current_actor,
                self.selected_action
            )
        else:
            self._start_targeting()

    # ============================================================
    # INPUT
    # ============================================================

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            if self.state == "PLAYER_ACTION":
                for i, rect in enumerate(self.skill_button_rects):
                    if rect.collidepoint(mouse_pos):
                        self._choose_player_action(i)
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
                self.is_fast_forward = not self.is_fast_forward
                self.current_delay = (
                    self.fast_delay
                    if self.is_fast_forward
                    else self.base_delay
                )

            if self.state == "GAME_OVER":
                if event.key == pygame.K_RETURN:
                    if self.pending_ending:
                        self.screen_manager.pop()

                        from src.screens.ending_screen import EndingScreen
                        self.screen_manager.push(EndingScreen(self.screen_manager))
                        return

                    self.screen_manager.pop()
                return

            elif self.state == "PLAYER_ACTION":
                if event.key == pygame.K_1:
                    self._choose_player_action(0)

                elif event.key == pygame.K_2:
                    self._choose_player_action(1)

                elif event.key == pygame.K_3:
                    self._choose_player_action(2)

                elif event.key == pygame.K_4:
                    self._choose_player_action(3)

            elif self.state == "PLAYER_TARGET":
                alive_enemies = self._get_alive_enemies()

                if not alive_enemies:
                    return

                if event.key == pygame.K_UP or event.key == pygame.K_LEFT:
                    self.target_idx = (self.target_idx - 1) % len(alive_enemies)

                elif event.key == pygame.K_DOWN or event.key == pygame.K_RIGHT:
                    self.target_idx = (self.target_idx + 1) % len(alive_enemies)

                elif event.key == pygame.K_RETURN:
                    if self.target_idx >= len(alive_enemies):
                        self.target_idx = 0

                    target = alive_enemies[self.target_idx]

                    self._execute_action(
                        self.current_actor,
                        target,
                        self.selected_action
                    )

    def _handle_escape_key(self):
        """
        Handles ESC safely.

        Fix:
        - Normal farm battles can be exited.
        - Boss and final boss battles cannot be escaped.
        - After final boss victory, ENTER should be used to continue ending flow.
        """
        if self.state == "GAME_OVER":
            if self.pending_ending:
                self.combat_log.append("Press [ENTER] to finish the story.")
                self._trim_log()
                return

            self.screen_manager.pop()
            return

        npc_type = getattr(self.npc, "npc_type", "farm")

        if npc_type in ("boss", "final_boss"):
            self.combat_log.append("You cannot escape from this battle!")
            self._trim_log()
            return

        self.screen_manager.pop()

    # ============================================================
    # UPDATE / TURN FLOW
    # ============================================================

    def update(self):
        current_time = pygame.time.get_ticks()

        if self.state == "NEXT_TURN":
            if current_time - self.delay_timer > self.current_delay:
                self._start_turn()

        elif self.state == "ENEMY_TURN":
            if current_time - self.delay_timer > self.current_delay:
                self._execute_enemy_turn()

    def _start_turn(self):
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
        alive_enemies = self._get_alive_enemies()

        if not alive_enemies:
            return

        self.state = "PLAYER_TARGET"
        self.target_idx = 0

        self.combat_log.append(
            f"Select target for {self.selected_action['name']}."
        )
        self._trim_log()

    # ============================================================
    # ACTION EXECUTION
    # ============================================================

    def _execute_action(self, actor, target, action):
        if actor is None or action is None:
            return

        action_name = action.get("name", "Unknown Action")
        damage_mult = action.get("mult", 1.0)

        if action.get("item_id"):
            item_id = action.get("item_id")
            heal_amount = action.get("heal", 0)
            session = self.screen_manager.game_session

            if session.inventory.remove_item_by_id(item_id):
                target.heal(heal_amount)
                self.combat_log.append(
                    f"* {actor.name} used {action_name}. {target.name} recovered {heal_amount} HP."
                )
            else:
                self.combat_log.append(
                    f"* No {action_name} item remains."
                )

            self._check_end_condition()
            return

        if target is not None and damage_mult > 0:
            raw_damage = int(actor.attack * damage_mult)
            damage_dealt = target.take_damage(raw_damage)

            self.combat_log.append(
                f"* {actor.name} used {action_name} on {target.name} for {damage_dealt} DMG!"
            )
        else:
            self.combat_log.append(
                f"* {actor.name} used {action_name}!"
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

                    self.combat_log.append(
                        f"{status_target.name} is affected by {status.get('type')}!"
                    )
                else:
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

                new_speed = stage_target.speed

                if stat_name == "speed" and new_speed != old_speed:
                    speed_changed = True

        if speed_changed:
            self.combat_manager.refresh_turn_order()

        self._check_end_condition()

    def _execute_enemy_turn(self):
        alive_players = [
            p for p in self.combat_manager.player_team
            if p.is_alive()
        ]

        if not alive_players:
            self._check_end_condition()
            return

        action = EnemySkillLibrary.choose_action(self.current_actor)

        if action.get("target") == "self":
            target = self.current_actor
        else:
            target = random.choice(alive_players)

        self._execute_action(self.current_actor, target, action)

    def _check_end_condition(self):
        status = self.combat_manager.check_battle_status()

        if status == "VICTORY":
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
        return [
            e for e in self.combat_manager.enemy_team
            if e.is_alive()
        ]

    def _trim_log(self):
        if len(self.combat_log) > 4:
            self.combat_log = self.combat_log[-4:]

    # ============================================================
    # DRAWING
    # ============================================================

    def draw(self, surface):
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

        self._draw_battlefield_background(surface, battlefield_rect)
        self._draw_battlefield(surface, battlefield_rect)

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
        self.enemy_card_rects = []

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

        all_draw_items.sort(key=lambda item: item[1][1])

        alive_enemies = self._get_alive_enemies()

        for entity, pos, is_enemy in all_draw_items:
            center_x, ground_y = pos

            is_selected_target = (
                is_enemy
                and self.state == "PLAYER_TARGET"
                and entity in alive_enemies
                and alive_enemies.index(entity) == self.target_idx
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

    def _get_formation_positions(self, rect, side, count):
        """
        Returns 3-vs-3 facing formation positions.
        """
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

            sprite_rect = sprite.get_rect()
            sprite_rect.midbottom = (center_x, unit_ground_y)

            surface.blit(
                sprite,
                sprite_rect
            )

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
        if hasattr(entity, "get_status_summary"):
            return entity.get_status_summary()

        return "Normal"