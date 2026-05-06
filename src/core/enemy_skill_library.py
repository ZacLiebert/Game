import copy
import random


class EnemySkillLibrary:
    """
    Central enemy combat action definitions.

    Enemies list skill IDs in data/enemies.json. The combat screen asks this
    library for a weighted action each enemy turn.
    """

    DEFAULT_SKILL_ID = "feral_swipe"

    ACTIONS = {
        "feral_swipe": {
            "name": "Feral Swipe",
            "mult": 0.95,
            "target": "enemy",
            "weight": 6
        },
        "rending_pounce": {
            "name": "Rending Pounce",
            "mult": 1.2,
            "target": "enemy",
            "stage_change": {
                "target": "enemy",
                "stat": "defense",
                "amount": -1
            },
            "weight": 2
        },
        "venom_spit": {
            "name": "Venom Spit",
            "mult": 0.75,
            "target": "enemy",
            "status": {
                "target": "enemy",
                "type": "poison",
                "duration": 3,
                "power": 4,
                "chance": 1.0,
                "apply_chance": 0.75
            },
            "weight": 4
        },
        "quick_strike": {
            "name": "Quick Strike",
            "mult": 0.85,
            "target": "enemy",
            "weight": 5
        },
        "gore": {
            "name": "Gore",
            "mult": 1.05,
            "target": "enemy",
            "weight": 5
        },
        "harden_hide": {
            "name": "Harden Hide",
            "mult": 0,
            "target": "self",
            "stage_change": {
                "target": "self",
                "stat": "defense",
                "amount": 1
            },
            "weight": 2
        },
        "maul": {
            "name": "Maul",
            "mult": 1.25,
            "target": "enemy",
            "weight": 4
        },
        "crushing_roar": {
            "name": "Crushing Roar",
            "mult": 0,
            "target": "enemy",
            "stage_changes": [
                {
                    "target": "enemy",
                    "stat": "attack",
                    "amount": -1
                },
                {
                    "target": "enemy",
                    "stat": "defense",
                    "amount": -1
                }
            ],
            "weight": 2
        },
        "swift_kick": {
            "name": "Swift Kick",
            "mult": 0.8,
            "target": "enemy",
            "weight": 6
        },
        "darting_reflex": {
            "name": "Darting Reflex",
            "mult": 0,
            "target": "self",
            "stage_change": {
                "target": "self",
                "stat": "speed",
                "amount": 1
            },
            "weight": 2
        },
        "sonic_screech": {
            "name": "Sonic Screech",
            "mult": 0.65,
            "target": "enemy",
            "status": {
                "target": "enemy",
                "type": "paralysis",
                "duration": 2,
                "power": 0,
                "chance": 0.3,
                "apply_chance": 0.65
            },
            "stage_change": {
                "target": "enemy",
                "stat": "speed",
                "amount": -1
            },
            "weight": 4
        },
        "chimera_rend": {
            "name": "Chimera Rend",
            "mult": 1.3,
            "target": "enemy",
            "weight": 4
        },
        "toxic_howl": {
            "name": "Toxic Howl",
            "mult": 0.85,
            "target": "enemy",
            "status": {
                "target": "enemy",
                "type": "poison",
                "duration": 3,
                "power": 6,
                "chance": 1.0,
                "apply_chance": 0.8
            },
            "stage_change": {
                "target": "enemy",
                "stat": "speed",
                "amount": -1
            },
            "weight": 3
        },
        "alpha_focus": {
            "name": "Alpha Focus",
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
            ],
            "weight": 2
        }
    }

    @classmethod
    def build_action(cls, skill_id):
        action = cls.ACTIONS.get(skill_id)

        if not action:
            action = cls.ACTIONS[cls.DEFAULT_SKILL_ID]

        return copy.deepcopy(action)

    @classmethod
    def choose_action(cls, enemy):
        skill_ids = getattr(enemy, "enemy_skill_ids", None)

        if not skill_ids:
            skill_ids = [cls.DEFAULT_SKILL_ID]

        actions = [
            cls.build_action(skill_id)
            for skill_id in skill_ids
            if skill_id in cls.ACTIONS
        ]

        if not actions:
            actions = [cls.build_action(cls.DEFAULT_SKILL_ID)]

        weights = [
            max(1, action.get("weight", 1))
            for action in actions
        ]

        return random.choices(actions, weights=weights, k=1)[0]
