from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent

ASSETS_DIR = ROOT_DIR / "assets"
DATA_DIR = ROOT_DIR / "data"
SAVE_DIR = ROOT_DIR / "save_data"

MAPS_DIR = ASSETS_DIR / "maps"
SPRITES_DIR = ASSETS_DIR / "sprites"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
RAW_ASSETS_DIR = ASSETS_DIR / "raw"

MAP_DATA_FILE = MAPS_DIR / "maps.json"
LEGACY_MAP_DATA_FILE = ASSETS_DIR / "maps.json"
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
    SPRITES_DIR / "tiles",
    RAW_ASSETS_DIR,
)


def resolve_asset_path(filename, search_dirs=None):
    """
    Finds an asset by filename while allowing assets to live in clean subfolders.
    """
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


def resolve_map_path(filename):
    return resolve_asset_path(
        filename,
        search_dirs=(
            MAPS_DIR,
            ASSETS_DIR,
        )
    )
