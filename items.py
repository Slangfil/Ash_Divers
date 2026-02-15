"""Ash Diver — Item definitions, loot tables, containers, ground items."""

import math
import random
from dataclasses import dataclass, field

import pygame

from settings import (
    ASSETS_DIR, TILE_SIZE,
    SCRAP_WOOD, SCRAP_METAL, SCRAP_ELECTRONICS, RARE_COMPONENT,
)


# ── Item definitions ─────────────────────────────────────────────────────────

@dataclass
class ItemDef:
    id: str
    name: str
    item_type: str  # "scrap", "weapon", "ammo"
    sprite_name: str
    stack_size: int = 1

ITEM_DEFS: dict[str, ItemDef] = {
    SCRAP_WOOD: ItemDef(SCRAP_WOOD, "Scrap Wood", "scrap", "item_scrap_wood", 10),
    SCRAP_METAL: ItemDef(SCRAP_METAL, "Scrap Metal", "scrap", "item_scrap_metal", 10),
    SCRAP_ELECTRONICS: ItemDef(SCRAP_ELECTRONICS, "Electronics", "scrap", "item_scrap_electronics", 5),
    RARE_COMPONENT: ItemDef(RARE_COMPONENT, "Rare Component", "scrap", "item_rare_component", 3),
    "pipe": ItemDef("pipe", "Pipe", "weapon", "item_pipe"),
    "pistol": ItemDef("pistol", "Pistol", "weapon", "item_pistol"),
    "shotgun": ItemDef("shotgun", "Shotgun", "weapon", "item_shotgun"),
    "ammo_box": ItemDef("ammo_box", "Ammo Box", "ammo", "item_ammo_box", 5),
    "medkit": ItemDef("medkit", "Medkit", "consumable", "item_medkit"),
}


# ── Loot tables ──────────────────────────────────────────────────────────────

# Each entry: (item_id, weight, min_count, max_count)
LOOT_TABLE_CRATE = [
    (SCRAP_WOOD, 30, 1, 3),
    (SCRAP_METAL, 25, 1, 2),
    ("ammo_box", 15, 1, 1),
    ("pipe", 10, 1, 1),
    (SCRAP_ELECTRONICS, 10, 1, 1),
]

LOOT_TABLE_LOCKER = [
    (SCRAP_METAL, 25, 1, 2),
    (SCRAP_ELECTRONICS, 20, 1, 1),
    ("pistol", 8, 1, 1),
    ("ammo_box", 20, 1, 2),
    (RARE_COMPONENT, 5, 1, 1),
]

LOOT_TABLE_RUBBLE = [
    (SCRAP_WOOD, 40, 1, 2),
    (SCRAP_METAL, 30, 1, 1),
    (SCRAP_ELECTRONICS, 10, 1, 1),
]

LOOT_TABLES = {
    "crate": LOOT_TABLE_CRATE,
    "locker": LOOT_TABLE_LOCKER,
    "rubble_pile": LOOT_TABLE_RUBBLE,
}


def roll_loot(table_name: str, rng: random.Random | None = None) -> list[tuple[str, int]]:
    """Roll 1-3 items from a loot table. Returns [(item_id, count), ...]."""
    r = rng or random
    table = LOOT_TABLES.get(table_name, LOOT_TABLE_CRATE)
    items_out = []
    num_rolls = r.randint(1, 3)
    total_weight = sum(w for _, w, _, _ in table)
    for _ in range(num_rolls):
        roll = r.random() * total_weight
        cumulative = 0
        for item_id, weight, mn, mx in table:
            cumulative += weight
            if roll <= cumulative:
                count = r.randint(mn, mx)
                items_out.append((item_id, count))
                break
    return items_out


# ── Inventory slot ───────────────────────────────────────────────────────────

@dataclass
class InvSlot:
    item_id: str
    count: int


# ── Container (in-world lootable object) ────────────────────────────────────

class Container:
    def __init__(self, x: float, y: float, container_type: str):
        self.x = x
        self.y = y
        self.container_type = container_type  # "crate", "locker", "rubble_pile"
        self.opened = False
        self.sprite_name = f"obj_{container_type}"

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), TILE_SIZE, TILE_SIZE)

    def open(self, rng: random.Random | None = None) -> list[tuple[str, int]]:
        if self.opened:
            return []
        self.opened = True
        return roll_loot(self.container_type, rng)


# ── Ground item (dropped or spawned on the map) ─────────────────────────────

class GroundItem:
    def __init__(self, x: float, y: float, item_id: str, count: int = 1):
        self.x = x
        self.y = y
        self.item_id = item_id
        self.count = count
        self.bob_timer = random.random() * math.pi * 2  # offset for bob animation
        self.sprite_name = ITEM_DEFS[item_id].sprite_name if item_id in ITEM_DEFS else "item_scrap_wood"

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), 12, 12)

    def update(self, dt: float):
        self.bob_timer += dt * 3.0

    @property
    def draw_y_offset(self) -> float:
        return math.sin(self.bob_timer) * 2.0


# ── Balloon Crate ────────────────────────────────────────────────────────────

class BalloonCrate:
    STATE_INACTIVE = 0
    STATE_INFLATING = 1
    STATE_READY = 2

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.state = self.STATE_INACTIVE
        self.timer = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), TILE_SIZE, TILE_SIZE)

    @property
    def sprite_name(self) -> str:
        if self.state == self.STATE_INACTIVE:
            return "obj_balloon_inactive"
        elif self.state == self.STATE_INFLATING:
            return "obj_balloon_inflating"
        return "obj_balloon_ready"
