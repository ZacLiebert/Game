"""Enemy combat skills and AI scoring."""

import copy
import random


class EnemySkillLibrary:
    """Builds enemy skills and chooses AI actions during combat."""

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

    STAT_UTILITY = {
        "attack": 18,
        "defense": 12,
        "speed": 10
    }

    @classmethod
    def build_action(cls, skill_id):
        """Create a fresh enemy action dictionary."""
        action = cls.ACTIONS.get(skill_id)

        if not action:
            action = cls.ACTIONS[cls.DEFAULT_SKILL_ID]

        return copy.deepcopy(action)

    @classmethod
    def _get_enemy_actions(cls, enemy):
        """Return the enemy actions."""
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

        return actions

    @classmethod
    def choose_action(cls, enemy, valid_targets=None):
        """Choose an enemy action for older and newer callers."""
        if valid_targets:
            action, _target = cls.choose_action_and_target(enemy, valid_targets)
            return action

        actions = cls._get_enemy_actions(enemy)
        weights = [
            max(1, action.get("weight", 1))
            for action in actions
        ]
        return random.choices(actions, weights=weights, k=1)[0]

    @classmethod
    def choose_action_and_target(cls, enemy, valid_targets):
        """Choose the best enemy skill and target by score."""
        living_targets = [
            target for target in valid_targets
            if target is not None and target.is_alive()
        ]

        actions = cls._get_enemy_actions(enemy)

        if not living_targets:
            return actions[0], enemy

        best_score = None
        best_action = None
        best_target = None

        for action in actions:
            possible_targets = [enemy]
            if action.get("target") != "self":
                possible_targets = living_targets

            for target in possible_targets:
                score = cls._score_action(enemy, target, action)

                # Small random tie-breaker keeps AI from feeling rigid.
                score += random.uniform(0.0, 1.0)

                if best_score is None or score > best_score:
                    best_score = score
                    best_action = action
                    best_target = target

        return best_action, best_target

    @classmethod
    def _score_action(cls, enemy, target, action):
        """Score one enemy action against one target."""
        score = float(action.get("weight", 1)) * 0.75

        damage_mult = action.get("mult", 0)

        if target is not None and damage_mult > 0:
            expected_damage = cls._estimate_damage(enemy, target, damage_mult)
            score += expected_damage * 4.0

            hp_ratio = cls._hp_ratio(target)
            score += (1.0 - hp_ratio) * 10.0

            if expected_damage >= target.current_hp:
                score += 75.0

            # Prefer dangerous or fragile targets.
            score += getattr(target, "attack", 1) * 0.25
            score += max(0, 8 - getattr(target, "defense", 1)) * 0.4

        status = action.get("status")
        if status:
            status_target = enemy if status.get("target") == "self" else target
            score += cls._score_status(status_target, status)

        stage_changes = cls._get_stage_changes(action)
        for change in stage_changes:
            stage_target = enemy if change.get("target") == "self" else target
            score += cls._score_stage_change(stage_target, change)

        return score

    @classmethod
    def _estimate_damage(cls, attacker, target, mult):
        """Estimate damage before choosing an action."""
        raw_damage = int(getattr(attacker, "attack", 1) * mult)
        defense = getattr(target, "defense", 0)
        return max(1, raw_damage - defense)

    @classmethod
    def _hp_ratio(cls, entity):
        """Return current HP as a 0 to 1 ratio."""
        max_hp = max(1, getattr(entity, "max_hp", 1))
        current_hp = max(0, getattr(entity, "current_hp", 0))
        return current_hp / max_hp

    @classmethod
    def _score_status(cls, target, status):
        """Score a poison or paralysis effect."""
        if target is None or not target.is_alive():
            return 0.0

        status_type = status.get("type")
        apply_chance = status.get("apply_chance", 1.0)
        duration = status.get("duration", 1)
        power = status.get("power", 0)
        chance = status.get("chance", 1.0)

        if hasattr(target, "has_status") and target.has_status(status_type):
            return -18.0

        if status_type == "poison":
            return power * duration * apply_chance * 1.4

        if status_type == "paralysis":
            return 28.0 * chance * apply_chance + duration * 2.0

        return 8.0 * apply_chance

    @classmethod
    def _get_stage_changes(cls, action):
        """Return the stage changes."""
        stage_changes = action.get("stage_changes")

        if stage_changes is None:
            single_change = action.get("stage_change")
            stage_changes = [single_change] if single_change else []

        return stage_changes

    @classmethod
    def _score_stage_change(cls, target, change):
        """Score a temporary buff or debuff."""
        if target is None or not target.is_alive():
            return 0.0

        stat_name = change.get("stat")
        amount = change.get("amount", 0)
        current_stage = getattr(target, "stat_stages", {}).get(stat_name, 0)
        min_stage = getattr(target, "MIN_STAGE", -2)
        max_stage = getattr(target, "MAX_STAGE", 3)
        stat_value = getattr(target, stat_name, 1)
        base_value = cls.STAT_UTILITY.get(stat_name, 8)

        if amount > 0:
            if current_stage >= max_stage:
                return -20.0

            # Defensive buffs matter more when hurt.
            remaining_room = max_stage - current_stage
            urgency = 1.0
            if stat_name == "defense":
                urgency += (1.0 - cls._hp_ratio(target)) * 0.75

            return base_value * min(amount, remaining_room) * urgency

        if amount < 0:
            if current_stage <= min_stage:
                return -20.0

            remaining_room = current_stage - min_stage
            threat_bonus = min(12.0, stat_value * 0.35)
            return (base_value + threat_bonus) * min(abs(amount), remaining_room)

        return 0.0
