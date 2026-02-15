#!/usr/bin/env python3
"""Ash Diver — Entry point.

Airship hub -> freefall -> explore suburbs -> fight sirens -> extract or die.
"""

import random
import time

import pygame

from settings import SCREEN_W, SCREEN_H, FPS, SCENE_AIRSHIP, SCENE_FREEFALL, SCENE_SURFACE, SCENE_DEATH, PLAYER_MAX_HP
from scenes import AirshipScene, FreefallScene, SurfaceScene, DeathScene


def seed_screen(screen: pygame.Surface, clock: pygame.time.Clock) -> int | None:
    """Show seed input screen. Returns chosen seed, or None if user quit."""
    font_title = pygame.font.SysFont(None, 64)
    font = pygame.font.SysFont(None, 36)
    font_small = pygame.font.SysFont(None, 24)

    seed_text = ""
    cursor_blink = 0.0

    while True:
        dt = clock.tick(FPS) / 1000.0
        cursor_blink += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if seed_text.strip():
                        # Try numeric seed, otherwise hash the string
                        try:
                            return int(seed_text.strip())
                        except ValueError:
                            return hash(seed_text.strip()) & 0x7FFFFFFF
                    else:
                        # Random seed
                        return random.randint(0, 999999)
                if event.key == pygame.K_BACKSPACE:
                    seed_text = seed_text[:-1]
                elif event.unicode and event.unicode.isprintable():
                    if len(seed_text) < 20:
                        seed_text += event.unicode

        # Render
        screen.fill((15, 15, 25))

        title = font_title.render("ASH DIVER", True, (200, 200, 210))
        screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 120))

        subtitle = font_small.render("Roguelike Exploration Platformer", True, (120, 120, 140))
        screen.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, 185))

        prompt = font.render("Enter seed (or press Enter for random):", True, (180, 180, 190))
        screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, 300))

        # Input box
        box_w = 320
        box_h = 44
        box_x = SCREEN_W // 2 - box_w // 2
        box_y = 350
        pygame.draw.rect(screen, (40, 40, 55), (box_x, box_y, box_w, box_h))
        pygame.draw.rect(screen, (100, 100, 120), (box_x, box_y, box_w, box_h), 2)

        cursor = "|" if int(cursor_blink * 2) % 2 == 0 else ""
        display_text = seed_text + cursor
        input_surf = font.render(display_text, True, (220, 220, 230))
        screen.blit(input_surf, (box_x + 10, box_y + 8))

        hint1 = font_small.render("ENTER = start    ESC = quit    F11 = fullscreen", True, (90, 90, 110))
        screen.blit(hint1, (SCREEN_W // 2 - hint1.get_width() // 2, 420))

        # Controls reference
        controls = [
            "WASD / Arrows - Move + Jump",
            "Space - Jump (also jump off ladders)",
            "Left Click - Attack (melee or ranged)",
            "Q - Swap weapon",
            "H - Use medkit",
            "E - Interact (open crates, activate extraction)",
            "Tab - Inventory",
        ]
        cy = 490
        header = font_small.render("Controls:", True, (140, 140, 160))
        screen.blit(header, (SCREEN_W // 2 - 120, cy))
        cy += 24
        for line in controls:
            t = font_small.render(line, True, (100, 100, 120))
            screen.blit(t, (SCREEN_W // 2 - 120, cy))
            cy += 20

        pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
    pygame.display.set_caption("Ash Diver")
    clock = pygame.time.Clock()

    # Seed selection screen
    seed = seed_screen(screen, clock)
    if seed is None:
        pygame.quit()
        return

    # Persistent state across runs
    game_state: dict = {
        "scrap_wood": 0,
        "scrap_metal": 0,
        "scrap_electronics": 0,
        "rare_component": 0,
        "hp": PLAYER_MAX_HP,
        "run_seed": seed,
    }

    def make_scene(scene_id: str):
        if scene_id == SCENE_AIRSHIP:
            return AirshipScene(game_state)
        elif scene_id == SCENE_FREEFALL:
            return FreefallScene(game_state)
        elif scene_id == SCENE_SURFACE:
            return SurfaceScene(game_state)
        elif scene_id == SCENE_DEATH:
            return DeathScene(game_state)
        return AirshipScene(game_state)

    current_scene = make_scene(SCENE_AIRSHIP)
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()

        if not running:
            break

        next_scene = current_scene.handle_events(events)
        if next_scene == "quit":
            running = False
            break
        if next_scene is None:
            next_scene = current_scene.update(dt)
        if next_scene == "quit":
            running = False
            break

        if next_scene and next_scene != "quit":
            current_scene = make_scene(next_scene)

        current_scene.render(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
