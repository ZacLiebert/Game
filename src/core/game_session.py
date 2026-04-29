from src.core.database import GameDatabase
from src.core.inventory_manager import InventoryManager

class GameSession:
    """
    Holds all global persistent data: Player Party, Inventory, and Mutations.
    Everything is now dynamically loaded from JSON databases!
    """
    def __init__(self):
        self.db = GameDatabase()
        self.inventory = InventoryManager()
        
        # 1. Load Party from JSON via Hash Table
        self.party = [
            self.db.create_entity("p1", is_enemy=False),
            self.db.create_entity("p2", is_enemy=False),
            self.db.create_entity("p3", is_enemy=False)
        ]
        
        # 2. Give starting items
        potion = self.db.get_item("pot_hp_small")
        if potion:
            self.inventory.add_item(potion)
            self.inventory.add_item(self.db.get_item("pot_hp_small"))

        # 3. Load Mutation Tree directly from JSON!
        self.mutation_tree = self.db.load_mutation_tree()
        
        if not self.mutation_tree:
            print("CRITICAL: data/mutations.json not found or tree failed to build!")

    def export_save_data(self):
        """Packages the current global state into a dictionary for encryption."""
        return {
            "party": [
                {
                    "id": p.entity_id, 
                    "hp": p.current_hp,
                    "attack": p.attack,
                    "defense": p.defense,
                    "speed": p.speed
                } for p in self.party
            ],
            # Extract just the string IDs from the Item objects
            "inventory": [item.item_id for item in self.inventory.items],
            "mutations": self.mutation_tree.get_unlocked_nodes()
        }

    def import_save_data(self, save_dict):
        """Restores global state from a decrypted dictionary."""
        if not save_dict: 
            return
            
        # 1. Restore Party Stats
        for i, p_data in enumerate(save_dict.get("party", [])):
            if i < len(self.party):
                self.party[i].current_hp = p_data["hp"]
                self.party[i].attack = p_data["attack"]
                self.party[i].defense = p_data["defense"]
                self.party[i].speed = p_data["speed"]
                
        # 2. Restore Inventory via Hash Table Lookups
        self.inventory.items = [] 
        for item_id in save_dict.get("inventory", []):
            item_obj = self.db.get_item(item_id)
            if item_obj:
                self.inventory.add_item(item_obj)
                
        # 3. Restore Mutation Tree
        if self.mutation_tree:
            self.mutation_tree.restore_unlocked_nodes(save_dict.get("mutations", []))