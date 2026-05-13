"""Turn-order helpers for combat."""


class CombatManager:
    """Controls turn order and battle status for small 3v3 fights."""

    def __init__(self, player_team, enemy_team):
        """Set up initial state."""
        self.player_team = player_team
        self.enemy_team = enemy_team
        self._remaining_entities = []
        self.round_count = 0

    def _team_order(self):
        """Return the stable turn order used to break speed ties."""
        return self.player_team + self.enemy_team

    def _add_remaining_entity(self, entity):
        """Add remaining entity."""
        for existing in self._remaining_entities:
            if existing is entity:
                return

        self._remaining_entities.append(entity)

    def prepare_round(self):
        """Start a new round with all living combatants."""
        self.round_count += 1
        self._remaining_entities = []

        for entity in self._team_order():
            if entity.is_alive():
                self._add_remaining_entity(entity)

    def get_next_in_line(self):
        """Return the next in line."""
        self.remove_dead_from_queue()

        if not self._remaining_entities:
            return None

        best_index = 0
        best_entity = self._remaining_entities[0]

        for index in range(1, len(self._remaining_entities)):
            candidate = self._remaining_entities[index]
            if candidate.speed > best_entity.speed:
                best_index = index
                best_entity = candidate

        return self._remaining_entities.pop(best_index)

    def refresh_turn_order(self):
        """Refresh remaining turns after deaths or speed changes."""
        self.remove_dead_from_queue()

    def remove_dead_from_queue(self):
        """Remove defeated combatants from the turn list."""
        living_entities = []

        for entity in self._remaining_entities:
            if entity.is_alive():
                living_entities.append(entity)

        self._remaining_entities = living_entities

    def get_valid_targets(self, target_team):
        """Return the valid targets."""
        return [
            entity for entity in target_team
            if entity.is_alive()
        ]

    def check_battle_status(self):
        """Return whether the player won, lost, or battle continues."""
        if not self.get_valid_targets(self.enemy_team):
            return "VICTORY"

        if not self.get_valid_targets(self.player_team):
            return "DEFEAT"

        return "ONGOING"
