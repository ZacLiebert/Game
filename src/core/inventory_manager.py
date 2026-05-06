from src.data_structures.sort_search import InventoryAlgorithms
from src.data_structures.string_matching import StringMatcher


class InventoryManager:
    """
    Handles the player's collection of mutated parts and items.

    Internally, inventory still stores repeated Item objects:
    - Rabbit Foot
    - Rabbit Foot
    - Rabbit Foot

    But screens can use get_unique_items() to display:
    - Rabbit Foot x3
    """

    def __init__(self):
        self.items = []

    def add_item(self, item_obj):
        """
        Adds one item object to the inventory.
        """
        if item_obj:
            self.items.append(item_obj)

    def add_item_amount(self, item_obj, amount):
        """
        Adds multiple copies of the same item.
        """
        for _ in range(amount):
            self.add_item(item_obj)

    def remove_item(self, item_id):
        """
        Removes all items with the matching item_id.
        """
        self.items = [
            item for item in self.items
            if item.item_id != item_id
        ]

    def remove_item_by_id(self, item_id):
        """
        Removes one instance of an item ID.
        Useful for using one potion.
        """
        for i in range(len(self.items)):
            if self.items[i].item_id == item_id:
                self.items.pop(i)
                return True

        return False

    def remove_item_count(self, item_id, count):
        """
        Removes a specific number of items.

        Returns:
            True if enough items were removed.
            False if the inventory did not have enough items.
        """
        if self.get_item_count(item_id) < count:
            return False

        removed = 0
        new_items = []

        for item in self.items:
            if item.item_id == item_id and removed < count:
                removed += 1
            else:
                new_items.append(item)

        self.items = new_items
        return True

    def get_item_count(self, item_id):
        """
        Returns the number of items with a specific ID.
        """
        count = 0

        for item in self.items:
            if item.item_id == item_id:
                count += 1

        return count

    def get_unique_items(self):
        """
        Returns one representative Item object for each item_id.

        Example:
            [Rabbit Foot, Rabbit Foot, Potion]
        becomes:
            [Rabbit Foot, Potion]
        """
        seen = set()
        unique_items = []

        for item in self.items:
            if item.item_id not in seen:
                seen.add(item.item_id)
                unique_items.append(item)

        return unique_items

    def get_total_item_count(self):
        """
        Returns total item objects, including duplicates.
        """
        return len(self.items)

    def sort_by_name(self):
        """
        Sorts the inventory alphabetically by item name.
        """
        self.items = InventoryAlgorithms.quick_sort(self.items, "name")

    def search_items(self, query):
        """
        Searches unique item list using KMP.

        Returns unique item objects, not duplicate copies.
        """
        unique_items = self.get_unique_items()

        if not query:
            return unique_items

        results = []

        for item in unique_items:
            if StringMatcher.kmp_search(item.name, query) or \
               StringMatcher.kmp_search(item.description, query):
                results.append(item)

        return results