from src.data_structures.max_heap import MaxHeap

class CombatManager:
    """
    Manages a 3vs3 turn-based battle.
    Uses a Max Heap to coordinate turns for all 6 entities based on Speed.
    """
    def __init__(self, player_team, enemy_team):
        """
        Args:
            player_team (list): Exactly 3 Player Entity objects.
            enemy_team (list): Exactly 3 Monster Entity objects.
        """
        self.player_team = player_team
        self.enemy_team = enemy_team
        self.turn_queue = MaxHeap()
        self.round_count = 0

    def prepare_round(self):
        """
        Re-populates the Max Heap with all surviving members from both teams.
        This handles up to 6 entities in a single priority queue.
        """
        self.round_count += 1
        self.turn_queue = MaxHeap()
        
        # Insert all living players into the turn queue
        for player in self.player_team:
            if player.is_alive():
                self.turn_queue.insert(player)
                
        # Insert all living enemies into the turn queue
        for enemy in self.enemy_team:
            if enemy.is_alive():
                self.turn_queue.insert(enemy)

    def get_next_in_line(self):
        """Extracts the fastest remaining entity for the current turn."""
        return self.turn_queue.extract_max()

    def get_valid_targets(self, target_team):
        """
        Returns a list of entities in the target team that are still alive.
        Useful for the UI to show which enemies can be clicked/attacked.
        """
        return [entity for entity in target_team if entity.is_alive()]

    def check_battle_status(self):
        """Determines if a team has been completely defeated."""
        if not self.get_valid_targets(self.enemy_team):
            return "VICTORY"
        if not self.get_valid_targets(self.player_team):
            return "DEFEAT"
        return "ONGOING"