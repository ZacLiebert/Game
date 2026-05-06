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

        # Collision hitbox
        self.rect = pygame.Rect(x, y, 40, 40)

        # Enemy IDs used when entering combat
        self.enemy_ids = enemy_ids if enemy_ids else []

        # NPC type:
        # "farm" = can be battled repeatedly
        # "boss" = disappears after victory
        # "dialogue" = talks to player
        # "shop" = opens shop screen
        self.npc_type = npc_type

        # Dialogue / shop data
        self.dialogue = dialogue if dialogue else []
        self.shop_items = shop_items if shop_items else []

        # State
        self.defeated = False

        # Sprite settings
        self.sprite_filename = sprite_filename
        self.sprite_sheet = sprite_sheet

        self.sprite_width = 64
        self.sprite_height = 64

        # Sprite is larger than hitbox, so offset it.
        self.draw_offset_x = -12
        self.draw_offset_y = -24

        # Load sprite
        self.sprite = self._load_sprite()

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

            # Row 0, frame 0 = facing down / idle frame
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
        return

    def draw(self, surface, camera=None):
        """
        Draws the NPC.
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