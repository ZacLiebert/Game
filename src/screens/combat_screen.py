import pygame
import random
from src.screens.base_screen import BaseScreen
from src.core.combat_manager import CombatManager
from src.entities.entity import Entity
from src.entities.item import Item
from src.graphics.sprite_manager import SpriteManager

class CombatScreen(BaseScreen):
    def __init__(self, screen_manager, npc):
        super().__init__(screen_manager)
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        
        self.npc = npc # Save the NPC so we can update them later!
        session = self.screen_manager.game_session
        self.db = session.db
        
        players = session.party
        
        enemies = [self.db.create_entity(eid, is_enemy=True) for eid in self.npc.enemy_ids]
        enemies = [e for e in enemies if e is not None]

        self.combat_manager = CombatManager(players, enemies)
        self.combat_manager.prepare_round()
        
        self.combat_log = ["Battle Started! Determining first turn..."]
        
        self.state = "NEXT_TURN" 
        self.current_actor = None
        self.selected_action = None
        self.target_idx = 0
        
        # Add a timer to handle automatic delays without freezing the game
        self.delay_timer = pygame.time.get_ticks() 
        self.base_delay = 1200  # Normal speed (1.2 seconds)
        self.fast_delay = 200   # Fast forward (0.2 seconds)
        self.current_delay = self.base_delay
        self.is_fast_forward = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.screen_manager.pop()
                
            # --- NEW: TOGGLE FAST FORWARD ---
            elif event.key == pygame.K_f:
                self.is_fast_forward = not self.is_fast_forward
                self.current_delay = self.fast_delay if self.is_fast_forward else self.base_delay
                
            if self.state == "GAME_OVER":
                if event.key == pygame.K_RETURN:
                    self.screen_manager.pop()
                return

            # PLAYER CHOOSING ACTION
            elif self.state == "PLAYER_ACTION":
                if event.key == pygame.K_1:
                    self.selected_action = {"name": "Basic Attack", "mult": 1.0}
                    self._start_targeting()
                elif event.key == pygame.K_2:
                    self.selected_action = {"name": "Heavy Strike", "mult": 1.5}
                    self._start_targeting()

            # PLAYER CHOOSING TARGET
            elif self.state == "PLAYER_TARGET":
                alive_enemies = [e for e in self.combat_manager.enemy_team if e.is_alive()]
                
                if event.key == pygame.K_UP:
                    self.target_idx = (self.target_idx - 1) % len(alive_enemies)
                elif event.key == pygame.K_DOWN:
                    self.target_idx = (self.target_idx + 1) % len(alive_enemies)
                elif event.key == pygame.K_RETURN:
                    target = alive_enemies[self.target_idx]
                    self._execute_action(self.current_actor, target, self.selected_action)

    def update(self):
        """Automatically processes turns using a dynamic delay."""
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
            self.combat_log.append("--- Round over! Rebuilding Max Heap... ---")
            self.combat_manager.prepare_round()
            self.state = "NEXT_TURN"
            self.delay_timer = pygame.time.get_ticks()
        elif self.current_actor in self.combat_manager.player_team:
            self.state = "PLAYER_ACTION"
            self.combat_log.append(f"> {self.current_actor.name}'s turn! [1] Attack or [2] Heavy Strike?")
        else:
            self.state = "ENEMY_TURN"
            self.combat_log.append(f"> {self.current_actor.name} is preparing to attack...")
            self.delay_timer = pygame.time.get_ticks() # Start the timer for the enemy

        self._trim_log()

    def _start_targeting(self):
        self.state = "PLAYER_TARGET"
        self.target_idx = 0 
        self.combat_log.append(f"Select target with UP/DOWN. Press ENTER to use {self.selected_action['name']}!")
        self._trim_log()

    def _execute_action(self, actor, target, action):
        raw_damage = int(actor.attack * action["mult"])
        damage_dealt = target.take_damage(raw_damage)
        
        self.combat_log.append(f"* {actor.name} used {action['name']} on {target.name} for {damage_dealt} DMG!")
        self._check_end_condition()

    def _execute_enemy_turn(self):
        alive_players = [p for p in self.combat_manager.player_team if p.is_alive()]
        target = random.choice(alive_players)
        
        action = {"name": "Vicious Bite", "mult": 1.0}
        self._execute_action(self.current_actor, target, action)

    def _check_end_condition(self):
        status = self.combat_manager.check_battle_status()
        
        if status == "VICTORY":
            self.state = "GAME_OVER"
            self.combat_log.append("=== VICTORY! ===")
            self.npc.defeated = True
            for enemy in self.combat_manager.enemy_team:
                if enemy.loot_id: 
                    item = self.db.get_item(enemy.loot_id)
                    if item:
                        self.screen_manager.game_session.inventory.add_item(item)
                        self.combat_log.append(f"Found: {item.name} from {enemy.name}")
            self.combat_log.append("Press [ENTER] to return to map.")
        elif status == "DEFEAT":
            self.state = "GAME_OVER"
            self.combat_log.append("=== DEFEAT! Your team was wiped out. ===")
            self.combat_log.append("Press [ENTER] to return to the map.")
            from src.screens.game_over_screen import GameOverScreen
            self.screen_manager.push(GameOverScreen(self.screen_manager))
        else:
            self.state = "NEXT_TURN"
            self.delay_timer = pygame.time.get_ticks() 
            
        self._trim_log()
        
    def _trim_log(self):
        """Keeps the combat log to exactly 2 lines max."""
        if len(self.combat_log) > 2:
            self.combat_log = self.combat_log[-2:]

    def draw(self, surface):
        surface.fill((45, 10, 10)) 
        
        screen_w = surface.get_width()
        screen_h = surface.get_height()
        
        # --- HEADERS ---
        header = self.font.render(f"COMBAT SYSTEM - State: {self.state}", True, (255, 200, 200))
        header_rect = header.get_rect(center=(screen_w // 2, 30))
        surface.blit(header, header_rect)
        
        ff_color = (255, 255, 0) if self.is_fast_forward else (150, 150, 150)
        ff_text = self.small_font.render(f"[F] Fast Forward: {'ON' if self.is_fast_forward else 'OFF'}", True, ff_color)
        surface.blit(ff_text, (20, 20))

       # --- DRAW PLAYERS (Left Side) ---
        player_start_x = 100
        y_offset = 150
        for p in self.combat_manager.player_team:
            if p.is_alive():
                # Check if it's the main character's sprite sheet
                if p.sprite_name == "zac.png":
                    sheet = SpriteManager.load_sprite_sheet(p.sprite_name, rows=4, cols=4, target_width=80, target_height=80)
                    sprite = sheet[0][0] # Grab the first frame (Idle Down)
                else:
                    sprite = SpriteManager.get_sprite(p.sprite_name, width=80, height=80)
                
                # Highlight active turn
                if p == self.current_actor:
                    pygame.draw.rect(surface, (150, 255, 150), (player_start_x - 5, y_offset - 5, 90, 90), 3, border_radius=5)
                
                surface.blit(sprite, (player_start_x, y_offset))
                self._draw_health_bar(surface, p, player_start_x + 100, y_offset + 30)
            
            y_offset += 120
            
        # --- DRAW ENEMIES (Right Side) ---
        enemy_start_x = screen_w - 180
        y_offset = 150
        alive_enemies = [e for e in self.combat_manager.enemy_team if e.is_alive()]
        
        for e in self.combat_manager.enemy_team:
            if e.is_alive():
                sprite = SpriteManager.get_sprite(e.sprite_name, width=80, height=80)
                
                # Highlight active turn
                if e == self.current_actor:
                    pygame.draw.rect(surface, (255, 150, 150), (enemy_start_x - 5, y_offset - 5, 90, 90), 3, border_radius=5)
                
                # Draw Targeting Cursor
                if self.state == "PLAYER_TARGET" and e in alive_enemies:
                    if alive_enemies.index(e) == self.target_idx:
                        cursor = self.font.render(">>>", True, (255, 255, 0)) 
                        surface.blit(cursor, (enemy_start_x - 60, y_offset + 25))

                surface.blit(sprite, (enemy_start_x, y_offset))
                self._draw_health_bar(surface, e, enemy_start_x - 140, y_offset + 30)
                
            y_offset += 120
            
        # --- COMBAT LOG (Bottom Screen) ---
        pygame.draw.rect(surface, (20, 5, 5), (0, screen_h - 120, screen_w, 120))
        pygame.draw.line(surface, (100, 50, 50), (0, screen_h - 120), (screen_w, screen_h - 120), 3)
        
        log_y = screen_h - 100
        for msg in self.combat_log:
            log_text = self.font.render(msg, True, (200, 200, 255))
            surface.blit(log_text, (50, log_y))
            log_y += 40

    def _draw_health_bar(self, surface, entity, x, y, width=120, height=15):
        """Draws a visual health bar for an entity."""
        # Draw red background (missing health)
        pygame.draw.rect(surface, (150, 50, 50), (x, y, width, height))
        
        # Draw green foreground (current health)
        if entity.max_hp > 0:
            health_ratio = max(0, entity.current_hp / entity.max_hp)
            pygame.draw.rect(surface, (50, 200, 50), (x, y, int(width * health_ratio), height))
            
        # Draw text overlay underneath the bar
        hp_text = self.small_font.render(f"{entity.name} (SPD: {entity.speed})", True, (200, 200, 200))
        surface.blit(hp_text, (x, y - 20))