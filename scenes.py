"""Ash Diver — Scene base + all scene implementations."""

import math
import random

import pygame

from settings import (
    SCREEN_W, SCREEN_H, TILE_SIZE, FPS,
    PLAYER_W, PLAYER_H, PLAYER_MAX_HP,
    T_AIR, T_SPAWN, T_CONTAINER, T_BALLOON_CRATE, T_ROAD, T_FLOOR,
    SOLID_TILES, TILE_SPRITES, TILE_COLORS, ASSETS_DIR,
    SCENE_AIRSHIP, SCENE_FREEFALL, SCENE_SURFACE, SCENE_DEATH,
    EXTRACTION_TIME, HORDE_WAVE_INTERVAL, HORDE_WAVE_COUNT, HORDE_SIRENS_PER_WAVE,
    FREEFALL_DURATION, FREEFALL_START_SPEED, FREEFALL_END_SPEED,
    FREEFALL_PLAYER_SPEED, LIGHTNING_TELEGRAPH_TIME, LIGHTNING_DAMAGE, CLOUD_DAMAGE,
    SIREN_H, SIREN_W, SIREN_HP,
    SCRAP_TYPES, WEAPON_STATS, SHOP_ITEMS,
)
from camera import Camera
from player import Player
from enemies import Siren
from items import Container, GroundItem, BalloonCrate, ITEM_DEFS
from hud import HUD, SpriteCache


# ── Scene base ───────────────────────────────────────────────────────────────

class Scene:
    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        return None

    def update(self, dt: float) -> str | None:
        return None

    def render(self, screen: pygame.Surface):
        pass


# ── Sprite loading helper ────────────────────────────────────────────────────

def load_sprite(name: str) -> pygame.Surface | None:
    return SpriteCache.get(name)


def get_tile_surface(tile_id: int) -> pygame.Surface | None:
    sprite_name = TILE_SPRITES.get(tile_id)
    if sprite_name:
        return load_sprite(sprite_name)
    return None


# ── Airship Scene ────────────────────────────────────────────────────────────

# Hand-authored airship layout: 40x15 tiles
AIRSHIP_WIDTH = 40
AIRSHIP_HEIGHT = 15

# Tile IDs for airship (reuse existing + airship-specific rendering)
_A = T_AIR
_W = 100  # metal wall
_F = 101  # metal floor
_N = 102  # window
_H = 103  # hatch
_Q = 104  # quartermaster NPC position
_S = T_SPAWN

AIRSHIP_LAYOUT = [
    [_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W],
    [_W,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_W],
    [_W,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_W],
    [_W,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_W],
    [_W,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_W],
    [_N,_A,_A,_A,_A,_A,_A,_A,_N,_A,_A,_A,_A,_A,_A,_A,_N,_A,_A,_A,_A,_A,_A,_A,_N,_A,_A,_A,_A,_A,_A,_A,_N,_A,_A,_A,_A,_A,_A,_N],
    [_W,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_W],
    [_W,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_W],
    [_W,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_W],
    [_W,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_W],
    [_W,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_W],
    [_W,_A,_A,_Q,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_S,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_A,_H,_A,_A,_W],
    [_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F],
    [_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W],
    [_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W,_W],
]

AIRSHIP_SOLID = {_W, _F}
AIRSHIP_TILE_SPRITES = {
    _W: "tile_metal_wall",
    _F: "tile_metal_floor",
    _N: "tile_window",
}


class AirshipScene(Scene):
    def __init__(self, game_state: dict):
        self.game_state = game_state
        self.grid = [row[:] for row in AIRSHIP_LAYOUT]
        self.grid_w = AIRSHIP_WIDTH
        self.grid_h = AIRSHIP_HEIGHT

        # Find spawn
        sx, sy = 19, 11
        for y, row in enumerate(self.grid):
            for x, val in enumerate(row):
                if val == _S:
                    sx, sy = x, y
                    self.grid[y][x] = _A

        self.player = Player(
            sx * TILE_SIZE + (TILE_SIZE - PLAYER_W) // 2,
            sy * TILE_SIZE + (TILE_SIZE - PLAYER_H),
        )
        self.player.hp = game_state.get("hp", PLAYER_MAX_HP)
        self.player.max_hp = PLAYER_MAX_HP

        map_pw = self.grid_w * TILE_SIZE
        map_ph = self.grid_h * TILE_SIZE
        self.camera = Camera(max(map_pw, SCREEN_W), max(map_ph, SCREEN_H))
        self.camera.snap(self.player.center_x, self.player.center_y)

        # Find special positions
        self.hatch_pos = None
        self.npc_pos = None
        for y, row in enumerate(AIRSHIP_LAYOUT):
            for x, val in enumerate(row):
                if val == _H:
                    self.hatch_pos = (x * TILE_SIZE, y * TILE_SIZE)
                elif val == _Q:
                    self.npc_pos = (x * TILE_SIZE, y * TILE_SIZE)

        self.font = pygame.font.SysFont(None, 28)
        self.font_small = pygame.font.SysFont(None, 22)
        self.font_large = pygame.font.SysFont(None, 48)
        self.prompt_text = ""
        self.prompt_timer = 0.0

        # Shop state
        self.shop_open = False
        self.shop_cursor = 0
        # Loadout: items bought for the next dive (reset each dive)
        if "loadout" not in self.game_state:
            self.game_state["loadout"] = []

    def _is_solid(self, col: int, row: int) -> bool:
        if 0 <= col < self.grid_w and 0 <= row < self.grid_h:
            return self.grid[row][col] in AIRSHIP_SOLID
        return True

    def _make_collision_grid(self) -> list[list[int]]:
        """Create a grid compatible with player collision using SOLID_TILES."""
        from settings import T_FILL
        cg = [[T_AIR] * self.grid_w for _ in range(self.grid_h)]
        for y in range(self.grid_h):
            for x in range(self.grid_w):
                if self.grid[y][x] in AIRSHIP_SOLID:
                    cg[y][x] = T_FILL
        return cg

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.shop_open:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_e:
                        self.shop_open = False
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.shop_cursor = max(0, self.shop_cursor - 1)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.shop_cursor = min(len(SHOP_ITEMS) - 1, self.shop_cursor + 1)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self._buy_item(self.shop_cursor)
                    continue

                if event.key == pygame.K_ESCAPE:
                    return "quit"
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    if self._near_hatch():
                        # New seed for each dive so the map is different every time
                        self.game_state["run_seed"] = self.game_state.get("run_seed", 0) + 1
                        return SCENE_FREEFALL
                if event.key == pygame.K_e:
                    if self._near_npc():
                        self.shop_open = True
                        self.shop_cursor = 0
        return None

    def _can_afford(self, item_idx: int) -> bool:
        item = SHOP_ITEMS[item_idx]
        for stype, needed in item["cost"].items():
            if self.game_state.get(stype, 0) < needed:
                return False
        return True

    def _buy_item(self, item_idx: int):
        if not self._can_afford(item_idx):
            self.prompt_text = "Not enough scrap!"
            self.prompt_timer = 2.0
            return
        item = SHOP_ITEMS[item_idx]
        # Deduct cost from stash
        for stype, needed in item["cost"].items():
            self.game_state[stype] = self.game_state.get(stype, 0) - needed
        # Add to loadout for next dive
        self.game_state["loadout"].append(item["id"])
        self.prompt_text = f"Bought {item['name']}!"
        self.prompt_timer = 2.0

    def _near_hatch(self) -> bool:
        if self.hatch_pos is None:
            return False
        dx = abs(self.player.center_x - (self.hatch_pos[0] + TILE_SIZE / 2))
        dy = abs(self.player.center_y - (self.hatch_pos[1] + TILE_SIZE / 2))
        return dx < TILE_SIZE * 2 and dy < TILE_SIZE * 2

    def _near_npc(self) -> bool:
        if self.npc_pos is None:
            return False
        dx = abs(self.player.center_x - (self.npc_pos[0] + TILE_SIZE / 2))
        dy = abs(self.player.center_y - (self.npc_pos[1] + TILE_SIZE / 2))
        return dx < TILE_SIZE * 2 and dy < TILE_SIZE * 2

    def update(self, dt: float) -> str | None:
        if self.prompt_timer > 0:
            self.prompt_timer -= dt
        if self.shop_open:
            return None

        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        cg = self._make_collision_grid()
        self.player.update(dt, cg, self.grid_w, self.grid_h)
        self.camera.update(self.player.center_x, self.player.center_y)
        return None

    def render(self, screen: pygame.Surface):
        screen.fill((50, 55, 65))

        cam_x, cam_y = int(self.camera.x), int(self.camera.y)

        for y in range(self.grid_h):
            for x in range(self.grid_w):
                tile = self.grid[y][x]
                if tile == _A or tile == _S:
                    continue
                sx = x * TILE_SIZE - cam_x
                sy = y * TILE_SIZE - cam_y
                if sx < -TILE_SIZE or sx > SCREEN_W or sy < -TILE_SIZE or sy > SCREEN_H:
                    continue
                sprite_name = AIRSHIP_TILE_SPRITES.get(tile)
                if sprite_name:
                    sprite = load_sprite(sprite_name)
                    if sprite:
                        screen.blit(sprite, (sx, sy))
                        continue
                # Fallback color
                color = {_W: (85, 90, 100), _F: (100, 105, 115), _N: (160, 210, 240)}.get(tile, (100, 100, 100))
                pygame.draw.rect(screen, color, (sx, sy, TILE_SIZE, TILE_SIZE))

        # Draw hatch
        if self.hatch_pos:
            hx = self.hatch_pos[0] - cam_x
            hy = self.hatch_pos[1] - cam_y
            hatch_sprite = load_sprite("obj_hatch")
            if hatch_sprite:
                screen.blit(hatch_sprite, (hx, hy))
            else:
                pygame.draw.rect(screen, (200, 200, 50), (hx, hy, TILE_SIZE, TILE_SIZE))
            if self._near_hatch():
                hint = self.font.render("[S/DOWN] Dive", True, (255, 255, 100))
                screen.blit(hint, (hx - hint.get_width() // 2 + 8, hy - 22))

        # Draw NPC
        if self.npc_pos:
            nx = self.npc_pos[0] - cam_x
            ny = self.npc_pos[1] - cam_y
            npc_sprite = load_sprite("obj_npc")
            if npc_sprite:
                screen.blit(npc_sprite, (nx, ny))
            else:
                pygame.draw.rect(screen, (60, 60, 140), (nx, ny, TILE_SIZE, TILE_SIZE))
            if self._near_npc():
                hint = self.font.render("[E] Talk", True, (255, 255, 100))
                screen.blit(hint, (nx - hint.get_width() // 2 + 8, ny - 22))

        # Draw player
        px, py = self.camera.apply(self.player.x, self.player.y)
        sprite = load_sprite(self.player.get_sprite_name())
        if sprite:
            if self.player.facing < 0:
                sprite = pygame.transform.flip(sprite, True, False)
            screen.blit(sprite, (px, py))
        else:
            pygame.draw.rect(screen, (255, 255, 255), (px, py, PLAYER_W, PLAYER_H))

        # Stash display
        stash_x, stash_y = 10, 10
        stash_text = "STASH: "
        for stype in SCRAP_TYPES:
            count = self.game_state.get(stype, 0)
            name = stype.replace("scrap_", "").replace("rare_", "R:").capitalize()
            stash_text += f"{name}:{count}  "
        st = self.font.render(stash_text, True, (200, 200, 200))
        screen.blit(st, (stash_x, stash_y))

        # Prompt text
        if self.prompt_timer > 0 and self.prompt_text:
            pt = self.font.render(self.prompt_text, True, (255, 255, 200))
            screen.blit(pt, (SCREEN_W // 2 - pt.get_width() // 2, SCREEN_H - 60))

        # Loadout display (top-right)
        loadout = self.game_state.get("loadout", [])
        if loadout:
            ly = 40
            lt = self.font_small.render("LOADOUT:", True, (180, 200, 180))
            screen.blit(lt, (SCREEN_W - 160, ly))
            for i, lid in enumerate(loadout):
                name = lid.replace("_", " ").title()
                lt2 = self.font_small.render(f"  {name}", True, (160, 180, 160))
                screen.blit(lt2, (SCREEN_W - 160, ly + 18 + i * 16))

        # Shop overlay
        if self.shop_open:
            self._render_shop(screen)

    def _render_shop(self, screen: pygame.Surface):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        title = self.font_large.render("QUARTERMASTER", True, (255, 255, 200))
        screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 60))

        # Stash display
        stash_text = "Stash: "
        for stype in SCRAP_TYPES:
            count = self.game_state.get(stype, 0)
            name = stype.replace("scrap_", "").replace("rare_", "R:").capitalize()
            stash_text += f"{name}:{count}  "
        st = self.font.render(stash_text, True, (180, 200, 180))
        screen.blit(st, (SCREEN_W // 2 - st.get_width() // 2, 110))

        # Items
        start_y = 155
        for i, item in enumerate(SHOP_ITEMS):
            y = start_y + i * 70
            selected = i == self.shop_cursor
            can_buy = self._can_afford(i)

            # Selection highlight
            if selected:
                pygame.draw.rect(screen, (60, 60, 80), (SCREEN_W // 2 - 250, y - 4, 500, 62))
                pygame.draw.rect(screen, (120, 120, 160), (SCREEN_W // 2 - 250, y - 4, 500, 62), 2)

            # Item icon
            ix = SCREEN_W // 2 - 230
            item_def = ITEM_DEFS.get(item["id"])
            if item_def:
                sprite = SpriteCache.get(item_def.sprite_name)
                if sprite:
                    screen.blit(pygame.transform.scale(sprite, (32, 32)), (ix, y + 4))

            # Name and description
            name_color = (255, 255, 255) if can_buy else (120, 120, 120)
            nt = self.font.render(item["name"], True, name_color)
            screen.blit(nt, (ix + 40, y))
            desc_color = (180, 180, 180) if can_buy else (100, 100, 100)
            dt_text = self.font_small.render(item["desc"], True, desc_color)
            screen.blit(dt_text, (ix + 40, y + 24))

            # Cost
            cost_parts = []
            for stype, needed in item["cost"].items():
                have = self.game_state.get(stype, 0)
                name = stype.replace("scrap_", "").replace("rare_", "R:").capitalize()
                color = (100, 255, 100) if have >= needed else (255, 80, 80)
                cost_parts.append((f"{name}:{needed}", color))
            cx = SCREEN_W // 2 + 100
            for part_text, color in cost_parts:
                ct = self.font_small.render(part_text, True, color)
                screen.blit(ct, (cx, y + 12))
                cx += ct.get_width() + 10

        # Bought loadout for this dive
        loadout = self.game_state.get("loadout", [])
        if loadout:
            ly = start_y + len(SHOP_ITEMS) * 70 + 10
            lt = self.font.render("Loadout for next dive:", True, (180, 200, 180))
            screen.blit(lt, (SCREEN_W // 2 - lt.get_width() // 2, ly))
            loadout_str = ", ".join(lid.replace("_", " ").title() for lid in loadout)
            ls = self.font_small.render(loadout_str, True, (160, 200, 160))
            screen.blit(ls, (SCREEN_W // 2 - ls.get_width() // 2, ly + 24))

        # Controls hint
        hint = self.font_small.render("UP/DOWN: Select    ENTER: Buy    E/ESC: Close", True, (130, 130, 150))
        screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 40))


# ── Freefall Scene ───────────────────────────────────────────────────────────

class FreefallScene(Scene):
    def __init__(self, game_state: dict):
        self.game_state = game_state
        self.player_x = SCREEN_W / 2.0
        self.player_y = 100.0
        self.player_hp = game_state.get("hp", PLAYER_MAX_HP)
        self.scroll_y = 0.0
        self.elapsed = 0.0
        self.done = False

        # Hazards
        self.rng = random.Random(game_state.get("run_seed", 42))
        self.clouds: list[dict] = []
        self.lightning_bolts: list[dict] = []
        self._spawn_hazards()

        self.invuln_timer = 0.0
        self.font = pygame.font.SysFont(None, 36)

    def _spawn_hazards(self):
        # Pre-generate clouds and lightning along the descent path
        total_distance = FREEFALL_DURATION * (FREEFALL_START_SPEED + FREEFALL_END_SPEED) / 2
        for _ in range(12):
            self.clouds.append({
                "x": self.rng.uniform(50, SCREEN_W - 150),
                "y": self.rng.uniform(200, total_distance - 200),
                "w": self.rng.uniform(80, 180),
                "h": self.rng.uniform(30, 60),
                "hit": False,
            })
        for _ in range(8):
            self.lightning_bolts.append({
                "x": self.rng.uniform(100, SCREEN_W - 100),
                "y": self.rng.uniform(300, total_distance - 300),
                "telegraph_shown": False,
                "struck": False,
                "timer": 0.0,
                "active_timer": 0.0,
            })

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
        return None

    def update(self, dt: float) -> str | None:
        if self.done:
            return None

        self.elapsed += dt
        if self.invuln_timer > 0:
            self.invuln_timer -= dt

        # Scroll speed increases over time
        progress = min(self.elapsed / FREEFALL_DURATION, 1.0)
        speed = FREEFALL_START_SPEED + (FREEFALL_END_SPEED - FREEFALL_START_SPEED) * progress
        self.scroll_y += speed * dt

        # Player horizontal movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player_x -= FREEFALL_PLAYER_SPEED * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player_x += FREEFALL_PLAYER_SPEED * dt
        self.player_x = max(10, min(SCREEN_W - PLAYER_W - 10, self.player_x))

        # Check cloud collisions
        player_rect = pygame.Rect(int(self.player_x), int(self.player_y), PLAYER_W, PLAYER_H)
        for cloud in self.clouds:
            cy = cloud["y"] - self.scroll_y + SCREEN_H / 2
            cloud_rect = pygame.Rect(int(cloud["x"]), int(cy), int(cloud["w"]), int(cloud["h"]))
            if player_rect.colliderect(cloud_rect) and not cloud["hit"]:
                cloud["hit"] = True
                self._take_damage(CLOUD_DAMAGE)

        # Check lightning
        for bolt in self.lightning_bolts:
            screen_y = bolt["y"] - self.scroll_y + SCREEN_H / 2
            if abs(screen_y - self.player_y) < 200 and not bolt["telegraph_shown"]:
                bolt["telegraph_shown"] = True
                bolt["timer"] = LIGHTNING_TELEGRAPH_TIME
            if bolt["telegraph_shown"] and not bolt["struck"]:
                bolt["timer"] -= dt
                if bolt["timer"] <= 0:
                    bolt["struck"] = True
                    bolt["active_timer"] = 0.3
                    # Check if player is near the strike
                    if abs(self.player_x + PLAYER_W / 2 - bolt["x"]) < 40:
                        self._take_damage(LIGHTNING_DAMAGE)
            if bolt["struck"] and bolt["active_timer"] > 0:
                bolt["active_timer"] -= dt

        # Check completion
        if self.elapsed >= FREEFALL_DURATION:
            self.done = True
            self.game_state["hp"] = self.player_hp
            return SCENE_SURFACE

        # Check death
        if self.player_hp <= 0:
            self.game_state["hp"] = 0
            return SCENE_DEATH

        return None

    def _take_damage(self, amount: int):
        if self.invuln_timer > 0:
            return
        self.player_hp -= amount
        self.invuln_timer = 1.0

    def render(self, screen: pygame.Surface):
        # Dark storm sky
        progress = min(self.elapsed / FREEFALL_DURATION, 1.0)
        bg_r = int(40 + 20 * progress)
        bg_g = int(45 + 15 * progress)
        bg_b = int(55 + 10 * progress)
        screen.fill((bg_r, bg_g, bg_b))

        # Parallax cloud layers (background)
        for i in range(3):
            layer_speed = 0.3 + i * 0.2
            for cx in range(0, SCREEN_W + 200, 200):
                cy = ((self.scroll_y * layer_speed + i * 300 + cx * 0.5) % (SCREEN_H + 100)) - 50
                alpha = 30 + i * 15
                cloud_surf = pygame.Surface((120, 40), pygame.SRCALPHA)
                cloud_surf.fill((100, 100, 120, alpha))
                screen.blit(cloud_surf, (cx - 60, cy))

        # Draw hazard clouds
        for cloud in self.clouds:
            cy = cloud["y"] - self.scroll_y + SCREEN_H / 2
            if -100 < cy < SCREEN_H + 100:
                cloud_surf = pygame.Surface((int(cloud["w"]), int(cloud["h"])), pygame.SRCALPHA)
                cloud_surf.fill((80, 80, 100, 140))
                screen.blit(cloud_surf, (int(cloud["x"]), int(cy)))

        # Draw lightning
        for bolt in self.lightning_bolts:
            screen_y = bolt["y"] - self.scroll_y + SCREEN_H / 2
            if bolt["telegraph_shown"] and not bolt["struck"]:
                # Telegraph: flashing line
                alpha = int(128 + 127 * math.sin(bolt["timer"] * 20))
                line_surf = pygame.Surface((4, SCREEN_H), pygame.SRCALPHA)
                line_surf.fill((255, 255, 100, alpha))
                screen.blit(line_surf, (int(bolt["x"]) - 2, 0))
            elif bolt["struck"] and bolt["active_timer"] > 0:
                # Active strike
                pygame.draw.line(screen, (255, 255, 200), (int(bolt["x"]), 0), (int(bolt["x"]), SCREEN_H), 3)

        # Draw player
        sprite = load_sprite("player_fall")
        px, py = int(self.player_x), int(self.player_y)
        if sprite:
            # Blink when invulnerable
            if self.invuln_timer > 0 and int(self.invuln_timer * 10) % 2:
                pass  # skip drawing (blink effect)
            else:
                screen.blit(sprite, (px, py))
        else:
            if not (self.invuln_timer > 0 and int(self.invuln_timer * 10) % 2):
                pygame.draw.rect(screen, (255, 255, 255), (px, py, PLAYER_W, PLAYER_H))

        # HP display
        for i in range(PLAYER_MAX_HP):
            color = (220, 40, 40) if i < self.player_hp else (80, 30, 30)
            pygame.draw.rect(screen, color, (10 + i * 16, 10, 12, 12))

        # Altitude indicator
        alt_text = self.font.render(f"ALT: {int((1.0 - progress) * 5000)}m", True, (200, 200, 200))
        screen.blit(alt_text, (SCREEN_W - alt_text.get_width() - 10, 10))


# ── Surface Scene ────────────────────────────────────────────────────────────

class SurfaceScene(Scene):
    def __init__(self, game_state: dict):
        self.game_state = game_state
        self.rng = random.Random(game_state.get("run_seed", 42))

        # Generate suburb map
        from gen_suburbs import SuburbsGenerator, SuburbsConfig
        cfg = SuburbsConfig(seed=game_state.get("run_seed", 42))
        gen = SuburbsGenerator(cfg)
        self.grid = gen.generate()
        self.grid_h = len(self.grid)
        self.grid_w = len(self.grid[0])

        # Find spawn
        spawn_x = gen.spawn_pos[0] * TILE_SIZE + (TILE_SIZE - PLAYER_W) // 2
        spawn_y = gen.spawn_pos[1] * TILE_SIZE + (TILE_SIZE - PLAYER_H)

        self.player = Player(spawn_x, spawn_y)
        self.player.hp = game_state.get("hp", PLAYER_MAX_HP)
        # Every diver drops with a sidearm and a handful of rounds
        self.player.weapon = "pistol"
        self.player.owned_weapons.add("pistol")
        self.player.ammo = 12

        # Apply loadout from shop purchases
        loadout = game_state.get("loadout", [])
        for item_id in loadout:
            if item_id == "ammo_crate":
                self.player.ammo += 12
            elif item_id == "pipe":
                self.player.owned_weapons.add("pipe")
            elif item_id == "medkit":
                self.player.medkits += 1
            elif item_id == "armor_vest":
                self.player.max_hp += 2
                self.player.hp = min(self.player.hp + 2, self.player.max_hp)
            elif item_id == "shotgun":
                self.player.owned_weapons.add("shotgun")
        # Clear loadout after applying (one-time use per dive)
        game_state["loadout"] = []

        self.camera = Camera(self.grid_w * TILE_SIZE, self.grid_h * TILE_SIZE)
        self.camera.snap(self.player.center_x, self.player.center_y)

        # HUD
        self.hud = HUD()

        # Containers
        self.containers: list[Container] = []
        for cx, cy, ctype in gen.container_positions:
            self.containers.append(Container(cx * TILE_SIZE, cy * TILE_SIZE, ctype))

        # Balloon crates
        self.balloon_crates: list[BalloonCrate] = []
        for bx, by in gen.balloon_positions:
            self.balloon_crates.append(BalloonCrate(bx * TILE_SIZE, by * TILE_SIZE))

        # Ground items
        self.ground_items: list[GroundItem] = []
        for gx, gy, item_id in gen.ground_items:
            self.ground_items.append(GroundItem(
                gx * TILE_SIZE + 2, gy * TILE_SIZE + 2, item_id
            ))

        # Enemies
        self.sirens: list[Siren] = []
        for zx, zy in gen.siren_spawn_zones:
            num = self.rng.randint(2, 4)
            for _ in range(num):
                sx = zx * TILE_SIZE + self.rng.randint(-32, 32)
                sy = zy * TILE_SIZE
                self.sirens.append(Siren(sx, sy))

        # Extraction state
        self.extracting = False
        self.extraction_timer = 0.0
        self.extraction_crate: BalloonCrate | None = None
        self.horde_wave = 0
        self.horde_timer = 0.0
        self.extraction_choice_active = False
        self.extraction_choice_crate: BalloonCrate | None = None

        # Pre-render tile surfaces
        self.tile_cache: dict[int, pygame.Surface | None] = {}
        for tid in set(t for row in self.grid for t in row):
            self.tile_cache[tid] = get_tile_surface(tid)

        self.font = pygame.font.SysFont(None, 28)
        self.font_large = pygame.font.SysFont(None, 48)

    def _mouse_to_world(self, mouse_pos: tuple[int, int]) -> tuple[float, float]:
        """Convert screen mouse position to world coordinates."""
        return mouse_pos[0] + self.camera.x, mouse_pos[1] + self.camera.y

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.extraction_choice_active:
                        self.extraction_choice_active = False
                    else:
                        return "quit"
                if event.key == pygame.K_TAB:
                    self.hud.toggle_inventory()
                if event.key == pygame.K_e and not self.hud.show_inventory:
                    result = self._interact()
                    if result:
                        return result
                if event.key == pygame.K_q:
                    self.player.swap_weapon()
                if event.key == pygame.K_h:
                    self.player.use_medkit()
                # Extraction choice
                if self.extraction_choice_active:
                    if event.key == pygame.K_1:
                        self._send_loot()
                        self.extraction_choice_active = False
                    elif event.key == pygame.K_2:
                        self._start_extraction()
                        self.extraction_choice_active = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.hud.show_inventory and not self.extraction_choice_active:
                    wx, wy = self._mouse_to_world(event.pos)
                    self._do_attack(wx, wy)

        return None

    def _interact(self) -> str | None:
        pr = self.player.rect

        # Check containers
        for container in self.containers:
            if not container.opened and pr.inflate(16, 16).colliderect(container.rect):
                loot = container.open(self.rng)
                for item_id, count in loot:
                    gi = GroundItem(
                        container.x + self.rng.randint(-8, 8),
                        container.y - 8,
                        item_id, count,
                    )
                    self.ground_items.append(gi)
                return None

        # Check balloon crates
        for crate in self.balloon_crates:
            if crate.state == BalloonCrate.STATE_INACTIVE and pr.inflate(16, 16).colliderect(crate.rect):
                self.extraction_choice_active = True
                self.extraction_choice_crate = crate
                return None

        return None

    def _do_attack(self, target_wx: float, target_wy: float):
        """Left click — melee or ranged depending on equipped weapon."""
        hitbox = self.player.attack(target_wx, target_wy)
        # If melee, check for enemy hits
        if hitbox is not None:
            stats = WEAPON_STATS.get(self.player.weapon or "pipe", WEAPON_STATS["pipe"])
            damage = stats.get("damage", 1)
            for siren in self.sirens:
                if siren.alive and hitbox.colliderect(siren.rect):
                    siren.take_damage(damage)

    def _send_loot(self):
        """Send loot via balloon — lose 50% of scrap, keep nothing."""
        counts = self.player.get_scrap_counts()
        for stype, count in counts.items():
            kept = count // 2
            self.game_state[stype] = self.game_state.get(stype, 0) + kept
        # Clear player inventory
        self.player.inventory = [None] * len(self.player.inventory)
        # Crate launches away
        if self.extraction_choice_crate:
            self.extraction_choice_crate.state = BalloonCrate.STATE_READY

    def _start_extraction(self):
        if self.extraction_choice_crate:
            self.extracting = True
            self.extraction_timer = 0.0
            self.extraction_crate = self.extraction_choice_crate
            self.extraction_crate.state = BalloonCrate.STATE_INFLATING
            self.horde_wave = 0
            self.horde_timer = 0.0
            self.hud.set_extraction(True, 0.0, EXTRACTION_TIME)

    def update(self, dt: float) -> str | None:
        if self.hud.show_inventory or self.extraction_choice_active:
            return None

        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update(dt, self.grid, self.grid_w, self.grid_h)
        self.camera.update(self.player.center_x, self.player.center_y)

        # Update ground items
        for gi in self.ground_items:
            gi.update(dt)

        # Pickup ground items
        pr = self.player.rect
        picked = []
        for i, gi in enumerate(self.ground_items):
            if pr.colliderect(gi.rect):
                if self.player.pick_up(gi.item_id, gi.count):
                    picked.append(i)
        for i in reversed(picked):
            self.ground_items.pop(i)

        # Update enemies
        for siren in self.sirens:
            siren.update(dt, self.grid, self.grid_w, self.grid_h,
                         self.player.center_x, self.player.center_y)
            # Siren attacks
            if siren.alive:
                dmg = siren.try_attack(pr)
                if dmg > 0:
                    self.player.take_damage(dmg)

        # Projectile vs enemy collisions
        for proj in self.player.projectiles:
            if not proj.alive:
                continue
            for siren in self.sirens:
                if siren.alive and proj.rect.colliderect(siren.rect):
                    siren.take_damage(proj.damage)
                    proj.alive = False
                    break

        # Clean up dead sirens (after death animation)
        for siren in self.sirens[:]:
            if siren.state == Siren.STATE_DEAD and siren.death_timer <= 0:
                loot = siren.drop_loot()
                for item_id, count in loot:
                    self.ground_items.append(GroundItem(siren.x, siren.y - 4, item_id, count))
                self.sirens.remove(siren)

        # Extraction logic
        if self.extracting:
            self.extraction_timer += dt
            self.hud.set_extraction(True, self.extraction_timer, EXTRACTION_TIME)

            # Horde waves
            self.horde_timer += dt
            if self.horde_timer >= HORDE_WAVE_INTERVAL and self.horde_wave < HORDE_WAVE_COUNT:
                self._spawn_horde_wave()
                self.horde_wave += 1
                self.horde_timer = 0.0

            # Check extraction complete
            if self.extraction_timer >= EXTRACTION_TIME:
                if self.extraction_crate:
                    self.extraction_crate.state = BalloonCrate.STATE_READY
                return self._complete_extraction()

        # Check player death
        if not self.player.alive:
            self.game_state["hp"] = 0
            return SCENE_DEATH

        return None

    def _spawn_horde_wave(self):
        for _ in range(HORDE_SIRENS_PER_WAVE):
            # Spawn from map edges
            if self.rng.random() < 0.5:
                sx = self.rng.choice([0, self.grid_w * TILE_SIZE - SIREN_W])
            else:
                sx = self.rng.randint(0, self.grid_w * TILE_SIZE)
            sy = (self.rng.randint(self.grid_h - 20, self.grid_h - 5)) * TILE_SIZE
            siren = Siren(sx, sy)
            siren.state = Siren.STATE_CHASE
            self.sirens.append(siren)

    def _complete_extraction(self) -> str:
        # Add all player scrap to stash
        counts = self.player.get_scrap_counts()
        for stype, count in counts.items():
            self.game_state[stype] = self.game_state.get(stype, 0) + count
        self.game_state["hp"] = self.player.hp
        self.game_state["extracted"] = True
        return SCENE_AIRSHIP

    def render(self, screen: pygame.Surface):
        # Sky background
        screen.fill(TILE_COLORS.get(T_AIR, (135, 206, 235)))

        cam_x, cam_y = int(self.camera.x), int(self.camera.y)

        # Visible tile range
        c0, c1, r0, r1 = self.camera.visible_tile_range()
        for row in range(r0, min(r1, self.grid_h)):
            for col in range(c0, min(c1, self.grid_w)):
                tile = self.grid[row][col]
                if tile == T_AIR or tile == T_SPAWN:
                    continue
                sx = col * TILE_SIZE - cam_x
                sy = row * TILE_SIZE - cam_y

                # Skip non-visible container/balloon markers (drawn as objects instead)
                if tile in (T_CONTAINER, T_BALLOON_CRATE):
                    continue

                surf = self.tile_cache.get(tile)
                if surf:
                    screen.blit(surf, (sx, sy))
                else:
                    color = TILE_COLORS.get(tile, (255, 0, 255))
                    pygame.draw.rect(screen, color, (sx, sy, TILE_SIZE, TILE_SIZE))

        # Draw containers
        for container in self.containers:
            cx, cy = self.camera.apply(container.x, container.y)
            if -TILE_SIZE < cx < SCREEN_W + TILE_SIZE and -TILE_SIZE < cy < SCREEN_H + TILE_SIZE:
                sprite = load_sprite(container.sprite_name)
                if container.opened:
                    # Darker version for opened containers
                    if sprite:
                        dark = sprite.copy()
                        dark.fill((100, 100, 100), special_flags=pygame.BLEND_MULT)
                        screen.blit(dark, (cx, cy))
                    else:
                        pygame.draw.rect(screen, (80, 60, 40), (cx, cy, TILE_SIZE, TILE_SIZE))
                else:
                    if sprite:
                        screen.blit(sprite, (cx, cy))
                    else:
                        pygame.draw.rect(screen, (140, 110, 60), (cx, cy, TILE_SIZE, TILE_SIZE))

        # Draw balloon crates (with pulsing glow to stand out)
        pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) * 0.5  # 0..1
        for crate in self.balloon_crates:
            bx, by = self.camera.apply(crate.x, crate.y)
            if -TILE_SIZE * 2 < bx < SCREEN_W + TILE_SIZE * 2 and -TILE_SIZE * 2 < by < SCREEN_H + TILE_SIZE * 2:
                # Pulsing glow ring behind the crate
                glow_r = int(12 + 6 * pulse)
                glow_alpha = int(80 + 80 * pulse)
                glow_color = (255, 180, 40) if crate.state == BalloonCrate.STATE_INACTIVE else (255, 100, 30)
                glow_surf = pygame.Surface((glow_r * 2 + TILE_SIZE, glow_r * 2 + TILE_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*glow_color, glow_alpha),
                                   (glow_r + TILE_SIZE // 2, glow_r + TILE_SIZE // 2), glow_r + TILE_SIZE // 2)
                screen.blit(glow_surf, (bx - glow_r, by - glow_r))

                sprite = load_sprite(crate.sprite_name)
                if sprite:
                    screen.blit(sprite, (bx, by))
                else:
                    color = {
                        BalloonCrate.STATE_INACTIVE: (230, 140, 20),
                        BalloonCrate.STATE_INFLATING: (255, 130, 50),
                        BalloonCrate.STATE_READY: (255, 100, 30),
                    }.get(crate.state, (230, 140, 20))
                    pygame.draw.rect(screen, color, (bx, by, TILE_SIZE, TILE_SIZE))

                # "EXTRACT" label above inactive crates
                if crate.state == BalloonCrate.STATE_INACTIVE:
                    label_alpha = int(160 + 95 * pulse)
                    label = self.font.render("EXTRACT", True, (255, 220, 60))
                    label.set_alpha(label_alpha)
                    screen.blit(label, (bx - label.get_width() // 2 + TILE_SIZE // 2, by - 18))

        # Draw ground items
        for gi in self.ground_items:
            gx, gy = self.camera.apply(gi.x, gi.y + gi.draw_y_offset)
            if -12 < gx < SCREEN_W + 12 and -12 < gy < SCREEN_H + 12:
                sprite = load_sprite(gi.sprite_name)
                if sprite:
                    screen.blit(sprite, (gx, gy))
                else:
                    pygame.draw.rect(screen, (200, 200, 100), (gx, gy, 8, 8))

        # Draw sirens
        for siren in self.sirens:
            ex, ey = self.camera.apply(siren.x, siren.y)
            if -SIREN_W < ex < SCREEN_W + SIREN_W and -SIREN_H < ey < SCREEN_H + SIREN_H:
                sprite = load_sprite(siren.get_sprite_name())
                if sprite:
                    if siren.facing < 0:
                        sprite = pygame.transform.flip(sprite, True, False)
                    screen.blit(sprite, (ex, ey))
                else:
                    color = (220, 200, 190) if siren.alive else (100, 80, 70)
                    pygame.draw.rect(screen, color, (ex, ey, SIREN_W, SIREN_H))
                # HP bar for damaged sirens
                if siren.alive and siren.hp < SIREN_HP:
                    bar_w = SIREN_W
                    bar_h = 3
                    fill = int(bar_w * siren.hp / SIREN_HP)
                    pygame.draw.rect(screen, (60, 0, 0), (ex, ey - 5, bar_w, bar_h))
                    pygame.draw.rect(screen, (220, 40, 40), (ex, ey - 5, fill, bar_h))

        # Draw projectiles
        for proj in self.player.projectiles:
            px, py = self.camera.apply(proj.x, proj.y)
            pygame.draw.rect(screen, (255, 255, 100), (px, py, 4, 3))

        # Draw player
        px, py = self.camera.apply(self.player.x, self.player.y)
        if self.player.invuln_timer > 0 and int(self.player.invuln_timer * 10) % 2:
            pass  # blink
        else:
            sprite = load_sprite(self.player.get_sprite_name())
            if sprite:
                if self.player.facing < 0:
                    sprite = pygame.transform.flip(sprite, True, False)
                screen.blit(sprite, (px, py))
            else:
                pygame.draw.rect(screen, (255, 255, 255), (px, py, PLAYER_W, PLAYER_H))

        # HUD
        self.hud.render(screen, self.player)

        # Extraction choice overlay
        if self.extraction_choice_active:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))

            title = self.font_large.render("BALLOON CRATE", True, (255, 255, 200))
            screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 80))

            opt1 = self.font.render("[1] Send loot (lose 50%, stay behind)", True, (200, 200, 200))
            opt2 = self.font.render("[2] Ride out (extract with all loot, survive 30s)", True, (200, 200, 200))
            esc = self.font.render("[ESC] Cancel", True, (150, 150, 150))
            screen.blit(opt1, (SCREEN_W // 2 - opt1.get_width() // 2, SCREEN_H // 2 - 20))
            screen.blit(opt2, (SCREEN_W // 2 - opt2.get_width() // 2, SCREEN_H // 2 + 15))
            screen.blit(esc, (SCREEN_W // 2 - esc.get_width() // 2, SCREEN_H // 2 + 60))

        # Balloon crate edge indicator
        for crate in self.balloon_crates:
            if crate.state == BalloonCrate.STATE_INACTIVE:
                cx, cy = self.camera.apply(crate.x + TILE_SIZE / 2, crate.y + TILE_SIZE / 2)
                if cx < 0 or cx > SCREEN_W or cy < 0 or cy > SCREEN_H:
                    ix = max(10, min(SCREEN_W - 10, cx))
                    iy = max(10, min(SCREEN_H - 40, cy))
                    pygame.draw.circle(screen, (255, 80, 80), (ix, iy), 6)
                    marker = self.font.render("!", True, (255, 255, 255))
                    screen.blit(marker, (ix - 3, iy - 8))

        # Crosshair at mouse position
        if not self.hud.show_inventory and not self.extraction_choice_active:
            mx, my = pygame.mouse.get_pos()
            size = 6
            color = (255, 255, 255, 180)
            pygame.draw.line(screen, color, (mx - size, my), (mx + size, my))
            pygame.draw.line(screen, color, (mx, my - size), (mx, my + size))


# ── Death Scene ──────────────────────────────────────────────────────────────

class DeathScene(Scene):
    def __init__(self, game_state: dict):
        self.game_state = game_state
        self.font_large = pygame.font.SysFont(None, 64)
        self.font = pygame.font.SysFont(None, 28)
        self.fade_in = 0.0

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # Reset for next run
                    self.game_state["hp"] = PLAYER_MAX_HP
                    self.game_state["run_seed"] = self.game_state.get("run_seed", 42) + 1
                    self.game_state.pop("extracted", None)
                    return SCENE_AIRSHIP
        return None

    def update(self, dt: float) -> str | None:
        self.fade_in = min(self.fade_in + dt * 2, 1.0)
        return None

    def render(self, screen: pygame.Surface):
        screen.fill((15, 10, 10))

        alpha = int(255 * self.fade_in)

        title = self.font_large.render("ASH DIVER LOST", True, (200, 50, 50))
        title.set_alpha(alpha)
        screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 80))

        subtitle = self.font.render("All gathered materials have been lost.", True, (180, 180, 180))
        subtitle.set_alpha(alpha)
        screen.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, SCREEN_H // 2 - 20))

        hint = self.font.render("Press ENTER to dive again", True, (150, 150, 150))
        if self.fade_in >= 1.0:
            screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 40))
