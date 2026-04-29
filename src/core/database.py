import json
import os
from src.data_structures.hash_table import HashTable
from src.entities.item import Item
from src.entities.entity import Entity
from src.data_structures.tree import MutationNode, MutationTree

class GameDatabase:
    def __init__(self):
        self.item_db = HashTable(capacity=200)
        self.enemy_db = HashTable(capacity=100)
        self.ally_db = HashTable(capacity=50) # New table for heroes
        self._load_from_json()

    def get_map_data(self, map_id):
        """Loads and returns specific map data from the JSON database."""
        # CHANGE THIS LINE:
        path = "assets/maps.json" 
        
        if os.path.exists(path):
            with open(path, "r") as f:
                maps = json.load(f)
                return maps.get(map_id)
        return None

    def _load_from_json(self):
        # 1. Load Items
        self._load_file("data/items.json", self.item_db, "item")
        # 2. Load Enemies
        self._load_file("data/enemies.json", self.enemy_db, "raw")
        # 3. Load Allies
        self._load_file("data/allies.json", self.ally_db, "raw")

    def _load_file(self, path, table, mode):
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                for entry in data:
                    if mode == "item":
                        obj = Item(
                            entry["id"], entry["name"], entry["description"],
                            entry.get("type", "part"), entry.get("heal_amount", 0),
                            entry.get("stats_modifier", {})
                        )
                        table.insert(entry["id"], obj)
                    else:
                        # Store raw dict for entities
                        table.insert(entry["id"], entry)

    def get_item(self, item_id):
        return self.item_db.get(item_id)

    def create_entity(self, entity_id, is_enemy=True):
        data = self.enemy_db.get(entity_id) if is_enemy else self.ally_db.get(entity_id)
        
        if data:
            return Entity(
                entity_id=data["id"],
                name=data["name"],
                hp=data["hp"],
                attack=data["attack"],
                defense=data["defense"],
                speed=data["speed"],
                sprite_name=data.get("sprite", "placeholder.png"), # NEW
                loot_id=data.get("loot_id")
            )
        return None

    def load_mutation_tree(self):
        """
        Reads mutations.json and builds a real N-ary tree.
        """
        path = "data/mutations.json"
        if not os.path.exists(path):
            return None

        with open(path, "r") as f:
            data = json.load(f)

        # 1. Create all Node objects first and store them in a temp dict
        nodes = {}
        root = None
        
        for m in data:
            new_node = MutationNode(
                node_id=m["id"],
                name=m["name"],
                description=m["description"],
                required_item_id=m["req_item"]
            )
            nodes[m["id"]] = new_node
            if m["parent"] is None:
                root = new_node

        # 2. Connect children to parents
        for m in data:
            parent_id = m["parent"]
            if parent_id and parent_id in nodes:
                # Add the current node as a child of its parent
                nodes[parent_id].children.append(nodes[m["id"]])

        return MutationTree(root) if root else None