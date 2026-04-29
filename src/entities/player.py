import pygame
from src.graphics.sprite_manager import SpriteManager

class Player:
    """
    Handles the player's overworld representation, movement, and collision.
    """
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.speed = 5
        
        # Load the 4x4 sprite sheet you uploaded
        self.animations = SpriteManager.load_sprite_sheet("zac.png", rows=4, cols=4)
        
        # Based on your image: Row 0=Down, 1=Up, 2=Left, 3=Right
        self.DIR_DOWN = 0
        self.DIR_UP = 1
        self.DIR_LEFT = 2
        self.DIR_RIGHT = 3
        
        self.current_dir = self.DIR_DOWN
        self.frame_index = 0
        self.animation_speed = 0.15 # Controls how fast the legs move
        
        # Initialize the default static sprite so MapScreen can read it
        self.sprite = self.animations[self.current_dir][0]

    def handle_movement(self, keys, collision_rects):
        """
        Moves the player, checks for wall collisions, and updates the animation frame.
        """
        dx, dy = 0, 0
        moving = False
        
        # 1. Calculate intended movement and update direction
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
            self.current_dir = self.DIR_LEFT
            moving = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
            self.current_dir = self.DIR_RIGHT
            moving = True
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed
            self.current_dir = self.DIR_UP
            moving = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed
            self.current_dir = self.DIR_DOWN
            moving = True

        # 2. Apply X movement and check collisions
        self.rect.x += dx
        for wall in collision_rects:
            if self.rect.colliderect(wall):
                if dx > 0: # Moving right, hit left side of wall
                    self.rect.right = wall.left
                if dx < 0: # Moving left, hit right side of wall
                    self.rect.left = wall.right

        # 3. Apply Y movement and check collisions
        self.rect.y += dy
        for wall in collision_rects:
            if self.rect.colliderect(wall):
                if dy > 0: # Moving down, hit top of wall
                    self.rect.bottom = wall.top
                if dy < 0: # Moving up, hit bottom of wall
                    self.rect.top = wall.bottom

        # 4. Handle Animation Logic
        if moving:
            self.frame_index += self.animation_speed
            if self.frame_index >= 4: # Loop back after 4 frames
                self.frame_index = 0
        else:
            self.frame_index = 0 # Return to idle stance if stopped
            
        # Dynamically update the sprite property that MapScreen draws
        self.sprite = self.animations[self.current_dir][int(self.frame_index)]

    def draw(self, surface):
        """Draws the player onto the map."""
        surface.blit(self.sprite, (self.rect.x, self.rect.y))