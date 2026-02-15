# Ash Diver

2D exploration platformer built with Pygame-CE.

## Project Structure

- `generate_blueprint.py` — Procedural world generator. Outputs a 200x120 tile grid as CSV, TMX, and PNG to `output/`.
- `game.py` — Minimal playable prototype. Loads CSV, renders colored rectangles, platformer physics.
- `output/` — Generated artifacts (blueprint.csv, blueprint.tmx, blueprint.png). Gitignored, regenerate with `python generate_blueprint.py`.

## Tile System

| Constant | ID | Meaning |
|----------|-----|---------|
| T_AIR | 0 | Empty space (sky blue) |
| T_TOP | 1 | Walkable surface — T_FILL with air above (green) |
| T_FILL | 2 | Solid earth (brown) |
| T_GOAL | 8 | Win target, deep underground (red) |
| T_SPAWN | 9 | Player start, on surface (yellow) |

Canonical definitions live in `generate_blueprint.py`. Game imports them — no duplication.

## Design Goals

- Exploration over linear platforming
- Multiple vertical routes through tunnels and caves
- Guaranteed playability: minimum cave size, surface-to-underground connectivity, vertical clearance
- Seed-based deterministic generation (default seed 42)

## Running

```bash
source .venv/bin/activate
python generate_blueprint.py        # generate world
python game.py                       # play (optional: python game.py path/to/other.csv)
```

Dependencies: `pygame-ce`, `numpy`, `Pillow` (installed in `.venv/`).

## Planned Systems

- Ladder mechanics (climbable tiles)
- Shadow/fog-of-war below player
- TMX runtime loader (use Tiled-edited maps directly)
- Tileset art integration (power_station, exclusion_zone, industrial_zone)
- Improved cave accessibility validation
