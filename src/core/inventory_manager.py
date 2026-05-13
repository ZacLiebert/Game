"""Inventory storage and item search helpers."""

from src.data_structures.hash_table import HashTable
from src.data_structures.sort_search import InventoryAlgorithms
from src.data_structures.string_matching import StringMatcher


class InventoryManager:
    """Handles the player's collection of mutated parts and items."""

    def __init__(self):
        """Set up initial state."""
        self._item_counts = HashTable(capacity=32)
        self._unique_items = HashTable(capacity=32)
        self._unique_order = []
        self._total_count = 0

    @property
    def items(self):
        """Return inventory as an expanded item list."""
        expanded_items = []

        for item in self._unique_order:
            count = self.get_item_count(item.item_id)

            for _ in range(count):
                expanded_items.append(item)

        return expanded_items

    @items.setter
    def items(self, item_list):
        """Return inventory as an expanded item list."""
        self.clear()

        if not item_list:
            return

        for item in item_list:
            self.add_item(item)

    def clear(self):
        """Remove all items from the inventory."""
        self._item_counts = HashTable(capacity=32)
        self._unique_items = HashTable(capacity=32)
        self._unique_order = []
        self._total_count = 0

    def _remove_from_unique_order(self, item_id):
        """Remove an item from the display-order list."""
        for index, item in enumerate(self._unique_order):
            if item.item_id == item_id:
                self._unique_order.pop(index)
                return True

        return False

    def _remove_stack(self, item_id):
        """Remove one complete item stack."""
        self._item_counts.delete(item_id)
        self._unique_items.delete(item_id)
        self._remove_from_unique_order(item_id)

    def add_item(self, item_obj):
        """Add one item to the inventory."""
        self.add_item_amount(item_obj, 1)

    def add_item_amount(self, item_obj, amount):
        """Add several copies of one item."""
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            return

        if not item_obj or amount <= 0:
            return

        item_id = getattr(item_obj, "item_id", None)

        if not item_id:
            return

        old_count = self._item_counts.get_or_default(item_id, 0)

        if old_count == 0:
            self._unique_items.insert(item_id, item_obj)
            self._unique_order.append(item_obj)

        self._item_counts.insert(item_id, old_count + amount)
        self._total_count += amount

    def remove_item(self, item_id):
        """Remove a whole item stack by ID."""
        current_count = self.get_item_count(item_id)

        if current_count <= 0:
            return False

        self._total_count -= current_count
        self._remove_stack(item_id)
        return True

    def remove_item_by_id(self, item_id):
        """Remove one copy of an item by ID."""
        return self.remove_item_count(item_id, 1)

    def remove_item_count(self, item_id, count):
        """Remove a chosen number of item copies."""
        try:
            count = int(count)
        except (TypeError, ValueError):
            return False

        if count <= 0:
            return True

        if not item_id:
            return False

        current_count = self.get_item_count(item_id)

        if current_count < count:
            return False

        new_count = current_count - count
        self._total_count -= count

        if new_count == 0:
            self._remove_stack(item_id)
        else:
            self._item_counts.insert(item_id, new_count)

        return True

    def get_item_count(self, item_id):
        """Return the item count."""
        if not item_id:
            return 0

        return self._item_counts.get_or_default(item_id, 0)

    def get_item(self, item_id):
        """Return the stored item object for an ID."""
        if not item_id:
            return None

        return self._unique_items.get_or_default(item_id)

    def get_unique_items(self):
        """Return one item object per inventory stack."""
        return list(self._unique_order)

    def get_total_item_count(self):
        """Return the total item count."""
        return self._total_count

    def export_counts(self):
        """Return item counts for the save file."""
        result = []

        for item in self._unique_order:
            count = self.get_item_count(item.item_id)

            if count > 0:
                result.append({
                    "id": item.item_id,
                    "count": count
                })

        return result

    def sort_by_name(self):
        """Sort the visible inventory list by name."""
        self._unique_order = InventoryAlgorithms.quick_sort(
            self._unique_order,
            "name"
        )

    def search_items(self, query):
        """Find items whose name or description matches the query."""
        unique_items = self.get_unique_items()

        if not query:
            return unique_items

        pattern, lps = StringMatcher.prepare_pattern(query)
        results = []

        for item in unique_items:
            if (
                StringMatcher.kmp_search_prepared(item.name, pattern, lps)
                or StringMatcher.kmp_search_prepared(item.description, pattern, lps)
            ):
                results.append(item)

        return results
