# Mutation RPG

A Python/Pygame turn-based RPG prototype set on Quarantine Island. The player explores a TMX map, fights mutated enemies, collects materials, unlocks mutation upgrades, manages a skill loadout, and clears the final containment objective.

## Requirements

- Python 3.10 or newer
- `pygame==2.6.1`
- `pytmx==3.32`

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Run the command from the project root folder, the same folder that contains `main.py`.

## Controls

| Key | Action |
| --- | --- |
| Arrow keys / WASD | Move Zac on the map |
| E | Interact with NPCs, shop, and boss encounters |
| Enter | Confirm menu/action |
| Esc | Back / close current screen |
| I | Open inventory |
| M | Open mutation tree |
| K | Open skill loadout |
| Space | Toggle selected skill in the loadout screen |
| P | Mute / unmute all audio |

## Audio

The game includes looping background music and sound effects:

- `forest.ogg`: warm, non-scary main menu and non-map menu ambience
- `map_relax.ogg`: melodic RPG-style overworld loop for map exploration
- `battle.ogg`: normal battle BGM
- `boss.ogg`: boss battle BGM
- Click, alert, hit, success, error, and game-over SFX
- Press `P` at any time to mute or unmute audio

Map-related overlay screens such as dialogue, inventory, mutation, shop, and skill loadout keep the melodic map music instead of switching back to the menu track.

## Animation

The game includes lightweight animations to make combat and exploration feel less static:

- Player walking animation on the overworld map using Zac's sprite sheet
- Idle bobbing for combat sprites
- Attack lunge when a unit uses a skill
- Target hit flash and small battlefield shake on damage
- Floating damage, heal, status, buff, and debuff popups

## Inventory and Consumables

The inventory has multiple consumable tiers for combat strategy:

- Med Kits restore 20, 30, or 50 HP.
- Adrenal Serum I/II raises Attack by +1 or +2 combat stages.
- Sprint Serum I/II raises Speed by +1 or +2 combat stages.
- Revive Shot I/II revives a defeated ally with 30 or 60 HP.

In combat, Zac can choose **Items**, select a consumable, then choose an ally target. Healing and buff items target living allies, while revive items target defeated allies. The shop sells all consumable tiers, and the player starts with a few basic supplies.

## Story and Objective Flow

Zac wakes inside the sealed Quarantine Woods after a mutation outbreak escapes from the research lab. Dr. Biologist explains that Zac can stabilize mutation samples because an old stabilizer trial left adaptive markers in his cells. Mira, the field medic, and Kael, the frontline security defender, join Zac as the last containment team.

1. Talk to Dr. Biologist at base camp to learn the outbreak story.
2. Speak with Mira and Kael so the player understands why both allies are in the party.
3. Visit Quartermaster Rhea to review healing, buff, speed, and revive items.
4. Fight wild beasts and collect mutation materials.
5. Unlock two non-basic mutations and equip useful combat skills.
6. Defeat the Mutant Bear blocking the clean route; it now drops enough Bear Bone for Bone Plating.
7. Unlock at least four non-basic mutations, equip a non-basic skill, then reach the containment lab and defeat the Alpha Chimera.

## Map Story Blockers

The overworld now shows the two main story blockers directly on the map:

- Mutant Bear stands across the eastern trail and blocks movement until the `Contain the Mutant Bear` quest is active and completed. The Bear fight is gated behind two non-basic mutations so the boss does not appear too early.
- Alpha Chimera stands at the containment lab entrance and blocks the final route until the `End the Outbreak` quest is active. The final fight also requires four non-basic mutations and at least one equipped non-basic skill.

Before the correct quest is active, pressing `E` near a blocker shows a warning instead of starting the fight. After winning the battle, the blocker is marked defeated, disappears from the map, and the route opens.

## Algorithms / Data Structures

The project includes these DSA-focused parts that are actually implemented and used in gameplay:

- Custom Hash Table with chaining, resizing, rehashing, and safe lookup helpers
- Compressed inventory stack storage using custom HashTable counts
- Mutation Tree with DFS traversal, indexed node/parent lookup, and JSON validation
- Optimized Quick Sort inventory sorting plus custom render-order sorting
- KMP inventory search with one-time LPS preprocessing per query
- Greedy utility-based enemy AI for smart skill selection
- Manual linear turn selection for 3vs3 combat order by speed

Enemy combat is not purely random. Each enemy evaluates its available skills against the living player targets and chooses the highest-scoring skill-target pair based on expected damage, kill potential, status value, and buff/debuff usefulness. Mira now has First Aid, Kael has Shield Bash / Protective Guard, and Zac's defensive mutation path unlocks Guard Stance / Iron Guard / Counter Shell. 

Random encounters also use light regional weighting so material farming feels less arbitrary: cave-side paths favor bats/snakes, forest-edge paths favor boars/rabbits/tigers, and the eastern pass can spawn bears after the Bear boss is defeated.

## Project Structure

```text
MutationRPG/
├── assets/          # Sprites, backgrounds, TMX map assets, audio, and credited assets
├── data/            # JSON data for allies, enemies, items, and mutations
├── src/             # Game source code
├── main.py          # Entry point
├── requirements.txt # Python dependencies
└── README.md        # Run instructions and project notes
```

## Notes for Reviewers

- This submitted package intentionally excludes Python cache files, compiled bytecode, local save files, and logs. Audio is included and used in-game.
- No local save file is submitted; the game creates `save_data/save1.dat` during play when saving.
- The TMX map uses credited Python-Monsters / Clean Code-style visual assets, with a custom Quarantine Island layout for this project.

## Credits

Map, tileset, and object art:

- Python-Monsters / Clean Code project assets
- Artwork credited by the original project to Scarloxy / MPWSP01
- Used here as a custom Quarantine Woods / Quarantine Island map, not by copying the original `world.tmx` layout.

Code integration:

- Uses Tiled TMX map structure and PyTMX loading approach.

## NPC and Map Monster Sprites

This build integrates the uploaded **2D Top Down Pixel Art Characters** asset pack by **Jephed / Game Between The Lines**. The pack is used for the visible MapScreen characters:

- Dr. Biologist
- Mira, field medic with First Aid support
- Kael, frontline defender with Shield Bash and Protective Guard
- Quartermaster Rhea
- Sample Herbalist
- Mutant Bear map blocker
- Alpha Chimera map blocker

The final submitted project keeps only the processed in-game NPC sheets and credits the original asset pack in `assets/credits.txt`.

## MapScreen animations

The overworld now includes animated NPC/monster idle frames, subtle bobbing, pulsing boss-blocker auras, floating exclamation markers when Zac approaches story blockers, animated tall-grass encounter shimmer, and a short flash/letterbox transition before combat.

## Package Contents

The submitted package keeps only the source code, data files, tests, documentation, and assets used by the current game build. Python cache files, local save files, logs, unused art, and internal fix notes are not included.


## Build EXE

To create a Windows executable, run `build_exe.bat` on Windows. The output file will be `dist/MutationRPG.exe`. See `BUILD_EXE.md` for details.
