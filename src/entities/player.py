import pygame
from src.graphics.sprite_manager import SpriteManager


class Player:
    """
    Handles the player's overworld representation, smooth movement,
    collision, and walking animation.

    Movement style:
    - One input step = a small step, not a full tile.
    - Movement is smooth, not instant.
    - Main rect = player anchor position.
    - collision_rect = smaller foot hitbox for natural collision.
    - Sprite is larger than 1 tile so Zac visually fits with bushes/grass.
    """

    def __init__(self, x, y, tile_size=64):
        self.tile_size = tile_size

        # Smaller movement step.
        # 16px lets Zac move closer to NPCs instead of stopping 1 full tile away.
        self.step_size = tile_size // 4

        # Store position.
        self.x = float(x)
        self.y = float(y)

        # Anchor rect.
        self.rect = pygame.Rect(x, y, tile_size, tile_size)

        # Smaller collision box around Zac's feet.
        self.collision_rect = pygame.Rect(
            x + 18,
            y + 42,
            28,
            18
        )

        # Sprite display size.
        self.sprite_width = 112
        self.sprite_height = 112

        # Center 112x112 sprite on a 64x64 tile.
        self.draw_offset_x = -24
        self.draw_offset_y = -28

        # Smooth movement settings.
        self.is_moving = False
        self.target_x = self.rect.x
        self.target_y = self.rect.y

        # Pixels per frame.
        self.move_speed = 8

        # Zac sprite sheet is 4 rows x 6 columns.
        self.frame_count = 6

        self.animations = SpriteManager.load_sprite_sheet(
            "zac.png",
            rows=4,
            cols=self.frame_count,
            target_width=self.sprite_width,
            target_height=self.sprite_height
        )

        # Sprite sheet row order:
        # Row 0 = Down / Front
        # Row 1 = Left
        # Row 2 = Right
        # Row 3 = Up / Back
        self.DIR_DOWN = 0
        self.DIR_LEFT = 1
        self.DIR_RIGHT = 2
        self.DIR_UP = 3

        self.current_dir = self.DIR_DOWN

        # Animation settings.
        self.frame_index = 0
        self.animation_timer = pygame.time.get_ticks()
        self.animation_delay = 100

        self.sprite = self.animations[self.current_dir][self.frame_index]

    def _sync_collision_rect(self):
        """
        Keeps Zac's foot collision box aligned with his anchor position.
        """
        self.collision_rect.x = self.rect.x + 18
        self.collision_rect.y = self.rect.y + 42

    def handle_movement(self, keys, collision_rects):
        """
        Handles smooth small-step movement.

        Returns:
            True only when Zac has just finished moving into a new position.
            False otherwise.
        """
        if self.is_moving:
            return self._continue_movement()

        dx = 0
        dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.step_size
            self.current_dir = self.DIR_LEFT

        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.step_size
            self.current_dir = self.DIR_RIGHT

        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.step_size
            self.current_dir = self.DIR_UP

        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.step_size
            self.current_dir = self.DIR_DOWN

        else:
            self.frame_index = 0
            self.sprite = self.animations[self.current_dir][self.frame_index]
            return False

        return self._start_move(dx, dy, collision_rects)

    def _start_move(self, dx, dy, collision_rects):
        """
        Starts moving toward the next small step if it is not blocked.
        """
        target_rect = self.rect.move(dx, dy)
        target_collision_rect = self.collision_rect.move(dx, dy)

        for wall in collision_rects:
            if target_collision_rect.colliderect(wall):
                self.frame_index = 0
                self.sprite = self.animations[self.current_dir][self.frame_index]
                return False

        self.target_x = target_rect.x
        self.target_y = target_rect.y
        self.is_moving = True

        self._update_animation()
        return False

    def _continue_movement(self):
        """
        Moves Zac smoothly toward the target position.
        """
        if self.rect.x < self.target_x:
            self.rect.x += min(self.move_speed, self.target_x - self.rect.x)

        elif self.rect.x > self.target_x:
            self.rect.x -= min(self.move_speed, self.rect.x - self.target_x)

        if self.rect.y < self.target_y:
            self.rect.y += min(self.move_speed, self.target_y - self.rect.y)

        elif self.rect.y > self.target_y:
            self.rect.y -= min(self.move_speed, self.rect.y - self.target_y)

        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self._sync_collision_rect()

        self._update_animation()

        if self.rect.x == self.target_x and self.rect.y == self.target_y:
            self.is_moving = False
            self.x = float(self.rect.x)
            self.y = float(self.rect.y)
            self._sync_collision_rect()
            return True

        return False

    def _update_animation(self):
        """
        Updates walking animation while moving.
        """
        current_time = pygame.time.get_ticks()

        if current_time - self.animation_timer >= self.animation_delay:
            self.animation_timer = current_time
            self.frame_index = (self.frame_index + 1) % self.frame_count

        self.sprite = self.animations[self.current_dir][self.frame_index]

    def draw(self, surface):
        """
        Draws the player onto the map.
        """
        surface.blit(
            self.sprite,
            (
                self.rect.x + self.draw_offset_x,
                self.rect.y + self.draw_offset_y
            )
        )