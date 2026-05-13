"""NPC loading, animation, and simple map AI."""

import math

import pygame
from src.paths import resolve_asset_path


class NPC:
    """Map character that can talk, fight, or open a shop."""

    PLAYER_SPRITE_WIDTH = 64
    PLAYER_SPRITE_HEIGHT = 64
    PLAYER_DRAW_OFFSET_X = 0
    PLAYER_DRAW_OFFSET_Y = 0

    def __init__(
        self,
        name,
        x,
        y,
        enemy_ids=None,
        sprite_filename="sprites/npcs/story/sample_herbalist.png",
        npc_type="farm",
        sprite_sheet=False,
        dialogue=None,
        shop_items=None,
        sprite_rows=4,
        sprite_cols=6,
        sprite_width=PLAYER_SPRITE_WIDTH,
        sprite_height=PLAYER_SPRITE_HEIGHT,
    ):
        """Set up initial state."""
        self.name = name
        self.x = float(x)
        self.y = float(y)

        self.rect = pygame.Rect(x, y, 64, 64)
        self.collision_rect = pygame.Rect(x + 10, y + 36, 44, 24)
        self.custom_collision_rect = None
        self._sync_collision_rect()

        self.enemy_ids = enemy_ids if enemy_ids else []
        self.npc_type = npc_type
        self.dialogue = dialogue if dialogue else []
        self.shop_items = shop_items if shop_items else []
        self.required_quest = None
        self.battle_required_quest = None
        self.blocker = False
        self.defeated = False

        self.sprite_filename = sprite_filename
        self.sprite_sheet = sprite_sheet
        self.sprite_rows = int(sprite_rows)
        self.sprite_cols = int(sprite_cols)
        self.sprite_width = int(sprite_width)
        self.sprite_height = int(sprite_height)
        self.idle_frame_index = max(0, min(self.sprite_cols // 2, self.sprite_cols - 1))
        # Only boss markers animate; regular NPCs stay idle.
        self.animate_on_map = self.sprite_sheet and self.npc_type in ("boss", "final_boss")

        # Align player-sized NPC sprites with Zac.
        if (
            self.sprite_width == self.PLAYER_SPRITE_WIDTH
            and self.sprite_height == self.PLAYER_SPRITE_HEIGHT
        ):
            self.draw_offset_x = self.PLAYER_DRAW_OFFSET_X
            self.draw_offset_y = self.PLAYER_DRAW_OFFSET_Y
        else:
            self.draw_offset_x = (self.rect.width - self.sprite_width) // 2
            self.draw_offset_y = self.rect.height - self.sprite_height

        self.animation_frames = []
        self.animation_timer = pygame.time.get_ticks()
        self.animation_delay = 240
        self.animation_frame_index = 0
        self.idle_phase = (abs(hash(self.name)) % 628) / 100.0

        self.sprite = self._load_sprite()

    def _sync_collision_rect(self):
        """Update the NPC collision rectangle."""
        if self.custom_collision_rect is not None:
            self.collision_rect = self.custom_collision_rect.copy()
            return

        if self.name == "Mutant Bear":
            self.collision_rect = pygame.Rect(self.rect.x - 64, self.rect.y + 30, 320, 72)
            return

        self.collision_rect.x = self.rect.x + 10
        self.collision_rect.y = self.rect.y + 36

    def _fit_surface_to_canvas(self, source, trim=False):
        """Scale a sprite frame into the NPC canvas."""
        if trim:
            bbox = source.get_bounding_rect(min_alpha=1)
            if bbox.width > 0 and bbox.height > 0:
                source = source.subsurface(bbox).copy()

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

    def _load_sprite_sheet_frames(self):
        """Load animation frames from a sprite sheet."""
        path = resolve_asset_path(self.sprite_filename)
        if not path.exists():
            return []

        sheet = pygame.image.load(str(path)).convert_alpha()
        sheet_w, sheet_h = sheet.get_size()
        frame_w = sheet_w // self.sprite_cols
        frame_h = sheet_h // self.sprite_rows
        frames = []

        for col in range(self.sprite_cols):
            rect = pygame.Rect(col * frame_w, 0, frame_w, frame_h)
            frame = sheet.subsurface(rect).copy()
            frames.append(self._fit_surface_to_canvas(frame, trim=False))

        return frames

    def _load_static_sprite(self):
        """Load a single-frame NPC sprite."""
        path = resolve_asset_path(self.sprite_filename)
        if not path.exists():
            fallback = pygame.Surface((self.sprite_width, self.sprite_height), pygame.SRCALPHA)
            fallback.fill((255, 0, 255, 255))
            return fallback

        source = pygame.image.load(str(path)).convert_alpha()
        return self._fit_surface_to_canvas(source, trim=True)

    def _load_sprite(self):
        """Load the NPC sprite or fallback image."""
        if self.sprite_sheet:
            self.animation_frames = self._load_sprite_sheet_frames()
            if self.animation_frames:
                if self.animate_on_map:
                    self.animation_frame_index = 0
                    return self.animation_frames[0]
                return self.animation_frames[self.idle_frame_index]

        self.animation_frames = []
        return self._load_static_sprite()

    def update_ai(self, player_rect, collision_rects):
        """Update simple NPC idle animation."""
        self._sync_collision_rect()
        self._update_idle_animation()


    def _update_idle_animation(self):
        # Boss markers can loop through their idle frames.
        """Advance the idle animation timer."""
        if not self.animate_on_map or not self.animation_frames:
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.animation_timer >= self.animation_delay:
            self.animation_timer = current_time
            self.animation_frame_index = (
                self.animation_frame_index + 1
            ) % len(self.animation_frames)
            self.sprite = self.animation_frames[self.animation_frame_index]

    def get_idle_bob_offset(self):
        """Return the idle bob offset."""
        return 0

    def get_attention_pulse(self):
        """Return the attention pulse."""
        current_time = pygame.time.get_ticks() / 1000.0
        return 0.5 + 0.5 * math.sin(current_time * 5.0 + self.idle_phase)

    def draw(self, surface, camera=None):
        """Draw the NPC on the map."""
        if self.defeated:
            return

        draw_rect = camera.apply(self.rect) if camera else self.rect
        surface.blit(
            self.sprite,
            (
                draw_rect.x + self.draw_offset_x,
                draw_rect.y + self.draw_offset_y,
            ),
        )
