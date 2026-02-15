#!/usr/bin/env python3
"""Build Ash Diver into a standalone executable.

Usage:
    python build_exe.py

Produces dist/AshDiver/ with the executable and all assets.
PyInstaller builds for the current OS — run this on Windows to get a .exe.

Requirements:
    pip install pyinstaller pygame-ce pillow numpy
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

def main():
    # Ensure sprites are generated
    print("Generating sprites...")
    subprocess.run([sys.executable, str(ROOT / "generate_sprites.py")], check=True)

    args = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AshDiver",
        "--onedir",
        "--windowed",
        "--add-data", f"{ROOT / 'assets'}{':' if sys.platform != 'win32' else ';'}assets",
        "--icon", "NONE",
        "--clean",
        "--noconfirm",
        str(ROOT / "ash_diver.py"),
    ]
    print("Running PyInstaller...")
    subprocess.run(args, check=True)
    print("\nBuild complete! Output in dist/AshDiver/")


if __name__ == "__main__":
    main()
