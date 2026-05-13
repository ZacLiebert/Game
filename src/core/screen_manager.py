"""Screen-stack helper."""

class ScreenManager:
    """Maintains the active screen stack."""

    def __init__(self):
        """Set up initial state."""
        self._screens = []
        self.game_session = None
        self.audio = None

    def push(self, screen):
        """Open a new screen above the current one."""
        self._screens.append(screen)

    def pop(self):
        """Close and return the current screen."""
        if not self._screens:
            raise IndexError("No active screen to close")
        return self._screens.pop()

    def peek(self):
        """Return the current screen without closing it."""
        if not self._screens:
            raise IndexError("No active screen")
        return self._screens[-1]

    def previous(self):
        """Return the screen under the current one."""
        if len(self._screens) < 2:
            return None
        return self._screens[-2]

    def size(self):
        """Return how many screens are open."""
        return len(self._screens)
