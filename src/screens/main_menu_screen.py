import pygame
import os
from src.screens.base_screen import BaseScreen
from src.data_structures.cryptography import SaveEncryption

class MainMenuScreen(BaseScreen):
    """
    The title screen of the game.
    Handles starting a new game or loading an encrypted save file.
    """
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self.title_font = pygame.font.SysFont(None, 60)
        self.menu_font = pygame.font.SysFont(None, 40)
        self.small_font = pygame.font.SysFont(None, 24)
        
        # Path to the encrypted save file
        self.save_file_path = "save_data/save1.dat"
        self.status_message = ""

    def handle_event(self, event):
        """Handles menu selection via keyboard."""
        if event.type == pygame.KEYDOWN:
            
            # --- NEW GAME ---
            if event.key == pygame.K_n:
                # Local import to prevent circular dependency
                from src.screens.map_screen import MapScreen
                self.screen_manager.push(MapScreen(self.screen_manager))
                
            # --- LOAD GAME (DECRYPT) ---
            elif event.key == pygame.K_l:
                if os.path.exists(self.save_file_path):
                    save_data = SaveEncryption.load_game(self.save_file_path)
                    if save_data:
                        print("Save file decrypted and loaded successfully!")
                        
                        # Inject decrypted data into the active GameSession
                        self.screen_manager.game_session.import_save_data(save_data)
                        
                        # Local import to prevent circular dependency
                        from src.screens.map_screen import MapScreen
                        self.screen_manager.push(MapScreen(self.screen_manager))
                    else:
                        self.status_message = "ERROR: Save file corrupted or tampered with!"
                else:
                    self.status_message = "No save file found. Start a New Game first."
                    
            # --- SAVE GAME (ENCRYPT) ---
            elif event.key == pygame.K_s:
                # Pull the live state from the GameSession
                save_data = self.screen_manager.game_session.export_save_data()
                
                # Encrypt and write to disk via RC4
                SaveEncryption.save_game(save_data, self.save_file_path)
                self.status_message = "Game Session Encrypted & Saved!"
                
            # --- QUIT ---
            elif event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self):
        """No logic updates needed for a static menu."""
        pass

    def draw(self, surface):
        """Renders the title screen UI."""
        surface.fill((15, 15, 20)) # Deep space dark background
        
        center_x = surface.get_width() // 2
        
        # Title
        title_surf = self.title_font.render("MUTATION RPG", True, (152, 195, 121))
        title_rect = title_surf.get_rect(center=(center_x, 150))
        surface.blit(title_surf, title_rect)
        
        # Menu Options
        y_offset = 250
        options = [
            "[N] New Game",
            "[L] Load Encrypted Save",
            "[S] Test Save Mechanism",
            "[ESC] Quit"
        ]
        
        for option in options:
            opt_surf = self.menu_font.render(option, True, (220, 220, 220))
            opt_rect = opt_surf.get_rect(center=(center_x, y_offset))
            surface.blit(opt_surf, opt_rect)
            y_offset += 60
            
        # Dynamic Status Message (Shows Success/Error logs)
        if self.status_message:
            color = (100, 200, 255) if "Saved" in self.status_message else (255, 100, 100)
            status_surf = self.small_font.render(self.status_message, True, color)
            status_rect = status_surf.get_rect(center=(center_x, y_offset + 20))
            surface.blit(status_surf, status_rect)