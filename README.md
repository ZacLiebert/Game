# Mutation RPG

## Project Layout

```text
main.py                  # Game entrypoint
src/
  core/                  # Game session, database, combat, inventory, skills
  data_structures/       # DSA implementations used by the project
  entities/              # Player, NPC, combat entity, item models
  graphics/              # Camera, tilemap, sprite loading
  screens/               # Pygame screens / UI flow
  ui/                    # Shared theme and widgets
  paths.py               # Central project paths and asset resolver
assets/
  backgrounds/           # Battle/map backgrounds
  maps/                  # Map JSON and tile text files
  raw/                   # Source art before conversion
  sprites/
    characters/
    enemies/
    tiles/
data/                    # Gameplay JSON data
save_data/               # Encrypted save files
tools/                   # Development helper scripts
```

Run the game:

```bash
python main.py
```
