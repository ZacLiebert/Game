import pygame

class Camera:
    def __init__(self, width, height, map_width, map_height):
        # The rectangle representing the camera's view [cite: 176]
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.map_width = map_width
        self.map_height = map_height

    def apply(self, entity_rect):
        """Returns a new rect shifted by the camera offset."""
        return entity_rect.move(self.camera.topleft)

    def update(self, target_rect):
        """Strictly centers the camera on the player at all times."""
        # Calculate center position relative to the screen [cite: 177]
        x = -target_rect.centerx + int(self.width / 2)
        y = -target_rect.centery + int(self.height / 2)

        # Apply the coordinates to the camera rect [cite: 178]
        self.camera.topleft = (x, y)