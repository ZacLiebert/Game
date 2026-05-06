class MutationNode:
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
        self.node_id = node_id
        self.mutation_id = node_id
        self.name = name
        self.description = description

        self.required_item_id = required_item_id
        self.required_count = required_count

        self.stats_modifier = stats_modifier if stats_modifier else {}

        # Skill unlocked by this mutation.
        # Example:
        # echolocation -> sonic_pulse
        # venom_fang -> venom_bite
        # swift_legs -> beast_focus
        self.unlock_skill = unlock_skill

        self.is_unlocked = False
        self.children = []

    def add_child(self, child_node):
        """
        Adds a child mutation node to this node.
        """
        self.children.append(child_node)

    def can_unlock(self, inventory_manager):
        """
        Checks whether this mutation can be unlocked based on inventory quantity.
        """
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
    """
    Tree data structure managing the evolution diagram and unlock constraints.
    """

    def __init__(self, root_node):
        self.root = root_node
        self.root.is_unlocked = True

    def find_node(self, current_node, mutation_id):
        """
        Recursively searches the tree to find a specific mutation by ID.
        """
        if current_node.mutation_id == mutation_id:
            return current_node

        for child in current_node.children:
            result = self.find_node(child, mutation_id)

            if result:
                return result

        return None

    def add_mutation(self, parent_id, new_node):
        """
        Inserts a new mutation into the tree under a specific parent node.
        """
        parent_node = self.find_node(self.root, parent_id)

        if parent_node:
            parent_node.add_child(new_node)
            return True

        return False

    def find_parent(self, child_id, current_node=None):
        """
        Recursively searches the N-ary tree to find the parent of a specific node.
        """
        if current_node is None:
            current_node = self.root

        for child in current_node.children:
            if child.node_id == child_id:
                return current_node

            found_parent = self.find_parent(child_id, child)

            if found_parent:
                return found_parent

        return None

    def can_unlock(self, mutation_id):
        """
        Validates tree constraints only.
        Inventory cost is checked inside MutationNode.can_unlock().
        """
        target_node = self.find_node(self.root, mutation_id)
        parent_node = self.find_parent(mutation_id)

        if not target_node:
            return False

        if target_node.is_unlocked:
            return False

        if parent_node and parent_node.is_unlocked:
            return True

        return False

    def unlock_mutation(self, mutation_id):
        """
        Attempts to unlock the specified mutation if tree constraints are met.
        """
        if self.can_unlock(mutation_id):
            node = self.find_node(self.root, mutation_id)
            node.is_unlocked = True
            return True

        return False

    def get_unlocked_nodes(self, current_node=None):
        """
        Recursively collects a list of all unlocked mutation IDs.
        """
        if current_node is None:
            current_node = self.root

        unlocked = []

        if current_node.is_unlocked:
            unlocked.append(current_node.node_id)

        for child in current_node.children:
            unlocked.extend(self.get_unlocked_nodes(child))

        return unlocked

    # ============================================================
    # SAFE SAVE RESTORE HELPERS
    # ============================================================

    def reset_unlocks(self, current_node=None):
        """
        Resets the whole mutation tree before loading a save.

        Important:
        - Root stays unlocked.
        - Every other node becomes locked.
        - This prevents old unlocked mutations from remaining active after
          loading an older save.
        """
        if current_node is None:
            current_node = self.root

        current_node.is_unlocked = current_node is self.root

        for child in current_node.children:
            self.reset_unlocks(child)

    def _lock_subtree(self, current_node):
        """
        Locks a node and all of its children.
        """
        current_node.is_unlocked = False

        for child in current_node.children:
            self._lock_subtree(child)

    def _restore_valid_unlock_chain(self, current_node, unlocked_ids):
        """
        Restores unlocked nodes only when their parent is already unlocked.

        This prevents edited save files from unlocking deep mutations directly
        without unlocking their required parent mutations first.
        """
        for child in current_node.children:
            if child.node_id in unlocked_ids and current_node.is_unlocked:
                child.is_unlocked = True
                self._restore_valid_unlock_chain(child, unlocked_ids)
            else:
                self._lock_subtree(child)

    def restore_unlocked_nodes(self, unlocked_ids, current_node=None):
        """
        Restores the unlocked state from a loaded save file.

        Backward compatible:
        - The current_node parameter is kept so old calls do not crash.
        - Normal usage should call restore_unlocked_nodes(unlocked_ids).

        Safer behavior:
        - Reset tree first.
        - Keep root unlocked.
        - Only unlock valid parent-child chains.
        """
        if current_node is not None:
            # Legacy recursive behavior support.
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