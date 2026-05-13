"""Custom hash table used for fast lookups."""

class Node:
    """Node used in the custom hash-table collision chain."""

    def __init__(self, key, value, next_node=None):
        """Set up initial state."""
        self.key = key
        self.value = value
        self.next = next_node


class HashTable:
    """Custom hash table using separate chaining and resizing."""

    MIN_CAPACITY = 8

    def __init__(self, capacity=100, max_load_factor=0.75):
        """Set up initial state."""
        self.capacity = max(self.MIN_CAPACITY, int(capacity))
        self.max_load_factor = max(0.1, float(max_load_factor))
        self.size = 0
        self.table = [None] * self.capacity

    def __len__(self):
        """Return the number of stored entries."""
        return self.size

    def _hash_with_capacity(self, key, capacity):
        """Map a key to a bucket index for a capacity."""
        hash_value = 0

        for char in str(key):
            hash_value = (hash_value * 31 + ord(char)) % capacity

        return hash_value

    def _hash(self, key):
        """Map a key to a bucket index."""
        return self._hash_with_capacity(key, self.capacity)

    def _resize(self, new_capacity):
        """Rebuild the table with more buckets."""
        old_table = self.table
        self.capacity = max(self.MIN_CAPACITY, int(new_capacity))
        self.table = [None] * self.capacity

        for head in old_table:
            current = head

            while current:
                next_node = current.next
                index = self._hash(current.key)
                current.next = self.table[index]
                self.table[index] = current
                current = next_node

    def _should_resize_for_insert(self):
        """Return whether another insert should grow the table."""
        return (self.size + 1) / self.capacity > self.max_load_factor

    def insert(self, key, value):
        """Add or update a key-value pair."""
        index = self._hash(key)
        current = self.table[index]

        while current:
            if current.key == key:
                current.value = value
                return

            current = current.next

        if self._should_resize_for_insert():
            self._resize(self.capacity * 2)
            index = self._hash(key)

        self.table[index] = Node(key, value, self.table[index])
        self.size += 1

    def _find_node(self, key):
        """Find the node for a key in its bucket chain."""
        index = self._hash(key)
        current = self.table[index]

        while current:
            if current.key == key:
                return current

            current = current.next

        return None

    def get(self, key):
        """Return the value for a key, or None."""
        node = self._find_node(key)
        return node.value if node is not None else None

    def get_or_default(self, key, default=None):
        """Return the value for a key, or a default value."""
        node = self._find_node(key)
        return node.value if node is not None else default

    def get_with_status(self, key):
        """Return whether the key exists and its value."""
        node = self._find_node(key)

        if node is None:
            return False, None

        return True, node.value

    def contains(self, key):
        """Return whether the key exists."""
        return self._find_node(key) is not None

    def delete(self, key):
        """Remove a key-value pair if it exists."""
        index = self._hash(key)
        current = self.table[index]
        previous = None

        while current:
            if current.key == key:
                if previous is None:
                    self.table[index] = current.next
                else:
                    previous.next = current.next

                self.size -= 1
                return True

            previous = current
            current = current.next

        return False

    def items(self):
        """Yield all stored key-value pairs."""
        for head in self.table:
            current = head

            while current:
                yield current.key, current.value
                current = current.next
