import pygame
import sys

# Import your Data Structure and Screen classes
from src.data_structures.stack import Stack
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

    # Attach the global GameSession to the Stack.
    screen_manager.game_session = GameSession()

    start_screen = MainMenuScreen(screen_manager)
    screen_manager.push(start_screen)

    # 3. Main Game Loop
    running = True

    while running:
        # Safely get current active screen
        try:
            current_screen = screen_manager.peek()
        except IndexError:
            running = False
            break

        # =========================
        # EVENT HANDLING
        # =========================
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            current_screen.handle_event(event)

            # Important:
            # The active screen may change during handle_event().
            # Example: DialogueScreen can pop itself after ENTER/SPACE.
            try:
                current_screen = screen_manager.peek()
            except IndexError:
                running = False
                break

        if not running:
            break

        # Re-check the active screen after all events.
        # This prevents update/draw from using an old popped screen.
        try:
            current_screen = screen_manager.peek()
        except IndexError:
            running = False
            break

        # =========================
        # UPDATE LOGIC
        # =========================
        current_screen.update()

        # The screen may change during update() too.
        try:
            current_screen = screen_manager.peek()
        except IndexError:
            running = False
            break

        # =========================
        # RENDER GRAPHICS
        # =========================
        current_screen.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()