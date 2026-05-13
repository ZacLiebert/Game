"""Base class for screen objects."""

class BaseScreen:
    """Common interface used by all game screens."""
    def __init__(self, screen_manager):
        """Set up initial state."""
        self.screen_manager = screen_manager

    def handle_event(self, event):
        """Handle the event."""
        pass

    def update(self):
        """Update this screen for the current frame."""
        pass

    def draw(self, surface):
        """Draw this screen."""
        pass

    def play_sfx(self, name):
        """Play sfx."""
        audio = getattr(self.screen_manager, "audio", None)

        if audio:
            audio.play_sfx(name)

    def play_bgm(self, track_name):
        """Play bgm."""
        audio = getattr(self.screen_manager, "audio", None)

        if audio:
            audio.play_bgm(track_name)

