"""Custom sort and search algorithms."""


class InventoryAlgorithms:
    """Custom sorting algorithms for inventory stacks and render-order lists."""

    INSERTION_SORT_THRESHOLD = 12

    @staticmethod
    def quick_sort(arr, attribute):
        """Sort inventory items using custom quick sort."""
        result = list(arr)

        if len(result) <= 1:
            return result

        InventoryAlgorithms._quick_sort_3way(result, 0, len(result) - 1, attribute)
        return result

    @staticmethod
    def _key(item, attribute):
        """Return the comparable value for sorting."""
        value = getattr(item, attribute)

        if isinstance(value, str):
            return value.lower()

        return value

    @staticmethod
    def _median_of_three(values, low, high, attribute):
        """Choose a stable pivot index for quick sort."""
        mid = (low + high) // 2
        a = InventoryAlgorithms._key(values[low], attribute)
        b = InventoryAlgorithms._key(values[mid], attribute)
        c = InventoryAlgorithms._key(values[high], attribute)

        if a <= b <= c or c <= b <= a:
            return b
        if b <= a <= c or c <= a <= b:
            return a
        return c

    @staticmethod
    def _insertion_sort(values, low, high, attribute):
        """Sort a small range using insertion sort."""
        for i in range(low + 1, high + 1):
            current = values[i]
            current_key = InventoryAlgorithms._key(current, attribute)
            j = i - 1

            while j >= low and InventoryAlgorithms._key(values[j], attribute) > current_key:
                values[j + 1] = values[j]
                j -= 1

            values[j + 1] = current

    @staticmethod
    def _quick_sort_3way(values, low, high, attribute):
        """Sort a range using three-way quick sort."""
        if high - low + 1 <= InventoryAlgorithms.INSERTION_SORT_THRESHOLD:
            InventoryAlgorithms._insertion_sort(values, low, high, attribute)
            return

        pivot_key = InventoryAlgorithms._median_of_three(values, low, high, attribute)
        lt = low
        i = low
        gt = high

        while i <= gt:
            current_key = InventoryAlgorithms._key(values[i], attribute)

            if current_key < pivot_key:
                values[lt], values[i] = values[i], values[lt]
                lt += 1
                i += 1
            elif current_key > pivot_key:
                values[i], values[gt] = values[gt], values[i]
                gt -= 1
            else:
                i += 1

        if low < lt - 1:
            InventoryAlgorithms._quick_sort_3way(values, low, lt - 1, attribute)

        if gt + 1 < high:
            InventoryAlgorithms._quick_sort_3way(values, gt + 1, high, attribute)

    @staticmethod
    def quick_sort_by_key(arr, key_func):
        """Sort objects using a custom key function."""
        result = list(arr)

        if len(result) <= 1:
            return result

        InventoryAlgorithms._quick_sort_3way_by_key(
            result,
            0,
            len(result) - 1,
            key_func
        )
        return result

    @staticmethod
    def _median_of_three_by_key(values, low, high, key_func):
        """Choose a pivot index using a key function."""
        mid = (low + high) // 2
        a = key_func(values[low])
        b = key_func(values[mid])
        c = key_func(values[high])

        if a <= b <= c or c <= b <= a:
            return b
        if b <= a <= c or c <= a <= b:
            return a
        return c

    @staticmethod
    def _insertion_sort_by_key(values, low, high, key_func):
        """Insertion-sort a small range using a key function."""
        for i in range(low + 1, high + 1):
            current = values[i]
            current_key = key_func(current)
            j = i - 1

            while j >= low and key_func(values[j]) > current_key:
                values[j + 1] = values[j]
                j -= 1

            values[j + 1] = current

    @staticmethod
    def _quick_sort_3way_by_key(values, low, high, key_func):
        """Three-way quick-sort a range using a key function."""
        if high - low + 1 <= InventoryAlgorithms.INSERTION_SORT_THRESHOLD:
            InventoryAlgorithms._insertion_sort_by_key(values, low, high, key_func)
            return

        pivot_key = InventoryAlgorithms._median_of_three_by_key(
            values,
            low,
            high,
            key_func
        )
        lt = low
        i = low
        gt = high

        while i <= gt:
            current_key = key_func(values[i])

            if current_key < pivot_key:
                values[lt], values[i] = values[i], values[lt]
                lt += 1
                i += 1
            elif current_key > pivot_key:
                values[i], values[gt] = values[gt], values[i]
                gt -= 1
            else:
                i += 1

        if low < lt - 1:
            InventoryAlgorithms._quick_sort_3way_by_key(values, low, lt - 1, key_func)

        if gt + 1 < high:
            InventoryAlgorithms._quick_sort_3way_by_key(values, gt + 1, high, key_func)
