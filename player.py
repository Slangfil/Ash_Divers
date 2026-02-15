"""Ash Diver — Player: physics, health, inventory, combat."""

import math
import random

import pygame

from settings import (
    PLAYER_W, PLAYER_H, GRAVITY, JUMP_VEL, MOVE_SPEED, MAX_FALL,
    PLAYER_MAX_HP, PLAYER_INVULN_TIME, INVENTORY_SIZE, TILE_SIZE,
    SOLID_TILES, CLIMBABLE_TILES, LADDER_CLIMB_SPEED, WEAPON_STATS,
    MELEE_RANGE, MELEE_COOLDOWN, RANGED_COOLDOWN, RANGED_SPEED, RANGED_LIFETIME,
)
from items import ITEM_DEFS, InvSlot, GroundItem


# ── Projectile ───────────────────────────────────────────────────────────────

class Projectile:
    def __init__(self, x: float, y: float, vx: float, vy: float, damage: int):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.alive = True
        self.timer = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), 4, 3)

    def update(self, dt: float, grid: list[list[int]], grid_w: int, grid_h: int):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.timer += dt
        if self.timer > RANGED_LIFETIME:
            self.alive = False
            return
        # Check wall collision
        col = int(self.x + 2) // TILE_SIZE
        row = int(self.y + 1) // TILE_SIZE
        if 0 <= col < grid_w and 0 <= row < grid_h:
            if grid[row][col] in SOLID_TILES:
                self.alive = False
        # Out of bounds
        if col < 0 or col >= grid_w or row < 0 or row >= grid_h:
            self.alive = False


# ── Player ───────────────────────────────────────────────────────────────────

class Player:
    # All weapons the player can cycle through (None = fists)
    WEAPON_CYCLE = [None, "pipe", "pistol", "shotgun"]

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing = 1  # 1 = right, -1 = left

        # Health
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.invuln_timer = 0.0
        self.alive = True

        # Inventory
        self.inventory: list[InvSlot | None] = [None] * INVENTORY_SIZE
        self.weapon: str | None = None  # "pipe", "pistol", or None (fists)
        self.owned_weapons: set[str] = set()  # weapons we've picked up
        self.ammo = 0

        # Consumables
        self.medkits = 0

        # Combat
        self.attack_timer = 0.0
        self.attacking = False
        self.attack_anim_timer = 0.0

        # Projectiles owned by this player
        self.projectiles: list[Projectile] = []

        # Ladder state
        self.on_ladder = False
        self.climb_input = 0  # -1 up, +1 down, 0 none

        # Animation state
        self.walk_timer = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), PLAYER_W, PLAYER_H)

    @property
    def center_x(self) -> float:
        return self.x + PLAYER_W / 2

    @property
    def center_y(self) -> float:
        return self.y + PLAYER_H / 2

    # ── Weapon swap ─────────────────────────────────────────────────────────

    def swap_weapon(self):
        """Cycle to the next owned weapon. None → pipe → pistol → None ..."""
        available = [None]  # fists always available
        for w in self.WEAPON_CYCLE:
            if w is not None and w in self.owned_weapons:
                available.append(w)

        if len(available) <= 1:
            return  # nothing to swap to

        try:
            idx = available.index(self.weapon)
        except ValueError:
            idx = -1
        self.weapon = available[(idx + 1) % len(available)]

    @property
    def weapon_display_name(self) -> str:
        if self.weapon is None:
            return "FISTS"
        return self.weapon.upper()

    @property
    def is_ranged(self) -> bool:
        if self.weapon is None:
            return False
        stats = WEAPON_STATS.get(self.weapon)
        return stats is not None and stats["type"] == "ranged"

    @property
    def is_melee(self) -> bool:
        return not self.is_ranged

    # ── Physics ──────────────────────────────────────────────────────────────

    def _is_on_ladder(self, grid, grid_w, grid_h) -> bool:
        col = int(self.center_x) // TILE_SIZE
        row = int(self.center_y) // TILE_SIZE
        if 0 <= col < grid_w and 0 <= row < grid_h:
            if grid[row][col] in CLIMBABLE_TILES:
                return True
        row_feet = int(self.y + PLAYER_H - 2) // TILE_SIZE
        if 0 <= col < grid_w and 0 <= row_feet < grid_h:
            if grid[row_feet][col] in CLIMBABLE_TILES:
                return True
        return False

    def update(self, dt: float, grid: list[list[int]], grid_w: int, grid_h: int):
        # Timers
        if self.invuln_timer > 0:
            self.invuln_timer -= dt
        if self.attack_timer > 0:
            self.attack_timer -= dt
        if self.attack_anim_timer > 0:
            self.attack_anim_timer -= dt
        else:
            self.attacking = False

        # Walk animation
        if abs(self.vx) > 1:
            self.walk_timer += dt * 8
        else:
            self.walk_timer = 0

        # Ladder check
        touching_ladder = self._is_on_ladder(grid, grid_w, grid_h)
        if touching_ladder and self.climb_input != 0:
            self.on_ladder = True
        elif not touching_ladder:
            self.on_ladder = False

        if self.on_ladder:
            self.vy = self.climb_input * LADDER_CLIMB_SPEED
            self.x += self.vx * 0.5 * dt
            self._resolve_x(grid, grid_w, grid_h)
            self.y += self.vy * dt
            self._resolve_y(grid, grid_w, grid_h)
        else:
            self.vy = min(self.vy + GRAVITY * dt, MAX_FALL)
            self.x += self.vx * dt
            self._resolve_x(grid, grid_w, grid_h)
            self.y += self.vy * dt
            self._resolve_y(grid, grid_w, grid_h)

        # Map boundary clamping
        map_w_px = grid_w * TILE_SIZE
        map_h_px = grid_h * TILE_SIZE
        if self.x < 0:
            self.x = 0
            self.vx = 0
        elif self.x + PLAYER_W > map_w_px:
            self.x = map_w_px - PLAYER_W
            self.vx = 0
        if self.y < 0:
            self.y = 0
            self.vy = 0
        elif self.y + PLAYER_H > map_h_px:
            self.y = map_h_px - PLAYER_H
            self.vy = 0
            self.on_ground = True

        # Update projectiles
        for p in self.projectiles:
            p.update(dt, grid, grid_w, grid_h)
        self.projectiles = [p for p in self.projectiles if p.alive]

    def handle_input(self, keys: pygame.key.ScancodeWrapper):
        move = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move += 1
        self.vx = move * MOVE_SPEED
        if move != 0:
            self.facing = move

        # Vertical input (for ladders)
        climb = 0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            climb -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            climb += 1
        self.climb_input = climb

        # Jump — works on ground or on ladder
        if keys[pygame.K_SPACE]:
            if self.on_ladder:
                self.on_ladder = False
                self.vy = JUMP_VEL
            elif self.on_ground:
                self.vy = JUMP_VEL

    # ── Collision ────────────────────────────────────────────────────────────

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
                self.x = tile_rect.left - PLAYER_W
            elif self.vx < 0:
                self.x = tile_rect.right
            else:
                r = self.rect
                overlap_left = r.right - tile_rect.left
                overlap_right = tile_rect.right - r.left
                if overlap_left < overlap_right:
                    self.x = tile_rect.left - PLAYER_W
                else:
                    self.x = tile_rect.right

    def _resolve_y(self, grid, grid_w, grid_h):
        self.on_ground = False
        for _col, _row, tile_rect in self._get_overlapping_tiles(grid, grid_w, grid_h):
            if self.vy > 0:
                self.y = tile_rect.top - PLAYER_H
                self.vy = 0.0
                self.on_ground = True
            elif self.vy < 0:
                self.y = tile_rect.bottom
                self.vy = 0.0
            else:
                r = self.rect
                overlap_top = r.bottom - tile_rect.top
                overlap_bottom = tile_rect.bottom - r.top
                if overlap_top < overlap_bottom:
                    self.y = tile_rect.top - PLAYER_H
                    self.on_ground = True
                else:
                    self.y = tile_rect.bottom

    # ── Health ───────────────────────────────────────────────────────────────

    def take_damage(self, amount: int):
        if self.invuln_timer > 0 or not self.alive:
            return
        self.hp -= amount
        self.invuln_timer = PLAYER_INVULN_TIME
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def use_medkit(self) -> bool:
        if self.medkits <= 0 or self.hp >= self.max_hp:
            return False
        self.medkits -= 1
        self.hp = min(self.hp + 2, self.max_hp)
        return True

    # ── Combat ───────────────────────────────────────────────────────────────

    def attack(self, target_wx: float, target_wy: float) -> pygame.Rect | None:
        """Unified attack toward a world-space target.

        Returns a melee hitbox if melee, or None.
        Ranged attacks spawn projectiles internally.
        """
        # Face toward target
        if target_wx > self.center_x:
            self.facing = 1
        elif target_wx < self.center_x:
            self.facing = -1

        if self.is_ranged:
            self._ranged_attack(target_wx, target_wy)
            return None
        else:
            return self._melee_attack(target_wx, target_wy)

    def _melee_attack(self, target_wx: float, target_wy: float) -> pygame.Rect | None:
        if self.attack_timer > 0:
            return None
        stats = WEAPON_STATS.get(self.weapon or "pipe", WEAPON_STATS["pipe"])
        self.attack_timer = stats["cooldown"]
        self.attacking = True
        self.attack_anim_timer = 0.2

        # Direction toward target
        dx = target_wx - self.center_x
        dy = target_wy - self.center_y
        dist = max(1.0, (dx * dx + dy * dy) ** 0.5)
        nx = dx / dist
        ny = dy / dist

        rng = stats["range"]
        cx = self.center_x + nx * (PLAYER_W / 2 + rng / 2)
        cy = self.center_y + ny * (PLAYER_H / 4)
        return pygame.Rect(
            int(cx - rng / 2),
            int(cy - rng / 2),
            rng,
            rng,
        )

    def _ranged_attack(self, target_wx: float, target_wy: float) -> bool:
        if self.attack_timer > 0:
            return False
        stats = WEAPON_STATS.get(self.weapon)
        if stats is None or stats["type"] != "ranged":
            return False
        ammo_cost = stats.get("ammo_cost", 1)
        if self.ammo < ammo_cost:
            return False

        self.attack_timer = stats["cooldown"]
        self.ammo -= ammo_cost
        self.attacking = True
        self.attack_anim_timer = 0.15

        # Old unreliable guns — damage varies between 1 and base damage
        base_dmg = stats["damage"]
        damage = random.randint(max(1, base_dmg - 1), base_dmg)

        # Aim toward mouse target
        px = self.center_x
        py = self.center_y - 2
        dx = target_wx - px
        dy = target_wy - py
        dist = max(1.0, (dx * dx + dy * dy) ** 0.5)
        base_angle = math.atan2(dy, dx)
        speed = stats["speed"]
        pellets = stats.get("pellets", 1)
        spread = stats.get("spread", 0.0)

        for i in range(pellets):
            if pellets == 1:
                angle = base_angle
            else:
                # Spread pellets evenly across the spread arc
                angle = base_angle + spread * (i / (pellets - 1) - 0.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.projectiles.append(Projectile(px, py, vx, vy, damage))
        return True

    # ── Inventory ────────────────────────────────────────────────────────────

    def pick_up(self, item_id: str, count: int = 1) -> bool:
        defn = ITEM_DEFS.get(item_id)
        if defn is None:
            return False

        # Weapons go into owned set; auto-equip if nothing equipped
        if defn.item_type == "weapon":
            self.owned_weapons.add(item_id)
            if self.weapon is None:
                self.weapon = item_id
            return True

        # Ammo adds directly
        if defn.item_type == "ammo":
            self.ammo += count * 6
            return True

        # Consumables
        if defn.item_type == "consumable":
            if item_id == "medkit":
                self.medkits += count
            return True

        # Try to stack
        for slot in self.inventory:
            if slot and slot.item_id == item_id and slot.count < defn.stack_size:
                add = min(count, defn.stack_size - slot.count)
                slot.count += add
                count -= add
                if count <= 0:
                    return True

        # Try to find empty slot
        while count > 0:
            for i, slot in enumerate(self.inventory):
                if slot is None:
                    add = min(count, defn.stack_size)
                    self.inventory[i] = InvSlot(item_id, add)
                    count -= add
                    break
            else:
                return False  # inventory full
        return True

    def count_item(self, item_id: str) -> int:
        total = 0
        for slot in self.inventory:
            if slot and slot.item_id == item_id:
                total += slot.count
        return total

    def get_scrap_counts(self) -> dict[str, int]:
        from settings import SCRAP_TYPES
        return {s: self.count_item(s) for s in SCRAP_TYPES}

    # ── Sprite state ─────────────────────────────────────────────────────────

    def get_sprite_name(self) -> str:
        if not self.alive:
            return "player_death"
        if self.attacking:
            return "player_attack"
        if self.on_ladder:
            frame = int(self.walk_timer) % 2
            return f"player_walk{frame + 1}" if self.climb_input != 0 else "player_idle"
        if not self.on_ground:
            if self.vy < 0:
                return "player_jump"
            return "player_fall"
        if abs(self.vx) > 1:
            frame = int(self.walk_timer) % 2
            return f"player_walk{frame + 1}"
        return "player_idle"
