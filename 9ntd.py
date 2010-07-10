#!/usr/bin/env python
#vim:fileencoding=utf-8

import random

from collections import deque
import itertools
from itertools import product, count
from math import sqrt
import datetime

import pygame
from pygame.locals import *

import field
import interface
import util
from cfg import *
from gameobjects import Creep, Wall, SimpleBullet, SimpleTower, Starter, Tower, Blood
from util import Vec

import testlevel

class BuildError(Exception):
    pass

def norm(vec):
    return sqrt(vec[0] ** 2 + vec[1] ** 2)

# TODO: use Vec class
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

    pygame.draw.aaline(surface, color, begin, end)
    pygame.draw.aaline(surface, color, end, side_end1)
    pygame.draw.aaline(surface, color, end, side_end2)


class Cell(object):
    allowed = set(('empty', 'enter', 'exit', 'obstacle'))

    __slots__ = ['content']

    def __init__(self, content='empty'):
        self.setcontent(content)

    def isexit(self):
        return self.content == 'exit'

    def setcontent(self, content):
        if content not in self.allowed:
            raise ValueError, "set content to %s is not allowed" % content
        self.content = content


class World(object):
    def __init__(self, level):
        enters =[(0, i) for i in xrange(GAME_Y_SIZE)]
        exits = [(GAME_X_SIZE - 1, i) for i in xrange(GAME_Y_SIZE)]
        self.field = Field(GAME_X_SIZE, GAME_Y_SIZE, enters, exits)

        self.creeps = pygame.sprite.Group()
        self.towers = pygame.sprite.Group()
        self.missles = pygame.sprite.Group()
        self.corpse = pygame.sprite.Group()
        self.ticks_elapsed = 0

        self.creepwave = Starter(
                level.CREEP_WAVES[0]['creeps'],
                self.spawn_creep)

        self.money = level.INIT_MONEY
        self.lives = level.LIVES

    def add_creep(self, creep):
        creep.add([self.creeps])

    def get_money(self):
        return self.money

    def get_lives(self):
        return self.lives

    def build_tower(self, tower_cls, pos):
        if tower_cls.cost > self.get_money():
            raise BuildError, "Not enough money"
        sizes = (tower_cls.size, tower_cls.size)
        topleft = util.placeintrect(pos, sizes)
        canbuild = all(
                self.field.canbuildon(p)
                for p in util.iterpoints(topleft, sizes))
        
        if canbuild:
            self.add_tower(topleft, tower_cls)
        else:
            raise BuildError, "Can't build here"

    def add_tower(self, pos, cls):
        if cls is Wall:
            tower = cls(pos)
        elif cls is SimpleTower:
            tower = SimpleTower(pos, self.creeps, self.missles)
        else:
            raise ValueError, "Unknown tower type: %s" % repr(cls)

        if pygame.sprite.spritecollideany(tower, self.creeps):
            raise BuildError, "Can't build on creeps"
        
        buildcells = list(util.iterpoints(pos, (cls.size, cls.size)))
        self.field.buildon(*buildcells)

        # check if we block creeps
        block_creeps = False
        for creep in self.creeps:
            if tuple(creep.current_cell()) not in self.field.dir_field:
                block_creeps = True
                break
        for e in self.field._enters:
            if e not in self.field.dir_field:
                block_creeps = True
                break
        if block_creeps:
            self.field.clearon(*buildcells)
            raise BuildError, "Blocking"

        tower.add([self.towers])
        for creep in self.creeps:
            creep.forget_way()
        self.money -= tower.cost

    def update(self, ticks):
        self.ticks_elapsed += ticks
        self.creepwave.update(ticks)

        self.towers.update(ticks)
        self.creeps.update(ticks)
        self.missles.update(ticks)

    def draw(self, surface):
        self.creeps.draw(surface)
        self.missles.draw(surface)

    def spawn_creep(self, creep=None):
        if creep is None:
            creep = Creep(health=3, speed=2)
        creep_pos = random.choice(list(self.field._enters))
        creep.place(creep_pos, self.field, self.oncreepexit, self.oncreepdeath)
        self.add_creep(creep)

    def oncreepexit(self, creep):
        self.lives -= 1

    def oncreepdeath(self, creep):
        self.money += creep.money
        self.corpse.add(Blood(creep))

class Field(object):
    def __init__(self, size_x, size_y, enters, exits):
        self._x_size = size_x
        self._y_size = size_y
        self._field = []
        for i in xrange(size_x):
            self._field.append([Cell() for j in xrange(size_y)])
        self._changed = set()
        self._exits = set(exits)
        for pos in self._exits:
            cell = self._get_cell(pos)
            cell.setcontent('exit')
        self._enters = set(enters)
        for pos in self._enters:
            cell = self._get_cell(pos)
            cell.setcontent('enter')
        self._recalculate_paths()

    def get_enter(self):
        return self.enter

    def buildon(self, *pos):
        for p in pos:
            if not self.canbuildon(p):
                raise ValueError,\
                        "Cant build on %s. Already contains: %s" % (
                            p, self.get_content(p))
        for p in pos:
            self._get_cell(p).content = 'obstacle'
        self._recalculate_paths()

    def clearon(self, *pos):
        for p in pos:
            if self._get_cell(p).content != 'obstacle':
                raise ValueError, "Can't clear on %s. Content is not obstacle" % p
        for p in pos:
            self._get_cell(p).content = 'empty'
        self._recalculate_paths()

    def contains(self, pos):
        return 0 <= pos[0] < self._x_size and 0 <= pos[1] < self._y_size

    def canmoveon(self, pos):
        return self.get_content(pos) != 'obstacle'

    def canbuildon(self, pos):
        return self.contains(pos) and self.get_content(pos) == 'empty'

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

    def _recalculate_paths(self):
        self.dir_field = field.build_dir_field(self, self._exits)

    def set_dir_field(self, dir_field):
        self.dir_field = dir_field

    def get_next_pos(self, pos):
        d = self.get_direction(pos)
        if d is None:
            return None
        else:
            return self.get_direction(pos).next_vertex

    def get_direction(self, pos):
        pos = tuple(pos)
        direction = self.dir_field.get(pos, None)
        if direction is None:
            return None
        else:
            return direction

    def in_edges(self, pos):
        sq2 = sqrt(2)
        neighbours = [
                    ((pos[0] + 1, pos[1]), 1),
                    ((pos[0] + 1, pos[1] + 1), sq2),
                    ((pos[0], pos[1] + 1), 1),
                    ((pos[0] - 1, pos[1] + 1), sq2),
                    ((pos[0] - 1, pos[1]), 1),
                    ((pos[0] - 1, pos[1] - 1), sq2),
                    ((pos[0], pos[1] - 1), 1),
                    ((pos[0] + 1, pos[1] - 1), sq2)]
        for i,n in enumerate(neighbours):
            if self.contains(n[0]) and self.canmoveon(n[0]):
                good = False
                if i % 2 == 0:
                    good = True
                else:
                    ni = neighbours[(i + 1) % len(neighbours)]
                    pi = neighbours[(i - 1) % len(neighbours)]
                    if self.contains(ni[0]) and self.canmoveon(ni[0]) and\
                       self.contains(pi[0]) and self.canmoveon(pi[0]):
                           good = True
                if good:
                    yield field.Edge(n[0], pos, n[1])


class Game(object):
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('9nTd')
        field_x_size = GAME_X_SIZE * GAME_CELL_SIZE
        field_y_size = GAME_Y_SIZE * GAME_CELL_SIZE

        panel_x_size = field_x_size
        panel_y_size = MAIN_PANEL_Y_SIZE

        top_panel_x_size = field_x_size
        top_panel_y_size = TOP_PANEL_Y_SIZE

        window_x_size = field_x_size
        window_y_size = field_y_size + panel_y_size + top_panel_y_size
        
        window = pygame.display.set_mode((window_x_size, window_y_size))
        self._screen = pygame.display.get_surface()

        field_rect = Rect((0,top_panel_y_size), (field_x_size, field_y_size))
        self._field_rect = field_rect
        self._field_surface = self._screen.subsurface(field_rect)
        self._game_speed = 1
        self._clock = None
        self._messages = util.MessageQueue()

        self._tower_sketch_rect = None
        self._tower_for_build_class = None
        self._selected_object = None
        self._selection_surface = None
        self._selection_rect = None

        # creating interface.

        panel_rect = Rect((0, top_panel_y_size + field_y_size), (panel_x_size, panel_y_size))
        self._panel = interface.PanelHolder(self._screen, panel_rect)

        top_panel_rect = Rect((0,0), (top_panel_x_size, top_panel_y_size))
        self._top_panel = interface.PanelHolder(self._screen, top_panel_rect)

        menu_rect = Rect((0, 0), (top_panel_x_size / 6, top_panel_y_size))
        self.menu_button = interface.MenuButton(
                self._top_panel.surface, menu_rect)
        self._top_panel.addsubpanel(self.menu_button, menu_rect)

        def get_money_text():
            return '%d $' % self.world.get_money()
        money_rect = Rect((top_panel_x_size * 5 / 6, 0), (top_panel_x_size / 6, top_panel_y_size))
        money_info = interface.TextInfo(
                self._top_panel.surface, money_rect, get_money_text)
        self._top_panel.addsubpanel(money_info, menu_rect)

        def get_lives_text():
            return str(self.world.get_lives())
        lives_rect = Rect((top_panel_x_size * 4 / 6, 0), (top_panel_x_size / 6, top_panel_y_size))
        lives_info = interface.TextInfo(
                self._top_panel.surface, lives_rect, get_lives_text)
        self._top_panel.addsubpanel(lives_info, lives_rect)

        def get_time_text():
            if self.world is None:
                return ''
            else:
                secs = self.world.ticks_elapsed / TICK_PER_SEC
                return '%02d:%02d' % (secs / 60, secs % 60)
        time_rect = Rect((top_panel_x_size / 6, 0), (top_panel_x_size / 6, top_panel_y_size))
        time_info = interface.TextInfo(
                self._top_panel.surface, time_rect, get_time_text)
        self._top_panel.addsubpanel(time_info, time_rect)

        def get_message():
            return self._messages.get_message()
        msg_rect = Rect((top_panel_x_size * 2 / 6, 0), (top_panel_x_size * 2 / 6, top_panel_y_size))
        msg_info = interface.TextInfo(
                self._top_panel.surface, msg_rect, get_message)
        self._top_panel.addsubpanel(msg_info, msg_rect)

        build_rect = Rect((panel_x_size * 2 / 3, 0), (panel_x_size / 3, panel_y_size))
        self.build_panel = interface.PanelHolder(self._panel.surface, build_rect)
        self._panel.addsubpanel(self.build_panel, build_rect)

        # place buttons
        for i, towercls in enumerate(testlevel.TOWERS):
            img, rect = towercls.get_img_rect()
            icon_sizes = (GAME_CELL_SIZE, GAME_CELL_SIZE)
            icon = pygame.transform.scale(img, icon_sizes)
            icon_rect = Rect((i * GAME_CELL_SIZE, 0), icon_sizes)
            def pushfunc(a=towercls):
                self.select_tower_for_build(a)
            button = interface.TowerButton(
                    self.build_panel.surface.subsurface(icon_rect),
                    icon,
                    pushfunc)
            self._panel.addsubpanel(button, icon_rect)

        info_rect = Rect((panel_x_size / 3, 0), (panel_x_size / 3, panel_y_size))
        self.info_slot = interface.Slot(self._panel.surface.subsurface(info_rect))
        self._panel.addsubpanel(self.info_slot, info_rect)
        self._restart()

    def _restart(self):
        reload(testlevel)
        self.world = World(testlevel)
        self._continue_main_loop = True
        self._clock = pygame.time.Clock()
        self._state = 'PLAY'
        self.background = pygame.Surface(self._field_surface.get_size()).convert()
        color = (255,255,255)
        self.background.fill(color)
        self.pause_mask = pygame.Surface(self._field_surface.get_size()).convert_alpha()
        self.pause_mask.fill((100,100,100,150))

        self.static = self.background.copy()
        self.ground = self.background.copy()
        self.air = self.background.copy()
        self._messages.post_message('Start!', 3)

        self._field_surface.blit(self.background, (0,0))

        self.update_panel()

    def _main_loop(self):
        while self._continue_main_loop:
            time_passed = self._clock.tick(TICK_PER_SEC)
            events = pygame.event.get()
            for e in events:
                if self._state == 'PLAY':
                    self._dispatch_play_event(e)
                elif self._state == 'PAUSE':
                    self._dispatch_pause_event(e)

            if self._state == 'PLAY':
                self.world.creeps.clear(self._field_surface, self.static)
                self.world.missles.clear(self._field_surface, self.static)
                if self._tower_sketch_rect is not None:
                    self._field_surface.blit(self.static, self._tower_sketch_rect.topleft, self._tower_sketch_rect)
                if self._selection_rect is not None:
                    self._field_surface.blit(self.static, self._selection_rect.topleft, self._selection_rect)

                self.world.update(self._game_speed)

                if BLOOD:
                    self.world.corpse.draw(self.background)
                    self.world.corpse.draw(self.static)
                    self.world.corpse.draw(self._field_surface)

                self.world.corpse.empty()
                self.world.creeps.draw(self._field_surface)
                self.world.missles.draw(self._field_surface)

                self._draw_tower_sketch()
                self._draw_selection()


            self._top_panel.update()
            self._panel.update()

            pygame.display.flip()
    
    def _draw_tower_sketch(self):
        tower_cls = self._tower_for_build_class
        if tower_cls is not None:
            mpos = self._to_field_coord(pygame.mouse.get_pos())
            if mpos is None:
                return
            g_pos = util.screen2fgame(mpos)
            g_topleft = util.placeintrect(g_pos, (tower_cls.size, ) * 2)
            s_topleft = util.game2tlscreen(g_topleft)
            self._tower_sketch_rect = tower_cls.draw_oksketch_on(
                    self._field_surface, s_topleft)

    def _draw_selection(self):
        if self._selected_object is not None:
            self._selection_rect = self._selection_surface.get_rect()
            self._selection_rect.center = self._selected_object.rect.center
            self._field_surface.blit(self._selection_surface, self._selection_rect.topleft)
            if not self._selected_object.alive():
                self._selected_object = None


    def _to_field_coord(self, pos):
        if self._field_rect.collidepoint(pos):
            return (pos[0] - self._field_rect.left,
                    pos[1] - self._field_rect.top)
        else:
            return None

    def select_tower_for_build(self, tower_cls):
        self._tower_for_build_class = tower_cls
        self._selected_object = None
        self.info_slot.set_panel(None)

    def select_object(self, obj):
        self._tower_for_build_class = None
        self._selected_object = obj
        if obj is not None:
            self._selection_surface = pygame.surface.Surface((
                obj.rect.width + 4, obj.rect.height + 4)).convert_alpha()
            self._selection_surface.fill((0,0,0,0))
            pygame.draw.rect(
                    self._selection_surface, (0,255,0),
                    self._selection_surface.get_rect(), 1)

            if isinstance(obj, Tower):
                towerinfo = interface.TowerInfo(
                        self.info_slot.surface, obj)
                self.info_slot.set_panel(towerinfo)
            elif isinstance(obj, Creep):
                creepinfo = interface.CreepInfo(
                        self.info_slot.surface, obj)
                self.info_slot.set_panel(creepinfo)
            else:
                self.info_slot.set_panel(None)

    def reset_selection(self):
        self._tower_for_build_class = None
        self._selected_object = None
        self.info_slot.set_panel(None)

    def toggle_pause(self):
        if self._state == 'PLAY':
            self._state = 'PAUSE'
            self._field_surface.blit(self.pause_mask, (0,0))
            self._messages.post_message('Pause!', 3)
        elif self._state == 'PAUSE':
            self._state = 'PLAY'
            self._messages.post_message('Play!', 3)
            self._field_surface.blit(self.static, (0,0))

    def _dispatch_pause_event(self, event):
        if (event.type == QUIT) or (
                event.type == KEYDOWN and event.key == K_ESCAPE):
            self._exit()
        elif event.type == KEYDOWN:
            if event.key == K_RETURN:
                self.toggle_pause()

    def _dispatch_play_event(self, event):
        if (event.type == QUIT) or (
                event.type == KEYDOWN and event.key == K_ESCAPE):
            self._exit()
        elif event.type == KEYDOWN:
            if event.key == K_w:
                self.select_tower_for_build(Wall)
            elif event.key == K_s:
                self.select_tower_for_build(SimpleTower)
            elif event.key == K_SPACE:
                self._game_speed = 4
            elif event.key == K_RETURN:
                self.toggle_pause()
            elif event.key == K_F10:
                self._restart()
        elif event.type == KEYUP:
            if event.key == K_SPACE:
                self._game_speed = 1
        elif event.type == MOUSEBUTTONDOWN:
            if self._field_rect.collidepoint(event.pos):
                pos = self._to_field_coord(event.pos)
                if event.button == 1:
                    game_pos = util.screen2fgame(pos)
                    if self._tower_for_build_class is None:
                        for obj in itertools.chain(self.world.towers, self.world.creeps):
                            if obj.rect.collidepoint(pos):
                                self.select_object(obj)
                                break
                    else:
                        try:
                            self.world.build_tower(self._tower_for_build_class, game_pos)
                            self.update_static_layer()
                        except BuildError, e:
                            self._messages.post_message(str(e), 3)
                elif event.button == 2:
                    for creep in self.world.creeps:
                        b = SimpleBullet(util.screen2fgame(pos), creep, 1, 20)
                        self.world.missles.add(b)
                        break
                elif event.button == 3:
                    self.reset_selection()
            elif self._top_panel.rect.collidepoint(event.pos):
                self._top_panel.onclick(event.pos, event.button)
            elif self._panel.rect.collidepoint(event.pos):
                pos = Vec(event.pos) - Vec(self._panel.rect.topleft)
                self._panel.onclick(pos, event.button)
        elif event.type == MOUSEBUTTONUP:
            if self._top_panel.rect.collidepoint(event.pos):
                self._top_panel.onrelease(event.pos, event.button)

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
        self._panel.surface.fill((150, 150, 150))
        self._top_panel.surface.fill((150, 150, 150))
        self._top_panel.redraw()
        self._panel.redraw()

if __name__ == '__main__':
    g = Game()
    g.run()
