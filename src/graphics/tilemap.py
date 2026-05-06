import pygame


class TileMap:
    """
    Manages the 2D grid world, rendering graphics and handling collision data.
    """
    def __init__(self, tile_size=32):
        self.tile_size = tile_size
        self.tiles = {}
        self.map_grid = []
        self.collision_tiles = set()

    def add_tile(self, tile_id, surface, is_collision=False):
        """Registers a graphic to an ID and sets its solid/walkable status."""
        self.tiles[tile_id] = surface

        if is_collision:
            self.collision_tiles.add(tile_id)

    def load_map(self, grid_data):
        """Loads the 2D array representation of the level."""
        self.map_grid = grid_data

    def get_colliding_rects(self):
        """
        Returns smaller collision rectangles for solid tiles.

        For tree tiles, using the whole 64x64 tile feels too strict.
        This version only blocks the lower/base part of each tree.
        """
        rects = []

        for row_idx, row in enumerate(self.map_grid):
            for col_idx, tile_id in enumerate(row):
                if tile_id in self.collision_tiles:
                    x = col_idx * self.tile_size
                    y = row_idx * self.tile_size

                    # Collision only around the tree trunk/base.
                    collision_x = x + int(self.tile_size * 0.10)
                    collision_y = y + int(self.tile_size * 0.35)
                    collision_w = int(self.tile_size * 0.80)
                    collision_h = int(self.tile_size * 0.60)

                    rects.append(
                        pygame.Rect(
                            collision_x,
                            collision_y,
                            collision_w,
                            collision_h
                        )
                    )

        return rects

    def draw(self, surface):
        """Draws the map onto the screen."""
        for row_idx, row in enumerate(self.map_grid):
            for col_idx, tile_id in enumerate(row):
                if tile_id in self.tiles:
                    x = col_idx * self.tile_size
                    y = row_idx * self.tile_size
                    surface.blit(self.tiles[tile_id], (x, y))