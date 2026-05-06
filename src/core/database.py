import json

from src.data_structures.hash_table import HashTable
from src.entities.item import Item
from src.entities.entity import Entity
from src.data_structures.tree import MutationNode, MutationTree
from src.paths import (
    ALLIES_DATA_FILE,
    ENEMIES_DATA_FILE,
    ITEMS_DATA_FILE,
    LEGACY_MAP_DATA_FILE,
    MAP_DATA_FILE,
    MUTATIONS_DATA_FILE,
)


class GameDatabase:
    def __init__(self):
        self.item_db = HashTable(capacity=200)
        self.enemy_db = HashTable(capacity=100)
        self.ally_db = HashTable(capacity=50)

        self._load_from_json()

    def get_map_data(self, map_id):
        for path in (MAP_DATA_FILE, LEGACY_MAP_DATA_FILE):
            if path.exists():
                with path.open("r", encoding="utf-8") as f:
                    maps = json.load(f)
                    return maps.get(map_id)

        return None

    def _load_from_json(self):
        self._load_file(ITEMS_DATA_FILE, self.item_db, "item")
        self._load_file(ENEMIES_DATA_FILE, self.enemy_db, "raw")
        self._load_file(ALLIES_DATA_FILE, self.ally_db, "raw")

    def _load_file(self, path, table, mode):
        if not path.exists():
            print(f"WARNING: Missing file {path}")
            return

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

            for entry in data:
                if mode == "item":
                    obj = Item(
                        item_id=entry["id"],
                        name=entry["name"],
                        description=entry["description"],
                        item_type=entry.get("type", "part"),
                        heal_amount=entry.get("heal_amount", 0),
                        stats_modifier=entry.get("stats_modifier", {}),
                        buy_price=entry.get("buy_price", 0),
                        sell_price=entry.get("sell_price", 0)
                    )
                    table.insert(entry["id"], obj)

                else:
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
                sprite_name=data.get("sprite", "placeholder.png"),
                loot_id=data.get("loot_id"),
                loot_chance=data.get("loot_chance", 1.0),
                loot_amount=data.get("loot_amount", 1),
                gold_reward=data.get("gold_reward", 0),
                enemy_skill_ids=data.get("skills", [])
            )

        return None

    def load_mutation_tree(self):
        path = MUTATIONS_DATA_FILE

        if not path.exists():
            return None

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        nodes = {}
        root = None

        # First pass: create all nodes.
        for m in data:
            req_item = m.get("req_item")
            req_count = m.get("req_count", 0 if req_item is None else 1)

            new_node = MutationNode(
                node_id=m["id"],
                name=m["name"],
                description=m["description"],
                required_item_id=req_item,
                required_count=req_count,
                stats_modifier=m.get("stats_modifier", {}),
                unlock_skill=m.get("unlock_skill")
            )

            nodes[m["id"]] = new_node

            if m["parent"] is None:
                root = new_node

        # Second pass: connect parent -> children.
        for m in data:
            parent_id = m["parent"]

            if parent_id and parent_id in nodes:
                nodes[parent_id].children.append(nodes[m["id"]])

        return MutationTree(root) if root else None
