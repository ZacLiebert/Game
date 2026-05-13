"""Combat skill definitions and loadout rules."""

import copy


class SkillLibrary:
    """Defines player, ally, and mutation combat skills."""

    MAX_LOADOUT_SIZE = 4

    UPGRADE_REPLACEMENTS = {
        "venom_bite": "toxic_bite",
        "sonic_pulse": "sonic_pulse_plus",
        "guard_stance": "iron_guard"
    }

    ALLY_LOADOUTS = {
        "p2": ["basic_attack", "first_aid"],
        "p3": ["basic_attack", "shield_bash", "protective_guard"]
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
            "mult": 0.65,
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
            "mult": 0.85,
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
        },

        "guard_stance": {
            "name": "Guard Stance",
            "mult": 0,
            "target": "self",
            "stage_changes": [
                {
                    "target": "self",
                    "stat": "defense",
                    "amount": 1
                }
            ]
        },

        "iron_guard": {
            "name": "Iron Guard",
            "mult": 0,
            "target": "self",
            "stage_changes": [
                {
                    "target": "self",
                    "stat": "defense",
                    "amount": 2
                }
            ]
        },

        "counter_shell": {
            "name": "Counter Shell",
            "mult": 0.75,
            "target": "enemy",
            "stage_changes": [
                {
                    "target": "self",
                    "stat": "defense",
                    "amount": 1
                },
                {
                    "target": "enemy",
                    "stat": "attack",
                    "amount": -1
                }
            ]
        },

        "first_aid": {
            "name": "First Aid",
            "mult": 0,
            "target": "ally",
            "heal_amount": 24,
            "clear_statuses": ["poison"]
        },

        "shield_bash": {
            "name": "Shield Bash",
            "mult": 0.75,
            "target": "enemy",
            "stage_change": {
                "target": "enemy",
                "stat": "attack",
                "amount": -1
            }
        },

        "protective_guard": {
            "name": "Protective Guard",
            "mult": 0,
            "target": "self",
            "stage_changes": [
                {
                    "target": "self",
                    "stat": "defense",
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
            "effect": "Deals 65% ATK damage, may paralyze, and lowers enemy SPD by 1 stage."
        },
        "sonic_pulse_plus": {
            "description": "An upgraded sound-wave attack unlocked by Sonic Pulse Organ.",
            "effect": "Deals 85% ATK damage, has stronger paralysis, and lowers enemy SPD by 2 stages."
        },
        "beast_focus": {
            "description": "A self-buff unlocked by Swift Legs.",
            "effect": "Raises Zac's ATK and SPD by 1 stage."
        },
        "guard_stance": {
            "description": "A defensive mutation skill unlocked by Hardened Body.",
            "effect": "Raises Zac's DEF by 1 stage."
        },
        "iron_guard": {
            "description": "An upgraded defense skill unlocked by Thick Hide.",
            "effect": "Raises Zac's DEF by 2 stages."
        },
        "counter_shell": {
            "description": "A bone-plated counter technique unlocked by Bone Plating.",
            "effect": "Deals 75% ATK damage, raises Zac's DEF, and lowers enemy ATK."
        },
        "first_aid": {
            "description": "Mira's field support technique.",
            "effect": "Restores 24 HP to one living ally and clears poison."
        },
        "shield_bash": {
            "description": "Kael's frontline control strike.",
            "effect": "Deals 75% ATK damage and lowers enemy ATK by 1 stage."
        },
        "protective_guard": {
            "description": "Kael braces himself to hold the front line.",
            "effect": "Raises Kael's DEF by 1 stage."
        }
    }

    @classmethod
    def get_unlocked_mutation_ids(cls, mutation_tree):
        """Return the unlocked mutation ids."""
        if not mutation_tree:
            return set()

        return set(mutation_tree.get_unlocked_nodes())

    @classmethod
    def get_available_skill_ids(cls, mutation_tree):
        """Return the available skill ids."""
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

        if "hardened_body" in unlocked:
            if "thick_hide" in unlocked:
                skill_ids.append("iron_guard")
            else:
                skill_ids.append("guard_stance")

        if "bone_plating" in unlocked:
            skill_ids.append("counter_shell")

        return skill_ids

    @classmethod
    def get_ally_skill_ids(cls, ally_id):
        """Return the ally skill ids."""
        return list(cls.ALLY_LOADOUTS.get(ally_id, ["basic_attack"]))

    @classmethod
    def auto_equip_new_skills(cls, loadout, mutation_tree):
        """Keep the loadout valid after new skills unlock."""
        cleaned = cls.sanitize_loadout(loadout, mutation_tree)

        for skill_id in cls.get_available_skill_ids(mutation_tree):
            if skill_id not in cleaned and len(cleaned) < cls.MAX_LOADOUT_SIZE:
                cleaned.append(skill_id)

        return cls.sanitize_loadout(cleaned, mutation_tree)

    @classmethod
    def sanitize_loadout(cls, loadout, mutation_tree):
        """Remove invalid, duplicate, and extra skills from a loadout."""
        available = cls.get_available_skill_ids(mutation_tree)
        available_set = set(available)

        if not loadout:
            loadout = ["basic_attack"]

        cleaned = []

        for skill_id in loadout:
            replacement_id = cls.UPGRADE_REPLACEMENTS.get(skill_id)

            # Replace old skills only after the upgrade unlocks.
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
        """Create a fresh action dictionary for combat."""
        if skill_id not in cls.SKILL_ACTIONS:
            skill_id = "basic_attack"

        return copy.deepcopy(cls.SKILL_ACTIONS[skill_id])

    @classmethod
    def get_skill_name(cls, skill_id):
        """Return the skill name."""
        return cls.SKILL_ACTIONS.get(
            skill_id,
            cls.SKILL_ACTIONS["basic_attack"]
        ).get("name", skill_id)

    @classmethod
    def get_skill_info(cls, skill_id):
        """Return the skill info."""
        return cls.SKILL_INFO.get(
            skill_id,
            {
                "description": "No description available.",
                "effect": "No effect information available."
            }
        )
