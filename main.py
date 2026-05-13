"""Run Mutation RPG."""

import pygame
import sys

from src.core.screen_manager import ScreenManager
from src.screens.main_menu_screen import MainMenuScreen
from src.core.game_session import GameSession
from src.core.audio_manager import AudioManager


def main():
    # Set up Pygame and the window.
    """Start the game and run the main loop."""
    pygame.init()

    WIDTH, HEIGHT = 1280, 720
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Turn-based RPG: Mutation")

    clock = pygame.time.Clock()
    FPS = 60

    # Create shared managers and the first screen.
    screen_manager = ScreenManager()

    screen_manager.game_session = GameSession()
    screen_manager.audio = AudioManager()

    start_screen = MainMenuScreen(screen_manager)
    screen_manager.push(start_screen)

    # Main game loop.
    running = True
    last_music_track = object()

    while running:
        # Read the active screen.
        try:
            current_screen = screen_manager.peek()
        except IndexError:
            running = False
            break

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                screen_manager.audio.toggle_mute()
                # Re-apply music after unmuting.
                last_music_track = object()
                continue

            current_screen.handle_event(event)

            # A screen can change while handling input.
            try:
                current_screen = screen_manager.peek()
            except IndexError:
                running = False
                break

        if not running:
            break

        # Re-read the active screen before updating.
        try:
            current_screen = screen_manager.peek()
        except IndexError:
            running = False
            break

        music_track = getattr(current_screen, "music_track", "forest")
        if music_track != last_music_track:
            if music_track is None:
                screen_manager.audio.stop_bgm()
            else:
                screen_manager.audio.play_bgm(music_track)
            last_music_track = music_track

        # Update
        current_screen.update()

        # Update can also change the active screen.
        try:
            current_screen = screen_manager.peek()
        except IndexError:
            running = False
            break

        # Drawing
        current_screen.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    screen_manager.audio.shutdown()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
