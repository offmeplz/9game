#!/usr/bin/env python
#vim:fileencoding=utf-8

import numpy

import pygame
from pygame.locals import *

GAME_X_SIZE = 2.
GAME_Y_SIZE = 5.
CELL_SIZE = 100
TICK_PER_SEC = 100

def game2screen(g_coord):
    gx, gy = g_coord
    sx = gx * CELL_SIZE
    sy = (GAME_Y_SIZE - gy) * CELL_SIZE
    return sx, sy

def vec2d(x, y=None):
    if y is None:
        if len(x) != 2:
            raise ValueError, "Can't make 2-d vector from %s" % str(x)
        return vec2d(x[0], x[1])
    else:
        return numpy.array((x,y), numpy.float64)
            

class Physical(object):
    def prelive(self):
        pass

    def live(self, time):
        pass

    def postlive(self):
        pass

    def iter_subobjects(self):
        return iter([])


class MassPoint(Physical):
    def __init__(self, coord, velocity = (0,0)):
        self._coord = vec2d(coord)
        self._velocity = vec2d(velocity)
    
    def get_coordinates(self):
        return (self._coord[0], self._coord[1])

    def live(self, time):
        self._coord += self._velocity
        return True


class Universe(Physical):
    def __init__(self, game_size_x, game_size_y):
        self._objects = set()
        self._g_sz_x = game_size_x
        self._g_sz_y = game_size_y
        self._changes = set()

    def add(self, obj):
        if obj not in self._objects:
            self._objects.add(obj)
            self._changes.add(obj)
            for so in obj.iter_subobjects():
                self.add(so)

    def prelive(self):
        pass

    def live(self, time):
        for obj in self:
            changed = obj.live(time)
            self._changes.add(obj)

    def postlive(self):
        pass

    def __iter__(self):
        return iter(self._objects)

    def iter_subobjects(self):
        return iter(self)

    def extract_changes(self):
        changes = self._changes
        self._changes = set()
        return changes


class Model(object):
    def __init__(self):
        self._universe = Universe(GAME_X_SIZE, GAME_Y_SIZE)
        self._tick_time = 1.0 / TICK_PER_SEC
        self._universe.add(MassPoint((GAME_X_SIZE / 2, 3 * GAME_Y_SIZE / 4), (0.01, 0.01)))
        self._object2view = {}

    def next_state(self):
        self._universe.live(self._tick_time)

    def extract_changes(self):
        """
        return list of (old_view, new_view) pairs
        """
        changed_objects = self._universe.extract_changes()
        result = []
        for co in changed_objects:
            new_view = View.create(co)
            old_view = self._object2view.get(co, EmptyView)
            self._object2view[co] = new_view
            result.append((old_view, new_view))
        return result


class View(object):
    @staticmethod
    def create(obj):
        if obj.__class__ is MassPoint:
            return PointView(obj.get_coordinates())
        return View()

    def clear(self, surface, background):
        pass

    def draw(self, surface):
        pass

class PointView(View):
    def __init__(self, g_coord):
        s_coord = game2screen(g_coord)
        self._sprite = pygame.sprite.Sprite()

        image = pygame.surface.Surface((9,9)).convert_alpha()
        image.fill(pygame.color.Color(255, 255, 255, 255))
        pygame.draw.circle(image, (0,0,0), (5,5), 3)
        self._sprite.image = image
        self._sprite.rect = image.get_rect().move(s_coord)
        self._sprite_group = pygame.sprite.RenderPlain([self._sprite])

    def clear(self, surface, background):
        self._sprite_group.clear(surface, background)

    def draw(self, surface):
        self._sprite_group.draw(surface)

EmptyView = View()


class Game(object):
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('9nPhys')
        x_size = int(GAME_X_SIZE * CELL_SIZE)
        y_size = int(GAME_Y_SIZE * CELL_SIZE)
        window = pygame.display.set_mode((x_size, y_size))
        self._screen = pygame.display.get_surface()
        self._background = self._create_background()
        self._restart()

    def _restart(self):
        self._clock = pygame.time.Clock()
        self._continue_main_loop = True
        self._state = 'PLAY'
        self._model = Model()

    def _create_background(self):
        color = (255,255,255)
        background = pygame.Surface(self._screen.get_size())
        background = background.convert()
        background.fill(color)
        return background

    def _dispatch_event(self, event):
        if (event.type == QUIT) or (
                event.type == KEYDOWN and event.key == K_ESCAPE):
            self._exit()

    def _draw_background(self):
        self._screen.blit(self._background, (0, 0))

    def _exit(self):
        self._state = 'EXIT'
        self._continue_main_loop = False

    def _main_loop(self):
        while self._continue_main_loop:
            time_passed = self._clock.tick(TICK_PER_SEC)
            events = pygame.event.get()
            for e in events:
                self._dispatch_event(e)
            self._model.next_state()
            changed = self._model.extract_changes()
            self._redraw(changed)

    def _redraw(self, view_iter):
        for old_view, new_view in view_iter:
            old_view.clear(self._screen, self._background)
            new_view.draw(self._screen)
        pygame.display.flip()

    def _redraw_all(self):
        self._draw_background()
        pygame.display.flip()

    def run(self):
        self._redraw_all()
        self._main_loop()
        pygame.display.quit()

if __name__ == '__main__':
    g = Game()
    g.run()
