"""Ash Diver — Camera (extracted from game.py)."""

import pygame

from settings import SCREEN_W, SCREEN_H, TILE_SIZE, CAMERA_LERP


class Camera:
    def __init__(self, map_w: int, map_h: int):
        self.x = 0.0
        self.y = 0.0
        self.map_w = map_w
        self.map_h = map_h

    def update(self, target_x: float, target_y: float):
        goal_x = target_x - SCREEN_W / 2
        goal_y = target_y - SCREEN_H / 2
        self.x += (goal_x - self.x) * CAMERA_LERP
        self.y += (goal_y - self.y) * CAMERA_LERP
        self.x = max(0.0, min(self.x, self.map_w - SCREEN_W))
        self.y = max(0.0, min(self.y, self.map_h - SCREEN_H))

    def snap(self, target_x: float, target_y: float):
        self.x = target_x - SCREEN_W / 2
        self.y = target_y - SCREEN_H / 2
        self.x = max(0.0, min(self.x, self.map_w - SCREEN_W))
        self.y = max(0.0, min(self.y, self.map_h - SCREEN_H))

    def visible_tile_range(self) -> tuple[int, int, int, int]:
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

    def apply(self, x: float, y: float) -> tuple[int, int]:
        return int(x - self.x), int(y - self.y)
