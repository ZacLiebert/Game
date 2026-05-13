"""TMX map loading and drawing."""

from dataclasses import dataclass
from pathlib import Path

import pygame
from pytmx.util_pygame import load_pygame


@dataclass
class TmxDrawItem:
    """Represents the Tmx Draw Item component used by Mutation RPG."""
    image: pygame.Surface
    rect: pygame.Rect
    y_sort: int
    layer: str = "main"
    glow: bool = False


class ClearCodeTmxWorld:
    """Loader/renderer for a custom Tiled TMX map using Clean Code Python-Monsters tilesets."""

    def __init__(self, tmx_path):
        """Set up initial state."""
        self.tmx_path = Path(tmx_path)
        if not self.tmx_path.exists():
            raise FileNotFoundError(f"TMX map not found: {self.tmx_path}")

        self.tmx_data = load_pygame(str(self.tmx_path))
        self.tile_width = int(self.tmx_data.tilewidth)
        self.tile_height = int(self.tmx_data.tileheight)
        self.width = int(self.tmx_data.width) * self.tile_width
        self.height = int(self.tmx_data.height) * self.tile_height

        # assets/cc_monsters/data/maps/quarantine_woods.tmx -> assets/cc_monsters
        self.asset_root = self.tmx_path.parents[2]

        self.background_items = []
        self.main_items = []
        self.foreground_items = []
        self.collision_rects = []
        self.encounter_rects = []

        self.water_frames = self._load_water_frames()
        self.coast_frames = self._load_coast_frames()

        self._build_layers()

    # Asset helpers

    def _safe_load_image(self, path):
        """Load an image and return None if it fails."""
        if not path.exists():
            return None
        return pygame.image.load(str(path)).convert_alpha()

    def _load_water_frames(self):
        """Load the water frames."""
        folder = self.asset_root / "graphics" / "tilesets" / "water"
        frames = []
        if folder.exists():
            # Asset-loading order only, not part of the submitted DSA components.
            # Core sorting algorithms are implemented manually in src/data_structures.
            for path in sorted(folder.glob("*.png"), key=lambda p: int(p.stem)):
                image = self._safe_load_image(path)
                if image:
                    frames.append(image)
        return frames

    def _load_coast_frames(self):
        """Load the coast frames."""
        path = self.asset_root / "graphics" / "tilesets" / "coast.png"
        source = self._safe_load_image(path)
        if source is None:
            return {}

        cols, rows = 24, 12
        cell_w = source.get_width() // cols
        cell_h = source.get_height() // rows

        frame_dict = {}
        for col in range(cols):
            for row in range(rows):
                frame = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
                frame.blit(source, (0, 0), pygame.Rect(col * cell_w, row * cell_h, cell_w, cell_h))
                frame_dict[(col, row)] = frame

        terrains = ["grass", "grass_i", "sand_i", "sand", "rock", "rock_i", "ice", "ice_i"]
        sides = {
            "topleft": (0, 0),
            "top": (1, 0),
            "topright": (2, 0),
            "left": (0, 1),
            "right": (2, 1),
            "bottomleft": (0, 2),
            "bottom": (1, 2),
            "bottomright": (2, 2),
        }

        result = {}
        for index, terrain in enumerate(terrains):
            result[terrain] = {}
            for side, pos in sides.items():
                result[terrain][side] = frame_dict.get((pos[0] + index * 3, pos[1]))
        return result

    # Layer build

    def _layer_exists(self, name):
        """Return whether a TMX layer exists."""
        try:
            self.tmx_data.get_layer_by_name(name)
            return True
        except ValueError:
            return False

    def _build_layers(self):
        """Build collision and draw data from TMX layers."""
        for layer_name in ("Terrain", "Terrain Top"):
            if not self._layer_exists(layer_name):
                continue

            for tile_x, tile_y, image in self.tmx_data.get_layer_by_name(layer_name).tiles():
                rect = pygame.Rect(
                    tile_x * self.tile_width,
                    tile_y * self.tile_height,
                    self.tile_width,
                    self.tile_height,
                )
                self.background_items.append(TmxDrawItem(image, rect, rect.bottom, "bg"))

        # Tile-object visual layer used by our custom map. This avoids
        # generated tile-object GIDs in Tiled's object panel and makes the map
        # visually editable directly as a normal tile layer. Larger image-collection
        # tiles are bottom-aligned to their grid cell, matching Tiled-style object placement.
        for layer_name in ("Object Tiles", "Object Top"):
            if self._layer_exists(layer_name):
                for tile_x, tile_y, image in self.tmx_data.get_layer_by_name(layer_name).tiles():
                    x = tile_x * self.tile_width
                    y = (tile_y + 1) * self.tile_height - image.get_height()
                    rect = pygame.Rect(x, y, image.get_width(), image.get_height())
                    item = TmxDrawItem(image, rect, rect.bottom, "main")
                    if layer_name == "Object Top":
                        self.foreground_items.append(item)
                    else:
                        self.main_items.append(item)

        # Water rectangles are not tile objects in the original map; Clear Code
        # repeats animated water frames over these rectangles. We use frame 0.
        if self._layer_exists("Water") and self.water_frames:
            water_image = self.water_frames[0]
            for obj in self.tmx_data.get_layer_by_name("Water"):
                start_x = int(obj.x)
                start_y = int(obj.y)
                end_x = int(obj.x + obj.width)
                end_y = int(obj.y + obj.height)

                # removed from the TMX because they blocked visible grass/shore
                # tiles. This keeps the rule simple: visible land/path is
                # walkable, water is not.
                self.collision_rects.append(
                    pygame.Rect(start_x, start_y, end_x - start_x, end_y - start_y)
                )

                for x in range(start_x, end_x, self.tile_width):
                    for y in range(start_y, end_y, self.tile_height):
                        rect = pygame.Rect(x, y, self.tile_width, self.tile_height)
                        self.background_items.append(TmxDrawItem(water_image, rect, rect.bottom, "water"))

        if self._layer_exists("Coast") and self.coast_frames:
            for obj in self.tmx_data.get_layer_by_name("Coast"):
                terrain = obj.properties.get("terrain")
                side = obj.properties.get("side")
                image = self.coast_frames.get(terrain, {}).get(side)
                if image:
                    rect = pygame.Rect(int(obj.x), int(obj.y), image.get_width(), image.get_height())
                    self.background_items.append(TmxDrawItem(image, rect, rect.bottom, "coast"))

                    # Coast graphics contain both water/rocks and a small amount
                    # Water rectangles, which left the water/rock pixels inside
                    # coast tiles walkable. Build a small color-mask collision
                    # from the coast image so Zac cannot step into water, while
                    # green/sand ground that is actually visible remains usable.
                    self.collision_rects.extend(
                        self._coast_collision_rects(image, rect.x, rect.y)
                    )

        if self._layer_exists("Objects"):
            for obj in self.tmx_data.get_layer_by_name("Objects"):
                image = getattr(obj, "image", None)
                if image is None:
                    continue

                rect = pygame.Rect(int(obj.x), int(obj.y), image.get_width(), image.get_height())
                item = TmxDrawItem(image, rect, rect.bottom, "main")

                if getattr(obj, "name", "") == "top":
                    self.foreground_items.append(item)
                else:
                    self.main_items.append(item)

        if self._layer_exists("Monsters"):
            for obj in self.tmx_data.get_layer_by_name("Monsters"):
                image = getattr(obj, "image", None)
                rect = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                self.encounter_rects.append(rect)
                if image is not None:
                    self.main_items.append(TmxDrawItem(image, rect, rect.bottom, "monster", glow=True))

        if self._layer_exists("Collisions"):
            for obj in self.tmx_data.get_layer_by_name("Collisions"):
                self.collision_rects.append(
                    pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                )

        self._add_object_tile_collisions()

    def _add_object_tile_collisions(self):
        """Add object tile collisions."""
        if not self._layer_exists("Object Tiles"):
            return

        layer = self.tmx_data.get_layer_by_name("Object Tiles")
        for tile_x, tile_y, image in layer.tiles():
            if image is None:
                continue

            width = int(image.get_width())
            height = int(image.get_height())
            world_x = tile_x * self.tile_width
            world_bottom = (tile_y + 1) * self.tile_height

            # Large buildings already have hand-authored collision rectangles
            # in the TMX `Collisions` group. Duplicating them can make doors
            # feel blocked too early, so leave those to the authored boxes.
            if width >= 300 or height >= 300:
                continue

            if width <= 72 and height <= 72:
                # Rocks and small ground props.
                rect = pygame.Rect(
                    world_x + 8,
                    world_bottom - 42,
                    max(16, width - 16),
                    34,
                )
            elif width <= 80:
                # Narrow pillars / small trees.
                rect = pygame.Rect(
                    world_x + 10,
                    world_bottom - 58,
                    max(20, width - 20),
                    50,
                )
            elif width <= 160:
                # Full trees: block the trunk/base, not the leafy canopy.
                rect = pygame.Rect(
                    world_x + width // 3,
                    world_bottom - 54,
                    max(28, width // 3),
                    46,
                )
            else:
                # Wide props such as gate tops: a thin base hitbox is enough.
                rect = pygame.Rect(
                    world_x + width // 4,
                    world_bottom - 34,
                    max(32, width // 2),
                    26,
                )

            self.collision_rects.append(rect)

    def _coast_collision_rects(self, image, world_x, world_y):
        """Build collision rectangles from coast pixels."""
        block = 8
        cols = max(1, (int(image.get_width()) + block - 1) // block)
        rows = max(1, (int(image.get_height()) + block - 1) // block)
        solid = [[False for _ in range(cols)] for _ in range(rows)]

        for row in range(rows):
            for col in range(cols):
                x0 = col * block
                y0 = row * block
                x1 = min(x0 + block, int(image.get_width()))
                y1 = min(y0 + block, int(image.get_height()))
                samples = 0
                blocked = 0
                for px in range(x0, x1, 2):
                    for py in range(y0, y1, 2):
                        samples += 1
                        if self._is_coast_blocking_pixel(image.get_at((px, py))):
                            blocked += 1

                # A low threshold intentionally treats jagged water/rock edges as
                # solid so the 28px foot hitbox cannot slip into water between
                # tiny visual gaps.
                solid[row][col] = samples > 0 and blocked / samples >= 0.20

        # Merge cells into larger rectangles: first horizontal runs, then stack
        # identical runs vertically. This keeps movement checks lightweight.
        row_runs = []
        for row in range(rows):
            runs = []
            col = 0
            while col < cols:
                if not solid[row][col]:
                    col += 1
                    continue
                start = col
                while col < cols and solid[row][col]:
                    col += 1
                runs.append((start * block, row * block, (col - start) * block, block))
            row_runs.append(runs)

        active = {}
        rects = []
        for row, runs in enumerate(row_runs):
            current = {}
            for x, y, w, h in runs:
                key = (x, w)
                if key in active:
                    ax, ay, aw, ah = active[key]
                    current[key] = (ax, ay, aw, ah + block)
                else:
                    current[key] = (x, y, w, h)
            for key, rect in active.items():
                if key not in current:
                    rects.append(rect)
            active = current
        rects.extend(active.values())

        return [
            pygame.Rect(int(world_x + x), int(world_y + y), int(w), int(h))
            for x, y, w, h in rects
            if w > 0 and h > 0
        ]

    def _is_coast_blocking_pixel(self, color):
        """Return whether a coast pixel should block movement."""
        r, g, b, a = color
        if a < 24:
            return False

        # Blue/cyan water pixels.
        is_water = b >= 115 and g >= 70 and r <= 100 and (b - r) >= 35

        # Brown/orange rocky shoreline pixels. Sand and grass stay walkable; the
        # green/yellow land side of the coast tile is intentionally excluded.
        is_rock = (
            r >= 80
            and 35 <= g <= 180
            and b <= 120
            and (r - b) >= 35
            and r >= g
        )

        return is_water or is_rock

    # Public API

    def get_colliding_rects(self):
        """Return the colliding rects."""
        return [rect.copy() for rect in self.collision_rects]

    def player_in_encounter_zone(self, player_rect):
        """Return whether the player is inside an encounter zone."""
        foot_x = player_rect.centerx
        foot_y = player_rect.bottom - 1
        return any(rect.collidepoint(foot_x, foot_y) for rect in self.encounter_rects)

    def _visible(self, item, viewport):
        """Return whether a rectangle is inside the camera view."""
        return item.rect.colliderect(viewport)

    def draw_background(self, surface, camera, play_area):
        """Draw animated background map layers."""
        viewport = pygame.Rect(-camera.camera.x, -camera.camera.y, camera.width, camera.height)
        for item in self.background_items:
            if self._visible(item, viewport):
                screen_rect = camera.apply(item.rect)
                screen_rect.x += play_area.x
                screen_rect.y += play_area.y
                surface.blit(item.image, screen_rect)

    def get_visible_main_items(self, camera):
        """Return the visible main items."""
        viewport = pygame.Rect(-camera.camera.x, -camera.camera.y, camera.width, camera.height)
        return [item for item in self.main_items if self._visible(item, viewport)]

    def draw_item(self, surface, item, camera, play_area):
        """Draw one visible map item."""
        screen_rect = camera.apply(item.rect)
        screen_rect.x += play_area.x
        screen_rect.y += play_area.y
        surface.blit(item.image, screen_rect)

        if item.glow:
            glow = pygame.Surface((screen_rect.width, screen_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow, (0, 255, 150, 20), glow.get_rect(), border_radius=4)
            surface.blit(glow, screen_rect.topleft)

    def draw_foreground(self, surface, camera, play_area):
        """Draw foreground map layers above actors."""
        viewport = pygame.Rect(-camera.camera.x, -camera.camera.y, camera.width, camera.height)
        for item in self.foreground_items:
            if self._visible(item, viewport):
                self.draw_item(surface, item, camera, play_area)
