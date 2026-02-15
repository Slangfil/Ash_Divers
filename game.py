#!/usr/bin/env python3
"""Ash Diver — Minimal Playable Prototype

Run from project root:
    python game.py [path/to/blueprint.csv]

Controls:
    Arrow keys / WASD  - Move
    Up / W / Space     - Jump
    Escape             - Quit
    R (when won)       - Restart
"""

import sys
from pathlib import Path

import pygame

from generate_blueprint import (
    T_AIR,
    T_FILL,
    T_GOAL,
    T_SPAWN,
    T_TOP,
    TILE_COLORS,
)

# ── Constants ────────────────────────────────────────────────────────────────

SCREEN_W, SCREEN_H = 1280, 720
TILE_SIZE = 16
PLAYER_W, PLAYER_H = 12, 28
GRAVITY = 980.0
JUMP_VEL = -330.0
MOVE_SPEED = 160.0
MAX_FALL = 600.0
CAMERA_LERP = 0.1

SOLID_TILES = {T_TOP, T_FILL}

# ── Helpers ──────────────────────────────────────────────────────────────────


def load_grid(path: str) -> list[list[int]]:
    """Read a CSV tile grid into a 2D list of ints."""
    grid: list[list[int]] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                grid.append([int(v) for v in line.split(",")])
    return grid


def find_tile(grid: list[list[int]], tile_id: int) -> tuple[int, int] | None:
    """Return the first (col, row) where *tile_id* appears, or None."""
    for row_idx, row in enumerate(grid):
        for col_idx, val in enumerate(row):
            if val == tile_id:
                return col_idx, row_idx
    return None


# ── Camera ───────────────────────────────────────────────────────────────────


class Camera:
    def __init__(self, map_w: int, map_h: int):
        self.x = 0.0
        self.y = 0.0
        self.map_w = map_w
        self.map_h = map_h

    def update(self, target_x: float, target_y: float):
        # Target: center the screen on the player
        goal_x = target_x - SCREEN_W / 2
        goal_y = target_y - SCREEN_H / 2
        self.x += (goal_x - self.x) * CAMERA_LERP
        self.y += (goal_y - self.y) * CAMERA_LERP
        # Clamp to map bounds
        self.x = max(0.0, min(self.x, self.map_w - SCREEN_W))
        self.y = max(0.0, min(self.y, self.map_h - SCREEN_H))

    def snap(self, target_x: float, target_y: float):
        """Immediately center on target (no lerp)."""
        self.x = target_x - SCREEN_W / 2
        self.y = target_y - SCREEN_H / 2
        self.x = max(0.0, min(self.x, self.map_w - SCREEN_W))
        self.y = max(0.0, min(self.y, self.map_h - SCREEN_H))

    def visible_tile_range(self) -> tuple[int, int, int, int]:
        """Return (col_start, col_end, row_start, row_end) of tiles on screen."""
        col_start = max(0, int(self.x) // TILE_SIZE)
        row_start = max(0, int(self.y) // TILE_SIZE)
        col_end = min(
            (int(self.x) + SCREEN_W) // TILE_SIZE + 1,
            self.map_w // TILE_SIZE,
        )
        row_end = min(
            (int(self.y) + SCREEN_H) // TILE_SIZE + 1,
            self.map_h // TILE_SIZE,
        )
        return col_start, col_end, row_start, row_end


# ── Player ───────────────────────────────────────────────────────────────────


class Player:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), PLAYER_W, PLAYER_H)

    def update(self, dt: float, grid: list[list[int]], grid_w: int, grid_h: int):
        # Gravity
        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL)

        # Move X
        self.x += self.vx * dt
        self._resolve_x(grid, grid_w, grid_h)

        # Move Y
        self.y += self.vy * dt
        self._resolve_y(grid, grid_w, grid_h)

    def _get_overlapping_tiles(self, grid: list[list[int]], grid_w: int, grid_h: int):
        """Yield (col, row, tile_rect) for every solid tile overlapping the player."""
        r = self.rect
        col_start = max(0, r.left // TILE_SIZE)
        col_end = min(grid_w, (r.right - 1) // TILE_SIZE + 1)
        row_start = max(0, r.top // TILE_SIZE)
        row_end = min(grid_h, (r.bottom - 1) // TILE_SIZE + 1)
        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                if grid[row][col] in SOLID_TILES:
                    tile_rect = pygame.Rect(
                        col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE
                    )
                    if r.colliderect(tile_rect):
                        yield col, row, tile_rect

    def _resolve_x(self, grid: list[list[int]], grid_w: int, grid_h: int):
        for _col, _row, tile_rect in self._get_overlapping_tiles(grid, grid_w, grid_h):
            r = self.rect
            if self.vx > 0:
                self.x = tile_rect.left - PLAYER_W
            elif self.vx < 0:
                self.x = tile_rect.right
            else:
                # Pushed into a tile without horizontal velocity — nudge out
                overlap_left = r.right - tile_rect.left
                overlap_right = tile_rect.right - r.left
                if overlap_left < overlap_right:
                    self.x = tile_rect.left - PLAYER_W
                else:
                    self.x = tile_rect.right

    def _resolve_y(self, grid: list[list[int]], grid_w: int, grid_h: int):
        self.on_ground = False
        for _col, _row, tile_rect in self._get_overlapping_tiles(grid, grid_w, grid_h):
            r = self.rect
            if self.vy > 0:
                self.y = tile_rect.top - PLAYER_H
                self.vy = 0.0
                self.on_ground = True
            elif self.vy < 0:
                self.y = tile_rect.bottom
                self.vy = 0.0
            else:
                overlap_top = r.bottom - tile_rect.top
                overlap_bottom = tile_rect.bottom - r.top
                if overlap_top < overlap_bottom:
                    self.y = tile_rect.top - PLAYER_H
                    self.on_ground = True
                else:
                    self.y = tile_rect.bottom

    def check_win(self, grid: list[list[int]], grid_w: int, grid_h: int) -> bool:
        """Return True if the player overlaps any T_GOAL tile."""
        r = self.rect
        col_start = max(0, r.left // TILE_SIZE)
        col_end = min(grid_w, (r.right - 1) // TILE_SIZE + 1)
        row_start = max(0, r.top // TILE_SIZE)
        row_end = min(grid_h, (r.bottom - 1) // TILE_SIZE + 1)
        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                if grid[row][col] == T_GOAL:
                    return True
        return False


# ── Game ─────────────────────────────────────────────────────────────────────


class Game:
    def __init__(self, csv_path: str):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Ash Diver")
        self.clock = pygame.time.Clock()

        self.csv_path = csv_path
        self.grid: list[list[int]] = []
        self.grid_w = 0
        self.grid_h = 0
        self.tile_surfaces: dict[int, pygame.Surface] = {}
        self.player: Player | None = None
        self.camera: Camera | None = None
        self.won = False
        self.font: pygame.font.Font | None = None

        self._load()

    def _load(self):
        self.grid = load_grid(self.csv_path)
        self.grid_h = len(self.grid)
        self.grid_w = len(self.grid[0]) if self.grid_h > 0 else 0

        # Pre-render a small colored surface for each tile type
        self.tile_surfaces.clear()
        for tile_id, rgba in TILE_COLORS.items():
            if tile_id == T_AIR:
                continue  # Air is the background fill
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surf.fill(rgba[:3])
            self.tile_surfaces[tile_id] = surf

        # Find spawn position
        spawn = find_tile(self.grid, T_SPAWN)
        if spawn is None:
            # Fallback: top-left air tile
            spawn = find_tile(self.grid, T_AIR)
        if spawn is None:
            spawn = (0, 0)

        sx = spawn[0] * TILE_SIZE + (TILE_SIZE - PLAYER_W) // 2
        sy = spawn[1] * TILE_SIZE + (TILE_SIZE - PLAYER_H)

        self.player = Player(sx, sy)
        self.camera = Camera(self.grid_w * TILE_SIZE, self.grid_h * TILE_SIZE)
        self.camera.snap(sx + PLAYER_W / 2, sy + PLAYER_H / 2)

        self.won = False
        self.font = pygame.font.SysFont(None, 48)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            dt = min(dt, 0.05)  # Cap delta to avoid spiral of death

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r and self.won:
                        self._load()

            if not self.won:
                self._handle_input(dt)
                self.player.update(dt, self.grid, self.grid_w, self.grid_h)
                if self.player.check_win(self.grid, self.grid_w, self.grid_h):
                    self.won = True

            self.camera.update(
                self.player.x + PLAYER_W / 2,
                self.player.y + PLAYER_H / 2,
            )
            self._render()

        pygame.quit()

    def _handle_input(self, dt: float):
        keys = pygame.key.get_pressed()

        # Horizontal
        move = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move += 1
        self.player.vx = move * MOVE_SPEED

        # Jump
        if (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]) and self.player.on_ground:
            self.player.vy = JUMP_VEL

    def _render(self):
        # Background: sky blue
        self.screen.fill(TILE_COLORS[T_AIR][:3])

        cam_x = int(self.camera.x)
        cam_y = int(self.camera.y)

        # Draw visible tiles
        c0, c1, r0, r1 = self.camera.visible_tile_range()
        for row in range(r0, r1):
            grid_row = self.grid[row]
            y = row * TILE_SIZE - cam_y
            for col in range(c0, c1):
                tile_id = grid_row[col]
                surf = self.tile_surfaces.get(tile_id)
                if surf is not None:
                    self.screen.blit(surf, (col * TILE_SIZE - cam_x, y))

        # Draw player
        pr = self.player.rect.move(-cam_x, -cam_y)
        pygame.draw.rect(self.screen, (40, 40, 40), pr.inflate(2, 2))  # outline
        pygame.draw.rect(self.screen, (255, 255, 255), pr)

        # Win overlay
        if self.won:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            self.screen.blit(overlay, (0, 0))

            line1 = self.font.render("YOU WIN!", True, (255, 255, 100))
            line2 = self.font.render("Press R to restart", True, (220, 220, 220))
            self.screen.blit(line1, (SCREEN_W // 2 - line1.get_width() // 2, SCREEN_H // 2 - 40))
            self.screen.blit(line2, (SCREEN_W // 2 - line2.get_width() // 2, SCREEN_H // 2 + 10))

        pygame.display.flip()


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "output/blueprint.csv"
    if not Path(csv_path).exists():
        print(f"CSV not found: {csv_path}")
        print("Run  python generate_blueprint.py  first to generate the world.")
        sys.exit(1)
    Game(csv_path).run()


if __name__ == "__main__":
    main()
