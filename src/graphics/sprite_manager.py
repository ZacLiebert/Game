import pygame
import os

class SpriteManager:
    """
    A globally accessible image cacher using a Hash Map pattern.
    Ensures images are only loaded from the disk once to optimize memory and speed.
    """
    _cache = {}

    @classmethod
    def get_sprite(cls, filename, width=40, height=40):
        # O(1) Dictionary Lookup
        if filename not in cls._cache:
            path = os.path.join("assets", filename)
            
            if os.path.exists(path):
                # Load the image, preserve transparency, and scale it
                image = pygame.image.load(path).convert_alpha()
                image = pygame.transform.scale(image, (width, height))
                cls._cache[filename] = image
            else:
                # FALLBACK: If the image is missing, draw a bright pink "Missing Texture" square
                fallback = pygame.Surface((width, height))
                fallback.fill((255, 0, 255))
                cls._cache[filename] = fallback
                
        return cls._cache[filename]

    @classmethod
    def load_sprite_sheet(cls, filename, rows=4, cols=4, target_width=40, target_height=40):
        """Slices a sprite sheet into a 2D list of frames [row][col]."""
        cache_key = f"{filename}_sheet_{rows}x{cols}"
        
        if cache_key not in cls._cache:
            path = os.path.join("assets", filename)
            
            if os.path.exists(path):
                sheet = pygame.image.load(path).convert_alpha()
                sheet_w, sheet_h = sheet.get_size()
                
                # Calculate the raw pixel size of a single frame
                frame_w = sheet_w // cols
                frame_h = sheet_h // rows
                
                frames = []
                for row in range(rows):
                    row_frames = []
                    for col in range(cols):
                        # Define the rectangle to cut out
                        rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
                        # Slice the image using Pygame's subsurface
                        frame_surface = sheet.subsurface(rect)
                        # Scale it up to match your TileMap grid
                        frame_surface = pygame.transform.scale(frame_surface, (target_width, target_height))
                        row_frames.append(frame_surface)
                    frames.append(row_frames)
                    
                cls._cache[cache_key] = frames
            else:
                # Fallback: Pink squares if file is missing
                fallback = pygame.Surface((target_width, target_height))
                fallback.fill((255, 0, 255))
                cls._cache[cache_key] = [[fallback for _ in range(cols)] for _ in range(rows)]
                
        return cls._cache[cache_key]