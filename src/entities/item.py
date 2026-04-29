class Item:
    """
    Base class for all items in the game.
    Handles both equippable mutated parts and consumable potions.
    Designed to work with the Hash Table and Sorting/Searching algorithms.
    """
    def __init__(self, item_id, name, description, item_type="part", heal_amount=0, stats_modifier=None):
        """
        Args:
            item_id (str): Unique identifier (e.g., "potion_hp_01").
            name (str): Display name (e.g., "Minor Health Potion").
            description (str): Text description for UI.
            item_type (str): Category of the item ("part" or "potion").
            heal_amount (int): Amount of HP to restore when consumed.
            stats_modifier (dict): Stat boosts (e.g., {"attack": 15, "speed": 5}).
        """
        self.item_id = item_id
        self.name = name
        self.description = description
        self.item_type = item_type
        self.heal_amount = heal_amount
        self.stats_modifier = stats_modifier if stats_modifier else {}

    def apply_effect(self, target_entity):
        """
        Consumes the potion, applying healing and stat boosts to the target entity.
        """
        if self.item_type == "potion":
            # 1. Apply Healing
            if self.heal_amount > 0:
                target_entity.heal(self.heal_amount)
            
            # 2. Apply Stat Boosts
            if "attack" in self.stats_modifier:
                target_entity.attack += self.stats_modifier["attack"]
            if "speed" in self.stats_modifier:
                target_entity.speed += self.stats_modifier["speed"]

    def __repr__(self):
        return f"<{self.item_type.capitalize()}: {self.name}>"