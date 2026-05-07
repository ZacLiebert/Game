# fix_project_fonts.py

from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"

TARGET_PREFIX = "pygame.font.SysFont("


def find_matching_call_end(text, start_index):
    """
    Finds the closing parenthesis index for pygame.font.SysFont(...).
    start_index must point to the start of TARGET_PREFIX.
    """
    open_paren_index = start_index + len(TARGET_PREFIX) - 1
    depth = 0

    for i in range(open_paren_index, len(text)):
        char = text[i]

        if char == "(":
            depth += 1

        elif char == ")":
            depth -= 1

            if depth == 0:
                return i

    return -1


def replace_sysfont_none_calls(text):
    """
    Replaces:
        pygame.font.SysFont(None, SIZE)
    with:
        get_font(SIZE)

    Also supports:
        pygame.font.SysFont(None, SIZE, bold=True)
    becoming:
        get_font(SIZE, bold=True)
    """
    output = []
    index = 0
    changed = False

    while True:
        start = text.find(TARGET_PREFIX, index)

        if start == -1:
            output.append(text[index:])
            break

        output.append(text[index:start])

        args_start = start + len(TARGET_PREFIX)
        scan = args_start

        while scan < len(text) and text[scan].isspace():
            scan += 1

        # Only replace SysFont(None, ...)
        if not text.startswith("None", scan):
            output.append(TARGET_PREFIX)
            index = args_start
            continue

        scan += len("None")

        while scan < len(text) and text[scan].isspace():
            scan += 1

        if scan >= len(text) or text[scan] != ",":
            output.append(TARGET_PREFIX)
            index = args_start
            continue

        scan += 1

        while scan < len(text) and text[scan].isspace():
            scan += 1

        end = find_matching_call_end(text, start)

        if end == -1:
            output.append(TARGET_PREFIX)
            index = args_start
            continue

        remaining_args = text[scan:end].strip()
        output.append(f"get_font({remaining_args})")

        index = end + 1
        changed = True

    return "".join(output), changed


def add_font_import(text):
    import_line = "from src.ui.fonts import get_font"

    if import_line in text:
        return text

    theme_import = "from src.ui.theme import UITheme"

    if theme_import in text:
        return text.replace(
            theme_import,
            theme_import + "\n" + import_line,
            1
        )

    lines = text.splitlines()
    insert_index = 0

    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_index = i + 1

    lines.insert(insert_index, import_line)
    return "\n".join(lines) + "\n"


def main():
    if not SRC_DIR.exists():
        print("ERROR: src folder not found.")
        return

    changed_files = []

    for path in SRC_DIR.rglob("*.py"):
        if path.name == "fonts.py":
            continue

        original = path.read_text(encoding="utf-8")
        updated, changed = replace_sysfont_none_calls(original)

        if not changed:
            continue

        updated = add_font_import(updated)

        backup_path = path.with_suffix(path.suffix + ".bak")
        backup_path.write_text(original, encoding="utf-8")
        path.write_text(updated, encoding="utf-8")

        changed_files.append(path)

    if not changed_files:
        print("No pygame.font.SysFont(None, ...) calls found.")
        return

    print("Updated font usage in:")
    for path in changed_files:
        print(f"- {path.relative_to(ROOT)}")

    print("\nBackup files were created with .bak extension.")


if __name__ == "__main__":
    main()