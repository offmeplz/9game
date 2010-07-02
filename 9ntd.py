#!/usr/bin/env python
#vim:fileencoding=utf-8

from collections import deque
from itertools import product
from math import sqrt

import pygame
from pygame.locals import *

import util
from gameobjects import Creep, Wall
from cfg import *

def norm(vec):
    return sqrt(vec[0] ** 2 + vec[1] ** 2)

def draw_arrow(surface, color, begin, end):
    if begin == end:
        raise ValueError, "Begin and End are the same"
    vec = end[0] - begin[0], end[1] - begin[1]
    side_vec1 = - vec[0] - 0.5 * vec[1], + 0.5 * vec[0] - vec[1]
    side_vec2 = - vec[0] + 0.5 * vec[1], - 0.5 * vec[0] - vec[1]
    coef = 0.3 * norm(vec) / norm(side_vec1)

    side_vec1 = side_vec1[0] * coef, side_vec1[1] * coef
    side_vec2 = side_vec2[0] * coef, side_vec2[1] * coef

    side_end1 = side_vec1[0] + end[0], side_vec1[1] + end[1]
    side_end2 = side_vec2[0] + end[0], side_vec2[1] + end[1]

    pygame.draw.line(surface, color, begin, end)
    pygame.draw.line(surface, color, end, side_end1)
    pygame.draw.line(surface, color, end, side_end2)


class NothingType(object):
    obj = None
    def __new__(cls, *args, **kwargs):
        if cls.obj is None:
            cls.obj = object.__new__(cls, *args, **kwargs)
        return cls.obj

    def color(self):
        return (255,255,255)

Nothing = NothingType()

class Cell(object):
    def __init__(self, content=Nothing, is_exit=False):
        self.content = content
        self.is_exit = is_exit
        self.distance_to_exit = None
        self.next_pos_to_exit = None

class World(object):
    def __init__(self):
        self.field = Field(GAME_X_SIZE, GAME_Y_SIZE)
        self.field.set_exit([(GAME_X_SIZE / 2,0)])
        self.creeps = pygame.sprite.Group()
        self.towers = pygame.sprite.Group()
        self.next_spawn = 0
        self.time = 0
        self.spawn_period = 2 * TICK_PER_SEC

    def add_creep(self, pos, cls):
        creep = cls(pos, self.field)
        creep.add([self.creeps])

    def add_tower(self, pos, cls):
        tower = cls(pos)
        if pygame.sprite.spritecollideany(tower, self.creeps):
            return False
        self.field.put(pos, tower)
        tower.add([self.towers])
        for creep in self.creeps:
            creep.forget_way()

    def update(self, ticks):
        self.time += ticks
        if self.time > self.next_spawn:
            self.spawn_creep()
            self.next_spawn += self.spawn_period
        self.creeps.update(ticks)

    def draw(self, surface):
        self.creeps.draw(surface)

    def spawn_creep(self):
        self.add_creep((GAME_X_SIZE / 2, GAME_Y_SIZE - 1), Creep)

class Field(object):
    def __init__(self, size_x, size_y):
        self._x_size = size_x
        self._y_size = size_y
        self._field = []
        for i in xrange(size_x):
            self._field.append([Cell() for j in xrange(size_y)])
        self._changed = set()
        self._empty_fields = size_x * size_y
        self._exit_pos = set()
        self._recalculate_paths()

    def set_exit(self, exit_positions):
        for pos in self.iter_pos():
            cell = self._get_cell(pos)
            cell.is_exit = False
            cell.distance_to_exit = None
        self._exit_pos = set(exit_positions)
        for pos in self._exit_pos:
            cell = self._get_cell(pos)
            cell.is_exit = True
        self._recalculate_paths()

    def put(self, pos, obj):
        if not self.empty(pos):
            raise ValueError, 'Cell %s is not empty: %s' % (
                    pos, self._at(pos))

        self._set_content(pos, obj)
        self._changed.add(pos)
        self._empty_fields -= 1
        self._recalculate_paths()

    def contains(self, pos):
        return 0 <= pos[0] < self._x_size and 0 <= pos[1] < self._y_size

    def empty(self, pos):
        return self.get_content(pos) is Nothing

    def _get_cell(self, pos):
        return self._field[pos[0]][pos[1]]

    def get_content(self, pos):
        return self._get_cell(pos).content

    def _set_content(self, pos, obj):
        self._get_cell(pos).content = obj

    def iter_pos(self):
        return product(xrange(self._x_size), xrange(self._y_size))

    def extract_changed(self):
        changed = self._changed
        self._changed = set()
        return changed

    def get_neighbours(self, pos):
        res = [ (pos[0] + 1, pos[1]),
                (pos[0] - 1, pos[1]),
                (pos[0], pos[1] + 1),
                (pos[0], pos[1] - 1)]
        return [pos
                for pos in res
                if self.contains(pos) and self.empty(pos)]

    def _recalculate_paths(self):
        for pos in self.iter_pos():
            cell = self._get_cell(pos)
            cell.distance_to_exit = None
            cell.next_pos_to_exit = None

        queue = deque(self._exit_pos)
        for pos in queue:
            cell = self._get_cell(pos)
            cell.distance_to_exit = 0
        while len(queue) > 0:
            pos = queue.popleft()
            cell = self._get_cell(pos)
            cur_distance = cell.distance_to_exit
            for n_pos in self.get_neighbours(pos):
                n_cell = self._get_cell(n_pos)
                if n_cell.distance_to_exit is None and n_cell.content is Nothing:
                    n_cell.distance_to_exit = cur_distance
                    n_cell.next_pos_to_exit = pos
                    queue.append(n_pos)
                else:
                    assert n_cell.distance_to_exit <= cur_distance

    def get_next_pos(self, pos):
        return self._get_cell(pos).next_pos_to_exit


class Game(object):
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('9nMaze')
        x_size = GAME_X_SIZE * GAME_CELL_SIZE
        y_size = GAME_Y_SIZE * GAME_CELL_SIZE
        window = pygame.display.set_mode((x_size, y_size))
        self._screen = pygame.display.get_surface()
        self._restart()

    def _restart(self):
        self._continue_main_loop = True
        self._clock = pygame.time.Clock()
        self._state = 'PLAY'
        self.world = World()
        self.back = pygame.Surface(self._screen.get_size())
        self.back = self.back.convert()
        color = (255,255,255)
        self.back.fill(color)

    def _main_loop(self):
        while self._continue_main_loop:
            time_passed = self._clock.tick(TICK_PER_SEC)
            events = pygame.event.get()
            for e in events:
                self._dispatch_event(e)
            self.world.creeps.clear(self._screen, self.back)
            self.world.update(1)
            self.world.draw(self._screen)
            pygame.display.flip()

    def _dispatch_event(self, event):
        if (event.type == QUIT) or (
                event.type == KEYDOWN and event.key == K_ESCAPE):
            self._exit()
        elif event.type == MOUSEBUTTONDOWN:
            game_pos = util.screen2game(event.pos)
            if self.world.field.empty(game_pos) and game_pos != (0,0):
                self.world.add_tower(game_pos, Wall)
                self._update_background()
                pygame.display.flip()

    def _exit(self):
        self._state = 'EXIT'
        self._continue_main_loop = False

    def run(self):
        self._update_background()
        self._screen.blit(self.back, (0,0))
        pygame.display.flip()
        self._main_loop()
        pygame.display.quit()

    def _update_background(self):
        self._redraw_field(self.back)
        self._redraw_arrows(self.back)

    def _redraw_field(self, surf):
        self._redraw_cells(self.world.field.extract_changed(), surf)

    def _redraw_cells(self, pos, surf):
        self.world.towers.clear(self._screen, self.back)
        self.world.towers.draw(self._screen)

        return
        for p in pos:
            rect = pygame.Rect(util.game2screen(p), (GAME_CELL_SIZE, GAME_CELL_SIZE))
            item = self.world.field.get_content(p)
            color = item.color()
            pygame.draw.rect(surf, color, rect)

    def _redraw_arrows(self, surf):
        color = (255, 0, 0)
        for pos in self.world.field.iter_pos():
            n_pos = self.world.field.get_next_pos(pos)
            if n_pos is not None:
                center = util.game2cscreen(pos)
                n_center = util.game2cscreen(n_pos)
                draw_arrow(surf, color, center, n_center)

if __name__ == '__main__':
    g = Game()
    g.run()

