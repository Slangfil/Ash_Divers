# Ash Diver

2D roguelike exploration platformer built with Pygame-CE. Inspired by the Hell Divers book series.

## Project Structure

### Core game (Milestone 1 — COMPLETE)
- `ash_diver.py` — Entry point. Seed screen, scene manager, main loop. F11 fullscreen, pygame.RESIZABLE.
- `settings.py` — All shared constants: display, physics, combat, tile IDs, scene IDs, SHOP_ITEMS, WEAPON_STATS.
- `camera.py` — Camera class (smooth follow, tile-range culling).
- `player.py` — Player: physics, HP, inventory, melee/ranged combat, projectiles, weapon swap, medkit use, ladder climbing.
- `enemies.py` — Siren AI: wander/chase/attack states, collision, loot drops, boundary clamping.
- `items.py` — Item definitions (ITEM_DEFS), loot tables, Container, GroundItem, BalloonCrate.
- `hud.py` — HUD overlay (HP hearts, weapon icon+name, ammo, medkit count, quickbar, inventory screen, extraction bar). SpriteCache shared loader.
- `scenes.py` — All scenes: AirshipScene (with Quartermaster shop), FreefallScene, SurfaceScene, DeathScene.
- `gen_suburbs.py` — Suburbs zone procedural generator (houses with interior rooms, roads, rubble, containers, ladders, doorways).
- `generate_sprites.py` — Pillow script that generates all PNG sprites to `assets/`. No external art needed.
- `build_exe.py` — PyInstaller build script. Run on Windows to produce .exe. `python build_exe.py`

### Legacy / world gen
- `generate_blueprint.py` — Original underground world generator. Tile constants source of truth for IDs 0-9. UNCHANGED.
- `game.py` — Original prototype. UNCHANGED.

### Generated (gitignored except assets/)
- `assets/` — Generated sprite PNGs (committed; regenerate with `python generate_sprites.py`).
- `output/` — Generated map artifacts. Gitignored.
- `build/`, `dist/`, `*.spec` — PyInstaller artifacts. Gitignored.

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
| T_LADDER | 17 | Climbable ladder |

IDs 0-9: canonical in `generate_blueprint.py`. IDs 10+: defined in `settings.py`.

## Game Loop

1. **Seed Screen** — Enter a seed or press Enter for random. F11 fullscreen.
2. **Airship Hub** — Walk around, stash display on top-left, Quartermaster shop (E near NPC), dive hatch (S/Down).
3. **Freefall** — Auto-scrolling descent, dodge lightning + storm clouds. ~18 seconds.
4. **Surface (Suburbs)** — Explore procedural suburb zone, loot containers, fight sirens, find weapons. Player starts with pistol + 12 ammo. Seed increments each dive so map is always different.
5. **Extract** — Find balloon crate (orange, pulsing glow, "EXTRACT" label). Choose: [1] send loot (lose 50%, stay) or [2] ride out (survive 30s horde, extract with everything).
6. **Death** — Lose everything, dive again from airship.

## Controls

- **Arrow/WASD** — Move + jump
- **Space** — Jump (also jump off ladders)
- **Left Click** — Attack (melee or ranged depending on equipped weapon)
- **Q** — Swap weapon (cycles: Fists -> Pipe -> Pistol -> Shotgun, only owned weapons)
- **H** — Use medkit (heals 2 HP)
- **E** — Interact (open container, activate balloon crate, open shop)
- **Tab** — Toggle inventory
- **F11** — Toggle fullscreen
- **Escape** — Quit / close overlay

## Combat System

- **Fists** — Default melee, always available.
- **Pipe** — Melee weapon. Damage 1, cooldown 0.4s, range 28px.
- **Pistol** — Ranged. Damage 1-2 (variable, "old unreliable guns"), cooldown 0.6s, 1 ammo per shot.
- **Shotgun** — Ranged. 5 pellets with 0.3 radian spread, damage 1 per pellet, cooldown 0.9s, 2 ammo per shot.
- **Sirens** — HP 4, takes 2-4 pistol shots to kill. Wander/chase/attack AI. Drop scrap on death.
- Attacks aim toward mouse cursor (world-space targeting).

## Quartermaster Shop (AirshipScene)

Press E near the NPC on the airship. UP/DOWN to navigate, ENTER to buy, E/ESC to close.
Costs deducted from persistent stash. Purchases stored in `game_state["loadout"]`, applied when entering SurfaceScene, then cleared.

| Item | Effect | Cost |
|------|--------|------|
| Ammo Crate | +12 starting rounds | 3 wood, 2 metal |
| Pipe | Start with melee weapon | 2 wood, 1 metal |
| Medkit | Heal 2 HP mid-dive (H) | 2 metal, 1 electronics |
| Armor Vest | +2 max HP for this dive | 4 metal, 2 electronics |
| Shotgun | 5-pellet spread weapon | 5 metal, 3 electronics, 1 rare |

## Persistent State

`game_state` dict passed between scenes. Persists across dives within a session (no save/load yet):
- `scrap_wood`, `scrap_metal`, `scrap_electronics`, `rare_component` — stash counts
- `hp` — carried between scenes
- `run_seed` — increments each dive for unique maps
- `loadout` — list of shop purchase IDs for next dive

## Running

```bash
python generate_sprites.py           # generate sprite assets (once, already committed)
python ash_diver.py                  # play the game
python build_exe.py                  # build standalone exe (run on target OS)
python gen_suburbs.py                # standalone suburb generation test
python game.py                       # legacy prototype
```

Dependencies: `pygame-ce`, `numpy`, `Pillow` (installed in `.venv/`).
Build dependency: `pyinstaller` (for build_exe.py only).

## Architecture Notes

- All constants centralized in `settings.py`. Never duplicate tile IDs or physics values.
- `SpriteCache` in `hud.py` is the shared sprite loader — caches loaded PNGs, used everywhere.
- Scenes return scene ID strings from `handle_events()`/`update()` to trigger transitions.
- Airship uses its own tile IDs (100-104) for metal walls/floor/window/hatch/NPC, mapped to SOLID_TILES via `_make_collision_grid()`.
- Suburbs generator (`gen_suburbs.py`) outputs a 160x60 grid with houses, roads, containers, balloon crates, siren spawn zones.
- Player `owned_weapons` set tracks collected weapons. `swap_weapon()` cycles only through owned ones.
- Balloon crates have 3 states: INACTIVE -> INFLATING -> READY. Pulsing glow + edge indicators for visibility.

## Planned (Post-M1)

- **Engineer NPC** — Separate from Quartermaster. Ship upgrades with permanent benefits across runs.
- Save/load to disk
- Additional zones (industrial, residential, underground)
- Additional enemies (worms, bone beasts)
- Sound / music
- Fog of war / shadow system
- Controller support
- Pause menu
