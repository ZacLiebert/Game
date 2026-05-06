class Item:
    """
    Base class for all items in the game.
    Handles both mutated materials and consumable potions.
    Supports shop prices for buying and selling.
    """

    def __init__(
        self,
        item_id,
        name,
        description,
        item_type="part",
        heal_amount=0,
        stats_modifier=None,
        buy_price=0,
        sell_price=0
    ):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.item_type = item_type
        self.heal_amount = heal_amount
        self.stats_modifier = stats_modifier if stats_modifier else {}

        self.buy_price = buy_price
        self.sell_price = sell_price

    def apply_effect(self, target_entity):
        """
        Applies item effect to a target entity.
        Currently supports healing potions and simple stat boosts.
        """
        if self.item_type == "potion":
            if self.heal_amount > 0:
                target_entity.heal(self.heal_amount)

            if "attack" in self.stats_modifier:
                target_entity.attack += self.stats_modifier["attack"]

            if "defense" in self.stats_modifier:
                target_entity.defense += self.stats_modifier["defense"]

            if "speed" in self.stats_modifier:
                target_entity.speed += self.stats_modifier["speed"]

    def __repr__(self):
        return f"<{self.item_type.capitalize()}: {self.name}>"