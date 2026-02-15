#!/usr/bin/env python3
"""Ash Diver — Suburbs Zone Procedural Generator.

Generates a ruined suburb neighborhood as a tile grid.
Run standalone to produce output/suburbs.csv + output/suburbs.png.
"""

import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from settings import (
    T_AIR, T_TOP, T_FILL, T_SPAWN,
    T_ROAD, T_WALL, T_FLOOR, T_ROOF, T_RUBBLE, T_CONTAINER, T_BALLOON_CRATE,
    T_LADDER, TILE_COLORS,
)


@dataclass
class SuburbsConfig:
    seed: int = 42
    width: int = 160
    height: int = 60
    ground_y: int = 45  # base ground level (from top)
    num_houses: int = 10
    num_roads: int = 3
    num_containers: int = 15
    num_rubble_piles: int = 12
    num_balloon_crates: int = 2


class SuburbsGenerator:
    def __init__(self, config: SuburbsConfig | None = None):
        self.cfg = config or SuburbsConfig()
        self.rng = random.Random(self.cfg.seed)
        self.grid: list[list[int]] = []
        self.spawn_pos: tuple[int, int] = (0, 0)
        self.container_positions: list[tuple[int, int, str]] = []  # (x, y, type)
        self.balloon_positions: list[tuple[int, int]] = []
        self.siren_spawn_zones: list[tuple[int, int]] = []  # (x, y) center of each zone
        self.ground_items: list[tuple[int, int, str]] = []  # (x, y, item_id)

    def generate(self) -> list[list[int]]:
        self._init_grid()
        self._make_ground()
        self._place_roads()
        self._place_houses()
        self._place_exterior_ladders()
        self._scatter_rubble()
        self._place_containers()
        self._place_balloon_crates()
        self._place_ground_loot()
        self._place_siren_zones()
        self._place_spawn()
        self._top_detection()
        return self.grid

    def _init_grid(self):
        self.grid = [[T_AIR] * self.cfg.width for _ in range(self.cfg.height)]

    def _make_ground(self):
        w, h = self.cfg.width, self.cfg.height
        base_y = self.cfg.ground_y
        for x in range(w):
            # Slight elevation variation
            offset = self.rng.randint(-1, 1)
            gy = min(h - 1, max(base_y - 2, base_y + offset))
            for y in range(gy, h):
                self.grid[y][x] = T_FILL

    def _place_roads(self):
        w = self.cfg.width
        gy = self.cfg.ground_y
        # Horizontal roads at ground level
        road_xs = sorted(self.rng.sample(range(5, w - 5), min(self.cfg.num_roads * 2, w - 10)))
        for i in range(0, len(road_xs) - 1, 2):
            x_start = road_xs[i]
            x_end = min(road_xs[i] + self.rng.randint(20, 50), road_xs[i + 1] if i + 1 < len(road_xs) else w - 1)
            for x in range(x_start, min(x_end, w)):
                # Road replaces top ground tiles
                if gy - 1 >= 0:
                    self.grid[gy - 1][x] = T_AIR
                self.grid[gy][x] = T_ROAD
                # Clear 3 tiles above road for walkability
                for dy in range(1, 4):
                    if gy - dy >= 0:
                        self.grid[gy - dy][x] = T_AIR

    def _place_houses(self):
        w, h = self.cfg.width, self.cfg.height
        gy = self.cfg.ground_y
        placed = []

        for _ in range(self.cfg.num_houses * 3):  # more attempts than houses needed
            if len(placed) >= self.cfg.num_houses:
                break
            hw = self.rng.randint(8, 15)
            hh = self.rng.randint(5, 8)
            hx = self.rng.randint(2, w - hw - 2)
            hy = gy - hh  # house sits on ground

            # Check overlap with existing houses
            overlap = False
            for px, py, pw, ph in placed:
                if hx < px + pw + 3 and hx + hw + 3 > px and hy < py + ph + 2 and hy + hh + 2 > py:
                    overlap = True
                    break
            if overlap:
                continue

            self._build_house(hx, hy, hw, hh)
            placed.append((hx, hy, hw, hh))

    def _build_house(self, hx: int, hy: int, hw: int, hh: int):
        w, h = self.cfg.width, self.cfg.height
        is_ruined = self.rng.random() < 0.35

        for y in range(hy, hy + hh):
            for x in range(hx, hx + hw):
                if 0 <= x < w and 0 <= y < h:
                    # Roof (top row)
                    if y == hy:
                        if is_ruined and self.rng.random() < 0.3:
                            self.grid[y][x] = T_AIR  # collapsed roof section
                        else:
                            self.grid[y][x] = T_ROOF
                    # Walls (left and right edges)
                    elif x == hx or x == hx + hw - 1:
                        if is_ruined and self.rng.random() < 0.2:
                            self.grid[y][x] = T_RUBBLE
                        else:
                            self.grid[y][x] = T_WALL
                    # Floor (bottom row)
                    elif y == hy + hh - 1:
                        self.grid[y][x] = T_FLOOR
                    # Interior
                    else:
                        self.grid[y][x] = T_AIR

        # Doorways — punch holes in both side walls near the bottom
        door_y_start = hy + hh - 3  # 3 tiles of clearance for the player
        for y in range(door_y_start, hy + hh - 1):
            if 0 <= y < h:
                if 0 <= hx < w:
                    self.grid[y][hx] = T_AIR
                if 0 <= hx + hw - 1 < w:
                    self.grid[y][hx + hw - 1] = T_AIR

        # Interior ladder — place near one side wall, from floor to roof
        ladder_x = hx + 2 if self.rng.random() < 0.5 else hx + hw - 3
        if 0 <= ladder_x < w:
            for y in range(hy + 1, hy + hh - 1):
                if 0 <= y < h and self.grid[y][ladder_x] == T_AIR:
                    self.grid[y][ladder_x] = T_LADDER
            # Open one roof tile above ladder for roof access
            if 0 <= hy < h:
                self.grid[hy][ladder_x] = T_LADDER

        # Internal divider wall for multi-room houses
        if hw >= 12:
            div_x = hx + hw // 2
            for y in range(hy + 1, hy + hh - 1):
                if 0 <= div_x < w and 0 <= y < h:
                    # Leave a doorway
                    if y >= hy + hh - 3:
                        self.grid[y][div_x] = T_AIR
                    else:
                        self.grid[y][div_x] = T_WALL

    def _place_exterior_ladders(self):
        """Place freestanding ladders in open areas for general vertical mobility."""
        w, h = self.cfg.width, self.cfg.height
        gy = self.cfg.ground_y
        spacing = w // 8  # roughly every 20 tiles
        for x_base in range(10, w - 10, spacing):
            lx = x_base + self.rng.randint(-3, 3)
            lx = max(1, min(lx, w - 2))
            # Place a 4-tile ladder rising from ground level
            for dy in range(4):
                ly = gy - 1 - dy
                if 0 <= ly < h and self.grid[ly][lx] == T_AIR:
                    self.grid[ly][lx] = T_LADDER

    def _scatter_rubble(self):
        w = self.cfg.width
        gy = self.cfg.ground_y
        for _ in range(self.cfg.num_rubble_piles):
            rx = self.rng.randint(2, w - 3)
            ry = gy - 1
            if 0 <= ry < self.cfg.height and self.grid[ry][rx] == T_AIR:
                self.grid[ry][rx] = T_RUBBLE

    def _place_containers(self):
        w, h = self.cfg.width, self.cfg.height
        gy = self.cfg.ground_y
        placed = 0

        # Also check air tiles inside houses (wider y range)
        for _ in range(self.cfg.num_containers * 10):
            if placed >= self.cfg.num_containers:
                break
            cx = self.rng.randint(3, w - 4)
            cy = self.rng.randint(max(0, gy - 12), gy - 1)
            if 0 <= cy < h and 0 <= cx < w and self.grid[cy][cx] == T_AIR:
                # Check has floor below (any solid surface)
                if cy + 1 < h and self.grid[cy + 1][cx] not in (T_AIR, T_SPAWN, T_CONTAINER, T_BALLOON_CRATE):
                    self.grid[cy][cx] = T_CONTAINER
                    ctype = self.rng.choice(["crate", "crate", "locker", "rubble_pile"])
                    self.container_positions.append((cx, cy, ctype))
                    placed += 1

    def _place_balloon_crates(self):
        w, h = self.cfg.width, self.cfg.height
        gy = self.cfg.ground_y
        placed = 0

        for _ in range(100):
            if placed >= self.cfg.num_balloon_crates:
                break
            bx = self.rng.randint(10, w - 10)
            by = gy - 1
            if 0 <= by < h and self.grid[by][bx] == T_AIR:
                # Check clear sky above
                clear = True
                for y in range(0, by):
                    if self.grid[y][bx] != T_AIR:
                        clear = False
                        break
                if clear and by + 1 < h and self.grid[by + 1][bx] in (T_FILL, T_ROAD, T_FLOOR):
                    self.grid[by][bx] = T_BALLOON_CRATE
                    self.balloon_positions.append((bx, by))
                    placed += 1

    def _place_ground_loot(self):
        w, h = self.cfg.width, self.cfg.height
        gy = self.cfg.ground_y
        loot_items = ["scrap_wood", "scrap_metal", "scrap_wood", "scrap_electronics"]
        placed = 0
        for _ in range(200):
            if placed >= 8:
                break
            lx = self.rng.randint(5, w - 5)
            ly = self.rng.randint(max(0, gy - 10), gy - 1)
            if 0 <= ly < h and self.grid[ly][lx] == T_AIR:
                if ly + 1 < h and self.grid[ly + 1][lx] not in (T_AIR, T_SPAWN, T_CONTAINER, T_BALLOON_CRATE):
                    item = self.rng.choice(loot_items)
                    self.ground_items.append((lx, ly, item))
                    placed += 1

    def _place_siren_zones(self):
        w = self.cfg.width
        # Place siren zones away from spawn (which will be near left edge)
        num_zones = 4
        for i in range(num_zones):
            zx = self.rng.randint(w // 3, w - 10)
            zy = self.cfg.ground_y - 2
            self.siren_spawn_zones.append((zx, zy))

    def _place_spawn(self):
        gy = self.cfg.ground_y
        # Spawn near left edge in open area
        for x in range(5, 20):
            y = gy - 1
            if 0 <= y < self.cfg.height and self.grid[y][x] == T_AIR:
                # Check ground below
                if y + 1 < self.cfg.height and self.grid[y + 1][x] in (T_FILL, T_ROAD, T_FLOOR):
                    self.grid[y][x] = T_SPAWN
                    self.spawn_pos = (x, y)
                    return
        # Fallback
        self.grid[gy - 1][5] = T_SPAWN
        self.spawn_pos = (5, gy - 1)

    def _top_detection(self):
        h, w = self.cfg.height, self.cfg.width
        for y in range(1, h):
            for x in range(w):
                if self.grid[y][x] == T_FILL and self.grid[y - 1][x] in (T_AIR, T_SPAWN):
                    self.grid[y][x] = T_TOP


# ── Export ───────────────────────────────────────────────────────────────────

def export_csv(grid: list[list[int]], path: str):
    with open(path, "w") as f:
        for row in grid:
            f.write(",".join(str(v) for v in row))
            f.write("\n")


def export_png(grid: list[list[int]], path: str, scale: int = 4):
    h = len(grid)
    w = len(grid[0]) if h > 0 else 0
    img = Image.new("RGBA", (w, h))
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            tile = grid[y][x]
            color = TILE_COLORS.get(tile, (255, 0, 255))
            if len(color) == 3:
                color = color + (255,)
            pixels[x, y] = color
    img = img.resize((w * scale, h * scale), Image.NEAREST)
    img.save(path)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    p = argparse.ArgumentParser(description="Suburbs zone generator")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output-dir", default="output")
    args = p.parse_args()

    cfg = SuburbsConfig(seed=args.seed)
    gen = SuburbsGenerator(cfg)
    print(f"Generating suburbs (seed={cfg.seed}, {cfg.width}x{cfg.height})...")
    gen.generate()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    csv_path = out / "suburbs.csv"
    png_path = out / "suburbs.png"
    export_csv(gen.grid, str(csv_path))
    export_png(gen.grid, str(png_path))

    print(f"Exported: {csv_path}, {png_path}")
    print(f"Spawn: {gen.spawn_pos}")
    print(f"Containers: {len(gen.container_positions)}")
    print(f"Balloon crates: {len(gen.balloon_positions)}")
    print(f"Siren zones: {len(gen.siren_spawn_zones)}")
    print(f"Ground loot: {len(gen.ground_items)}")


if __name__ == "__main__":
    main()
