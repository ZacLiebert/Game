"""Camera helper for scrolling maps."""

import pygame

class Camera:
    """Keeps the map view centered on the player."""
    def __init__(self, width, height, map_width, map_height):
        """Set up initial state."""
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.map_width = map_width
        self.map_height = map_height

    def apply(self, entity_rect):
        """Apply the camera offset to a rectangle."""
        return entity_rect.move(self.camera.topleft)

    def update(self, target_rect):
        """Move the camera to follow the target."""
        x = -target_rect.centerx + int(self.width / 2)
        y = -target_rect.centery + int(self.height / 2)

        self.camera.topleft = (x, y)
