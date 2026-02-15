#!/usr/bin/env python3
"""Ash Diver — Procedural Blueprint Generator

Generates explorable underground terrain and exports as PNG, CSV, and TMX.
"""

import argparse
import os
import xml.etree.ElementTree as ET
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

# ── Tile constants ──────────────────────────────────────────────────────────

T_AIR = 0
T_TOP = 1
T_FILL = 2
T_GOAL = 8
T_SPAWN = 9

# Colors for PNG export (RGBA)
TILE_COLORS = {
    T_AIR: (135, 206, 235, 255),   # sky blue
    T_TOP: (34, 139, 34, 255),     # green
    T_FILL: (139, 90, 43, 255),    # brown
    T_GOAL: (255, 0, 0, 255),      # red
    T_SPAWN: (255, 255, 0, 255),   # yellow
}


# ── Configuration ───────────────────────────────────────────────────────────

@dataclass
class BlueprintConfig:
    seed: int = 42
    width: int = 200
    height: int = 120

    # Surface
    surface_y_min: int = 8
    surface_y_max: int = 18
    surface_step_max: int = 2

    # Tunnels
    num_tunnels: int = 5
    tunnel_min_width: int = 3
    tunnel_vertical_clearance: int = 3
    tunnel_branch_chance: float = 0.15

    # Caves
    num_caves: int = 12
    cave_radius_min: int = 5
    cave_radius_max: int = 18
    cave_noise_strength: float = 0.35

    # Filter
    min_region_size: int = 50

    # Export
    output_dir: str = "output"
    png_scale: int = 4


# ── Generator ───────────────────────────────────────────────────────────────

class BlueprintGenerator:
    def __init__(self, config: BlueprintConfig | None = None):
        self.cfg = config or BlueprintConfig()
        self.rng = np.random.default_rng(self.cfg.seed)
        self.grid = np.full((self.cfg.height, self.cfg.width), T_FILL, dtype=np.int8)
        self.surface_line: np.ndarray | None = None

    def generate(self) -> np.ndarray:
        """Run the full 9-step pipeline."""
        self._step1_init()
        self._step2_surface()
        self._step3_tunnels()
        self._step4_caves()
        self._step5_filter()
        self._step6_connect()
        self._step7_surface_entry_check()
        self._step8_spawn_goal()
        self._step9_top_detection()
        return self.grid

    # Step 1: Init ────────────────────────────────────────────────────────────

    def _step1_init(self):
        self.grid[:] = T_FILL

    # Step 2: Surface ─────────────────────────────────────────────────────────

    def _step2_surface(self):
        w, h = self.cfg.width, self.cfg.height
        y_min, y_max = self.cfg.surface_y_min, self.cfg.surface_y_max
        step_max = self.cfg.surface_step_max

        surface = np.zeros(w, dtype=np.int32)
        y = self.rng.integers(y_min, y_max + 1)
        for x in range(w):
            dy = self.rng.integers(-step_max, step_max + 1)
            y = int(np.clip(y + dy, y_min, y_max))
            surface[x] = y
            self.grid[:y, x] = T_AIR

        self.surface_line = surface

    # Step 3: Tunnels ─────────────────────────────────────────────────────────

    def _step3_tunnels(self):
        w, h = self.cfg.width, self.cfg.height
        n = self.cfg.num_tunnels
        min_w = self.cfg.tunnel_min_width
        clearance = self.cfg.tunnel_vertical_clearance

        start_xs = np.linspace(w * 0.1, w * 0.9, n, dtype=int)

        for sx in start_xs:
            self._carve_tunnel(int(sx), min_w, clearance)

    def _carve_tunnel(self, start_x: int, min_w: int, clearance: int):
        w, h = self.cfg.width, self.cfg.height
        x = start_x
        y = int(self.surface_line[start_x])
        half = min_w // 2

        max_depth = h - 5
        while y < max_depth:
            # Carve a cross-section
            for dx in range(-half, half + 1):
                for dy in range(clearance):
                    cx, cy = x + dx, y + dy
                    if 0 <= cx < w and 0 <= cy < h:
                        self.grid[cy, cx] = T_AIR

            # Biased random walk: mostly down, sometimes sideways
            direction = self.rng.random()
            if direction < 0.6:
                y += 1
            elif direction < 0.8:
                x = max(half, min(x - 1, w - 1 - half))
            else:
                x = max(half, min(x + 1, w - 1 - half))

            # Random step size for variety
            if self.rng.random() < 0.3:
                y += 1

            # Optional branch
            if self.rng.random() < self.cfg.tunnel_branch_chance and y < h - 20:
                branch_len = self.rng.integers(10, 30)
                bx, by = x, y
                branch_dir = self.rng.choice([-1, 1])
                for _ in range(branch_len):
                    for dx in range(-half, half + 1):
                        for dy in range(clearance):
                            cx, cy = bx + dx, by + dy
                            if 0 <= cx < w and 0 <= cy < h:
                                self.grid[cy, cx] = T_AIR
                    bx += branch_dir
                    if self.rng.random() < 0.4:
                        by += 1
                    bx = max(half, min(bx, w - 1 - half))
                    if by >= h - 2:
                        break

    # Step 4: Caves ───────────────────────────────────────────────────────────

    def _step4_caves(self):
        w, h = self.cfg.width, self.cfg.height
        n = self.cfg.num_caves
        r_min = self.cfg.cave_radius_min
        r_max = self.cfg.cave_radius_max
        noise = self.cfg.cave_noise_strength

        surface_max = int(self.surface_line.max()) + 10

        for _ in range(n):
            cx = self.rng.integers(r_max + 2, w - r_max - 2)
            cy = self.rng.integers(surface_max, h - r_max - 2)

            # Deeper caves tend to be larger
            depth_ratio = (cy - surface_max) / max(1, h - surface_max - r_max)
            base_r = r_min + (r_max - r_min) * depth_ratio
            base_r = max(r_min, min(base_r, r_max))

            # Per-angle radius noise for organic shapes
            num_angles = 36
            angles = np.linspace(0, 2 * np.pi, num_angles, endpoint=False)
            radii = base_r * (1.0 + noise * (self.rng.random(num_angles) * 2 - 1))

            for y in range(max(0, int(cy - r_max - 2)), min(h, int(cy + r_max + 2))):
                for x in range(max(0, int(cx - r_max - 2)), min(w, int(cx + r_max + 2))):
                    dx = x - cx
                    dy = y - cy
                    angle = np.arctan2(dy, dx) % (2 * np.pi)
                    # Find the two nearest angle samples and interpolate
                    idx = angle / (2 * np.pi) * num_angles
                    i0 = int(idx) % num_angles
                    i1 = (i0 + 1) % num_angles
                    frac = idx - int(idx)
                    r = radii[i0] * (1 - frac) + radii[i1] * frac
                    if dx * dx + dy * dy < r * r:
                        self.grid[y, x] = T_AIR

    # Step 5: Filter small regions ────────────────────────────────────────────

    def _step5_filter(self):
        """BFS flood fill; fill back regions smaller than min_region_size."""
        w, h = self.cfg.width, self.cfg.height
        visited = np.zeros((h, w), dtype=bool)

        for y in range(h):
            for x in range(w):
                if self.grid[y, x] == T_AIR and not visited[y, x]:
                    region = self._bfs_flood(x, y, visited)
                    if len(region) < self.cfg.min_region_size:
                        for rx, ry in region:
                            self.grid[ry, rx] = T_FILL

    def _bfs_flood(self, sx: int, sy: int, visited: np.ndarray) -> list[tuple[int, int]]:
        """BFS flood fill from (sx, sy), returns list of air coordinates."""
        w, h = self.cfg.width, self.cfg.height
        queue = deque([(sx, sy)])
        visited[sy, sx] = True
        region = []

        while queue:
            x, y = queue.popleft()
            region.append((x, y))
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx] and self.grid[ny, nx] == T_AIR:
                    visited[ny, nx] = True
                    queue.append((nx, ny))

        return region

    # Step 6: Connect ─────────────────────────────────────────────────────────

    def _step6_connect(self):
        """Ensure all air regions connect to the surface sky region."""
        w, h = self.cfg.width, self.cfg.height

        regions = self._find_air_regions()
        if len(regions) <= 1:
            return

        # The surface region is the one containing the topmost air tile
        surface_region_idx = 0
        min_y = h
        for i, region in enumerate(regions):
            for x, y in region:
                if y < min_y:
                    min_y = y
                    surface_region_idx = i

        # Connect each non-surface region to the surface region
        surface_set = set(regions[surface_region_idx])
        for i, region in enumerate(regions):
            if i == surface_region_idx:
                continue
            # Find closest pair of tiles between this region and the surface region
            best_dist = float("inf")
            best_a = best_b = None
            # Sample to keep it fast
            sample_size = min(200, len(region))
            sample_region = [region[j] for j in self.rng.choice(len(region), sample_size, replace=False)]
            surface_list = list(surface_set)
            sample_surface = [surface_list[j] for j in self.rng.choice(len(surface_list), min(200, len(surface_list)), replace=False)]

            for ax, ay in sample_region:
                for bx, by in sample_surface:
                    d = abs(ax - bx) + abs(ay - by)
                    if d < best_dist:
                        best_dist = d
                        best_a = (ax, ay)
                        best_b = (bx, by)

            if best_a and best_b:
                self._carve_l_tunnel(best_a, best_b)
                # Merge into surface set
                surface_set.update(region)

    def _find_air_regions(self) -> list[list[tuple[int, int]]]:
        w, h = self.cfg.width, self.cfg.height
        visited = np.zeros((h, w), dtype=bool)
        regions = []

        for y in range(h):
            for x in range(w):
                if self.grid[y, x] == T_AIR and not visited[y, x]:
                    region = self._bfs_flood(x, y, visited)
                    regions.append(region)

        return regions

    def _carve_l_tunnel(self, a: tuple[int, int], b: tuple[int, int]):
        """Carve an L-shaped tunnel from a to b (go horizontal then vertical)."""
        ax, ay = a
        bx, by = b
        half = self.cfg.tunnel_min_width // 2
        clearance = self.cfg.tunnel_vertical_clearance
        w, h = self.cfg.width, self.cfg.height

        # Horizontal leg
        x_start, x_end = min(ax, bx), max(ax, bx)
        for x in range(x_start, x_end + 1):
            for dy in range(-half, half + 1):
                cy = ay + dy
                if 0 <= x < w and 0 <= cy < h:
                    self.grid[cy, x] = T_AIR

        # Vertical leg
        y_start, y_end = min(ay, by), max(ay, by)
        for y in range(y_start, y_end + 1):
            for dx in range(-half, half + 1):
                cx = bx + dx
                if 0 <= cx < w and 0 <= y < h:
                    self.grid[y, cx] = T_AIR

    # Step 7: Surface entry check ─────────────────────────────────────────────

    def _step7_surface_entry_check(self):
        """Ensure at least one continuous air column connects sky to underground."""
        w, h = self.cfg.width, self.cfg.height
        underground_start = int(self.surface_line.max()) + 2

        for x in range(w):
            surf_y = int(self.surface_line[x])
            # Check if there's continuous air from surface down to underground
            connected = True
            for y in range(surf_y, min(underground_start + 5, h)):
                if self.grid[y, x] != T_AIR:
                    connected = False
                    break
            if connected:
                return

        # No entry found — carve one at the center
        cx = w // 2
        surf_y = int(self.surface_line[cx])
        half = self.cfg.tunnel_min_width // 2
        for y in range(surf_y, min(underground_start + 10, h)):
            for dx in range(-half, half + 1):
                xx = cx + dx
                if 0 <= xx < w:
                    self.grid[y, xx] = T_AIR

    # Step 8: Spawn & Goal ────────────────────────────────────────────────────

    def _step8_spawn_goal(self):
        w, h = self.cfg.width, self.cfg.height

        # Spawn: flattest surface near horizontal center
        center_x = w // 2
        best_score = float("inf")
        spawn_x = center_x

        for x in range(max(5, center_x - w // 4), min(w - 5, center_x + w // 4)):
            # Flatness = max height difference in a 5-tile window
            window = self.surface_line[max(0, x - 2):x + 3]
            flatness = int(window.max() - window.min())
            dist = abs(x - center_x)
            score = flatness * 10 + dist
            if score < best_score:
                best_score = score
                spawn_x = x

        spawn_y = int(self.surface_line[spawn_x]) - 1
        self.grid[spawn_y, spawn_x] = T_SPAWN

        # Goal: deepest air tile, far from spawn
        best_goal = None
        best_goal_score = -1.0

        for y in range(h - 1, -1, -1):
            for x in range(w):
                if self.grid[y, x] == T_AIR:
                    depth = y
                    dist = abs(x - spawn_x) + abs(y - spawn_y)
                    score = depth * 2 + dist
                    if score > best_goal_score:
                        best_goal_score = score
                        best_goal = (x, y)

        if best_goal:
            self.grid[best_goal[1], best_goal[0]] = T_GOAL

    # Step 9: T_TOP detection ─────────────────────────────────────────────────

    def _step9_top_detection(self):
        """Any T_FILL with T_AIR directly above becomes T_TOP."""
        # Vectorized: compare each row with the row above it
        air_above = self.grid[:-1, :] == T_AIR  # rows 0..h-2
        is_fill = self.grid[1:, :] == T_FILL    # rows 1..h-1
        mask = air_above & is_fill
        self.grid[1:, :] = np.where(mask, T_TOP, self.grid[1:, :])


# ── Export functions ────────────────────────────────────────────────────────

def export_png(grid: np.ndarray, path: str, scale: int = 4):
    h, w = grid.shape
    img = Image.new("RGBA", (w, h))
    pixels = img.load()

    for y in range(h):
        for x in range(w):
            pixels[x, y] = TILE_COLORS.get(int(grid[y, x]), (255, 0, 255, 255))

    img = img.resize((w * scale, h * scale), Image.NEAREST)
    img.save(path)


def export_csv(grid: np.ndarray, path: str):
    h, w = grid.shape
    with open(path, "w") as f:
        for y in range(h):
            f.write(",".join(str(grid[y, x]) for x in range(w)))
            f.write("\n")


def export_tmx(grid: np.ndarray, path: str):
    h, w = grid.shape
    tile_size = 16

    tmx_map = ET.Element("map", {
        "version": "1.10",
        "tiledversion": "1.10.2",
        "orientation": "orthogonal",
        "renderorder": "right-down",
        "width": str(w),
        "height": str(h),
        "tilewidth": str(tile_size),
        "tileheight": str(tile_size),
        "infinite": "0",
    })

    # Tileset (placeholder — references tiles by ID matching our constants + 1,
    # since TMX uses 1-based tile IDs where 0 = empty)
    tileset = ET.SubElement(tmx_map, "tileset", {
        "firstgid": "1",
        "name": "blueprint_tiles",
        "tilewidth": str(tile_size),
        "tileheight": str(tile_size),
        "tilecount": "10",
    })

    # Tile layer with CSV data (TMX uses 1-based IDs, so add 1)
    layer = ET.SubElement(tmx_map, "layer", {
        "id": "1",
        "name": "terrain",
        "width": str(w),
        "height": str(h),
    })
    data = ET.SubElement(layer, "data", {"encoding": "csv"})
    rows = []
    for y in range(h):
        rows.append(",".join(str(int(grid[y, x]) + 1) for x in range(w)))
    data.text = "\n" + "\n".join(rows) + "\n"

    # Object layer for spawn/goal markers
    obj_layer = ET.SubElement(tmx_map, "objectgroup", {
        "id": "2",
        "name": "markers",
    })

    obj_id = 1
    spawn_positions = np.argwhere(grid == T_SPAWN)
    for pos in spawn_positions:
        y, x = pos
        ET.SubElement(obj_layer, "object", {
            "id": str(obj_id),
            "name": "spawn",
            "type": "spawn",
            "x": str(x * tile_size),
            "y": str(y * tile_size),
            "width": str(tile_size),
            "height": str(tile_size),
        })
        obj_id += 1

    goal_positions = np.argwhere(grid == T_GOAL)
    for pos in goal_positions:
        y, x = pos
        ET.SubElement(obj_layer, "object", {
            "id": str(obj_id),
            "name": "goal",
            "type": "goal",
            "x": str(x * tile_size),
            "y": str(y * tile_size),
            "width": str(tile_size),
            "height": str(tile_size),
        })
        obj_id += 1

    tree = ET.ElementTree(tmx_map)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="unicode", xml_declaration=True)


# ── Verification ────────────────────────────────────────────────────────────

def verify_blueprint(grid: np.ndarray, surface_line: np.ndarray) -> list[str]:
    """Run structural invariant checks. Returns list of failure messages (empty = pass)."""
    h, w = grid.shape
    failures = []

    # 1. Single connected air region
    air_mask = np.isin(grid, [T_AIR, T_TOP, T_SPAWN, T_GOAL])
    visited = np.zeros((h, w), dtype=bool)
    region_count = 0

    for y in range(h):
        for x in range(w):
            if air_mask[y, x] and not visited[y, x]:
                queue = deque([(x, y)])
                visited[y, x] = True
                while queue:
                    cx, cy = queue.popleft()
                    for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                        if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx] and air_mask[ny, nx]:
                            visited[ny, nx] = True
                            queue.append((nx, ny))
                region_count += 1

    if region_count != 1:
        failures.append(f"Expected 1 connected air region, found {region_count}")

    # 2. Spawn exists and is on surface
    spawn_positions = np.argwhere(grid == T_SPAWN)
    if len(spawn_positions) == 0:
        failures.append("No spawn point found")
    elif len(spawn_positions) > 1:
        failures.append(f"Multiple spawn points found: {len(spawn_positions)}")
    else:
        sy, sx = spawn_positions[0]
        expected_y = int(surface_line[sx]) - 1
        if abs(sy - expected_y) > 2:
            failures.append(f"Spawn at y={sy} not near surface y={expected_y}")

    # 3. Goal exists and is deep underground
    goal_positions = np.argwhere(grid == T_GOAL)
    if len(goal_positions) == 0:
        failures.append("No goal point found")
    else:
        gy, gx = goal_positions[0]
        surface_max = int(surface_line.max())
        min_goal_depth = surface_max + (h - surface_max) // 3
        if gy < min_goal_depth:
            failures.append(f"Goal at y={gy} not deep enough (min expected: {min_goal_depth})")

    # 4. T_TOP tiles always have air/spawn above
    for y in range(1, h):
        for x in range(w):
            if grid[y, x] == T_TOP:
                above = grid[y - 1, x]
                if above not in (T_AIR, T_SPAWN, T_GOAL):
                    failures.append(f"T_TOP at ({x},{y}) has non-air tile above: {above}")
                    break
        else:
            continue
        break  # Only report first failure

    # 5. Vertical clearance spot check: pick some T_TOP tiles, check 3 tiles of air above
    top_positions = np.argwhere(grid == T_TOP)
    if len(top_positions) > 0:
        sample_size = min(50, len(top_positions))
        rng = np.random.default_rng(0)
        indices = rng.choice(len(top_positions), sample_size, replace=False)
        clearance_fails = 0
        for idx in indices:
            ty, tx = top_positions[idx]
            clear = 0
            for dy in range(1, 4):
                check_y = ty - dy
                if check_y >= 0 and grid[check_y, tx] in (T_AIR, T_SPAWN, T_GOAL, T_TOP):
                    clear += 1
            # We expect at least 1 tile of air (T_TOP itself is walkable)
            if clear == 0:
                clearance_fails += 1
        if clearance_fails > sample_size * 0.1:
            failures.append(f"Vertical clearance spot check: {clearance_fails}/{sample_size} failed")

    return failures


# ── CLI ─────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Ash Diver — Procedural Blueprint Generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--seed", type=int, default=42, help="RNG seed")
    p.add_argument("--width", type=int, default=200, help="Grid width in tiles")
    p.add_argument("--height", type=int, default=120, help="Grid height in tiles")
    p.add_argument("--surface-y-min", type=int, default=8, help="Minimum surface height")
    p.add_argument("--surface-y-max", type=int, default=18, help="Maximum surface height")
    p.add_argument("--num-tunnels", type=int, default=5, help="Number of tunnels")
    p.add_argument("--num-caves", type=int, default=12, help="Number of caves")
    p.add_argument("--cave-radius-min", type=int, default=5, help="Minimum cave radius")
    p.add_argument("--cave-radius-max", type=int, default=18, help="Maximum cave radius")
    p.add_argument("--min-region-size", type=int, default=50, help="Minimum air region size")
    p.add_argument("--output-dir", type=str, default="output", help="Output directory")
    p.add_argument("--png-scale", type=int, default=4, help="PNG upscale factor")
    p.add_argument("--verify", action="store_true", help="Run invariant checks after generation")
    p.add_argument("--fuzz", type=int, metavar="N", help="Run N seeds and verify each")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.fuzz:
        print(f"Fuzz testing {args.fuzz} seeds...")
        failed_seeds = []
        for seed in range(args.fuzz):
            cfg = BlueprintConfig(
                seed=seed,
                width=args.width,
                height=args.height,
                num_tunnels=args.num_tunnels,
                num_caves=args.num_caves,
                output_dir=args.output_dir,
            )
            gen = BlueprintGenerator(cfg)
            gen.generate()
            failures = verify_blueprint(gen.grid, gen.surface_line)
            if failures:
                failed_seeds.append((seed, failures))
                print(f"  FAIL seed={seed}: {failures}")
            else:
                print(f"  OK   seed={seed}")

        if failed_seeds:
            print(f"\n{len(failed_seeds)}/{args.fuzz} seeds FAILED")
            return 1
        else:
            print(f"\nAll {args.fuzz} seeds passed.")
            return 0

    cfg = BlueprintConfig(
        seed=args.seed,
        width=args.width,
        height=args.height,
        surface_y_min=args.surface_y_min,
        surface_y_max=args.surface_y_max,
        num_tunnels=args.num_tunnels,
        num_caves=args.num_caves,
        cave_radius_min=args.cave_radius_min,
        cave_radius_max=args.cave_radius_max,
        min_region_size=args.min_region_size,
        output_dir=args.output_dir,
        png_scale=args.png_scale,
    )

    gen = BlueprintGenerator(cfg)
    print(f"Generating blueprint (seed={cfg.seed}, {cfg.width}x{cfg.height})...")
    gen.generate()

    out = Path(cfg.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    png_path = out / "blueprint.png"
    csv_path = out / "blueprint.csv"
    tmx_path = out / "blueprint.tmx"

    export_png(gen.grid, str(png_path), cfg.png_scale)
    export_csv(gen.grid, str(csv_path))
    export_tmx(gen.grid, str(tmx_path))

    print(f"Exported: {png_path}, {csv_path}, {tmx_path}")

    if args.verify:
        failures = verify_blueprint(gen.grid, gen.surface_line)
        if failures:
            print("VERIFICATION FAILED:")
            for f in failures:
                print(f"  - {f}")
            return 1
        else:
            print("Verification passed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
