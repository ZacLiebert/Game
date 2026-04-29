class Node:
    """
    Node storing Key-Value pairs for the linked list in the Hash Table.
    Used to handle collisions via the Chaining method.
    """
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None

class HashTable:
    """
    Hash Table data structure.
    Manages the database for mutated monsters and items, ensuring O(1) lookup time.
    """
    def __init__(self, capacity=100):
        """
        Initialize the Hash Table with a default capacity.
        
        Args:
            capacity (int): The size of the hash array.
        """
        self.capacity = capacity
        self.size = 0
        self.table = [None] * capacity

    def _hash(self, key):
        """
        Hash function to convert a string key into a safe array index.
        
        Args:
            key (str): The key to hash (e.g., "Claw_Lvl_1").
        Returns:
            int: The calculated array index.
        """
        hash_value = 0
        for char in str(key):
            # Multiply by prime number 31 to distribute data evenly and reduce collisions
            hash_value = (hash_value * 31 + ord(char)) % self.capacity
        return hash_value

    def insert(self, key, value):
        """
        Insert a part/monster into the database. If the key exists, update its value.
        """
        index = self._hash(key)
        
        # If the slot is empty, create the first Node
        if self.table[index] is None:
            self.table[index] = Node(key, value)
            self.size += 1
            return

        # If data exists (collision), traverse the linked list
        current = self.table[index]
        while current:
            if current.key == key:
                current.value = value  # Update if key matches
                return
            if current.next is None:
                break
            current = current.next
            
        # Append to the end of the linked list
        current.next = Node(key, value)
        self.size += 1

    def get(self, key):
        """
        Retrieve data based on ID or Name.
        
        Returns:
            The corresponding value, or None if not found.
        """
        index = self._hash(key)
        current = self.table[index]
        
        while current:
            if current.key == key:
                return current.value
            current = current.next
        return None