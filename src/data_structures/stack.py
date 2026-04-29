class Stack:
    """
    Stack data structure (LIFO).
    Used to control the sequential flow between UI screens (Map, Combat, Inventory).
    """
    def __init__(self):
        """Initialize an empty stack."""
        self.stack = []

    def push(self, item):
        """
        Push a screen/state onto the top of the stack.

        Args:
            item: The UI state or screen object to display.
        """
        self.stack.append(item)

    def pop(self):
        """
        Remove and return the screen at the top of the stack (return to previous screen).

        Returns:
            The item just removed from the stack.
        Raises:
            IndexError: If the stack is empty.
        """
        if not self.is_empty():
            return self.stack.pop()
        raise IndexError("Stack is empty")

    def peek(self):
        """
        Get the current screen at the top of the stack without removing it.

        Returns:
            The item at the top of the stack.
        Raises:
            IndexError: If the stack is empty.
        """
        if not self.is_empty():
            return self.stack[-1]
        raise IndexError("Stack is empty")

    def is_empty(self):
        """
        Check if the stack is empty.

        Returns:
            bool: True if empty, False otherwise.
        """
        return len(self.stack) == 0

    def size(self):
        """
        Return the number of screens currently in the stack.

        Returns:
            int: The size of the stack.
        """
        return len(self.stack)