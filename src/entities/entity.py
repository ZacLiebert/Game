import random


class Entity:
    """
    Represents a combat entity such as Zac, allies, or enemies.

    Supports:
    - Permanent base stats: HP, ATK, DEF, SPD
    - Stat stages using multiplier system
    - Status effects: poison, paralysis
    - Loot drop data for enemies
    """

    STAT_STAGE_MULTIPLIERS = {
        -2: 0.25,
        -1: 0.5,
        0: 1.0,
        1: 1.5,
        2: 2.0,
        3: 2.5
    }

    MIN_STAGE = -2
    MAX_STAGE = 3

    def __init__(
        self,
        entity_id,
        name,
        hp,
        attack,
        defense,
        speed,
        sprite_name,
        loot_id=None,
        loot_chance=1.0,
        loot_amount=1,
        gold_reward=0,
        enemy_skill_ids=None
    ):
        self.entity_id = entity_id
        self.name = name

        self.max_hp = hp
        self.current_hp = hp

        self.base_attack = attack
        self.base_defense = defense
        self.base_speed = speed

        self.sprite_name = sprite_name

        # Loot data
        self.loot_id = loot_id
        self.loot_chance = loot_chance
        self.loot_amount = loot_amount
        self.gold_reward = gold_reward
        self.enemy_skill_ids = enemy_skill_ids if enemy_skill_ids else []

        self.stat_stages = {
            "attack": 0,
            "defense": 0,
            "speed": 0
        }

        self.status_effects = []

    # =========================
    # EFFECTIVE STATS
    # =========================

    @property
    def attack(self):
        return self._get_effective_stat("attack", self.base_attack)

    @attack.setter
    def attack(self, value):
        self.base_attack = value

    @property
    def defense(self):
        return self._get_effective_stat("defense", self.base_defense)

    @defense.setter
    def defense(self, value):
        self.base_defense = value

    @property
    def speed(self):
        return self._get_effective_stat("speed", self.base_speed)

    @speed.setter
    def speed(self, value):
        self.base_speed = value

    def _get_effective_stat(self, stat_name, base_value):
        stage = self.stat_stages.get(stat_name, 0)
        multiplier = self.STAT_STAGE_MULTIPLIERS.get(stage, 1.0)

        return max(1, int(base_value * multiplier))

    def change_stat_stage(self, stat_name, amount):
        if stat_name not in self.stat_stages:
            return f"{self.name} has no stat named {stat_name}."

        old_stage = self.stat_stages[stat_name]
        new_stage = old_stage + amount
        new_stage = max(self.MIN_STAGE, min(self.MAX_STAGE, new_stage))

        self.stat_stages[stat_name] = new_stage

        if new_stage == old_stage:
            if amount > 0:
                return f"{self.name}'s {stat_name.upper()} cannot go higher!"
            return f"{self.name}'s {stat_name.upper()} cannot go lower!"

        if amount > 0:
            return f"{self.name}'s {stat_name.upper()} rose to stage {new_stage}!"

        return f"{self.name}'s {stat_name.upper()} fell to stage {new_stage}!"

    def reset_stat_stages(self):
        self.stat_stages = {
            "attack": 0,
            "defense": 0,
            "speed": 0
        }

    # =========================
    # BASIC COMBAT METHODS
    # =========================

    def is_alive(self):
        return self.current_hp > 0

    def take_damage(self, amount):
        damage = max(1, amount - self.defense)
        self.current_hp -= damage
        self.current_hp = max(0, self.current_hp)
        return damage

    def take_true_damage(self, amount):
        damage = max(0, amount)
        self.current_hp -= damage
        self.current_hp = max(0, self.current_hp)
        return damage

    def heal(self, amount):
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    # =========================
    # STATUS EFFECT SYSTEM
    # =========================

    def add_status(self, status_type, duration, power=0, chance=1.0):
        for effect in self.status_effects:
            if effect.get("type") == status_type:
                effect["duration"] = max(effect.get("duration", 0), duration)
                effect["power"] = max(effect.get("power", 0), power)
                effect["chance"] = max(effect.get("chance", 1.0), chance)
                return

        self.status_effects.append({
            "type": status_type,
            "duration": duration,
            "power": power,
            "chance": chance
        })

    def has_status(self, status_type):
        for effect in self.status_effects:
            if effect.get("type") == status_type:
                return True

        return False

    def process_start_turn_status(self):
        messages = []
        skip_turn = False

        remaining_effects = []

        for effect in self.status_effects:
            effect_type = effect.get("type")
            duration = effect.get("duration", 0)
            power = effect.get("power", 0)
            chance = effect.get("chance", 1.0)

            if effect_type == "poison":
                damage = self.take_true_damage(power)
                messages.append(
                    f"{self.name} suffers {damage} poison damage."
                )

            elif effect_type == "paralysis":
                if random.random() < chance:
                    skip_turn = True
                    messages.append(
                        f"{self.name} is paralyzed and cannot move!"
                    )
                else:
                    messages.append(
                        f"{self.name} resists paralysis this turn."
                    )

            effect["duration"] = duration - 1

            if effect["duration"] > 0:
                remaining_effects.append(effect)
            else:
                messages.append(f"{self.name}'s {effect_type} effect wore off.")

        self.status_effects = remaining_effects

        return messages, skip_turn

    def get_status_summary(self):
        parts = []

        for effect in self.status_effects:
            effect_type = effect.get("type", "unknown")
            duration = effect.get("duration", 0)
            parts.append(f"{effect_type}({duration})")

        for stat_name, stage in self.stat_stages.items():
            if stage != 0:
                parts.append(f"{stat_name.upper()} {stage:+}")

        if not parts:
            return "Normal"

        return ", ".join(parts)
