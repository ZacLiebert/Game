import pygame
from src.graphics.sprite_manager import SpriteManager

class NPC:
    def __init__(self, name, x, y, enemy_ids, sprite_filename="slime.png"):
        self.name = name
        # The physical hitbox on the map
        self.rect = pygame.Rect(x, y, 40, 40) 
        
        # This holds the list of enemy IDs for combat
        self.enemy_ids = enemy_ids 
        
        # State tracking
        self.defeated = False 

        # This fetches the image from your HashTable cache
        self.sprite = SpriteManager.get_sprite(sprite_filename)

    def draw(self, surface, camera=None):
        """
        Note: Since MapScreen is now handling the drawing with the camera,
        this method is mostly a fallback.
        """
        if not self.defeated:
            if camera:
                surface.blit(self.sprite, camera.apply(self.rect))
            else:
                surface.blit(self.sprite, (self.rect.x, self.rect.y))