# Ash Diver

A 2D roguelike exploration platformer built with Pygame-CE. Drop from your airship into procedurally generated ruined suburbs, scavenge scrap, fight eyeless sirens, and extract before they overwhelm you.

## Quick Start

### Prerequisites

- Python 3.10+

### Install & Run

```bash
git clone https://github.com/Slangfil/Ash_Divers.git
cd Ash_Divers
python -m venv .venv

# Linux/Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install pygame-ce numpy Pillow
python generate_sprites.py
python ash_diver.py
```

## How to Play

You're an ash diver. You drop from an airship into the ruins below, scavenge what you can, and try to get out alive.

### The Loop

1. **Airship** — Your home base. Talk to the Quartermaster to buy gear, then walk to the hatch and press **S** to dive.
2. **Freefall** — Dodge lightning and storm clouds on the way down. Move left/right to avoid them.
3. **Surface** — Explore the ruined suburbs. Open crates and lockers for loot. Fight or avoid the sirens.
4. **Extract** — Find the glowing orange balloon crate. You can either send your loot up (keeps 50%, you stay behind) or ride it out yourself (survive a 30-second horde and escape with everything).
5. **Death** — If you die, you lose everything. Back to the airship with nothing.

Scrap you extract gets added to your stash on the airship. Spend it at the Quartermaster before your next dive.

### Controls

| Key | Action |
|-----|--------|
| **WASD / Arrows** | Move + jump |
| **Space** | Jump (also dismount ladders) |
| **Left Click** | Attack (melee or shoot, depends on weapon) |
| **Q** | Swap weapon |
| **H** | Use medkit (heals 2 HP) |
| **E** | Interact (open crates, talk to NPCs, activate extraction) |
| **Tab** | Inventory |
| **F11** | Fullscreen |
| **Esc** | Quit |

### Weapons

| Weapon | Type | Notes |
|--------|------|-------|
| Fists | Melee | Always available, weak |
| Pipe | Melee | Fast, reliable |
| Pistol | Ranged | You start each dive with one. 1-2 damage per shot (old guns are unreliable) |
| Shotgun | Ranged | 5 pellets, devastating up close, burns 2 ammo per shot |

### Shop

On the airship, walk to the Quartermaster (left side) and press **E**. Use arrow keys to browse and **Enter** to buy. Everything you buy applies to your next dive only.

## Building a Standalone Executable

```bash
pip install pyinstaller
python build_exe.py
```

Output goes to `dist/AshDiver/`. PyInstaller builds for whatever OS you run it on — run it on Windows to get a `.exe`.
