import pygame
from src.graphics.sprite_manager import SpriteManager


class NPC:
    """
    NPC / monster on the overworld map.

    Supports:
    - Farm monsters
    - Boss monsters
    - Dialogue NPCs
    - Shop NPCs
    - Static sprites
    - 4x6 sprite sheets

    Important:
    - self.rect is the NPC anchor position.
    - self.collision_rect is the foot/body hitbox used for collision.
    """

    def __init__(
        self,
        name,
        x,
        y,
        enemy_ids=None,
        sprite_filename="slime.png",
        npc_type="farm",
        sprite_sheet=False,
        dialogue=None,
        shop_items=None
    ):
        self.name = name

        # Position
        self.x = float(x)
        self.y = float(y)

        # Anchor rect.
        # Used as the NPC's map position and draw reference.
        self.rect = pygame.Rect(x, y, 40, 40)

        # NPC collision box.
        # This is larger than the tiny foot-only hitbox so Zac will not
        # visually stick into the NPC sprite, but it is still smaller than
        # the full 64x64 sprite area so it does not feel like a huge wall.
        self.collision_rect = pygame.Rect(
            x + 6,
            y + 18,
            52,
            42
        )

        # Enemy IDs used when entering combat.
        self.enemy_ids = enemy_ids if enemy_ids else []

        # NPC type:
        # "farm" = can be battled repeatedly
        # "boss" = disappears after victory
        # "dialogue" = talks to player
        # "shop" = opens shop screen
        self.npc_type = npc_type

        # Dialogue / shop data.
        self.dialogue = dialogue if dialogue else []
        self.shop_items = shop_items if shop_items else []

        # Optional quest gate.
        # MapScreen may set this after creating NPC.
        self.required_quest = None

        # State
        self.defeated = False

        # Sprite settings
        self.sprite_filename = sprite_filename
        self.sprite_sheet = sprite_sheet

        self.sprite_width = 84
        self.sprite_height = 84

        self.draw_offset_x = -22
        self.draw_offset_y = -18

        # Load sprite
        self.sprite = self._load_sprite()

    def _sync_collision_rect(self):
        """
        Keeps the NPC collision box aligned with the anchor rect.
        Useful if NPC movement is added later.
        """
        self.collision_rect.x = self.rect.x + 6
        self.collision_rect.y = self.rect.y + 18

    def _load_sprite(self):
        """
        Loads either:
        - A normal static image, or
        - The first frame of a 4x6 sprite sheet.
        """
        if self.sprite_sheet:
            sheet = SpriteManager.load_sprite_sheet(
                self.sprite_filename,
                rows=4,
                cols=6,
                target_width=self.sprite_width,
                target_height=self.sprite_height
            )

            # Row 0, frame 0 = facing down / idle frame.
            return sheet[0][0]

        return SpriteManager.get_sprite(
            self.sprite_filename,
            width=self.sprite_width,
            height=self.sprite_height
        )

    def update_ai(self, player_rect, collision_rects):
        """
        NPCs currently stand still.

        This method remains so MapScreen can call npc.update_ai()
        without causing errors.
        """
        self._sync_collision_rect()
        return

    def draw(self, surface, camera=None):
        """
        Draws the NPC.

        Note:
        MapScreen usually draws NPCs itself because it needs to offset by
        play_area. This method is still kept for compatibility.
        """
        if self.defeated:
            return

        draw_rect = camera.apply(self.rect) if camera else self.rect

        surface.blit(
            self.sprite,
            (
                draw_rect.x + self.draw_offset_x,
                draw_rect.y + self.draw_offset_y
            )
        )