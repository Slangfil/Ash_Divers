"""Ash Diver — HUD overlay + inventory screen."""

import pygame

from settings import (
    SCREEN_W, SCREEN_H, ASSETS_DIR, PLAYER_MAX_HP, INVENTORY_SIZE,
)
from items import ITEM_DEFS


class SpriteCache:
    """Shared sprite loader with caching."""

    _cache: dict[str, pygame.Surface] = {}

    @classmethod
    def get(cls, name: str) -> pygame.Surface | None:
        if name in cls._cache:
            return cls._cache[name]
        path = ASSETS_DIR / f"{name}.png"
        if path.exists():
            surf = pygame.image.load(str(path)).convert_alpha()
            cls._cache[name] = surf
            return surf
        return None

    @classmethod
    def clear(cls):
        cls._cache.clear()


class HUD:
    def __init__(self):
        self.font = pygame.font.SysFont(None, 24)
        self.font_large = pygame.font.SysFont(None, 36)
        self.font_weapon = pygame.font.SysFont(None, 20)
        self.show_inventory = False
        self.extraction_active = False
        self.extraction_timer = 0.0
        self.extraction_total = 0.0

    def toggle_inventory(self):
        self.show_inventory = not self.show_inventory

    def set_extraction(self, active: bool, timer: float = 0.0, total: float = 0.0):
        self.extraction_active = active
        self.extraction_timer = timer
        self.extraction_total = total

    def render(self, screen: pygame.Surface, player):
        self._render_hp_and_weapon(screen, player)
        self._render_ammo(screen, player)
        self._render_medkits(screen, player)
        self._render_quickbar(screen, player)
        if self.extraction_active:
            self._render_extraction_bar(screen)
        if self.show_inventory:
            self._render_inventory_screen(screen, player)

    def _render_hp_and_weapon(self, screen: pygame.Surface, player):
        """Hearts on the left, weapon icon + name right next to them."""
        heart = SpriteCache.get("ui_heart")
        heart_empty = SpriteCache.get("ui_heart_empty")
        x = 10
        y = 10
        for i in range(player.max_hp):
            sprite = heart if i < player.hp else heart_empty
            if sprite:
                screen.blit(sprite, (x + i * 16, y))
            else:
                color = (220, 40, 40) if i < player.hp else (80, 30, 30)
                pygame.draw.rect(screen, color, (x + i * 16, y, 12, 12))

        # Weapon icon + name right after hearts
        wx = x + player.max_hp * 16 + 12
        wy = y - 2

        # Slot background
        slot_bg = SpriteCache.get("ui_slot")
        if slot_bg:
            screen.blit(pygame.transform.scale(slot_bg, (28, 28)), (wx, wy))
        else:
            pygame.draw.rect(screen, (40, 40, 55), (wx, wy, 28, 28))
            pygame.draw.rect(screen, (100, 100, 120), (wx, wy, 28, 28), 1)

        # Weapon sprite
        if player.weapon:
            wep_sprite = SpriteCache.get(f"item_{player.weapon}")
            if wep_sprite:
                screen.blit(pygame.transform.scale(wep_sprite, (22, 22)), (wx + 3, wy + 3))
        else:
            # Fist icon: just draw a small fist shape
            pygame.draw.circle(screen, (200, 180, 160), (wx + 14, wy + 14), 8)
            pygame.draw.circle(screen, (180, 160, 140), (wx + 14, wy + 14), 8, 1)

        # Weapon name
        name_text = self.font_weapon.render(player.weapon_display_name, True, (200, 200, 210))
        screen.blit(name_text, (wx + 32, wy + 6))

        # Swap hint
        hint = self.font_weapon.render("[Q]", True, (120, 120, 140))
        screen.blit(hint, (wx + 32 + name_text.get_width() + 4, wy + 6))

    def _render_ammo(self, screen: pygame.Surface, player):
        """Ammo count below HP/weapon row, only when holding ranged weapon."""
        if not player.is_ranged:
            return
        x = 10 + player.max_hp * 16 + 12
        y = 30
        ammo_icon = SpriteCache.get("ui_ammo")
        if ammo_icon:
            screen.blit(ammo_icon, (x, y))
        color = (200, 200, 50) if player.ammo > 3 else (220, 60, 60)
        ammo_text = self.font.render(str(player.ammo), True, color)
        screen.blit(ammo_text, (x + 16, y))

    def _render_medkits(self, screen: pygame.Surface, player):
        """Medkit count in top-right area, only if player has any."""
        if player.medkits <= 0:
            return
        x = SCREEN_W - 80
        y = 10
        medkit_sprite = SpriteCache.get("item_medkit")
        if medkit_sprite:
            screen.blit(medkit_sprite, (x, y))
        else:
            pygame.draw.rect(screen, (200, 40, 40), (x, y, 12, 12))
        text = self.font.render(f"x{player.medkits} [H]", True, (200, 255, 200))
        screen.blit(text, (x + 16, y))

    def _render_quickbar(self, screen: pygame.Surface, player):
        slot_bg = SpriteCache.get("ui_slot")
        bar_w = INVENTORY_SIZE * 24 + (INVENTORY_SIZE - 1) * 2
        start_x = (SCREEN_W - bar_w) // 2
        y = SCREEN_H - 32

        for i in range(INVENTORY_SIZE):
            sx = start_x + i * 26
            if slot_bg:
                screen.blit(pygame.transform.scale(slot_bg, (24, 24)), (sx, y))
            else:
                pygame.draw.rect(screen, (40, 40, 50), (sx, y, 24, 24))
                pygame.draw.rect(screen, (80, 80, 90), (sx, y, 24, 24), 1)

            slot = player.inventory[i]
            if slot:
                item_sprite = SpriteCache.get(ITEM_DEFS[slot.item_id].sprite_name)
                if item_sprite:
                    screen.blit(pygame.transform.scale(item_sprite, (18, 18)), (sx + 3, y + 3))
                if slot.count > 1:
                    count_text = self.font.render(str(slot.count), True, (255, 255, 255))
                    screen.blit(count_text, (sx + 14, y + 14))

    def _render_extraction_bar(self, screen: pygame.Surface):
        bar_w = 300
        bar_h = 20
        x = (SCREEN_W - bar_w) // 2
        y = 60
        progress = self.extraction_timer / max(self.extraction_total, 0.01)
        progress = min(1.0, max(0.0, progress))

        pygame.draw.rect(screen, (40, 40, 50), (x - 2, y - 2, bar_w + 4, bar_h + 4))
        pygame.draw.rect(screen, (60, 60, 70), (x, y, bar_w, bar_h))
        fill_w = int(bar_w * progress)
        color = (50, 200, 50) if progress < 0.8 else (200, 200, 50)
        pygame.draw.rect(screen, color, (x, y, fill_w, bar_h))
        label = self.font.render("EXTRACTING...", True, (255, 255, 255))
        screen.blit(label, (x + bar_w // 2 - label.get_width() // 2, y - 20))

    def _render_inventory_screen(self, screen: pygame.Surface, player):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        title = self.font_large.render("INVENTORY", True, (255, 255, 255))
        screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 80))

        cols = 4
        slot_size = 48
        gap = 8
        grid_w = cols * (slot_size + gap)
        start_x = (SCREEN_W - grid_w) // 2
        start_y = 140

        slot_bg = SpriteCache.get("ui_slot")
        for i in range(INVENTORY_SIZE):
            col = i % cols
            row = i // cols
            sx = start_x + col * (slot_size + gap)
            sy = start_y + row * (slot_size + gap)

            if slot_bg:
                screen.blit(pygame.transform.scale(slot_bg, (slot_size, slot_size)), (sx, sy))
            else:
                pygame.draw.rect(screen, (60, 60, 70), (sx, sy, slot_size, slot_size))
                pygame.draw.rect(screen, (100, 100, 110), (sx, sy, slot_size, slot_size), 1)

            slot = player.inventory[i]
            if slot:
                defn = ITEM_DEFS.get(slot.item_id)
                if defn:
                    item_sprite = SpriteCache.get(defn.sprite_name)
                    if item_sprite:
                        scaled = pygame.transform.scale(item_sprite, (36, 36))
                        screen.blit(scaled, (sx + 6, sy + 2))
                    name_text = self.font.render(defn.name, True, (220, 220, 220))
                    screen.blit(name_text, (sx, sy + slot_size + 2))
                    if slot.count > 1:
                        ct = self.font.render(f"x{slot.count}", True, (200, 200, 100))
                        screen.blit(ct, (sx + slot_size - ct.get_width(), sy + slot_size - 16))

        # Weapon info
        wy = start_y + (INVENTORY_SIZE // cols + 1) * (slot_size + gap) + 20
        weapon_text = f"Weapon: {player.weapon_display_name}"
        if player.is_ranged:
            weapon_text += f"  Ammo: {player.ammo}"
        wt = self.font_large.render(weapon_text, True, (255, 255, 200))
        screen.blit(wt, (SCREEN_W // 2 - wt.get_width() // 2, wy))

        hint = self.font.render("Press TAB to close    Q to swap weapon", True, (150, 150, 150))
        screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 50))
