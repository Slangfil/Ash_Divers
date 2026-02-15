"""Ash Diver — Siren enemy AI + spawning."""

import random

import pygame

from settings import (
    TILE_SIZE, SOLID_TILES, GRAVITY, MAX_FALL,
    SIREN_HP, SIREN_SPEED, SIREN_DETECT_RANGE,
    SIREN_ATTACK_RANGE, SIREN_ATTACK_DAMAGE, SIREN_ATTACK_COOLDOWN,
    SIREN_JUMP_VEL, SIREN_W, SIREN_H,
    SCRAP_WOOD, SCRAP_METAL,
)


class Siren:
    STATE_WANDER = 0
    STATE_CHASE = 1
    STATE_ATTACK = 2
    STATE_DEAD = 3

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing = 1

        self.hp = SIREN_HP
        self.alive = True
        self.state = self.STATE_WANDER

        self.attack_cooldown = 0.0
        self.wander_timer = 0.0
        self.wander_dir = random.choice([-1, 1])
        self.death_timer = 0.0

        self.walk_timer = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), SIREN_W, SIREN_H)

    @property
    def center_x(self) -> float:
        return self.x + SIREN_W / 2

    @property
    def center_y(self) -> float:
        return self.y + SIREN_H / 2

    def take_damage(self, amount: int):
        if not self.alive:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.state = self.STATE_DEAD
            self.death_timer = 0.6

    def update(self, dt: float, grid: list[list[int]], grid_w: int, grid_h: int,
               player_x: float, player_y: float):
        if self.state == self.STATE_DEAD:
            self.death_timer -= dt
            return

        # Distance to player
        dx = player_x - self.center_x
        dy = player_y - self.center_y
        dist = (dx * dx + dy * dy) ** 0.5

        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        # State transitions
        if self.state == self.STATE_WANDER:
            if dist < SIREN_DETECT_RANGE:
                self.state = self.STATE_CHASE
        elif self.state == self.STATE_CHASE:
            if dist < SIREN_ATTACK_RANGE and self.attack_cooldown <= 0:
                self.state = self.STATE_ATTACK
            elif dist > SIREN_DETECT_RANGE * 1.5:
                self.state = self.STATE_WANDER
        elif self.state == self.STATE_ATTACK:
            self.state = self.STATE_CHASE

        # Behavior
        if self.state == self.STATE_WANDER:
            self._do_wander(dt)
        elif self.state == self.STATE_CHASE:
            self._do_chase(dt, dx, grid, grid_w, grid_h)

        # Walk animation
        if abs(self.vx) > 1:
            self.walk_timer += dt * 6
        else:
            self.walk_timer = 0

        # Physics
        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL)
        self.x += self.vx * dt
        self._resolve_x(grid, grid_w, grid_h)
        self.y += self.vy * dt
        self._resolve_y(grid, grid_w, grid_h)

        # Map boundary clamping
        map_w_px = grid_w * TILE_SIZE
        map_h_px = grid_h * TILE_SIZE
        self.x = max(0, min(self.x, map_w_px - SIREN_W))
        self.y = max(0, min(self.y, map_h_px - SIREN_H))

    def _do_wander(self, dt: float):
        self.wander_timer -= dt
        if self.wander_timer <= 0:
            self.wander_dir = random.choice([-1, 0, 0, 1])  # often stop
            self.wander_timer = random.uniform(1.0, 3.0)
        self.vx = self.wander_dir * SIREN_SPEED * 0.4
        if self.wander_dir != 0:
            self.facing = self.wander_dir

    def _do_chase(self, dt: float, dx: float,
                  grid: list[list[int]], grid_w: int, grid_h: int):
        if dx > 5:
            self.vx = SIREN_SPEED
            self.facing = 1
        elif dx < -5:
            self.vx = -SIREN_SPEED
            self.facing = -1
        else:
            self.vx = 0

        # Jump if blocked
        if self.on_ground and self._is_blocked_ahead(grid, grid_w, grid_h):
            self.vy = SIREN_JUMP_VEL

    def _is_blocked_ahead(self, grid: list[list[int]], grid_w: int, grid_h: int) -> bool:
        check_x = int(self.center_x + self.facing * (SIREN_W / 2 + 2)) // TILE_SIZE
        check_y = int(self.center_y) // TILE_SIZE
        if 0 <= check_x < grid_w and 0 <= check_y < grid_h:
            return grid[check_y][check_x] in SOLID_TILES
        return False

    def try_attack(self, player_rect: pygame.Rect) -> int:
        """Returns damage dealt (0 if no attack)."""
        if self.state != self.STATE_ATTACK:
            return 0
        if self.attack_cooldown > 0:
            return 0
        self.attack_cooldown = SIREN_ATTACK_COOLDOWN
        # Check if player is within attack range
        attack_rect = pygame.Rect(
            int(self.center_x + self.facing * SIREN_W / 2 - SIREN_ATTACK_RANGE / 2),
            int(self.y),
            SIREN_ATTACK_RANGE * 2,
            SIREN_H,
        )
        if attack_rect.colliderect(player_rect):
            return SIREN_ATTACK_DAMAGE
        return 0

    def drop_loot(self) -> list[tuple[str, int]]:
        """Roll loot on death. Returns [(item_id, count), ...]."""
        if random.random() < 0.4:
            item = random.choice([SCRAP_WOOD, SCRAP_METAL])
            return [(item, 1)]
        return []

    # ── Collision (same as player) ───────────────────────────────────────────

    def _get_overlapping_tiles(self, grid, grid_w, grid_h):
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

    def _resolve_x(self, grid, grid_w, grid_h):
        for _col, _row, tile_rect in self._get_overlapping_tiles(grid, grid_w, grid_h):
            if self.vx > 0:
                self.x = tile_rect.left - SIREN_W
            elif self.vx < 0:
                self.x = tile_rect.right
            else:
                r = self.rect
                overlap_left = r.right - tile_rect.left
                overlap_right = tile_rect.right - r.left
                if overlap_left < overlap_right:
                    self.x = tile_rect.left - SIREN_W
                else:
                    self.x = tile_rect.right

    def _resolve_y(self, grid, grid_w, grid_h):
        self.on_ground = False
        for _col, _row, tile_rect in self._get_overlapping_tiles(grid, grid_w, grid_h):
            if self.vy > 0:
                self.y = tile_rect.top - SIREN_H
                self.vy = 0.0
                self.on_ground = True
            elif self.vy < 0:
                self.y = tile_rect.bottom
                self.vy = 0.0
            else:
                r = self.rect
                if (r.bottom - tile_rect.top) < (tile_rect.bottom - r.top):
                    self.y = tile_rect.top - SIREN_H
                    self.on_ground = True
                else:
                    self.y = tile_rect.bottom

    # ── Sprite state ─────────────────────────────────────────────────────────

    def get_sprite_name(self) -> str:
        if self.state == self.STATE_DEAD:
            return "siren_death"
        if self.state == self.STATE_ATTACK:
            return "siren_attack"
        if abs(self.vx) > 1:
            frame = int(self.walk_timer) % 2
            return f"siren_walk{frame + 1}"
        return "siren_idle"
