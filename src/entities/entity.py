class Entity:
    def __init__(self, entity_id, name, hp, attack, defense, speed, sprite_name, loot_id=None):
        self.entity_id = entity_id
        self.name = name
        self.max_hp = hp
        self.current_hp = hp
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.sprite_name = sprite_name  # NEW: Loaded from JSON
        self.loot_id = loot_id 

    def is_alive(self):
        return self.current_hp > 0

    def take_damage(self, amount):
        damage = max(1, amount - self.defense)
        self.current_hp -= damage
        return damage

    def heal(self, amount):
        self.current_hp = min(self.max_hp, self.current_hp + amount)