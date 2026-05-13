"""Loads game data from JSON files."""

import json

from src.data_structures.hash_table import HashTable
from src.entities.item import Item
from src.entities.entity import Entity
from src.data_structures.tree import MutationNode, MutationTree
from src.paths import (
    ALLIES_DATA_FILE,
    ENEMIES_DATA_FILE,
    ITEMS_DATA_FILE,
    MAP_DATA_FILE,
    MUTATIONS_DATA_FILE,
)


class GameDatabase:
    """Loads JSON data and provides lookup helpers for game objects."""

    def __init__(self):
        """Set up initial state."""
        self.item_db = HashTable(capacity=200)
        self.enemy_db = HashTable(capacity=100)
        self.ally_db = HashTable(capacity=50)
        self._map_data = None
        self._load_from_json()

    def _load_map_data(self):
        """Load the map data."""
        if self._map_data is not None:
            return self._map_data

        if MAP_DATA_FILE.exists():
            with MAP_DATA_FILE.open("r", encoding="utf-8") as f:
                self._map_data = json.load(f)
                return self._map_data

        self._map_data = {}
        return self._map_data

    def get_map_data(self, map_id):
        """Return the map data."""
        return self._load_map_data().get(map_id)

    def _load_from_json(self):
        """Load the from json."""
        self._load_file(ITEMS_DATA_FILE, self.item_db, "item")
        self._load_file(ENEMIES_DATA_FILE, self.enemy_db, "raw")
        self._load_file(ALLIES_DATA_FILE, self.ally_db, "raw")

    def _load_file(self, path, table, mode):
        """Load the file."""
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
                    revive_amount=entry.get("revive_amount", 0),
                    stats_modifier=entry.get("stats_modifier", {}),
                    stat_stage_changes=entry.get("stat_stage_changes", []),
                    buy_price=entry.get("buy_price", 0),
                    sell_price=entry.get("sell_price", 0)
                )
                table.insert(entry["id"], obj)
            else:
                table.insert(entry["id"], entry)

    def get_item(self, item_id):
        """Return the item."""
        return self.item_db.get(item_id)

    def create_entity(self, entity_id, is_enemy=True):
        """Create entity."""
        data = self.enemy_db.get(entity_id) if is_enemy else self.ally_db.get(entity_id)

        if data:
            return Entity(
                entity_id=data["id"],
                name=data["name"],
                hp=data["hp"],
                attack=data["attack"],
                defense=data["defense"],
                speed=data["speed"],
                sprite_name=data.get("sprite", "bat.png" if is_enemy else "zac_battle.png"),
                loot_id=data.get("loot_id"),
                loot_chance=data.get("loot_chance", 1.0),
                loot_amount=data.get("loot_amount", 1),
                gold_reward=data.get("gold_reward", 0),
                enemy_skill_ids=data.get("skills", [])
            )

        return None

    def _validate_mutation_data(self, data):
        """Check mutation data before building the tree."""
        errors = []

        if not isinstance(data, list) or not data:
            return ["mutations.json must contain a non-empty list."]

        ids = HashTable(capacity=max(32, len(data) * 2))
        parent_by_id = HashTable(capacity=max(32, len(data) * 2))
        root_count = 0

        for index, mutation_data in enumerate(data):
            if not isinstance(mutation_data, dict):
                errors.append(f"Entry #{index} is not an object.")
                continue

            mutation_id = mutation_data.get("id")
            parent_id = mutation_data.get("parent")

            if not isinstance(mutation_id, str) or not mutation_id.strip():
                errors.append(f"Entry #{index} has an invalid id.")
                continue

            if ids.contains(mutation_id):
                errors.append(f"Duplicate mutation id '{mutation_id}'.")
                continue

            ids.insert(mutation_id, True)
            parent_by_id.insert(mutation_id, parent_id)

            if parent_id is None:
                root_count += 1
            elif not isinstance(parent_id, str) or not parent_id.strip():
                errors.append(f"Mutation '{mutation_id}' has an invalid parent id.")
            elif parent_id == mutation_id:
                errors.append(f"Mutation '{mutation_id}' cannot be its own parent.")

        if root_count != 1:
            errors.append(f"Expected exactly 1 root mutation, found {root_count}.")

        for mutation_data in data:
            if not isinstance(mutation_data, dict):
                continue

            mutation_id = mutation_data.get("id")
            parent_id = mutation_data.get("parent")

            if not isinstance(mutation_id, str):
                continue

            if isinstance(parent_id, str) and parent_id and not ids.contains(parent_id):
                errors.append(
                    f"Mutation '{mutation_id}' references missing parent '{parent_id}'."
                )

        # Detect parent-chain cycles.
        for mutation_data in data:
            if not isinstance(mutation_data, dict):
                continue

            current_id = mutation_data.get("id")

            if not isinstance(current_id, str) or not parent_by_id.contains(current_id):
                continue

            path = HashTable(capacity=32)

            while current_id is not None:
                if path.contains(current_id):
                    errors.append(f"Cycle detected in mutation parent chain at '{current_id}'.")
                    break

                path.insert(current_id, True)

                if not parent_by_id.contains(current_id):
                    break

                next_parent = parent_by_id.get_or_default(current_id)

                if next_parent is not None and not isinstance(next_parent, str):
                    break

                current_id = next_parent

        return errors

    def load_mutation_tree(self):
        """Load the mutation tree."""
        path = MUTATIONS_DATA_FILE

        if not path.exists():
            return None

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        validation_errors = self._validate_mutation_data(data)

        if validation_errors:
            raise ValueError(
                "Invalid mutation data in mutations.json:\n- "
                + "\n- ".join(validation_errors)
            )

        nodes = HashTable(capacity=max(32, len(data) * 2))
        root = None

        # Create nodes first.
        for mutation_data in data:
            req_item = mutation_data.get("req_item")
            req_count = mutation_data.get("req_count", 0 if req_item is None else 1)

            new_node = MutationNode(
                node_id=mutation_data["id"],
                name=mutation_data["name"],
                description=mutation_data["description"],
                required_item_id=req_item,
                required_count=req_count,
                stats_modifier=mutation_data.get("stats_modifier", {}),
                unlock_skill=mutation_data.get("unlock_skill")
            )

            nodes.insert(mutation_data["id"], new_node)

            if mutation_data["parent"] is None:
                root = new_node

        # Then connect parents to children.
        for mutation_data in data:
            parent_id = mutation_data["parent"]

            if parent_id:
                parent_node = nodes.get(parent_id)
                child_node = nodes.get(mutation_data["id"])

                if parent_node and child_node:
                    parent_node.add_child(child_node)

        return MutationTree(root) if root else None
