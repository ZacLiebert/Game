class CombatManager:
    """
    Manages a 3vs3 turn-based battle.

    This version uses linear scan instead of MaxHeap.

    Why:
    - Combat only has up to 6 entities.
    - Speed can change during a round.
    - Linear scan always uses the latest speed value.
    - Simpler and less bug-prone than updating heap priority.
    """

    def __init__(self, player_team, enemy_team):
        self.player_team = player_team
        self.enemy_team = enemy_team

        # Remaining entities that have not acted in the current round.
        self.turn_queue = []

        self.round_count = 0

    def prepare_round(self):
        """
        Starts a new round and collects all living entities.
        """
        self.round_count += 1
        self.turn_queue = []

        for player in self.player_team:
            if player.is_alive():
                self.turn_queue.append(player)

        for enemy in self.enemy_team:
            if enemy.is_alive():
                self.turn_queue.append(enemy)

    def get_next_in_line(self):
        """
        Finds and removes the living entity with the highest current speed.

        Since speed can change during combat, this method scans the remaining
        turn_queue every time. That means speed buffs/debuffs affect the current
        round immediately if the target has not acted yet.
        """
        self.remove_dead_from_queue()

        if not self.turn_queue:
            return None

        best_index = 0
        best_entity = self.turn_queue[0]

        for i in range(1, len(self.turn_queue)):
            entity = self.turn_queue[i]

            if entity.speed > best_entity.speed:
                best_index = i
                best_entity = entity

        return self.turn_queue.pop(best_index)

    def refresh_turn_order(self):
        """
        Keeps compatibility with CombatScreen.

        With linear scan, we do not need to rebuild a heap.
        We only remove dead entities. The next get_next_in_line() call will
        automatically use the latest speed values.
        """
        self.remove_dead_from_queue()

    def remove_dead_from_queue(self):
        """
        Removes dead entities from the remaining turn queue.
        """
        self.turn_queue = [
            entity for entity in self.turn_queue
            if entity.is_alive()
        ]

    def get_valid_targets(self, target_team):
        """
        Returns living entities in the target team.
        """
        return [
            entity for entity in target_team
            if entity.is_alive()
        ]

    def check_battle_status(self):
        """
        Determines whether the battle is over.
        """
        if not self.get_valid_targets(self.enemy_team):
            return "VICTORY"

        if not self.get_valid_targets(self.player_team):
            return "DEFEAT"

        return "ONGOING"