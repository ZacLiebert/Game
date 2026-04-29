import pygame
import sys

# Import your Data Structure and Screen classes
from src.data_structures.stack import Stack
from src.screens.map_screen import MapScreen
from src.screens.main_menu_screen import MainMenuScreen
from src.core.game_session import GameSession

def main():
    # 1. Initialize Pygame and the display window
    pygame.init()
    WIDTH, HEIGHT = 1280, 720
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Turn-based RPG: Mutation")
    clock = pygame.time.Clock()
    FPS = 60

    # 2. Initialize the State Machine (Stack)
    # This directly fulfills your DSA Stack requirement for UI flow.
    screen_manager = Stack()
    
    # Attach the global GameSession to the Stack!
    screen_manager.game_session = GameSession()

    start_screen = MainMenuScreen(screen_manager)
    screen_manager.push(start_screen)

    # 5. Main Game Loop
    running = True
    while running:
        # Safely peek at the top of the stack to see which screen is active
        try:
            current_screen = screen_manager.peek()
        except IndexError:
            # If the stack is completely empty, exit the game safely
            running = False
            break

        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Delegate event handling entirely to the active screen
            current_screen.handle_event(event)

        # --- UPDATE LOGIC ---
        # Delegate logic updates (animations, timers) to the active screen
        current_screen.update()

        # --- RENDER GRAPHICS ---
        # Delegate all drawing commands to the active screen
        current_screen.draw(screen)

        # Update the display and maintain frame rate
        pygame.display.flip()
        clock.tick(FPS)

    # Clean exit
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()