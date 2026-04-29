import pygame

class TileMap:
    """
    Manages the 2D grid world, rendering graphics and handling collision data.
    """
    def __init__(self, tile_size=32):
        self.tile_size = tile_size
        self.tiles = {}             # Maps tile ID to a Pygame Surface (graphic)
        self.map_grid = []          # 2D array representing the level layout
        self.collision_tiles = set() # Set of tile IDs that act as solid walls

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
        Scans the grid and returns a list of Pygame Rects for all solid walls.
        The Player class will use this to prevent walking out of bounds.
        """
        rects = []
        for row_idx, row in enumerate(self.map_grid):
            for col_idx, tile_id in enumerate(row):
                if tile_id in self.collision_tiles:
                    x = col_idx * self.tile_size
                    y = row_idx * self.tile_size
                    rects.append(pygame.Rect(x, y, self.tile_size, self.tile_size))
        return rects

    def draw(self, surface):
        """Draws the map onto the screen."""
        for row_idx, row in enumerate(self.map_grid):
            for col_idx, tile_id in enumerate(row):
                if tile_id in self.tiles:
                    x = col_idx * self.tile_size
                    y = row_idx * self.tile_size
                    surface.blit(self.tiles[tile_id], (x, y))