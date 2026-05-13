"""Sprite loading and caching."""

import pygame

from src.paths import resolve_asset_path


class SpriteManager:
    """Loads and caches sprites used by screens."""

    _cache = {}

    @classmethod
    def get_sprite(cls, filename, width=40, height=40):
        """Load and cache one sprite image."""
        cache_key = f"{filename}_{width}x{height}"

        if cache_key not in cls._cache:
            path = resolve_asset_path(filename)

            if path.exists():
                image = pygame.image.load(str(path)).convert_alpha()
                image = pygame.transform.scale(image, (width, height))
                cls._cache[cache_key] = image
            else:
                fallback = pygame.Surface((width, height))
                fallback.fill((255, 0, 255))
                cls._cache[cache_key] = fallback

        return cls._cache[cache_key]

    @classmethod
    def load_sprite_sheet(
        cls,
        filename,
        rows=4,
        cols=4,
        target_width=40,
        target_height=40
    ):
        """Load and slice a sprite sheet."""
        cache_key = (
            f"{filename}_sheet_"
            f"{rows}x{cols}_"
            f"{target_width}x{target_height}"
        )

        if cache_key not in cls._cache:
            path = resolve_asset_path(filename)

            if path.exists():
                sheet = pygame.image.load(str(path)).convert_alpha()
                sheet_w, sheet_h = sheet.get_size()

                frame_w = sheet_w // cols
                frame_h = sheet_h // rows

                frames = []

                for row in range(rows):
                    row_frames = []

                    for col in range(cols):
                        rect = pygame.Rect(
                            col * frame_w,
                            row * frame_h,
                            frame_w,
                            frame_h
                        )

                        frame_surface = sheet.subsurface(rect).copy()

                        frame_surface = pygame.transform.scale(
                            frame_surface,
                            (target_width, target_height)
                        )

                        row_frames.append(frame_surface)

                    frames.append(row_frames)

                cls._cache[cache_key] = frames

            else:
                fallback = pygame.Surface((target_width, target_height))
                fallback.fill((255, 0, 255))

                cls._cache[cache_key] = [
                    [fallback for _ in range(cols)]
                    for _ in range(rows)
                ]

        return cls._cache[cache_key]
