"""Build Mutation RPG into a Windows executable with PyInstaller."""

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC_FILE = ROOT / "MutationRPG.spec"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
EXE_FILE = DIST_DIR / "MutationRPG.exe"


def run(command):
    print("\n> " + " ".join(command))
    subprocess.check_call(command, cwd=ROOT)


def main():
    if not SPEC_FILE.exists():
        raise FileNotFoundError("MutationRPG.spec was not found.")

    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    shutil.rmtree(DIST_DIR, ignore_errors=True)

    run([
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE),
    ])

    if not EXE_FILE.exists():
        raise RuntimeError("Build finished, but dist/MutationRPG.exe was not created.")

    print("\nBuild complete!")
    print(f"EXE file: {EXE_FILE}")
    print("Save data will be created in dist/save_data when the EXE runs.")


if __name__ == "__main__":
    main()
