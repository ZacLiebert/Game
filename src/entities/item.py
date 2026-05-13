"""Item data and item-use effects."""

class Item:
    """Inventory item with price, type, and combat effect data."""

    def __init__(
        self,
        item_id,
        name,
        description,
        item_type="part",
        heal_amount=0,
        revive_amount=0,
        stats_modifier=None,
        stat_stage_changes=None,
        buy_price=0,
        sell_price=0
    ):
        """Set up initial state."""
        self.item_id = item_id
        self.name = name
        self.description = description
        self.item_type = item_type
        self.heal_amount = int(heal_amount or 0)
        self.revive_amount = int(revive_amount or 0)
        self.stats_modifier = stats_modifier if stats_modifier else {}
        self.stat_stage_changes = stat_stage_changes if stat_stage_changes else []

        self.buy_price = buy_price
        self.sell_price = sell_price

    def is_consumable(self):
        """Return whether the item can be used in battle."""
        return self.item_type == "potion"

    def needs_defeated_target(self):
        """Return whether the item revives a defeated ally."""
        return self.revive_amount > 0

    def can_use_on(self, target_entity):
        """Return whether this item can affect the target."""
        if target_entity is None or not self.is_consumable():
            return False

        is_alive = target_entity.is_alive()

        if self.revive_amount > 0:
            return not is_alive

        if not is_alive:
            return False

        has_effect = False

        if self.heal_amount > 0:
            current_hp = getattr(target_entity, "current_hp", 0)
            max_hp = getattr(target_entity, "max_hp", 0)
            has_effect = has_effect or current_hp < max_hp

        for change in self.stat_stage_changes:
            stat_name = change.get("stat")
            amount = int(change.get("amount", 0))
            current_stage = getattr(target_entity, "stat_stages", {}).get(stat_name, 0)
            min_stage = getattr(target_entity, "MIN_STAGE", -2)
            max_stage = getattr(target_entity, "MAX_STAGE", 3)

            if amount > 0 and current_stage < max_stage:
                has_effect = True
            elif amount < 0 and current_stage > min_stage:
                has_effect = True

        if self.stats_modifier:
            has_effect = True

        return has_effect

    def get_effect_summary(self):
        """Return readable text for the item effects."""
        parts = []

        if self.heal_amount > 0:
            parts.append(f"Restores {self.heal_amount} HP")

        if self.revive_amount > 0:
            parts.append(f"Revives a defeated ally with {self.revive_amount} HP")

        for change in self.stat_stage_changes:
            stat_name = str(change.get("stat", "stat")).upper()
            amount = int(change.get("amount", 0))
            sign = "+" if amount > 0 else ""
            parts.append(f"{stat_name} stage {sign}{amount}")

        for stat_name, amount in self.stats_modifier.items():
            sign = "+" if amount > 0 else ""
            parts.append(f"Permanent {str(stat_name).upper()} {sign}{amount}")

        if not parts:
            return "No direct effect."

        return "; ".join(parts) + "."

    def apply_effect(self, target_entity):
        """Apply the item effect and return battle log messages."""
        messages = []

        if not self.can_use_on(target_entity):
            return [f"{self.name} cannot be used on {getattr(target_entity, 'name', 'that target')}."]

        if self.revive_amount > 0:
            target_entity.current_hp = min(target_entity.max_hp, self.revive_amount)

            if hasattr(target_entity, "status_effects"):
                target_entity.status_effects = []

            if hasattr(target_entity, "reset_stat_stages"):
                target_entity.reset_stat_stages()

            messages.append(
                f"{target_entity.name} was revived with {target_entity.current_hp} HP."
            )
            return messages

        if self.heal_amount > 0:
            before_hp = target_entity.current_hp
            target_entity.heal(self.heal_amount)
            healed = target_entity.current_hp - before_hp
            messages.append(f"{target_entity.name} recovered {healed} HP.")

        for change in self.stat_stage_changes:
            stat_name = change.get("stat")
            amount = int(change.get("amount", 0))

            if hasattr(target_entity, "change_stat_stage"):
                messages.append(target_entity.change_stat_stage(stat_name, amount))

        for stat_name, amount in self.stats_modifier.items():
            amount = int(amount)

            if stat_name == "attack":
                target_entity.attack += amount
            elif stat_name == "defense":
                target_entity.defense += amount
            elif stat_name == "speed":
                target_entity.speed += amount
            elif stat_name == "max_hp":
                target_entity.max_hp += amount
                target_entity.current_hp = min(target_entity.current_hp + amount, target_entity.max_hp)

            messages.append(f"{target_entity.name}'s {stat_name.upper()} changed by {amount}.")

        return messages

    def __repr__(self):
        """Return a readable text form."""
        return f"<{self.item_type.capitalize()}: {self.name}>"
