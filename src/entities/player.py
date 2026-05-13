"""Player movement, collision, and animation."""

import math

import pygame
from src.paths import resolve_asset_path


class Player:
    """Player-controlled map character."""

    def __init__(self, x, y, tile_size=64):
        """Set up initial state."""
        self.tile_size = tile_size

        self.x = float(x)
        self.y = float(y)

        self.rect = pygame.Rect(x, y, tile_size, tile_size)
        self.collision_rect = pygame.Rect(x + 18, y + 42, 28, 18)

        # Tile-sized overworld scale so Zac and NPCs do not feel oversized.
        self.sprite_width = 64
        self.sprite_height = 64
        self.draw_offset_x = 0
        self.draw_offset_y = 0

        # held movement feel like a repeated start/stop. This speed is per frame.
        self.move_speed = 3.0
        self.encounter_step_distance = tile_size // 4
        self._encounter_distance_accumulator = 0.0

        self.idle_sprite_filename = "sprites/characters/craftpix_swordsman_lvl2/player_idle.png"
        self.walk_sprite_filename = "sprites/characters/craftpix_swordsman_lvl2/player_walk.png"
        self.sprite_rows = 4
        self.idle_frame_count = 12
        self.walk_frame_count = 6
        self.idle_frame_index = 0

        # Sheet row order: down, left, right, up.
        self.DIR_DOWN = 0
        self.DIR_LEFT = 1
        self.DIR_RIGHT = 2
        self.DIR_UP = 3
        self.current_dir = self.DIR_DOWN

        self.frame_index = 0
        self.animation_timer = pygame.time.get_ticks()
        self.animation_delay = 95

        self.idle_animations, self.walk_animations = self._load_all_animations()
        self.sprite = self.idle_animations[self.current_dir][self.idle_frame_index]

    def _sync_collision_rect(self):
        """Update the player collision rectangle."""
        self.collision_rect.x = self.rect.x + 18
        self.collision_rect.y = self.rect.y + 42

    def _collision_rect_for(self, rect):
        """Build a foot hitbox for a test position."""
        return pygame.Rect(rect.x + 18, rect.y + 42, 28, 18)

    def _key_down(self, keys, *keycodes):
        """Return whether a movement key is pressed."""
        for keycode in keycodes:
            try:
                if keys[keycode]:
                    return True
            except (KeyError, IndexError, TypeError):
                continue
        return False

    def _load_sheet(self, filename, frame_count):
        """Load the player sprite sheet."""
        path = resolve_asset_path(filename)
        if not path.exists():
            return None, None, None

        sheet = pygame.image.load(str(path)).convert_alpha()
        sheet_w, sheet_h = sheet.get_size()
        frame_w = sheet_w // frame_count
        frame_h = sheet_h // self.sprite_rows
        frames = []
        for row in range(self.sprite_rows):
            row_frames = []
            for col in range(frame_count):
                rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
                row_frames.append(sheet.subsurface(rect).copy())
            frames.append(row_frames)
        return frames, frame_w, frame_h

    def _make_fallback_animations(self, frame_count):
        """Create colored fallback frames if sprites are missing."""
        fallback = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
        fallback.fill((255, 0, 255, 255))
        return [[fallback for _ in range(frame_count)] for _ in range(self.sprite_rows)]

    def _compute_row_crop_boxes(self, *animation_sets):
        """Find useful crop boxes for each animation row."""
        crop_boxes = []
        for row in range(self.sprite_rows):
            min_x = None
            min_y = None
            max_x = None
            max_y = None
            for animation_set in animation_sets:
                if animation_set is None:
                    continue
                for frame in animation_set[row]:
                    bbox = frame.get_bounding_rect(min_alpha=1)
                    if bbox.width <= 0 or bbox.height <= 0:
                        continue
                    left = bbox.x
                    top = bbox.y
                    right = bbox.x + bbox.width
                    bottom = bbox.y + bbox.height
                    min_x = left if min_x is None else min(min_x, left)
                    min_y = top if min_y is None else min(min_y, top)
                    max_x = right if max_x is None else max(max_x, right)
                    max_y = bottom if max_y is None else max(max_y, bottom)
            if min_x is None:
                crop_boxes.append(None)
            else:
                crop_boxes.append(pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y))
        return crop_boxes

    def _fit_frame_to_canvas(self, source, crop_rect):
        """Scale one frame into the player canvas."""
        if crop_rect is not None and crop_rect.width > 0 and crop_rect.height > 0:
            source = source.subsurface(crop_rect).copy()

        src_w, src_h = source.get_size()
        if src_w <= 0 or src_h <= 0:
            fallback = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
            fallback.fill((255, 0, 255, 255))
            return fallback

        scale = min(self.sprite_width / src_w, self.sprite_height / src_h)
        scaled_w = max(1, int(round(src_w * scale)))
        scaled_h = max(1, int(round(src_h * scale)))
        scaled = pygame.transform.scale(source, (scaled_w, scaled_h))

        canvas = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
        canvas.blit(
            scaled,
            (
                (self.sprite_width - scaled_w) // 2,
                self.sprite_height - scaled_h,
            ),
        )
        return canvas

    def _apply_crop_boxes(self, animation_set, crop_boxes, frame_count):
        """Crop and scale all animation frames."""
        if animation_set is None:
            return self._make_fallback_animations(frame_count)

        output = []
        for row in range(self.sprite_rows):
            row_frames = []
            crop_rect = crop_boxes[row]
            for frame in animation_set[row]:
                row_frames.append(self._fit_frame_to_canvas(frame, crop_rect))
            output.append(row_frames)
        return output

    def _load_all_animations(self):
        """Load all walking and idle animations."""
        idle_raw, _, _ = self._load_sheet(self.idle_sprite_filename, self.idle_frame_count)
        walk_raw, _, _ = self._load_sheet(self.walk_sprite_filename, self.walk_frame_count)

        if idle_raw is None and walk_raw is None:
            return (
                self._make_fallback_animations(self.idle_frame_count),
                self._make_fallback_animations(self.walk_frame_count),
            )

        crop_boxes = self._compute_row_crop_boxes(idle_raw, walk_raw)
        idle = self._apply_crop_boxes(idle_raw, crop_boxes, self.idle_frame_count)
        walk = self._apply_crop_boxes(walk_raw, crop_boxes, self.walk_frame_count)
        return idle, walk

    def _set_idle_sprite(self):
        """Show the idle frame for the current direction."""
        self.sprite = self.idle_animations[self.current_dir][self.idle_frame_index]

    def _set_direction_from_vector(self, dx, dy):
        # Prefer the dominant axis so diagonal movement still uses a stable row.
        """Choose facing direction from movement input."""
        if abs(dx) > abs(dy):
            self.current_dir = self.DIR_RIGHT if dx > 0 else self.DIR_LEFT
        elif abs(dy) > 0:
            self.current_dir = self.DIR_DOWN if dy > 0 else self.DIR_UP

    def _can_move_to(self, rect, collision_rects):
        """Return whether the player can stand at a position."""
        candidate_collision_rect = self._collision_rect_for(rect)
        for wall in collision_rects:
            if candidate_collision_rect.colliderect(wall):
                return False
        return True

    def _move_axis(self, axis, amount, collision_rects):
        """Move on one axis while checking collisions."""
        if amount == 0:
            return 0.0

        old_x = self.x
        old_y = self.y
        old_rect_x = self.rect.x
        old_rect_y = self.rect.y

        if axis == "x":
            self.x += amount
            candidate_rect = self.rect.copy()
            candidate_rect.x = int(round(self.x))
            if self._can_move_to(candidate_rect, collision_rects):
                self.rect.x = candidate_rect.x
            else:
                self.x = float(self.rect.x)
        else:
            self.y += amount
            candidate_rect = self.rect.copy()
            candidate_rect.y = int(round(self.y))
            if self._can_move_to(candidate_rect, collision_rects):
                self.rect.y = candidate_rect.y
            else:
                self.y = float(self.rect.y)

        moved_x = self.rect.x - old_rect_x
        moved_y = self.rect.y - old_rect_y

        if axis == "x" and moved_x == 0:
            self.x = old_x
        if axis == "y" and moved_y == 0:
            self.y = old_y

        return float(moved_x if axis == "x" else moved_y)

    def handle_movement(self, keys, collision_rects):
        """Move the player from keyboard input."""
        input_x = 0
        input_y = 0

        if self._key_down(keys, pygame.K_LEFT, pygame.K_a):
            input_x -= 1
        if self._key_down(keys, pygame.K_RIGHT, pygame.K_d):
            input_x += 1
        if self._key_down(keys, pygame.K_UP, pygame.K_w):
            input_y -= 1
        if self._key_down(keys, pygame.K_DOWN, pygame.K_s):
            input_y += 1

        if input_x == 0 and input_y == 0:
            self.frame_index = 0
            self._set_idle_sprite()
            return False

        self._set_direction_from_vector(input_x, input_y)

        length = math.hypot(input_x, input_y)
        move_x = (input_x / length) * self.move_speed
        move_y = (input_y / length) * self.move_speed

        old_rect_x = self.rect.x
        old_rect_y = self.rect.y

        self._move_axis("x", move_x, collision_rects)
        self._move_axis("y", move_y, collision_rects)
        self._sync_collision_rect()

        actual_distance = math.hypot(self.rect.x - old_rect_x, self.rect.y - old_rect_y)

        if actual_distance > 0:
            self._encounter_distance_accumulator += actual_distance
            self._update_animation()
        else:
            self.frame_index = 0
            self._set_idle_sprite()
            return False

        if self._encounter_distance_accumulator >= self.encounter_step_distance:
            self._encounter_distance_accumulator -= self.encounter_step_distance
            return True

        return False

    def _update_animation(self):
        """Advance the walking animation."""
        current_time = pygame.time.get_ticks()
        if current_time - self.animation_timer >= self.animation_delay:
            self.animation_timer = current_time
            self.frame_index = (self.frame_index + 1) % self.walk_frame_count
        self.sprite = self.walk_animations[self.current_dir][self.frame_index]

    def draw(self, surface):
        """Draw the player on the map."""
        surface.blit(
            self.sprite,
            (self.rect.x + self.draw_offset_x, self.rect.y + self.draw_offset_y),
        )
