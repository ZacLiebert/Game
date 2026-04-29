class BaseScreen:
    """
    Base class for all UI screens in the game.
    Enforces a standard interface so the Screen Manager (Stack) can seamlessly
    interact with any active screen.
    """
    def __init__(self, screen_manager):
        """
        Args:
            screen_manager (Stack): The state machine managing screen transitions.
                                    Passed in so screens can push/pop themselves.
        """
        self.screen_manager = screen_manager

    def handle_event(self, event):
        """
        Processes Pygame events (e.g., keyboard presses, mouse clicks).
        Must be overridden by child classes.
        """
        pass

    def update(self):
        """
        Updates game logic (e.g., animations, timers) for the current frame.
        Must be overridden by child classes.
        """
        pass

    def draw(self, surface):
        """
        Renders the screen graphics onto the given Pygame surface.
        Must be overridden by child classes.
        """
        pass