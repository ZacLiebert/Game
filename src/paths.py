"""Shared project paths."""

import sys
from pathlib import Path


if getattr(sys, "frozen", False):
    ROOT_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    RUNTIME_DIR = Path(sys.executable).resolve().parent
else:
    ROOT_DIR = Path(__file__).resolve().parent.parent
    RUNTIME_DIR = ROOT_DIR

ASSETS_DIR = ROOT_DIR / "assets"
DATA_DIR = ROOT_DIR / "data"
SAVE_DIR = RUNTIME_DIR / "save_data"

MAPS_DIR = ASSETS_DIR / "maps"
SPRITES_DIR = ASSETS_DIR / "sprites"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
AUDIO_DIR = ASSETS_DIR / "audio"
BGM_DIR = AUDIO_DIR / "bgm"
SFX_DIR = AUDIO_DIR / "sfx"

MAP_DATA_FILE = MAPS_DIR / "maps.json"
DEFAULT_SAVE_FILE = SAVE_DIR / "save1.dat"

ITEMS_DATA_FILE = DATA_DIR / "items.json"
ENEMIES_DATA_FILE = DATA_DIR / "enemies.json"
ALLIES_DATA_FILE = DATA_DIR / "allies.json"
MUTATIONS_DATA_FILE = DATA_DIR / "mutations.json"

ASSET_SEARCH_DIRS = (
    ASSETS_DIR,
    MAPS_DIR,
    BACKGROUNDS_DIR,
    SPRITES_DIR,
    SPRITES_DIR / "characters",
    SPRITES_DIR / "enemies",
)


def resolve_asset_path(filename, search_dirs=None):
    """Return the best existing path for an asset."""
    asset_path = Path(filename)

    if asset_path.is_absolute():
        return asset_path

    base_dirs = search_dirs if search_dirs is not None else ASSET_SEARCH_DIRS
    candidates = [ASSETS_DIR / asset_path]

    for directory in base_dirs:
        candidates.append(directory / asset_path)

    candidates.append(ROOT_DIR / asset_path)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]
