#!/usr/bin/env python
#vim:fileencoding=utf-8

from collections import deque
from itertools import product
import random
from math import sqrt

import pygame
from pygame.locals import *

import util
from util import Vec
import field
from gameobjects import Creep, Wall, SimpleBullet, SimpleTower
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
        self.field.set_enter((GAME_X_SIZE / 2, GAME_Y_SIZE - 1))

        self.creeps = pygame.sprite.Group()
        self.towers = pygame.sprite.Group()
        self.missles = pygame.sprite.Group()

        self.next_spawn = 0
        self.time = 0
        self.spawn_period = 2 * TICK_PER_SEC

    def add_creep(self, creep):
        creep.add([self.creeps])

    def add_tower(self, pos, cls):
        if cls is Wall:
            tower = cls(pos)
        elif cls is SimpleTower:
            tower = SimpleTower(pos, self.creeps, self.missles)
        else:
            raise ValueError, "Unknown tower type: %s" % repr(cls)

        if pygame.sprite.spritecollideany(tower, self.creeps):
            return False
        self.field.put(pos, tower)
        block_creeps = False
        for creep in self.creeps:
            if tuple(creep.current_cell()) not in self.field.dir_field:
                block_creeps = True
                break
        if block_creeps:
            self.field.clear(pos)
            return
        tower.add([self.towers])
        for creep in self.creeps:
            creep.forget_way()

    def update(self, ticks):
        self.time += ticks
        if self.time > self.next_spawn:
            self.spawn_creep()
            self.next_spawn += self.spawn_period

        self.towers.update(ticks)
        self.creeps.update(ticks)
        self.missles.update(ticks)

    def draw(self, surface):
        self.creeps.draw(surface)
        self.missles.draw(surface)

    def spawn_creep(self):
        creep_pos = GAME_X_SIZE / 2, GAME_Y_SIZE - 1
        creep = Creep(creep_pos, 3, self.field, self.towers)
        self.add_creep(creep)


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
        self.enter = None

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

    def set_enter(self, pos):
        if not self.contains(pos):
            raise ValueError, "Invalid pos: %s" % str(pos)
        self.enter = tuple(pos)

    def get_enter(self):
        return self.enter

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

    def clear(self, pos):
        if self.empty(pos):
            raise ValueError, 'Cell %s is already emply' % pos
        self._set_content(pos, Nothing)
        self._changed.add(pos)
        self._empty_fields += 1
        self._recalculate_paths()

    def empty(self, pos):
        return self.get_content(pos) is Nothing and\
               tuple(pos) not in self._exit_pos

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
        self.dir_field = field.build_right_angle_dir_field(self, self._exit_pos)

    def set_dir_field(self, dir_field):
        self.dir_field = dir_field

    def get_next_pos(self, pos):
        return self.get_direction(pos).next_vertex

    def is_exit(self, pos):
        return tuple(pos) in self._exit_pos

    def get_direction(self, pos):
        pos = tuple(pos)
        direction = self.dir_field.get(pos, None)
        if direction is None:
            return None
        else:
            return direction

    def in_edges(self, endpos):
        return [field.Edge(begpos, endpos, 1)
                for begpos in self.get_neighbours(endpos)]

class Game(object):
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('9nMaze')
        field_x_size = GAME_X_SIZE * GAME_CELL_SIZE
        field_y_size = GAME_Y_SIZE * GAME_CELL_SIZE

        panel_x_size = PANEL_X_SIZE
        panel_y_size = field_x_size

        window_x_size = field_x_size + panel_x_size
        window_y_size = field_y_size
        
        window = pygame.display.set_mode((window_x_size, window_y_size))
        self._screen = pygame.display.get_surface()
        field_rect = Rect((0,0), (field_x_size, field_y_size))
        self._field_surface = self._screen.subsurface(field_rect)

        panel_rect = Rect((field_x_size, 0), (panel_x_size, panel_y_size))
        self._panel_surface = self._screen.subsurface(panel_rect)
        self._restart()
        self._game_speed = 1

    def _restart(self):
        self._continue_main_loop = True
        self._clock = pygame.time.Clock()
        self._state = 'PLAY'
        self.world = World()
        self.background = pygame.Surface(self._field_surface.get_size()).convert()
        color = (255,255,255)
        self.background.fill(color)

        self.static = self.background.copy()
        self.ground = self.background.copy()
        self.air = self.background.copy()

        self.update_panel()

    def _main_loop(self):
        while self._continue_main_loop:
            time_passed = self._clock.tick(TICK_PER_SEC)
            events = pygame.event.get()
            for e in events:
                self._dispatch_event(e)

            self.world.creeps.clear(self._field_surface, self.static)
            self.world.missles.clear(self._field_surface, self.static)

            self.world.update(self._game_speed)
            self.world.draw(self._field_surface)
            pygame.display.flip()

    def _dispatch_event(self, event):
        if (event.type == QUIT) or (
                event.type == KEYDOWN and event.key == K_ESCAPE):
            self._exit()
        elif event.type == KEYDOWN:
            if event.key == K_SPACE:
                self._game_speed = 4
        elif event.type == KEYUP:
            if event.key == K_SPACE:
                self._game_speed = 1
        elif event.type == MOUSEBUTTONDOWN:
            if self._field_surface.get_rect().collidepoint(event.pos):
                if event.button == 1:
                    game_pos = util.screen2game(event.pos)
                    if self.world.field.empty(game_pos) and\
                            tuple(game_pos) != self.world.field.enter:
                        self.world.add_tower(game_pos, SimpleTower)
                        self.update_static_layer()
                        pygame.display.flip()
                elif event.button == 2:
                    for creep in self.world.creeps:
                        b = SimpleBullet(util.screen2fgame(event.pos), creep, 1, 20)
                        b.add([self.world.missles])
                        break

    def _exit(self):
        self._state = 'EXIT'
        self._continue_main_loop = False

    def run(self):
        self.update_static_layer()
        pygame.display.flip()
        self._main_loop()
        pygame.display.quit()

    def update_static_layer(self):
        self.static.blit(self.background, (0,0))
        if DRAW_ARROWS:
            self._redraw_arrows(self.static)
        self.world.towers.draw(self.static)
        self._field_surface.blit(self.static, (0,0))

    def _redraw_cells(self, pos, surf):
        self.world.towers.clear(self._field_surface, self.background)
        self.world.towers.draw(self._field_surface)

    def _redraw_arrows(self, surf):
        color = (255, 0, 0)
        for pos in self.world.field.iter_pos():
            n_pos = self.world.field.get_next_pos(pos)
            if n_pos is not None:
                center = util.game2cscreen(pos)
                n_center = util.game2cscreen(n_pos)
                draw_arrow(surf, color, center, n_center)

    def update_panel(self):
        self._panel_surface.fill((150, 150, 150))

if __name__ == '__main__':
    g = Game()
    g.run()

