import copy


class QuestManager:
    """
    Tracks the main story quest chain.

    The chain is intentionally linear so the player always has one clear
    objective while the existing systems remain simple.
    """

    QUESTS = [
        {
            "id": "field_samples",
            "title": "Field Samples",
            "description": "Collect beast materials from wild encounters.",
            "objective_type": "loot",
            "required": 3
        },
        {
            "id": "first_evolution",
            "title": "First Evolution",
            "description": "Unlock any non-basic mutation in the mutation chamber.",
            "objective_type": "mutation",
            "required": 1
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

    def __init__(self):
        self.quest_states = {}
        self.active_index = 0

        for quest in self.QUESTS:
            self.quest_states[quest["id"]] = {
                "progress": 0,
                "completed": False
            }

    def get_current_quest(self):
        if self.active_index >= len(self.QUESTS):
            return None

        return self.QUESTS[self.active_index]

    def get_current_state(self):
        quest = self.get_current_quest()

        if not quest:
            return None

        return self.quest_states[quest["id"]]

    def get_current_summary(self):
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
        quest = self.get_current_quest()
        return quest is not None and quest["id"] == quest_id

    def is_completed(self, quest_id):
        state = self.quest_states.get(quest_id)
        return bool(state and state["completed"])

    def is_story_complete(self):
        return self.active_index >= len(self.QUESTS)

    def record_loot(self, amount=1):
        return self._record_progress("loot", amount=amount)

    def record_mutation(self, mutation_id):
        if mutation_id == "base":
            return False

        return self._record_progress("mutation", amount=1)

    def record_defeated_npc(self, npc_name):
        return self._record_progress(
            "defeat_npc",
            target=npc_name,
            amount=1
        )

    def _record_progress(self, objective_type, target=None, amount=1):
        quest = self.get_current_quest()

        if not quest:
            return False

        if quest["objective_type"] != objective_type:
            return False

        if quest.get("target") and quest.get("target") != target:
            return False

        state = self.quest_states[quest["id"]]

        if state["completed"]:
            return False

        state["progress"] += amount

        if state["progress"] >= quest["required"]:
            state["progress"] = quest["required"]
            state["completed"] = True
            self._advance_to_next_quest()

        return True

    def _advance_to_next_quest(self):
        while self.active_index < len(self.QUESTS):
            quest_id = self.QUESTS[self.active_index]["id"]

            if not self.quest_states[quest_id]["completed"]:
                break

            self.active_index += 1

    def export_state(self):
        return {
            "active_index": self.active_index,
            "quest_states": copy.deepcopy(self.quest_states)
        }

    def import_state(self, data):
        if not data:
            return

        saved_states = data.get("quest_states", {})

        for quest in self.QUESTS:
            quest_id = quest["id"]
            saved_state = saved_states.get(quest_id, {})
            state = self.quest_states[quest_id]

            state["progress"] = int(saved_state.get("progress", state["progress"]))
            state["completed"] = bool(saved_state.get("completed", state["completed"]))

        self.active_index = int(data.get("active_index", 0))
        self.active_index = max(0, min(self.active_index, len(self.QUESTS)))
        self._advance_to_next_quest()
