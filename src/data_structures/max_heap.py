class MaxHeap:
    """
    Max Heap data structure (Priority Queue).
    Used to coordinate turn order in multi-entity combat based on the Speed stat.
    """
    def __init__(self):
        """Initialize an empty Max Heap."""
        self.heap = []

    def _parent(self, index):
        return (index - 1) // 2

    def _left_child(self, index):
        return 2 * index + 1

    def _right_child(self, index):
        return 2 * index + 2

    def _swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]

    def insert(self, entity):
        """
        Insert an entity (character/monster) into the heap.
        
        Args:
            entity: An object that MUST have a 'speed' attribute.
        """
        self.heap.append(entity)
        self._heapify_up(len(self.heap) - 1)

    def extract_max(self):
        """
        Extract and return the entity with the highest speed.
        
        Returns:
            The entity object with the maximum speed, or None if heap is empty.
        """
        if not self.heap:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        
        # Save the entity with max speed
        max_entity = self.heap[0]
        # Move the last element to the root and heapify down
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)
        
        return max_entity

    def _heapify_up(self, index):
        """Maintain the max-heap property by bubbling up."""
        parent_idx = self._parent(index)
        # Compare based on the 'speed' attribute
        if index > 0 and self.heap[index].speed > self.heap[parent_idx].speed:
            self._swap(index, parent_idx)
            self._heapify_up(parent_idx)

    def _heapify_down(self, index):
        """Maintain the max-heap property by bubbling down."""
        largest = index
        left = self._left_child(index)
        right = self._right_child(index)

        # Check if left child exists and is greater than root
        if left < len(self.heap) and self.heap[left].speed > self.heap[largest].speed:
            largest = left

        # Check if right child exists and is greater than largest so far
        if right < len(self.heap) and self.heap[right].speed > self.heap[largest].speed:
            largest = right

        # If largest is not root, swap and continue heapifying
        if largest != index:
            self._swap(index, largest)
            self._heapify_down(largest)
            
    def is_empty(self):
        """
        Check if the heap is empty.
        
        Returns:
            bool: True if empty, False otherwise.
        """
        return len(self.heap) == 0