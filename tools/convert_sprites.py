from pathlib import Path
from PIL import Image


ROOT_DIR = Path(__file__).resolve().parents[1]


# ============================================================
# TARGET FORMAT USED BY THE GAME
# ============================================================

TARGET_FRAME_SIZE = 64
TARGET_ROWS = 4
TARGET_COLS = 6

# Game format:
# Row 0 = Down
# Row 1 = Left
# Row 2 = Right
# Row 3 = Up
TARGET_ORDER = ["down", "left", "right", "up"]


# ============================================================
# SPRITE CONFIG
# ============================================================

SPRITES = [
    {
        "name": "rabbit",
        "source": "assets/raw/rabbit_original.png",
        "rows": 4,
        "cols": 5,
        "source_order": ["down", "up", "left", "right"],
        "output": "assets/sprites/enemies/rabbit.png",
    }
]


def crop_source_frames(image, rows, cols):
    sheet_w, sheet_h = image.size

    frame_w = sheet_w // cols
    frame_h = sheet_h // rows

    frames = []

    for row in range(rows):
        row_frames = []

        for col in range(cols):
            left = col * frame_w
            top = row * frame_h
            right = left + frame_w
            bottom = top + frame_h

            frame = image.crop((left, top, right, bottom)).convert("RGBA")
            row_frames.append(frame)

        frames.append(row_frames)

    return frames


def normalize_frame_count(frames, target_count):
    """
    Converts any number of frames into exactly target_count frames.
    If fewer frames: repeat them.
    If more frames: sample evenly.
    """
    if not frames:
        raise ValueError("No frames found.")

    source_count = len(frames)

    if source_count == target_count:
        return frames

    normalized = []

    if source_count < target_count:
        for i in range(target_count):
            normalized.append(frames[i % source_count])
    else:
        for i in range(target_count):
            source_index = int(i * source_count / target_count)
            normalized.append(frames[source_index])

    return normalized


def convert_sprite(config):
    source_path = ROOT_DIR / config["source"]
    output_path = ROOT_DIR / config["output"]

    if not source_path.exists():
        print(f"[SKIP] Missing source file: {source_path}")
        return

    image = Image.open(source_path).convert("RGBA")

    source_frames = crop_source_frames(
        image,
        rows=config["rows"],
        cols=config["cols"]
    )

    source_order = config["source_order"]

    output_sheet = Image.new(
        "RGBA",
        (
            TARGET_FRAME_SIZE * TARGET_COLS,
            TARGET_FRAME_SIZE * TARGET_ROWS
        ),
        (0, 0, 0, 0)
    )

    for target_row, direction in enumerate(TARGET_ORDER):
        if direction not in source_order:
            raise ValueError(
                f"{config['name']} is missing direction '{direction}' "
                f"in source_order={source_order}"
            )

        source_row = source_order.index(direction)
        frames = source_frames[source_row]

        frames = normalize_frame_count(frames, TARGET_COLS)

        for col, frame in enumerate(frames):
            frame = frame.resize(
                (TARGET_FRAME_SIZE, TARGET_FRAME_SIZE),
                Image.Resampling.NEAREST
            )

            x = col * TARGET_FRAME_SIZE
            y = target_row * TARGET_FRAME_SIZE

            output_sheet.paste(frame, (x, y), frame)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_sheet.save(output_path)

    print(f"[OK] Created {output_path}")


def main():
    for config in SPRITES:
        convert_sprite(config)


if __name__ == "__main__":
    main()
