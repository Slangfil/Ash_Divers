#!/usr/bin/env python3
"""Ash Diver — Sprite Generator

Run once (or re-run) to generate all PNG assets into assets/.
Uses Pillow only — no external art required.
"""

from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).parent / "assets"

# ── Helpers ──────────────────────────────────────────────────────────────────


def make(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def save(img: Image.Image, name: str):
    img.save(ASSETS / f"{name}.png")


# ── Tiles (16x16) ───────────────────────────────────────────────────────────


def gen_tiles():
    # dirt
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(139, 90, 43))
    for pos in [(3, 2), (10, 5), (6, 11), (13, 8), (1, 14)]:
        d.point(pos, fill=(120, 75, 35))
    save(img, "tile_dirt")

    # grass-top
    img, d = make(16, 16)
    d.rectangle([0, 4, 15, 15], fill=(139, 90, 43))
    d.rectangle([0, 0, 15, 4], fill=(34, 139, 34))
    for x in range(0, 16, 3):
        d.line([(x, 0), (x, -2)], fill=(0, 100, 0), width=1)
    save(img, "tile_grass_top")

    # stone
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(128, 128, 128))
    d.line([(0, 5), (15, 5)], fill=(100, 100, 100))
    d.line([(8, 0), (8, 5)], fill=(100, 100, 100))
    d.line([(4, 5), (4, 15)], fill=(100, 100, 100))
    d.line([(12, 5), (12, 15)], fill=(100, 100, 100))
    save(img, "tile_stone")

    # suburb-road
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(60, 60, 60))
    d.line([(7, 0), (7, 5)], fill=(200, 200, 50))
    d.line([(7, 10), (7, 15)], fill=(200, 200, 50))
    save(img, "tile_road")

    # suburb-wall
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(180, 170, 150))
    d.line([(0, 7), (15, 7)], fill=(160, 150, 130))
    d.line([(7, 0), (7, 7)], fill=(160, 150, 130))
    d.line([(3, 7), (3, 15)], fill=(160, 150, 130))
    d.line([(11, 7), (11, 15)], fill=(160, 150, 130))
    save(img, "tile_wall")

    # suburb-floor
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(160, 140, 110))
    for y in range(0, 16, 4):
        d.line([(0, y), (15, y)], fill=(140, 120, 90))
    save(img, "tile_floor")

    # suburb-roof
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(140, 60, 60))
    d.line([(0, 0), (15, 0)], fill=(120, 50, 50))
    d.line([(0, 8), (15, 8)], fill=(120, 50, 50))
    save(img, "tile_roof")

    # rubble
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(0, 0, 0, 0))
    d.polygon([(2, 14), (6, 8), (10, 14)], fill=(150, 140, 120))
    d.polygon([(8, 14), (12, 6), (15, 14)], fill=(130, 120, 100))
    d.polygon([(0, 14), (3, 10), (5, 14)], fill=(140, 130, 110))
    save(img, "tile_rubble")

    # sky
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(135, 206, 235))
    save(img, "tile_sky")

    # sky dark (storm)
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(40, 45, 55))
    save(img, "tile_sky_dark")

    # ladder
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(0, 0, 0, 0))
    # Side rails
    d.rectangle([2, 0, 3, 15], fill=(160, 120, 50))
    d.rectangle([12, 0, 13, 15], fill=(160, 120, 50))
    # Rungs
    for ry in [2, 6, 10, 14]:
        d.rectangle([3, ry, 12, ry + 1], fill=(180, 140, 60))
    save(img, "tile_ladder")

    # airship metal floor
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(100, 105, 115))
    d.line([(0, 0), (15, 0)], fill=(80, 85, 95))
    d.line([(4, 0), (4, 15)], fill=(90, 95, 105))
    d.line([(12, 0), (12, 15)], fill=(90, 95, 105))
    save(img, "tile_metal_floor")

    # airship metal wall
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(85, 90, 100))
    d.rectangle([2, 2, 13, 13], fill=(90, 95, 105))
    for y in [4, 8, 12]:
        d.line([(0, y), (15, y)], fill=(75, 80, 90))
    save(img, "tile_metal_wall")

    # airship window
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(85, 90, 100))
    d.rectangle([2, 2, 13, 13], fill=(135, 190, 220))
    d.rectangle([3, 3, 12, 12], fill=(160, 210, 240))
    # window frame
    d.line([(2, 2), (13, 2)], fill=(60, 65, 75))
    d.line([(2, 13), (13, 13)], fill=(60, 65, 75))
    d.line([(2, 2), (2, 13)], fill=(60, 65, 75))
    d.line([(13, 2), (13, 13)], fill=(60, 65, 75))
    save(img, "tile_window")

    # container tile marker
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(0, 0, 0, 0))
    save(img, "tile_container")

    # balloon crate tile marker
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(0, 0, 0, 0))
    save(img, "tile_balloon_crate")


# ── Player (12x28) ──────────────────────────────────────────────────────────


def _draw_player_base(d: ImageDraw.ImageDraw):
    """Draw the ash diver suit base — white/grey suit with visor."""
    # Helmet
    d.rectangle([2, 0, 9, 6], fill=(200, 200, 210))
    # Visor
    d.rectangle([3, 2, 8, 4], fill=(80, 180, 220))
    # Body
    d.rectangle([1, 7, 10, 18], fill=(210, 210, 220))
    # Belt
    d.rectangle([1, 15, 10, 16], fill=(100, 100, 110))
    # Legs
    d.rectangle([1, 19, 4, 27], fill=(190, 190, 200))
    d.rectangle([7, 19, 10, 27], fill=(190, 190, 200))
    # Boots
    d.rectangle([0, 25, 4, 27], fill=(60, 60, 70))
    d.rectangle([7, 25, 11, 27], fill=(60, 60, 70))


def gen_player():
    # idle
    img, d = make(12, 28)
    _draw_player_base(d)
    # Arms at sides
    d.rectangle([0, 8, 1, 16], fill=(200, 200, 210))
    d.rectangle([10, 8, 11, 16], fill=(200, 200, 210))
    save(img, "player_idle")

    # walk frame 1
    img, d = make(12, 28)
    _draw_player_base(d)
    d.rectangle([0, 8, 1, 14], fill=(200, 200, 210))
    d.rectangle([10, 8, 11, 14], fill=(200, 200, 210))
    # Legs apart
    d.rectangle([1, 19, 4, 27], fill=(0, 0, 0, 0))
    d.rectangle([7, 19, 10, 27], fill=(0, 0, 0, 0))
    d.rectangle([0, 19, 3, 27], fill=(190, 190, 200))
    d.rectangle([8, 19, 11, 27], fill=(190, 190, 200))
    d.rectangle([0, 25, 3, 27], fill=(60, 60, 70))
    d.rectangle([8, 25, 11, 27], fill=(60, 60, 70))
    save(img, "player_walk1")

    # walk frame 2
    img, d = make(12, 28)
    _draw_player_base(d)
    d.rectangle([0, 8, 1, 14], fill=(200, 200, 210))
    d.rectangle([10, 8, 11, 14], fill=(200, 200, 210))
    # Legs together
    d.rectangle([3, 19, 8, 27], fill=(190, 190, 200))
    d.rectangle([3, 25, 8, 27], fill=(60, 60, 70))
    save(img, "player_walk2")

    # jump
    img, d = make(12, 28)
    _draw_player_base(d)
    # Arms up
    d.rectangle([0, 5, 1, 12], fill=(200, 200, 210))
    d.rectangle([10, 5, 11, 12], fill=(200, 200, 210))
    # Legs tucked
    d.rectangle([1, 19, 4, 27], fill=(0, 0, 0, 0))
    d.rectangle([7, 19, 10, 27], fill=(0, 0, 0, 0))
    d.rectangle([2, 19, 5, 25], fill=(190, 190, 200))
    d.rectangle([6, 19, 9, 25], fill=(190, 190, 200))
    d.rectangle([2, 23, 5, 25], fill=(60, 60, 70))
    d.rectangle([6, 23, 9, 25], fill=(60, 60, 70))
    save(img, "player_jump")

    # fall
    img, d = make(12, 28)
    _draw_player_base(d)
    # Arms out
    d.rectangle([0, 7, 1, 10], fill=(200, 200, 210))
    d.rectangle([10, 7, 11, 10], fill=(200, 200, 210))
    save(img, "player_fall")

    # melee attack
    img, d = make(12, 28)
    _draw_player_base(d)
    # Left arm at side
    d.rectangle([0, 8, 1, 16], fill=(200, 200, 210))
    # Right arm extended with weapon
    d.rectangle([10, 6, 11, 10], fill=(200, 200, 210))
    save(img, "player_attack")

    # death
    img, d = make(12, 28)
    # Lying down effect — draw sideways
    d.rectangle([0, 20, 11, 27], fill=(180, 180, 190))
    d.rectangle([0, 22, 3, 24], fill=(80, 160, 200))  # visor
    save(img, "player_death")


# ── Siren (16x24) ───────────────────────────────────────────────────────────


def _draw_siren_base(d: ImageDraw.ImageDraw):
    """Eyeless, pale, hunched humanoid."""
    # Head — smooth, no eyes
    d.ellipse([4, 0, 11, 7], fill=(220, 200, 190))
    # Mouth slit
    d.line([(6, 5), (9, 5)], fill=(80, 40, 40))
    # Hunched body
    d.polygon([(3, 8), (12, 8), (13, 18), (2, 18)], fill=(210, 190, 180))
    # Arms — long, dangling
    d.rectangle([0, 9, 2, 20], fill=(210, 190, 180))
    d.rectangle([13, 9, 15, 20], fill=(210, 190, 180))
    # Claws
    d.point((0, 20), fill=(180, 100, 100))
    d.point((1, 21), fill=(180, 100, 100))
    d.point((14, 20), fill=(180, 100, 100))
    d.point((15, 21), fill=(180, 100, 100))
    # Legs
    d.rectangle([3, 18, 6, 23], fill=(200, 180, 170))
    d.rectangle([9, 18, 12, 23], fill=(200, 180, 170))


def gen_siren():
    # idle
    img, d = make(16, 24)
    _draw_siren_base(d)
    save(img, "siren_idle")

    # walk1
    img, d = make(16, 24)
    _draw_siren_base(d)
    # Shift legs
    d.rectangle([3, 18, 6, 23], fill=(0, 0, 0, 0))
    d.rectangle([9, 18, 12, 23], fill=(0, 0, 0, 0))
    d.rectangle([2, 18, 5, 23], fill=(200, 180, 170))
    d.rectangle([10, 18, 13, 23], fill=(200, 180, 170))
    save(img, "siren_walk1")

    # walk2
    img, d = make(16, 24)
    _draw_siren_base(d)
    d.rectangle([3, 18, 6, 23], fill=(0, 0, 0, 0))
    d.rectangle([9, 18, 12, 23], fill=(0, 0, 0, 0))
    d.rectangle([4, 18, 7, 23], fill=(200, 180, 170))
    d.rectangle([8, 18, 11, 23], fill=(200, 180, 170))
    save(img, "siren_walk2")

    # attack
    img, d = make(16, 24)
    _draw_siren_base(d)
    # Arms reaching forward
    d.rectangle([0, 9, 2, 20], fill=(0, 0, 0, 0))
    d.rectangle([13, 9, 15, 20], fill=(0, 0, 0, 0))
    d.rectangle([0, 6, 2, 14], fill=(210, 190, 180))
    d.rectangle([13, 6, 15, 14], fill=(210, 190, 180))
    # Claws extended
    d.point((0, 5), fill=(180, 100, 100))
    d.point((15, 5), fill=(180, 100, 100))
    save(img, "siren_attack")

    # death
    img, d = make(16, 24)
    d.rectangle([0, 16, 15, 23], fill=(190, 170, 160))
    d.ellipse([1, 16, 6, 20], fill=(200, 180, 170))
    save(img, "siren_death")


# ── Items (12x12) ───────────────────────────────────────────────────────────


def gen_items():
    # scrap_wood
    img, d = make(12, 12)
    d.rectangle([2, 3, 9, 8], fill=(160, 120, 60))
    d.line([(3, 4), (8, 4)], fill=(140, 100, 40))
    d.line([(3, 7), (8, 7)], fill=(140, 100, 40))
    save(img, "item_scrap_wood")

    # scrap_metal
    img, d = make(12, 12)
    d.polygon([(2, 9), (6, 2), (10, 9)], fill=(170, 170, 180))
    d.polygon([(3, 8), (6, 3), (9, 8)], fill=(190, 190, 200))
    save(img, "item_scrap_metal")

    # scrap_electronics
    img, d = make(12, 12)
    d.rectangle([1, 2, 10, 9], fill=(30, 100, 30))
    # circuit lines
    d.line([(3, 4), (8, 4)], fill=(200, 200, 50))
    d.line([(5, 3), (5, 8)], fill=(200, 200, 50))
    d.line([(3, 7), (8, 7)], fill=(200, 200, 50))
    # chips
    d.rectangle([3, 5, 4, 6], fill=(40, 40, 40))
    d.rectangle([7, 5, 8, 6], fill=(40, 40, 40))
    save(img, "item_scrap_electronics")

    # rare_component
    img, d = make(12, 12)
    d.ellipse([1, 1, 10, 10], fill=(60, 40, 120))
    d.ellipse([3, 3, 8, 8], fill=(140, 80, 220))
    d.point((5, 5), fill=(255, 255, 255))
    save(img, "item_rare_component")

    # pipe (melee weapon)
    img, d = make(12, 12)
    d.rectangle([5, 0, 6, 11], fill=(150, 150, 160))
    d.rectangle([4, 0, 7, 1], fill=(130, 130, 140))
    d.rectangle([4, 8, 7, 11], fill=(80, 80, 90))  # grip
    save(img, "item_pipe")

    # pistol
    img, d = make(12, 12)
    d.rectangle([1, 3, 10, 5], fill=(50, 50, 55))  # barrel
    d.rectangle([3, 5, 7, 10], fill=(60, 50, 40))   # grip
    d.rectangle([8, 3, 10, 4], fill=(70, 70, 75))    # muzzle
    d.point((2, 3), fill=(40, 40, 45))                # sight
    save(img, "item_pistol")

    # ammo_box
    img, d = make(12, 12)
    d.rectangle([1, 2, 10, 9], fill=(60, 80, 50))
    d.rectangle([2, 3, 9, 8], fill=(70, 90, 60))
    # bullets visible
    for x in range(3, 9, 2):
        d.rectangle([x, 4, x, 7], fill=(200, 180, 50))
    save(img, "item_ammo_box")

    # shotgun
    img, d = make(12, 12)
    d.rectangle([0, 4, 11, 6], fill=(70, 55, 40))   # barrel (long, brown wood)
    d.rectangle([0, 3, 8, 4], fill=(50, 50, 55))     # top barrel (metal)
    d.rectangle([6, 6, 10, 9], fill=(80, 60, 40))    # grip/stock
    d.rectangle([0, 4, 1, 5], fill=(60, 60, 65))     # muzzle
    save(img, "item_shotgun")

    # medkit
    img, d = make(12, 12)
    d.rectangle([1, 2, 10, 9], fill=(200, 200, 210))  # white case
    d.rectangle([2, 3, 9, 8], fill=(220, 220, 230))
    # Red cross
    d.rectangle([5, 3, 6, 8], fill=(200, 40, 40))
    d.rectangle([3, 5, 8, 6], fill=(200, 40, 40))
    save(img, "item_medkit")


# ── Objects (16x16) ─────────────────────────────────────────────────────────


def gen_objects():
    # crate
    img, d = make(16, 16)
    d.rectangle([1, 3, 14, 14], fill=(140, 110, 60))
    d.rectangle([2, 4, 13, 13], fill=(160, 130, 70))
    # planks
    d.line([(1, 8), (14, 8)], fill=(120, 90, 40))
    d.line([(7, 3), (7, 14)], fill=(120, 90, 40))
    # metal corners
    d.rectangle([1, 3, 3, 5], fill=(130, 130, 140))
    d.rectangle([12, 3, 14, 5], fill=(130, 130, 140))
    save(img, "obj_crate")

    # locker
    img, d = make(16, 16)
    d.rectangle([2, 0, 13, 15], fill=(100, 110, 120))
    d.rectangle([3, 1, 12, 14], fill=(120, 130, 140))
    d.line([(7, 0), (7, 15)], fill=(80, 90, 100))
    # handles
    d.rectangle([5, 7, 6, 8], fill=(180, 180, 190))
    d.rectangle([9, 7, 10, 8], fill=(180, 180, 190))
    save(img, "obj_locker")

    # rubble pile
    img, d = make(16, 16)
    d.polygon([(0, 15), (3, 8), (7, 12), (10, 6), (15, 15)], fill=(150, 140, 120))
    d.polygon([(2, 15), (5, 10), (8, 15)], fill=(170, 160, 140))
    save(img, "obj_rubble_pile")

    # balloon crate — inactive (bright orange/yellow, stands out from brown crates)
    img, d = make(16, 16)
    # Bright orange crate body
    d.rectangle([1, 3, 14, 15], fill=(230, 140, 20))
    d.rectangle([2, 4, 13, 14], fill=(250, 170, 40))
    # Bold white arrow pointing up
    d.polygon([(7, 4), (3, 9), (5, 9)], fill=(255, 255, 255))
    d.polygon([(7, 4), (11, 9), (9, 9)], fill=(255, 255, 255))
    d.rectangle([6, 9, 8, 13], fill=(255, 255, 255))
    # Yellow hazard stripes on sides
    d.rectangle([1, 3, 2, 15], fill=(255, 220, 0))
    d.rectangle([13, 3, 14, 15], fill=(255, 220, 0))
    save(img, "obj_balloon_inactive")

    # balloon crate — inflating
    img, d = make(16, 16)
    # Crate body (smaller, sinking)
    d.rectangle([2, 8, 13, 15], fill=(230, 140, 20))
    d.rectangle([2, 8, 3, 15], fill=(255, 220, 0))
    d.rectangle([12, 8, 13, 15], fill=(255, 220, 0))
    # Expanding balloon — bright red-orange
    d.ellipse([3, 0, 12, 9], fill=(255, 100, 50))
    d.ellipse([4, 1, 11, 8], fill=(255, 130, 70))
    # Rope
    d.line([(7, 8), (7, 9)], fill=(200, 200, 200))
    save(img, "obj_balloon_inflating")

    # balloon crate — ready
    img, d = make(16, 16)
    # Crate body
    d.rectangle([3, 10, 12, 15], fill=(230, 140, 20))
    d.rectangle([3, 10, 4, 15], fill=(255, 220, 0))
    d.rectangle([11, 10, 12, 15], fill=(255, 220, 0))
    # Full balloon — bright and large
    d.ellipse([1, 0, 14, 11], fill=(255, 80, 30))
    d.ellipse([3, 1, 12, 9], fill=(255, 120, 60))
    # Rope
    d.line([(7, 10), (7, 11)], fill=(200, 200, 200))
    save(img, "obj_balloon_ready")

    # NPC placeholder
    img, d = make(16, 16)
    d.ellipse([4, 0, 11, 6], fill=(200, 160, 120))  # head
    d.rectangle([3, 7, 12, 15], fill=(60, 60, 140))  # body
    d.rectangle([5, 2, 6, 3], fill=(40, 40, 40))     # eye
    d.rectangle([9, 2, 10, 3], fill=(40, 40, 40))     # eye
    save(img, "obj_npc")

    # dive hatch
    img, d = make(16, 16)
    d.rectangle([0, 0, 15, 15], fill=(80, 85, 95))
    d.ellipse([2, 2, 13, 13], fill=(40, 40, 50))
    d.ellipse([4, 4, 11, 11], fill=(30, 30, 40))
    # arrows pointing down
    d.polygon([(6, 7), (9, 7), (7, 11)], fill=(200, 200, 50))
    save(img, "obj_hatch")


# ── UI Elements ─────────────────────────────────────────────────────────────


def gen_ui():
    # heart icon (12x12)
    img, d = make(12, 12)
    d.ellipse([0, 1, 5, 5], fill=(220, 40, 40))
    d.ellipse([5, 1, 11, 5], fill=(220, 40, 40))
    d.polygon([(0, 4), (5, 10), (11, 4)], fill=(220, 40, 40))
    save(img, "ui_heart")

    # heart empty
    img, d = make(12, 12)
    d.ellipse([0, 1, 5, 5], fill=(80, 30, 30))
    d.ellipse([5, 1, 11, 5], fill=(80, 30, 30))
    d.polygon([(0, 4), (5, 10), (11, 4)], fill=(80, 30, 30))
    save(img, "ui_heart_empty")

    # ammo icon (12x12)
    img, d = make(12, 12)
    d.rectangle([3, 1, 5, 10], fill=(200, 180, 50))
    d.rectangle([6, 1, 8, 10], fill=(200, 180, 50))
    d.rectangle([2, 8, 9, 10], fill=(160, 140, 40))
    save(img, "ui_ammo")

    # inventory slot background (20x20)
    img, d = make(20, 20)
    d.rectangle([0, 0, 19, 19], fill=(40, 40, 50))
    d.rectangle([1, 1, 18, 18], fill=(60, 60, 70))
    save(img, "ui_slot")

    # inventory slot selected (20x20)
    img, d = make(20, 20)
    d.rectangle([0, 0, 19, 19], fill=(200, 200, 80))
    d.rectangle([1, 1, 18, 18], fill=(60, 60, 70))
    save(img, "ui_slot_selected")


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    print("Generating sprites...")
    gen_tiles()
    print("  tiles done")
    gen_player()
    print("  player done")
    gen_siren()
    print("  siren done")
    gen_items()
    print("  items done")
    gen_objects()
    print("  objects done")
    gen_ui()
    print("  UI done")
    print(f"All sprites saved to {ASSETS}/")


if __name__ == "__main__":
    main()
