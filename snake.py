#!/usr/bin/env python
#vim:fileencoding=utf-8

from collections import deque
from itertools import product
import random
import sys

import pygame
from pygame.locals import *

GAME_X_SIZE = 19
GAME_Y_SIZE = 19
GAME_CELL_SIZE = 7
MOVE_PER_SEC = 10
CONTROLS = {
        K_UP: 'UP',
        K_DOWN: 'DOWN',
        K_LEFT: 'LEFT',
        K_RIGHT: 'RIGHT',
        }


def game2screen(game_pos):
    g_x, g_y = game_pos
    s_x, s_y = g_x * GAME_CELL_SIZE, g_y * GAME_CELL_SIZE
    return s_x, s_y


class GameOver(Exception):
    pass


class Field(object):
    def __init__(self, size_x, size_y):
        self._x_size = size_x
        self._y_size = size_y
        self._field = []
        for i in xrange(size_x):
            self._field.append([None] * size_y)
        self._changed = set()
        self._empty_fields = size_x * size_y

    def put(self, pos, obj):
        old_obj = self[pos]
        if old_obj is not None:
            raise ValueError, 'Cell %s is not empty: %s' % \
                    (str(pos), str(old_obj))
        self[pos] = obj
        self._changed.add(pos)
        self._empty_fields -= 1
        if self._empty_fields <= 0:
            raise GameOver

    def remove(self, pos):
        self[pos] = None
        self._changed.add(pos)
        self._empty_fields += 1

    def is_empty(self, pos):
        return self[pos] is None

    def can_move(self, pos):
        return 0 <= pos[0] < self._x_size and \
                0 <= pos[1] < self._y_size and \
                (type(self[pos]) is Rabbit or self[pos] is None)

    def can_eat(self, pos):
        return type(self[pos]) is Rabbit

    def eat(self, pos):
        if type(self[pos]) is not Rabbit:
            raise ValueError, 'Element at %s is not eatable: %s.' % (
                    pos, self.get(pos))
        self.remove(pos)
        self.spawn_rabbit()

    def spawn_rabbit(self):
        good_pos = False
        while not good_pos:
            pos_x = random.randrange(self._x_size)
            pos_y = random.randrange(self._y_size)
            pos = pos_x, pos_y
            good_pos = self.is_empty(pos)
        self.put(pos, Rabbit())

    def extract_changed(self):
        changed = self._changed
        self._changed = set()
        return changed

    def __getitem__(self, pos):
        return self._field[pos[0]][pos[1]]

    def __setitem__(self, pos, item):
        self._field[pos[0]][pos[1]] = item

    def __iter__(self):
        return product(xrange(self._x_size), xrange(self._y_size))


class Snake(object):
    direction_dict = {
            'UP' : (0, -1),
            'DOWN' : (0, 1),
            'RIGHT' : (1, 0),
            'LEFT' : (-1, 0)
            }

    def __init__(self, field, pos):
        self._field = field
        self._body = deque((pos[0],pos[1] + i) for i in (-1,0,1))
        for p in self._body:
            self._field.put(p, self)
        self._direction = 'UP'
        self._old_direction = 'UP'
        self._steps = 0
        self._times_for_shit = deque()

    def get_dir_vector(self):
        return self.direction_dict[self._direction]

    def make_step(self):
        direction = self.get_dir_vector()
        self._old_direction = self._direction
        new_head = self._body[0]
        new_head = new_head[0] + direction[0], new_head[1] + direction[1]
        if not self._field.can_move(new_head):
            raise GameOver
        if self._field.can_eat(new_head):
            self._field.eat(new_head)
            self._times_for_shit.append(self._steps + len(self._body))
        else:
            old_tail = self._body.pop()
            self._field.remove(old_tail)
            if len(self._times_for_shit) and \
                    self._times_for_shit[0] <= self._steps:
                self._field.put(old_tail, Shit())
                self._times_for_shit.popleft()

        self._body.appendleft(new_head)
        self._field.put(new_head, self)
        self._steps += 1

    def change_direction(self, new_direction):
        old_direction = self._old_direction
        if new_direction in ('UP', 'DOWN'):
            if old_direction not in ('RIGHT', 'LEFT'):
                raise ValueError, "Cant change direction from '%s' to '%s'" % (
                        old_direction, new_direction)
        elif new_direction in ('RIGHT', 'LEFT'):
            if old_direction not in ('UP', 'DOWN'):
                raise ValueError, "Cant change direction from '%s' to '%s'" % (
                        old_direction, new_direction)
        else:
            raise TypeError, "Cant change direction from '%s' to '%s'" % (
                    old_direction, new_direction)
        self._direction = new_direction

    def try_change_direction(self, new_direction):
        try:
            return self.change_direction(new_direction)
        except ValueError:
            return None


class Shit(object):
    pass
class Rabbit(object): pass


class Game(object):
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('9nSnake')
        x_size = GAME_X_SIZE * GAME_CELL_SIZE
        y_size = GAME_Y_SIZE * GAME_CELL_SIZE
        window = pygame.display.set_mode((x_size, y_size))
        self._screen = pygame.display.get_surface()
        self._restart()

    def _restart(self):
        self._clock = pygame.time.Clock()
        self._continue_main_loop = True
        self._state = 'PLAY'
        self._field = Field(GAME_X_SIZE, GAME_Y_SIZE)
        snake_init_pos = GAME_X_SIZE / 2, GAME_Y_SIZE / 2
        self._snake = Snake(self._field, snake_init_pos)
        self._field.spawn_rabbit()
        self._redraw_all()

    def _draw_background(self):
        if self._state == 'PLAY':
            color = (255,255,255)
        elif self._state == 'GAME OVER':
            color = (255,0,0)
        elif self._state == 'PAUSE':
            color = (100,100,100)
        else:
            raise Exception, 'Unexpected state: %s' % str(self._state)

        background = pygame.Surface(self._screen.get_size())
        background = background.convert()
        background.fill(color)
        self._screen.blit(background, (0, 0))
        pygame.display.flip()
        return background

    def _main_loop(self):
        while self._continue_main_loop:
            time_passed = self._clock.tick(MOVE_PER_SEC)
            events = pygame.event.get()
            for e in events:
                self._dispatch_event(e)
            if self._state == 'PLAY':
                try:
                    self._snake.make_step()
                    self._redraw_field()
                except GameOver:
                    self._state = 'GAME OVER'
                    self._draw_background()

    def _redraw_field(self):
        self._redraw_cells(self._field.extract_changed())

    def _redraw_all(self):
        self._draw_background()
        if (self._state == 'PLAY'):
            self._redraw_cells(iter(self._field))

    def _redraw_cells(self, cells):
        for c in cells:
            rect = pygame.Rect(game2screen(c), (GAME_CELL_SIZE, GAME_CELL_SIZE))
            item = self._field[c]
            if item is None:
                color = (255, 255, 255)
            elif type(item) is Snake:
                color = (0, 0, 255)
            elif type(item) is Rabbit:
                color = (0, 255, 0)
            elif type(item) is Shit:
                color = (90, 60, 20)
            else:
                raise ValueError, 'Unexpected item on %s: %s' %(
                        c, self._field[c])
            pygame.draw.rect(self._screen, color, rect)
        pygame.display.flip()

    def _dispatch_event(self, event):
        if (event.type == QUIT) or (
                event.type == KEYDOWN and event.key == K_ESCAPE):
            self._exit()
        elif event.type == KEYDOWN and event.key in CONTROLS:
            self._snake.try_change_direction(CONTROLS[event.key])
        elif event.type == KEYDOWN and event.key == K_SPACE:
            if self._state in ('PLAY', 'PAUSE'):
                self._toggle_pause()
            elif self._state == 'GAME OVER':
                self._restart()

    def _exit(self):
        self._state = 'EXIT'
        self._continue_main_loop = False

    def _toggle_pause(self):
        if self._state == 'PLAY':
            self._state = 'PAUSE'
        elif self._state == 'PAUSE':
            self._state = 'PLAY'
        self._redraw_all()

    def run(self):
        self._draw_background()
        self._main_loop()
        pygame.display.quit()


if __name__ == '__main__':
    g = Game()
    g.run()
