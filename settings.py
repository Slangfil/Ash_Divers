"""Ash Diver — Shared constants and configuration."""

from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────

ASSETS_DIR = Path(__file__).parent / "assets"

# ── Display ──────────────────────────────────────────────────────────────────

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60
TILE_SIZE = 16

# ── Player physics ───────────────────────────────────────────────────────────

PLAYER_W = 12
PLAYER_H = 28
GRAVITY = 980.0
JUMP_VEL = -330.0
MOVE_SPEED = 160.0
MAX_FALL = 600.0
CAMERA_LERP = 0.1

# ── Player stats ─────────────────────────────────────────────────────────────

PLAYER_MAX_HP = 5
PLAYER_INVULN_TIME = 1.0  # seconds of invulnerability after taking damage
INVENTORY_SIZE = 12

# ── Combat ───────────────────────────────────────────────────────────────────

MELEE_RANGE = 28  # pixels from player center
MELEE_COOLDOWN = 0.4
MELEE_DAMAGE = 1
RANGED_DAMAGE = 2
RANGED_SPEED = 400.0
RANGED_COOLDOWN = 0.6
RANGED_LIFETIME = 1.5  # seconds before bullet despawns

# ── Weapons ──────────────────────────────────────────────────────────────────

WEAPON_STATS = {
    "pipe": {
        "type": "melee",
        "damage": 1,
        "cooldown": 0.4,
        "range": 28,
    },
    "pistol": {
        "type": "ranged",
        "damage": 2,
        "cooldown": 0.6,
        "speed": 400.0,
        "range": 300,
    },
    "shotgun": {
        "type": "ranged",
        "damage": 1,
        "cooldown": 0.9,
        "speed": 350.0,
        "range": 150,
        "pellets": 5,
        "spread": 0.3,       # radians
        "ammo_cost": 2,
    },
}

# ── Shop ─────────────────────────────────────────────────────────────────────

# Each shop item: id, display name, description, cost {scrap_type: count}, effect key
SHOP_ITEMS = [
    {
        "id": "ammo_crate",
        "name": "Ammo Crate",
        "desc": "+12 starting rounds",
        "cost": {"scrap_wood": 3, "scrap_metal": 2},
    },
    {
        "id": "pipe",
        "name": "Pipe",
        "desc": "Start with a melee weapon",
        "cost": {"scrap_wood": 2, "scrap_metal": 1},
    },
    {
        "id": "medkit",
        "name": "Medkit",
        "desc": "Heal 2 HP mid-dive (press H)",
        "cost": {"scrap_metal": 2, "scrap_electronics": 1},
    },
    {
        "id": "armor_vest",
        "name": "Armor Vest",
        "desc": "+2 max HP for this dive",
        "cost": {"scrap_metal": 4, "scrap_electronics": 2},
    },
    {
        "id": "shotgun",
        "name": "Shotgun",
        "desc": "5-pellet spread, devastating up close",
        "cost": {"scrap_metal": 5, "scrap_electronics": 3, "rare_component": 1},
    },
]

# ── Enemies ──────────────────────────────────────────────────────────────────

SIREN_HP = 4
SIREN_SPEED = 60.0
SIREN_DETECT_RANGE = 128  # 8 tiles
SIREN_ATTACK_RANGE = 20
SIREN_ATTACK_DAMAGE = 1
SIREN_ATTACK_COOLDOWN = 1.2
SIREN_JUMP_VEL = -280.0
SIREN_W = 16
SIREN_H = 24

# ── Extraction ───────────────────────────────────────────────────────────────

EXTRACTION_TIME = 30.0  # seconds
HORDE_WAVE_INTERVAL = 8.0
HORDE_WAVE_COUNT = 3
HORDE_SIRENS_PER_WAVE = 4

# ── Suburbs tile IDs (extension of generate_blueprint constants) ─────────

# Original tiles from generate_blueprint.py: 0=air, 1=top, 2=fill, 8=goal, 9=spawn
T_AIR = 0
T_TOP = 1
T_FILL = 2
T_GOAL = 8
T_SPAWN = 9

# Suburb-specific tiles
T_ROAD = 10
T_WALL = 11
T_FLOOR = 12
T_ROOF = 13
T_RUBBLE = 14
T_CONTAINER = 15
T_BALLOON_CRATE = 16
T_LADDER = 17

SOLID_TILES = {T_TOP, T_FILL, T_WALL, T_ROOF}
CLIMBABLE_TILES = {T_LADDER}
LADDER_CLIMB_SPEED = 120.0
SURFACE_TILES = {T_TOP, T_ROAD, T_FLOOR}  # walkable surfaces

# Tile → sprite name mapping for rendering
TILE_SPRITES = {
    T_FILL: "tile_dirt",
    T_TOP: "tile_grass_top",
    T_ROAD: "tile_road",
    T_WALL: "tile_wall",
    T_FLOOR: "tile_floor",
    T_ROOF: "tile_roof",
    T_RUBBLE: "tile_rubble",
    T_CONTAINER: "tile_container",
    T_BALLOON_CRATE: "tile_balloon_crate",
    T_LADDER: "tile_ladder",
}

# Fallback colors (for tiles without sprites)
TILE_COLORS = {
    T_AIR: (135, 206, 235),
    T_TOP: (34, 139, 34),
    T_FILL: (139, 90, 43),
    T_GOAL: (255, 0, 0),
    T_SPAWN: (255, 255, 0),
    T_ROAD: (60, 60, 60),
    T_WALL: (180, 170, 150),
    T_FLOOR: (160, 140, 110),
    T_ROOF: (140, 60, 60),
    T_RUBBLE: (150, 140, 120),
    T_LADDER: (180, 140, 60),
}

# ── Scene IDs ────────────────────────────────────────────────────────────────

SCENE_AIRSHIP = "airship"
SCENE_FREEFALL = "freefall"
SCENE_SURFACE = "surface"
SCENE_DEATH = "death"

# ── Scrap types ──────────────────────────────────────────────────────────────

SCRAP_WOOD = "scrap_wood"
SCRAP_METAL = "scrap_metal"
SCRAP_ELECTRONICS = "scrap_electronics"
RARE_COMPONENT = "rare_component"

SCRAP_TYPES = [SCRAP_WOOD, SCRAP_METAL, SCRAP_ELECTRONICS, RARE_COMPONENT]

# ── Freefall ─────────────────────────────────────────────────────────────────

FREEFALL_DURATION = 18.0  # seconds
FREEFALL_START_SPEED = 100.0
FREEFALL_END_SPEED = 400.0
FREEFALL_PLAYER_SPEED = 200.0
LIGHTNING_TELEGRAPH_TIME = 0.8
LIGHTNING_DAMAGE = 1
CLOUD_DAMAGE = 1
CLOUD_SLOW_FACTOR = 0.4
