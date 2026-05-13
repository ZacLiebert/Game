"""Shared runtime state and save/load helpers."""

from src.core.database import GameDatabase
from src.core.inventory_manager import InventoryManager
from src.core.quest_manager import QuestManager
from src.core.skill_library import SkillLibrary
from src.paths import MUTATIONS_DATA_FILE


class GameSession:
    """Stores shared player, inventory, quest, map, and save data."""

    MAX_GOLD = 999999
    MAX_INVENTORY_ITEMS = 200

    def __init__(self):
        """Set up initial state."""
        self.db = GameDatabase()
        self.inventory = InventoryManager()

        # Player gold used by shops.
        self.gold = 100
        self.current_map_id = "forest_01"
        self.player_position = (128, 128)
        self.defeated_npcs = set()
        self.quest_manager = QuestManager()

        # Load the starting party.
        self.party = [
            self.db.create_entity("p1", is_enemy=False),
            self.db.create_entity("p2", is_enemy=False),
            self.db.create_entity("p3", is_enemy=False)
        ]

        # Ignore missing party members.
        self.party = [member for member in self.party if member is not None]

        # Give starting items.
        # Starting items make inventory useful early.
        starting_items = [
            ("pot_hp_small", 2),
            ("pot_hp_medium", 1),
            ("pot_atk_1", 1),
            ("pot_spd_1", 1),
            ("pot_revive_small", 1)
        ]

        for item_id, amount in starting_items:
            item = self.db.get_item(item_id)

            if item:
                self.inventory.add_item_amount(item, amount)

        # Load the mutation tree.
        self.mutation_tree = self.db.load_mutation_tree()

        if not self.mutation_tree:
            print(f"CRITICAL: {MUTATIONS_DATA_FILE} not found or tree failed to build!")

        self.quest_manager.set_mutation_progress_provider(
            self.get_unlocked_mutation_ids
        )

        # Set up the skill loadout.
        self.skill_loadout = ["basic_attack"]
        self.skill_loadout = SkillLibrary.sanitize_loadout(
            self.skill_loadout,
            self.mutation_tree
        )

    # Safe load helpers

    def _safe_int(self, value, default, min_value=None, max_value=None):
        """Convert a value to a clamped safe integer."""
        try:
            result = int(value)
        except (TypeError, ValueError):
            result = default

        if min_value is not None:
            result = max(min_value, result)

        if max_value is not None:
            result = min(max_value, result)

        return result

    def _safe_position(self, value, default):
        """Restore a valid two-number map position."""
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            return default

        x = self._safe_int(value[0], default[0], min_value=0, max_value=99999)
        y = self._safe_int(value[1], default[1], min_value=0, max_value=99999)

        return (x, y)

    def _reset_temporary_party_effects(self):
        """Clear combat-only status and stat changes."""
        for member in self.party:
            if hasattr(member, "status_effects"):
                member.status_effects = []

            if hasattr(member, "reset_stat_stages"):
                member.reset_stat_stages()

    def get_unlocked_mutation_ids(self):
        """Return the unlocked mutation ids."""
        if not self.mutation_tree:
            return []

        return self.mutation_tree.get_unlocked_nodes()

    def sync_mutation_quest_progress(self):
        """Update the mutation quest from unlocked mutations."""
        return self.quest_manager.sync_active_mutation_progress(
            self.get_unlocked_mutation_ids()
        )

    # Save / load

    def export_save_data(self):
        """Return save-ready game data."""
        return {
            "schema_version": 3,

            "gold": self.gold,
            "current_map_id": self.current_map_id,
            "player_position": list(self.player_position),
            "defeated_npcs": list(self.defeated_npcs),
            "quests": self.quest_manager.export_state(),

            "party": [
                {
                    "id": p.entity_id,
                    "hp": p.current_hp,
                    "max_hp": p.max_hp,
                    "attack": getattr(p, "base_attack", p.attack),
                    "defense": getattr(p, "base_defense", p.defense),
                    "speed": getattr(p, "base_speed", p.speed)
                } for p in self.party
            ],

            # Save one count per item ID.
            "inventory_counts": self.inventory.export_counts(),

            # Save unlocked mutations.
            "mutations": self.mutation_tree.get_unlocked_nodes()
            if self.mutation_tree else [],

            # Save equipped skills.
            "skill_loadout": self.skill_loadout
        }

    def import_save_data(self, save_dict):
        """Restore game data from a loaded save."""
        if not isinstance(save_dict, dict):
            return

        # Restore gold.
        self.gold = self._safe_int(
            save_dict.get("gold", self.gold),
            self.gold,
            min_value=0,
            max_value=self.MAX_GOLD
        )

        # Restore only a known map.
        saved_map_id = save_dict.get("current_map_id", self.current_map_id)

        if isinstance(saved_map_id, str) and self.db.get_map_data(saved_map_id):
            self.current_map_id = saved_map_id

        # Restore player position.
        self.player_position = self._safe_position(
            save_dict.get("player_position"),
            self.player_position
        )

        # Restore defeated NPCs.
        defeated = save_dict.get("defeated_npcs", [])

        if isinstance(defeated, list):
            self.defeated_npcs = {
                str(name) for name in defeated
                if isinstance(name, str)
            }

        # Restore quest progress.
        if "quests" in save_dict:
            self.quest_manager.import_state(save_dict.get("quests"))

        # Restore party data.
        saved_party = save_dict.get("party", [])

        if isinstance(saved_party, list):
            party_by_id = {
                member.entity_id: member
                for member in self.party
                if member is not None
            }

            for index, p_data in enumerate(saved_party):
                if not isinstance(p_data, dict):
                    continue

                saved_id = p_data.get("id")
                member = party_by_id.get(saved_id)

                # Support older save files.
                if member is None and index < len(self.party):
                    member = self.party[index]

                if member is None:
                    continue

                member.max_hp = self._safe_int(
                    p_data.get("max_hp", member.max_hp),
                    member.max_hp,
                    min_value=1,
                    max_value=9999
                )

                member.current_hp = self._safe_int(
                    p_data.get("hp", member.current_hp),
                    member.current_hp,
                    min_value=0,
                    max_value=member.max_hp
                )

                member.attack = self._safe_int(
                    p_data.get("attack", getattr(member, "base_attack", member.attack)),
                    getattr(member, "base_attack", member.attack),
                    min_value=1,
                    max_value=999
                )

                member.defense = self._safe_int(
                    p_data.get("defense", getattr(member, "base_defense", member.defense)),
                    getattr(member, "base_defense", member.defense),
                    min_value=0,
                    max_value=999
                )

                member.speed = self._safe_int(
                    p_data.get("speed", getattr(member, "base_speed", member.speed)),
                    getattr(member, "base_speed", member.speed),
                    min_value=1,
                    max_value=999
                )

        self._reset_temporary_party_effects()

        # Restore inventory from item IDs.
        # Preferred schema v3 format: compressed counts.
        # Backward compatible schema v2 format: list of duplicate item IDs.
        self.inventory.clear()

        saved_inventory_counts = save_dict.get("inventory_counts")
        restored_total = 0

        if isinstance(saved_inventory_counts, list):
            for entry in saved_inventory_counts:
                if not isinstance(entry, dict):
                    continue

                item_id = entry.get("id")

                if not isinstance(item_id, str):
                    continue

                remaining_space = self.MAX_INVENTORY_ITEMS - restored_total

                if remaining_space <= 0:
                    break

                amount = self._safe_int(
                    entry.get("count", 0),
                    0,
                    min_value=0,
                    max_value=remaining_space
                )

                if amount <= 0:
                    continue

                item_obj = self.db.get_item(item_id)

                if item_obj:
                    self.inventory.add_item_amount(item_obj, amount)
                    restored_total += amount
        else:
            saved_inventory = save_dict.get("inventory", [])

            if isinstance(saved_inventory, list):
                for item_id in saved_inventory[:self.MAX_INVENTORY_ITEMS]:
                    if not isinstance(item_id, str):
                        continue

                    item_obj = self.db.get_item(item_id)

                    if item_obj:
                        self.inventory.add_item(item_obj)

        # Restore Mutation Tree.
        # MutationTree.restore_unlocked_nodes() now resets old unlocks first
        # and only restores valid parent-child chains.
        if self.mutation_tree:
            saved_mutations = save_dict.get("mutations", [])

            if isinstance(saved_mutations, list):
                self.mutation_tree.restore_unlocked_nodes(saved_mutations)
            else:
                self.mutation_tree.restore_unlocked_nodes([])

        self.sync_mutation_quest_progress()

        # Restore Skill Loadout.
        saved_loadout = save_dict.get(
            "skill_loadout",
            ["basic_attack"]
        )

        if not isinstance(saved_loadout, list):
            saved_loadout = ["basic_attack"]

        self.skill_loadout = [
            skill_id for skill_id in saved_loadout
            if isinstance(skill_id, str)
        ]

        self.skill_loadout = SkillLibrary.sanitize_loadout(
            self.skill_loadout,
            self.mutation_tree
        )

    # MAP / STORY HELPERS

    def remember_map_position(self, map_id, player_rect):
        """Save the current map position for later loading."""
        self.current_map_id = map_id
        self.player_position = (
            int(player_rect.x),
            int(player_rect.y)
        )

    def mark_npc_defeated(self, npc_name):
        """Remember that an NPC has already been defeated."""
        self.defeated_npcs.add(npc_name)

    def is_npc_defeated(self, npc_name):
        """Return whether is npc defeated is true."""
        return npc_name in self.defeated_npcs

    def is_story_complete(self):
        """Return whether is story complete is true."""
        return self.quest_manager.is_story_complete()
