import pygame
import os
from src.screens.base_screen import BaseScreen
from src.entities.player import Player
from src.entities.npc import NPC
from src.graphics.tilemap import TileMap
from src.graphics.sprite_manager import SpriteManager
from src.graphics.camera import Camera
from src.screens.combat_screen import CombatScreen

class MapScreen(BaseScreen):
    def __init__(self, screen_manager, map_id="forest_01"):
        super().__init__(screen_manager)
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        
        # Access the DB
        self.db = self.screen_manager.game_session.db
        map_data = self.db.get_map_data(map_id)

        # 1. Initialize Player (Usually p1 in your allies.json)
        self.player = Player(x=100, y=100)
        
        # 2. Setup NPCs from JSON
        self.npcs = []
        if map_data:
            for n in map_data["npcs"]:
                new_npc = NPC(n["name"], n["x"], n["y"], n["enemies"], n["sprite"])
                self.npcs.append(new_npc)

        # 3. Setup TileMap
        self.tile_size = 40
        self.world_map = TileMap(tile_size=self.tile_size)
        
        # DYNAMIC TILE REGISTRATION
        if map_data:
            solid_tiles = map_data.get("solid_tiles", [])
            
            for tile_id, sprite_file in map_data["tile_sprites"].items():
                is_wall = (tile_id in solid_tiles) 
                self.world_map.add_tile(tile_id, SpriteManager.get_sprite(sprite_file), is_wall)
            
            # Load the grid from the text file
            map_filename = map_data.get("map_file", "forest_01.txt")
            self.level_data = self.load_map_from_file(map_filename)
            
            self.world_map.load_map(self.level_data)
            self.region_name = map_data["name"]
        
        # 4. Initialize Camera
        map_pixel_width = len(self.level_data[0]) * self.tile_size
        map_pixel_height = len(self.level_data) * self.tile_size
        self.camera = Camera(1280, 720, map_pixel_width, map_pixel_height)

    def load_map_from_file(self, filename):
        """Reads a .txt file containing ASCII map data (e.g., ###...###)"""
        path = os.path.join("assets", filename)
        grid = []
        try:
            with open(path, "r") as f:
                for line in f:
                    clean_line = line.strip()
                    if clean_line: # Ignore empty lines
                        grid.append(list(clean_line))
            return grid
        except FileNotFoundError:
            print(f"ERROR: Could not find {path}.")
            return [["#", "#", "#"], ["#", ".", "#"], ["#", "#", "#"]]

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

    def update(self):
        keys = pygame.key.get_pressed()
        walls = self.world_map.get_colliding_rects()
        self.player.handle_movement(keys, walls)
        self.camera.update(self.player.rect)
        
        for npc in self.npcs:
            if not npc.defeated and self.player.rect.colliderect(npc.rect):
                self.screen_manager.push(CombatScreen(self.screen_manager, npc))
                self.player.rect.y += 10 
                break 

    def draw(self, surface):
        # 0. Clear screen with a fallback dark color
        surface.fill((20, 20, 20)) 
        
        # --- ALL DRAWING USES THE CAMERA OFFSET ---
        
        for row_idx, row in enumerate(self.world_map.map_grid):
            for col_idx, tile_id in enumerate(row):
                tile_rect = pygame.Rect(
                    col_idx * self.tile_size, 
                    row_idx * self.tile_size, 
                    self.tile_size, 
                    self.tile_size
                )
                
                # LAYER 1: Always draw Grass (ID '.') as the background
                if "." in self.world_map.tiles:
                    surface.blit(self.world_map.tiles["."], self.camera.apply(tile_rect))
                
                # LAYER 2: If the tile ISN'T grass, draw it on top
                if tile_id != "." and tile_id in self.world_map.tiles:
                    surface.blit(self.world_map.tiles[tile_id], self.camera.apply(tile_rect))

        # 2. Draw NPCs
        for npc in self.npcs:
            if not npc.defeated:
                surface.blit(npc.sprite, self.camera.apply(npc.rect))
                name_tag = self.small_font.render(npc.name, True, (255, 255, 255))
                tag_pos = self.camera.apply(npc.rect)
                surface.blit(name_tag, (tag_pos.x, tag_pos.y - 20))

        # 3. Draw Player
        surface.blit(self.player.sprite, self.camera.apply(self.player.rect))
        
        # 4. Draw UI Overlay
        overlay_bg = pygame.Surface((1280, 80))
        overlay_bg.set_alpha(150)
        overlay_bg.fill((0, 0, 0))
        surface.blit(overlay_bg, (0, 0))
        
        text_surface = self.font.render("REGION: TOXIC WASTES", True, (0, 255, 100))
        surface.blit(text_surface, (20, 15))
        
        hint_text = "ESC: Menu | I: Inventory | M: Mutations"
        hint_surface = self.small_font.render(hint_text, True, (200, 200, 200))
        surface.blit(hint_surface, (20, 45))