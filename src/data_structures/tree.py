class MutationNode:
    def __init__(self, node_id, name, description="No description provided.", required_item_id=None):
        self.node_id = node_id
        # We also set mutation_id so the UI doesn't crash if it looks for either name
        self.mutation_id = node_id 
        self.name = name
        self.description = description # THE FIX
        self.required_item_id = required_item_id
        
        self.is_unlocked = False
        self.children = []

    def can_unlock(self, inventory_manager):
        if self.is_unlocked:
            return False, "Already unlocked!"
        if self.required_item_id is None:
            return True, "Ready to evolve!"
        
        count = inventory_manager.get_item_count(self.required_item_id)
        if count > 0:
            return True, f"Requirement met ({count} owned)"
        return False, f"Missing: {self.required_item_id}"

class MutationTree:
    """
    Tree data structure managing the evolution diagram and unlock constraints.
    """
    def __init__(self, root_node):
        """
        Initializes the Mutation Tree with a base biological form.
        The root node is always unlocked by default.
        """
        self.root = root_node
        self.root.is_unlocked = True

    def find_node(self, current_node, mutation_id):
        """
        Recursively searches the tree to find a specific mutation by ID.
        
        Args:
            current_node (MutationNode): The node to start searching from.
            mutation_id (str): The ID of the mutation to find.
            
        Returns:
            MutationNode: The found node, or None if it doesn't exist.
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
        Returns the parent MutationNode if found, otherwise returns None.
        """
        # If we just started the search, begin at the root
        if current_node is None:
            current_node = self.root
            
        # Check all immediate children of the current node
        for child in current_node.children:
            # If we found the child, the current node IS the parent!
            if child.node_id == child_id:
                return current_node
            
            # Otherwise, keep digging deeper into the tree recursively
            found_parent = self.find_parent(child_id, child)
            if found_parent: 
                return found_parent
                
        # If we checked the whole branch and found nothing
        return None

    def can_unlock(self, mutation_id):
        """
        Validates the logic constraints for unlocking a mutation.
        """
        target_node = self.find_node(self.root, mutation_id)
        
        # CHANGE THIS LINE:
        parent_node = self.find_parent(mutation_id)

        if not target_node or target_node.is_unlocked:
            return False
            
        if parent_node and parent_node.is_unlocked:
            return True
            
        return False

    def unlock_mutation(self, mutation_id):
        """
        Attempts to unlock the specified mutation if constraints are met.
        """
        if self.can_unlock(mutation_id):
            node = self.find_node(self.root, mutation_id)
            node.is_unlocked = True
            return True
        return False
    
    def get_unlocked_nodes(self, current_node=None):
        """Recursively collects a list of all unlocked mutation IDs."""
        if current_node is None:
            current_node = self.root
            
        unlocked = []
        if current_node.is_unlocked:
            unlocked.append(current_node.node_id)
            
        for child in current_node.children:
            unlocked.extend(self.get_unlocked_nodes(child))
            
        return unlocked

    def restore_unlocked_nodes(self, unlocked_ids, current_node=None):
        """Recursively restores the unlocked state from a loaded save file."""
        if current_node is None:
            current_node = self.root
            
        if current_node.node_id in unlocked_ids:
            current_node.is_unlocked = True
            
        for child in current_node.children:
            self.restore_unlocked_nodes(unlocked_ids, child)

