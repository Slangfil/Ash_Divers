# Ash Diver

2D roguelike exploration platformer built with Pygame-CE. Inspired by the Hell Divers book series.

## Project Structure

### Core game (Milestone 1)
- `ash_diver.py` — Entry point. Scene manager, main loop.
- `settings.py` — All shared constants: display, physics, combat, tile IDs, scene IDs.
- `camera.py` — Camera class (smooth follow, tile-range culling).
- `player.py` — Player: physics, HP, inventory, melee/ranged combat, projectiles.
- `enemies.py` — Siren AI: wander/chase/attack states, collision, loot drops.
- `items.py` — Item definitions, loot tables, Container, GroundItem, BalloonCrate.
- `hud.py` — HUD overlay (HP, weapon, quickbar, inventory screen, extraction bar).
- `scenes.py` — All scenes: AirshipScene, FreefallScene, SurfaceScene, DeathScene.
- `gen_suburbs.py` — Suburbs zone procedural generator (houses, roads, rubble, containers).
- `generate_sprites.py` — Pillow script that generates all PNG sprites to `assets/`.

### Legacy / world gen
- `generate_blueprint.py` — Original underground world generator. Tile constants source of truth for IDs 0-9.
- `game.py` — Original prototype. Loads CSV, renders colored rectangles, platformer physics.

### Generated
- `assets/` — Generated sprite PNGs (run `python generate_sprites.py`).
- `output/` — Generated map artifacts (blueprint.csv, suburbs.csv, etc.).

## Tile System

| Constant | ID | Meaning |
|----------|-----|---------|
| T_AIR | 0 | Empty space |
| T_TOP | 1 | Walkable surface (fill with air above) |
| T_FILL | 2 | Solid earth |
| T_GOAL | 8 | Win target (legacy) |
| T_SPAWN | 9 | Player start |
| T_ROAD | 10 | Suburb road |
| T_WALL | 11 | Suburb wall (solid) |
| T_FLOOR | 12 | Suburb floor (walkable) |
| T_ROOF | 13 | Suburb roof (solid) |
| T_RUBBLE | 14 | Decorative rubble |
| T_CONTAINER | 15 | Lootable container marker |
| T_BALLOON_CRATE | 16 | Extraction crate marker |

IDs 0-9: canonical in `generate_blueprint.py`. IDs 10+: defined in `settings.py`.

## Game Loop

1. **Airship Hub** — Walk around, stash display, dive hatch
2. **Freefall** — Dodge lightning + clouds during descent
3. **Surface (Suburbs)** — Explore, loot containers, fight sirens, find weapons
4. **Extract** — Find balloon crate, choose send-loot or ride-out
5. **Death** — Lose everything, dive again

## Running

```bash
python generate_sprites.py           # generate sprite assets (once)
python gen_suburbs.py                # generate suburbs map (optional, standalone test)
python ash_diver.py                  # play the game
python game.py                       # legacy prototype
```

Dependencies: `pygame-ce`, `numpy`, `Pillow` (installed in `.venv/`).

## Controls

- **Arrow/WASD** — Move + jump
- **J / Left-click** — Melee attack
- **K / Right-click** — Ranged attack (needs pistol + ammo)
- **E** — Interact (open container, activate balloon crate, talk to NPC)
- **Tab** — Toggle inventory
- **Escape** — Quit

## Planned (Post-M1)

- Shop / upgrade spending at Quartermaster
- Ship + player upgrades
- Save/load to disk
- Additional zones (industrial, residential, underground)
- Additional enemies (worms, bone beasts)
- Sound / music
- Controller support
