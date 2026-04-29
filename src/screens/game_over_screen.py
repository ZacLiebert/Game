import pygame
import sys
from src.screens.base_screen import BaseScreen

class GameOverScreen(BaseScreen):
    """
    The screen displayed when the entire party is defeated.
    """
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self.font = pygame.font.SysFont(None, 72)
        self.small_font = pygame.font.SysFont(None, 36)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # Pressing anything closes the game (for now)
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                pygame.quit()
                sys.exit()

    def update(self):
        pass

    def draw(self, surface):
        # A grim, dark red background
        surface.fill((40, 10, 10)) 
        
        center_x = surface.get_width() // 2
        
        # Main Title
        text = self.font.render("SYSTEM FAILURE: YOU DIED", True, (255, 50, 50))
        text_rect = text.get_rect(center=(center_x, surface.get_height() // 2 - 50))
        surface.blit(text, text_rect)
        
        # Subtext
        subtext = self.small_font.render("Press [ENTER] to Exit to Desktop", True, (200, 200, 200))
        sub_rect = subtext.get_rect(center=(center_x, surface.get_height() // 2 + 50))
        surface.blit(subtext, sub_rect)