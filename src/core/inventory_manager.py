from src.data_structures.sort_search import InventoryAlgorithms
from src.data_structures.string_matching import StringMatcher

class InventoryManager:
    """
    Handles the player's collection of mutated parts and items.
    Implements sorting and searching requirements using Quick Sort and KMP.
    """
    def __init__(self):
        """Initializes an empty inventory list."""
        self.items = []

    def add_item(self, item_obj):
        """
        Adds an item to the inventory.
        
        Args:
            item_obj (Item): The Item object to add.
        """
        self.items.append(item_obj)

    def remove_item(self, item_id):
        """Removes an item from the inventory by its ID."""
        self.items = [item for item in self.items if item.item_id != item_id]

    def sort_by_name(self):
        """
        Sorts the inventory alphabetically by item name.
        Uses the Quick Sort algorithm implemented in DSA requirements.
        """
        self.items = InventoryAlgorithms.quick_sort(self.items, "name")

    def search_items(self, query):
        """
        Filters the inventory for items matching a search string.
        Uses the KMP (Knuth-Morris-Pratt) algorithm for efficient matching.
        
        Args:
            query (str): The string to search for.
            
        Returns:
            list: A list of items that match the query.
        """
        if not query:
            return self.items
            
        results = []
        for item in self.items:
            # Check if the query exists in the item's name or description
            if StringMatcher.kmp_search(item.name, query) or \
               StringMatcher.kmp_search(item.description, query):
                results.append(item)
        
        return results


    def get_item_count(self, item_id):
        """Returns the number of items with a specific ID in the inventory."""
        count = 0
        for item in self.items:
            if item.item_id == item_id:
                count += 1
        return count

    def remove_item_by_id(self, item_id):
        """Removes one instance of an item ID (consumes it for mutation)."""
        for i in range(len(self.items)):
            if self.items[i].item_id == item_id:
                self.items.pop(i)
                return True
        return False
