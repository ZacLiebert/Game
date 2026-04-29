class InventoryAlgorithms:
    """
    A collection of algorithms to manage the player's inventory.
    Implements Quick Sort for organization and Binary Search for fast retrieval.
    """

    @staticmethod
    def quick_sort(arr, attribute):
        """
        Sorts a list of item objects using the Quick Sort algorithm.
        
        Args:
            arr (list): The list of items to sort.
            attribute (str): The attribute of the item to sort by (e.g., 'name', 'rarity').
            
        Returns:
            list: A new sorted list.
        """
        if len(arr) <= 1:
            return arr
            
        # Choosing the middle element as the pivot
        pivot = arr[len(arr) // 2]
        pivot_val = getattr(pivot, attribute)
        
        left = [x for x in arr if getattr(x, attribute) < pivot_val]
        middle = [x for x in arr if getattr(x, attribute) == pivot_val]
        right = [x for x in arr if getattr(x, attribute) > pivot_val]
        
        return InventoryAlgorithms.quick_sort(left, attribute) + middle + InventoryAlgorithms.quick_sort(right, attribute)

    @staticmethod
    def binary_search(sorted_arr, target_val, attribute):
        """
        Searches for a specific item in a SORTED list using Binary Search.
        
        Args:
            sorted_arr (list): The sorted list of items.
            target_val (any): The value we are looking for.
            attribute (str): The attribute we are matching against (e.g., 'name').
            
        Returns:
            object: The found item object, or None if not found.
        """
        low = 0
        high = len(sorted_arr) - 1

        while low <= high:
            mid = (low + high) // 2
            mid_val = getattr(sorted_arr[mid], attribute)

            if mid_val == target_val:
                return sorted_arr[mid]  # Item found
            elif mid_val < target_val:
                low = mid + 1           # Target is in the upper half
            else:
                high = mid - 1          # Target is in the lower half

        return None  # Item not found