"""Manages game audio safely."""

import pygame

from src.paths import BGM_DIR, SFX_DIR


class AudioManager:
    """Safely manages background music, sound effects, and mute state."""

    BGM_FILES = {
        "forest": "forest.ogg",
        "map": "map_relax.ogg",
        "battle": "battle.ogg",
        "boss": "boss.ogg",
    }

    SFX_FILES = {
        "success": "success.wav",
        "game_over": "game_over.wav",
        "click": "click.wav",
        "error": "error.wav",
        "hit": "hit.wav",
        "alert": "alert.wav",
    }

    BGM_VOLUMES = {
        "forest": 0.45,
        "map": 0.52,
        "battle": 0.55,
        "boss": 0.55,
    }

    def __init__(self, music_volume=0.50, sfx_volume=0.70):
        """Set up initial state."""
        self.music_volume = music_volume
        self.sfx_volume = sfx_volume
        self.current_track = None
        self.muted = False
        self.available = False
        self.sounds = {}

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            self.available = True
            pygame.mixer.music.set_volume(self.music_volume)
            self._load_sfx()
        except pygame.error as exc:
            print(f"Audio disabled: {exc}")
            self.available = False

    def _load_sfx(self):
        """Load the sfx."""
        for name, filename in self.SFX_FILES.items():
            path = SFX_DIR / filename

            if not path.exists():
                continue

            try:
                sound = pygame.mixer.Sound(str(path))
                sound.set_volume(self.sfx_volume)
                self.sounds[name] = sound
            except pygame.error:
                continue

    def play_bgm(self, track_name, fade_ms=600):
        """Play background music for the current screen."""
        if not self.available or self.muted:
            return

        if self.current_track == track_name:
            return

        filename = self.BGM_FILES.get(track_name)
        if not filename:
            self.stop_bgm()
            return

        path = BGM_DIR / filename
        if not path.exists():
            return

        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(
                self.BGM_VOLUMES.get(track_name, self.music_volume)
            )
            pygame.mixer.music.play(-1, fade_ms=fade_ms)
            self.current_track = track_name
        except pygame.error as exc:
            print(f"Could not play music {path}: {exc}")

    def stop_bgm(self, fade_ms=400):
        """Stop the current background music."""
        if not self.available:
            return

        try:
            pygame.mixer.music.fadeout(fade_ms)
        except pygame.error:
            pass

        self.current_track = None

    def play_sfx(self, name):
        """Play a short sound effect by name."""
        if not self.available or self.muted:
            return

        sound = self.sounds.get(name)
        if not sound:
            return

        try:
            sound.play()
        except pygame.error:
            pass

    def toggle_mute(self):
        """Toggle all game audio on or off."""
        self.muted = not self.muted

        if self.muted:
            self.stop_bgm(fade_ms=100)
        else:
            self.current_track = None

        return self.muted

    def shutdown(self):
        """Close the audio mixer safely."""
        if not self.available:
            return

        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except pygame.error:
            pass
