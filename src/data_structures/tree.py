"""Custom mutation tree data structure."""

from src.data_structures.hash_table import HashTable


class MutationNode:
    """Node in the mutation tree."""

    def __init__(
        self,
        node_id,
        name,
        description="No description provided.",
        required_item_id=None,
        required_count=1,
        stats_modifier=None,
        unlock_skill=None
    ):
        """Set up initial state."""
        self.node_id = node_id
        self.mutation_id = node_id
        self.name = name
        self.description = description
        self.required_item_id = required_item_id
        self.required_count = required_count
        self.stats_modifier = stats_modifier if stats_modifier else {}
        self.unlock_skill = unlock_skill
        self.is_unlocked = False
        self.children = []

    def add_child(self, child_node):
        """Attach a child mutation node."""
        self.children.append(child_node)

    def can_unlock(self, inventory_manager):
        """Return whether this mutation can be unlocked."""
        if self.is_unlocked:
            return False, "Already unlocked."

        if self.required_item_id is None:
            return True, "Ready to evolve."

        owned = inventory_manager.get_item_count(self.required_item_id)
        needed = self.required_count

        if owned >= needed:
            return True, f"Requirement met. Owned: {owned}/{needed}"

        return False, f"Need {needed} item(s). Owned: {owned}/{needed}"


class MutationTree:
    """Custom tree for mutation unlock paths."""

    def __init__(self, root_node):
        """Set up initial state."""
        if root_node is None:
            raise ValueError("MutationTree requires a root node.")

        self.root = root_node
        validation_errors = self.validate_structure()

        if validation_errors:
            raise ValueError(
                "Invalid mutation tree structure:\n- "
                + "\n- ".join(validation_errors)
            )

        self.root.is_unlocked = True
        self.node_index = HashTable(capacity=32)
        self.parent_index = HashTable(capacity=32)
        self._rebuild_indexes()

    def validate_structure(self):
        """Validate parent links and tree structure."""
        errors = []
        visiting = HashTable(capacity=32)
        visited = HashTable(capacity=32)
        stack = [(self.root, None, "enter")]

        while stack:
            node, parent, state = stack.pop()

            if node is None:
                errors.append("None node found in mutation tree.")
                continue

            node_id = getattr(node, "node_id", None)

            if not node_id:
                errors.append("Mutation node has empty id.")
                continue

            if state == "exit":
                visiting.delete(node_id)
                visited.insert(node_id, True)
                continue

            if visiting.contains(node_id):
                errors.append(f"Cycle detected at mutation id '{node_id}'.")
                continue

            if visited.contains(node_id):
                errors.append(f"Duplicate/shared mutation id '{node_id}' found.")
                continue

            visiting.insert(node_id, True)
            stack.append((node, parent, "exit"))

            for child in reversed(node.children):
                if child is node:
                    errors.append(f"Mutation '{node_id}' cannot be its own child.")
                    continue

                stack.append((child, node, "enter"))

        return errors

    def _rebuild_indexes(self):
        """Refresh lookup tables for the tree."""
        self.node_index = HashTable(capacity=32)
        self.parent_index = HashTable(capacity=32)

        stack = [(self.root, None)]

        while stack:
            node, parent = stack.pop()
            self.node_index.insert(node.node_id, node)
            self.parent_index.insert(node.node_id, parent)

            for child in reversed(node.children):
                stack.append((child, node))

    def find_node(self, current_node_or_id, mutation_id=None):
        """Return a mutation node by ID."""
        lookup_id = mutation_id if mutation_id is not None else current_node_or_id
        return self.node_index.get(lookup_id)

    def find_node_dfs(self, mutation_id):
        """Find a mutation node using DFS."""
        stack = [self.root]

        while stack:
            node = stack.pop()

            if node.node_id == mutation_id:
                return node

            for child in reversed(node.children):
                stack.append(child)

        return None

    def add_mutation(self, parent_id, new_node):
        """Add a mutation node under its parent."""
        parent_node = self.find_node(parent_id)

        if not parent_node or new_node is None:
            return False

        if not getattr(new_node, "node_id", None):
            return False

        if parent_id == new_node.node_id or self.node_index.contains(new_node.node_id):
            return False

        parent_node.add_child(new_node)

        validation_errors = self.validate_structure()
        if validation_errors:
            parent_node.children.pop()
            return False

        self.node_index.insert(new_node.node_id, new_node)
        self.parent_index.insert(new_node.node_id, parent_node)
        return True

    def find_parent(self, child_id, current_node=None):
        """Return the parent of a mutation node."""
        return self.parent_index.get(child_id)

    def find_parent_dfs(self, child_id):
        """Find a parent node using DFS."""
        stack = [(self.root, None)]

        while stack:
            node, parent = stack.pop()

            if node.node_id == child_id:
                return parent

            for child in reversed(node.children):
                stack.append((child, node))

        return None

    def can_unlock(self, mutation_id):
        """Return whether a mutation can be unlocked."""
        target_node = self.find_node(mutation_id)

        if not target_node or target_node.is_unlocked:
            return False

        parent_node = self.find_parent(mutation_id)
        return parent_node is not None and parent_node.is_unlocked

    def unlock_mutation(self, mutation_id):
        """Unlock a mutation if all requirements are met."""
        node = self.find_node(mutation_id)

        if node and self.can_unlock(mutation_id):
            node.is_unlocked = True
            return True

        return False

    def get_unlocked_nodes(self, current_node=None):
        """Return all unlocked mutation nodes."""
        start_node = current_node if current_node is not None else self.root
        unlocked = []
        stack = [start_node]

        while stack:
            node = stack.pop()

            if node.is_unlocked:
                unlocked.append(node.node_id)

            for child in reversed(node.children):
                stack.append(child)

        return unlocked

    # Safe save restore helpers

    def reset_unlocks(self, current_node=None):
        """Lock every non-root mutation."""
        start_node = current_node if current_node is not None else self.root
        stack = [start_node]

        while stack:
            node = stack.pop()
            node.is_unlocked = node is self.root

            for child in node.children:
                stack.append(child)

    def _lock_subtree(self, current_node):
        """Lock a mutation and all of its children."""
        stack = [current_node]

        while stack:
            node = stack.pop()
            node.is_unlocked = False

            for child in node.children:
                stack.append(child)

    def _restore_valid_unlock_chain(self, current_node, unlocked_ids):
        """Restore one saved mutation only if its parent chain is valid."""
        for child in current_node.children:
            if child.node_id in unlocked_ids and current_node.is_unlocked:
                child.is_unlocked = True
                self._restore_valid_unlock_chain(child, unlocked_ids)
            else:
                self._lock_subtree(child)

    def restore_unlocked_nodes(self, unlocked_ids, current_node=None):
        """Restore unlocked mutations from save data."""
        if current_node is not None:
            if current_node.node_id in unlocked_ids:
                current_node.is_unlocked = True

            for child in current_node.children:
                self.restore_unlocked_nodes(unlocked_ids, child)

            return

        if not isinstance(unlocked_ids, (list, set, tuple)):
            unlocked_ids = []

        unlocked_ids = {
            str(node_id) for node_id in unlocked_ids
            if isinstance(node_id, str)
        }

        self.reset_unlocks()
        self.root.is_unlocked = True
        self._restore_valid_unlock_chain(self.root, unlocked_ids)
