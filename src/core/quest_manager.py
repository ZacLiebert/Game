"""Quest progress and story objective helpers."""

import copy


class QuestManager:
    """Tracks the linear main quest chain and current objective."""

    QUESTS = [
        {
            "id": "briefing",
            "title": "Emergency Briefing",
            "description": "Talk to Dr. Biologist at base camp.",
            "objective_type": "talk",
            "target": "Dr. Biologist",
            "required": 1
        },
        {
            "id": "meet_team",
            "title": "Meet the Field Team",
            "description": "Speak with Mira and Kael before leaving camp.",
            "objective_type": "talk",
            "target": ["Mira", "Kael"],
            "required": 2
        },
        {
            "id": "prepare_supplies",
            "title": "Prepare Supplies",
            "description": "Visit Quartermaster Rhea and review combat items.",
            "objective_type": "talk",
            "target": "Quartermaster Rhea",
            "required": 1
        },
        {
            "id": "field_samples",
            "title": "Field Samples",
            "description": "Collect beast materials from wild encounters.",
            "objective_type": "loot",
            "required": 3
        },
        {
            "id": "first_evolution",
            "title": "Combat Evolution",
            "description": "Unlock any two non-basic mutations before challenging the Bear.",
            "objective_type": "mutation",
            "required": 2
        },
        {
            "id": "contain_bear",
            "title": "Contain the Mutant Bear",
            "description": "Defeat the Mutant Bear blocking the eastern trail.",
            "objective_type": "defeat_npc",
            "target": "Mutant Bear",
            "required": 1
        },
        {
            "id": "final_boss",
            "title": "End the Outbreak",
            "description": "Defeat Alpha Chimera and stabilize the island.",
            "objective_type": "defeat_npc",
            "target": "Alpha Chimera",
            "required": 1
        }
    ]

    def __init__(self, mutation_progress_provider=None):
        """Set up initial state."""
        self.quest_states = {}
        self.active_index = 0
        self.mutation_progress_provider = mutation_progress_provider

        for quest in self.QUESTS:
            self.quest_states[quest["id"]] = {
                "progress": 0,
                "completed": False,
                "seen_targets": []
            }

    def set_mutation_progress_provider(self, provider):
        """Set mutation progress provider."""
        self.mutation_progress_provider = provider

    def _count_unlocked_non_basic_mutations(self, unlocked_mutation_ids=None):
        """Count unlocked mutations except Basic Form."""
        if unlocked_mutation_ids is None:
            if not self.mutation_progress_provider:
                unlocked_mutation_ids = []
            else:
                try:
                    unlocked_mutation_ids = self.mutation_progress_provider()
                except Exception:
                    unlocked_mutation_ids = []

        if not isinstance(unlocked_mutation_ids, (list, set, tuple)):
            return 0

        return len({
            str(mutation_id)
            for mutation_id in unlocked_mutation_ids
            if isinstance(mutation_id, str) and mutation_id != "base"
        })

    def sync_active_mutation_progress(self, unlocked_mutation_ids=None):
        """Sync mutation quest progress when it is active."""
        quest = self.get_current_quest()

        if not quest or quest.get("objective_type") != "mutation":
            return False

        changed = self._sync_mutation_quest_state(
            quest,
            unlocked_mutation_ids=unlocked_mutation_ids
        )

        state = self.quest_states[quest["id"]]

        if state["completed"]:
            self._advance_to_next_quest()

        return changed

    def _sync_mutation_quest_state(self, quest, unlocked_mutation_ids=None):
        """Apply the current mutation count to the quest state."""
        state = self.quest_states[quest["id"]]

        if state["completed"]:
            return False

        unlocked_count = self._count_unlocked_non_basic_mutations(
            unlocked_mutation_ids
        )
        new_progress = min(unlocked_count, quest["required"])

        old_progress = state["progress"]
        old_completed = state["completed"]

        state["progress"] = new_progress

        if new_progress >= quest["required"]:
            state["completed"] = True

        return (
            old_progress != state["progress"]
            or old_completed != state["completed"]
        )

    def get_current_quest(self):
        """Return the current quest."""
        if self.active_index >= len(self.QUESTS):
            return None

        return self.QUESTS[self.active_index]

    def get_current_state(self):
        """Return the current state."""
        quest = self.get_current_quest()

        if not quest:
            return None

        return self.quest_states[quest["id"]]

    def get_current_summary(self):
        """Return the current summary."""
        quest = self.get_current_quest()

        if not quest:
            return "Main Quest Complete"

        state = self.quest_states[quest["id"]]
        progress = min(state["progress"], quest["required"])

        return (
            f"{quest['title']}: {quest['description']} "
            f"({progress}/{quest['required']})"
        )

    def is_active(self, quest_id):
        """Return whether is active is true."""
        quest = self.get_current_quest()
        return quest is not None and quest["id"] == quest_id

    def is_completed(self, quest_id):
        """Return whether is completed is true."""
        state = self.quest_states.get(quest_id)
        return bool(state and state["completed"])

    def is_story_complete(self):
        """Return whether is story complete is true."""
        return self.active_index >= len(self.QUESTS)

    def record_talk(self, npc_name):
        """Record progress from talking to an NPC."""
        return self._record_progress(
            "talk",
            target=npc_name,
            amount=1
        )

    def record_loot(self, amount=1):
        """Record progress from collecting loot."""
        return self._record_progress("loot", amount=amount)

    def record_mutation(self, mutation_id):
        """Record progress from unlocking a mutation."""
        if mutation_id == "base":
            return False

        if self.mutation_progress_provider:
            return self.sync_active_mutation_progress()

        return self._record_progress("mutation", amount=1)

    def record_defeated_npc(self, npc_name):
        """Record progress from defeating an NPC."""
        return self._record_progress(
            "defeat_npc",
            target=npc_name,
            amount=1
        )

    def _record_progress(self, objective_type, target=None, amount=1):
        """Update the active quest if the action matches it."""
        quest = self.get_current_quest()

        if not quest:
            return False

        if quest["objective_type"] != objective_type:
            return False

        state = self.quest_states[quest["id"]]

        if state["completed"]:
            return False

        quest_target = quest.get("target")

        if objective_type == "talk":
            valid_targets = quest_target
            if isinstance(valid_targets, str):
                valid_targets = [valid_targets]

            if valid_targets and target not in valid_targets:
                return False

            if target in state["seen_targets"]:
                return False

            state["seen_targets"].append(target)
        elif quest_target and quest_target != target:
            return False

        state["progress"] += amount

        if state["progress"] >= quest["required"]:
            state["progress"] = quest["required"]
            state["completed"] = True
            self._advance_to_next_quest()

        return True

    def _advance_to_next_quest(self):
        """Move to the next quest in the story chain."""
        while self.active_index < len(self.QUESTS):
            quest = self.QUESTS[self.active_index]
            quest_id = quest["id"]
            state = self.quest_states[quest_id]

            if state["completed"]:
                self.active_index += 1
                continue

            if (
                quest.get("objective_type") == "mutation"
                and self.mutation_progress_provider
            ):
                self._sync_mutation_quest_state(quest)

                if state["completed"]:
                    self.active_index += 1
                    continue

            break

    def export_state(self):
        """Return save-ready state data."""
        return {
            "active_index": self.active_index,
            "quest_states": copy.deepcopy(self.quest_states)
        }

    def import_state(self, data):
        """Restore state from save data."""
        if not data:
            return

        saved_states = data.get("quest_states", {})

        for quest in self.QUESTS:
            quest_id = quest["id"]
            saved_state = saved_states.get(quest_id, {})
            state = self.quest_states[quest_id]

            state["progress"] = int(saved_state.get("progress", state["progress"]))
            state["completed"] = bool(saved_state.get("completed", state["completed"]))

            seen_targets = saved_state.get("seen_targets", state["seen_targets"])
            if isinstance(seen_targets, list):
                state["seen_targets"] = [str(name) for name in seen_targets]

        self.active_index = int(data.get("active_index", 0))
        self.active_index = max(0, min(self.active_index, len(self.QUESTS)))
        self._advance_to_next_quest()
