import copy


class SkillLibrary:
    """
    Central place for combat skill definitions and loadout rules.

    Rules:
    - Basic Attack is always available.
    - Zac can equip up to 4 combat skills.
    - Venom Fang unlocks Venom Bite.
    - Toxic Bite upgrades Venom Bite into Toxic Bite.
    - Echolocation unlocks Sonic Pulse.
    - Sonic Pulse Organ upgrades Sonic Pulse into Sonic Pulse+.
    - Swift Legs unlocks Beast Focus.
    """

    MAX_LOADOUT_SIZE = 4

    UPGRADE_REPLACEMENTS = {
        "venom_bite": "toxic_bite",
        "sonic_pulse": "sonic_pulse_plus"
    }

    SKILL_ACTIONS = {
        "basic_attack": {
            "name": "Basic Attack",
            "mult": 1.0,
            "target": "enemy"
        },

        "venom_bite": {
            "name": "Venom Bite",
            "mult": 0.8,
            "target": "enemy",
            "status": {
                "target": "enemy",
                "type": "poison",
                "duration": 3,
                "power": 5,
                "chance": 1.0,
                "apply_chance": 1.0
            }
        },

        "toxic_bite": {
            "name": "Toxic Bite",
            "mult": 1.0,
            "target": "enemy",
            "status": {
                "target": "enemy",
                "type": "poison",
                "duration": 4,
                "power": 8,
                "chance": 1.0,
                "apply_chance": 1.0
            }
        },

        "sonic_pulse": {
            "name": "Sonic Pulse",
            "mult": 0.6,
            "target": "enemy",
            "status": {
                "target": "enemy",
                "type": "paralysis",
                "duration": 2,
                "power": 0,
                "chance": 0.35,
                "apply_chance": 1.0
            },
            "stage_change": {
                "target": "enemy",
                "stat": "speed",
                "amount": -1
            }
        },

        "sonic_pulse_plus": {
            "name": "Sonic Pulse+",
            "mult": 0.8,
            "target": "enemy",
            "status": {
                "target": "enemy",
                "type": "paralysis",
                "duration": 3,
                "power": 0,
                "chance": 0.45,
                "apply_chance": 1.0
            },
            "stage_change": {
                "target": "enemy",
                "stat": "speed",
                "amount": -2
            }
        },

        "beast_focus": {
            "name": "Beast Focus",
            "mult": 0,
            "target": "self",
            "stage_changes": [
                {
                    "target": "self",
                    "stat": "attack",
                    "amount": 1
                },
                {
                    "target": "self",
                    "stat": "speed",
                    "amount": 1
                }
            ]
        }
    }

    SKILL_INFO = {
        "basic_attack": {
            "description": "A normal physical attack.",
            "effect": "Deals 100% ATK damage to one enemy."
        },
        "venom_bite": {
            "description": "A poisonous bite unlocked by Venom Fang.",
            "effect": "Deals 80% ATK damage and poisons the enemy for 3 turns."
        },
        "toxic_bite": {
            "description": "An upgraded venom attack unlocked by Toxic Bite.",
            "effect": "Deals 100% ATK damage and applies stronger poison for 4 turns."
        },
        "sonic_pulse": {
            "description": "A sound-wave attack unlocked by Echolocation.",
            "effect": "Deals 60% ATK damage, may paralyze, and lowers enemy SPD by 1 stage."
        },
        "sonic_pulse_plus": {
            "description": "An upgraded sound-wave attack unlocked by Sonic Pulse Organ.",
            "effect": "Deals 80% ATK damage, has stronger paralysis, and lowers enemy SPD by 2 stages."
        },
        "beast_focus": {
            "description": "A self-buff unlocked by Swift Legs.",
            "effect": "Raises Zac's ATK and SPD by 1 stage."
        }
    }

    @classmethod
    def get_unlocked_mutation_ids(cls, mutation_tree):
        if not mutation_tree:
            return set()

        return set(mutation_tree.get_unlocked_nodes())

    @classmethod
    def get_available_skill_ids(cls, mutation_tree):
        """
        Returns all skills Zac has unlocked.

        Upgrade mutations replace older skill versions:
        - toxic_bite replaces venom_bite
        - sonic_pulse_plus replaces sonic_pulse
        """
        unlocked = cls.get_unlocked_mutation_ids(mutation_tree)

        skill_ids = ["basic_attack"]

        if "venom_fang" in unlocked:
            if "toxic_bite" in unlocked:
                skill_ids.append("toxic_bite")
            else:
                skill_ids.append("venom_bite")

        if "echolocation" in unlocked:
            if "sonic_pulse_organ" in unlocked:
                skill_ids.append("sonic_pulse_plus")
            else:
                skill_ids.append("sonic_pulse")

        if "swift_legs" in unlocked:
            skill_ids.append("beast_focus")

        return skill_ids

    @classmethod
    def sanitize_loadout(cls, loadout, mutation_tree):
        """
        Cleans the saved skill loadout:
        - Keeps only available skills.
        - Always keeps Basic Attack.
        - Replaces old skills with upgraded versions only when the upgrade is actually available.
        - Removes duplicates.
        - Limits to MAX_LOADOUT_SIZE.
        """
        available = cls.get_available_skill_ids(mutation_tree)
        available_set = set(available)

        if not loadout:
            loadout = ["basic_attack"]

        cleaned = []

        for skill_id in loadout:
            replacement_id = cls.UPGRADE_REPLACEMENTS.get(skill_id)

            # Only replace old skill if the upgraded skill is already unlocked.
            if replacement_id and replacement_id in available_set:
                final_skill_id = replacement_id
            else:
                final_skill_id = skill_id

            if final_skill_id in available_set and final_skill_id not in cleaned:
                cleaned.append(final_skill_id)

        if "basic_attack" not in cleaned:
            cleaned.insert(0, "basic_attack")

        final_loadout = []

        for skill_id in cleaned:
            if skill_id in available_set and skill_id not in final_loadout:
                final_loadout.append(skill_id)

        return final_loadout[:cls.MAX_LOADOUT_SIZE]

    @classmethod
    def build_action(cls, skill_id):
        """
        Returns a fresh action dictionary for combat.
        """
        if skill_id not in cls.SKILL_ACTIONS:
            skill_id = "basic_attack"

        return copy.deepcopy(cls.SKILL_ACTIONS[skill_id])

    @classmethod
    def get_skill_name(cls, skill_id):
        return cls.SKILL_ACTIONS.get(
            skill_id,
            cls.SKILL_ACTIONS["basic_attack"]
        ).get("name", skill_id)

    @classmethod
    def get_skill_info(cls, skill_id):
        return cls.SKILL_INFO.get(
            skill_id,
            {
                "description": "No description available.",
                "effect": "No effect information available."
            }
        )
