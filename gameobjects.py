#!/usr/bin/env python
#vim:fileencoding=utf-8

import collections
import pygame

import util
from util import Vec, signum


from cfg import *

class GameObject(pygame.sprite.Sprite):
    img, img_rect = None, None

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = self.get_img_rect()

    @classmethod
    def get_img_rect(cls):
        if cls.img is None:
            cls.img, cls.img_rect = util.load_image(cls.resource_name)
        return cls.img, cls.img_rect.copy()

    def update(self, ticks):
        pass

class Blood(GameObject):
    resource_name = 'blood.png'
    def __init__(self, obj):
        GameObject.__init__(self)
        self.rect.center = obj.rect.center

class Starter(object):
    @staticmethod
    def defaultcallback(arg):
        raise NotImplementedError, "Callback is not set."

    def __init__(self, iargs, func):
        self.iargs = iter(iargs)
        try:
            self.nexttime, self.arg = next(self.iargs)
        except StopIteration:
            self.nexttime, self.arg = None, None

        if func is None:
            func = Starter.defaultcallback
        self.func = func
        self.curtime = 0

    def update(self, ticks):
        self.curtime += float(ticks) / TICK_PER_SEC
        while self.nexttime is not None and self.curtime > self.nexttime:
            self.func(self.arg)
            try:
                self.nexttime, self.arg = next(self.iargs)
            except StopIteration:
                self.nexttime, self.arg = None, None

class Creep(GameObject):
    resource_name = 'creep.png'
    speed = 2.
    health = 3
    
    def __init__(self, health=None, speed=None, money=1):
        GameObject.__init__(self)
        self.direction = Vec(0,1)
        self.money = money
        if health is not None:
            self.health = health
        else:
            self.health = Creep.health

        self.maxhealth = health

    @classmethod
    def get_img_rect(cls):
        if cls.img is None:
            cls.img, cls.img_rect = util.load_image(cls.resource_name)
        return cls.img, cls.img_rect.copy()

    def place(self, g_pos, field, onexit, ondeath):
        self.g_pos = Vec(g_pos)
        self.field = field
        self.rect.center = util.game2cscreen(self.g_pos)
        self.curdst = None
        self.onexit = onexit
        self.ondeath = ondeath

    def update(self, ticks):
        cell_pos = self.current_cell()
        cur_cell = self.field._get_cell(cell_pos)
        if self.curdst is None:
            if cur_cell.isexit():
                self.finish()
                self.onexit(self)
                return
            dst = self._find_next_dst()
            self.curdst = Vec(dst)
        dstvec = self.curdst - self.g_pos
        vecnorm = ticks * self.speed / float(TICK_PER_SEC)
        if abs(dstvec) <= vecnorm:
            self.curdst = None
        else:
            dstvec *= vecnorm / abs(dstvec)
        self.g_pos += dstvec
        self.change_direction(dstvec)
        self.rect.center = util.game2cscreen(self.g_pos)

    def _find_next_dst(self):
        return self.field.get_next_pos(self.current_cell())

    def _find_next_wp(self):
        cur_cell = self.current_cell()
        cur_direction = self.field.get_direction(cur_cell)

        if cur_direction.next_waypoint is not None:
            return cur_direction.next_waypoint

        radius = self.rect.width / 2
        s_cur_pos = util.game2cscreen(self.g_pos)
        dst = self.field.get_next_pos(cur_cell)
        while not self.field.is_exit(dst):
            nextdst = self.field.get_next_pos(dst)
            s_nextdst = util.game2cscreen(nextdst)
            walkable = util.is_walkable(
                    s_cur_pos, s_nextdst, radius, self.towers)
            if not walkable:
                break
            dst = nextdst
        cur_direction.next_waypoint = dst
        return dst

    def forget_way(self):
        self.curdst = None

    def finish(self):
        self.kill()

    def current_cell(self):
        return int(round(self.g_pos[0])), int(round(self.g_pos[1]))

    def change_direction(self, new_direction):
        direction = new_direction
        need_cut = False
        if 2 * abs(direction[0]) < abs(direction[1]):
            direction[0] = 0
            direction[1] = signum(direction[1])
        elif 2 * abs(direction[1]) < abs(direction[0]):
            direction[1] = 0
            direction[0] = signum(direction[0])
        else:
            direction[0] = signum(direction[0])
            direction[1] = signum(direction[1])
            need_cut = True

        if direction == self.direction:
            return
        self.direction = direction
        degrees = {
                ( 0, 0): 0,
                ( 0,-1): 0,
                (-1,-1): 45,
                (-1, 0): 90,
                (-1, 1): 135,
                ( 0, 1): 180,
                ( 1, 1): 225,
                ( 1, 0): 270,
                ( 1,-1): 315}[tuple(self.direction)]
        self.image = pygame.transform.rotate(self.img, degrees)
        if need_cut:
            bound_rect = self.image.get_bounding_rect()
            self.image = self.image.subsurface(bound_rect)

    def hurt(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.kill()
            self.ondeath(self)

class Tower(object):
    @classmethod
    def get_oksketch(cls):
        if not hasattr(cls, 'sketch'):
            sketch_size = GAME_CELL_SIZE * cls.size
            cls.sketch = pygame.surface.Surface((sketch_size, sketch_size)).convert_alpha()
            cls.sketch.fill((0,255,0,100))
        return cls.sketch

    
    @classmethod
    def draw_oksketch_on(cls, surface, s_towerlefttop):
        '''
        Returns updated rectangle.
        '''
        return surface.blit(cls.get_oksketch(), s_towerlefttop)


class Wall(GameObject, Tower):
    resource_name = 'wall.png'
    size = 1
    cost = 3
    damage = 0
    radius = 0
    def __init__(self, g_lefttop):
        GameObject.__init__(self)
        self.rect.center = util.game2cscreen(g_lefttop)

class SimpleBullet(GameObject):
    radius = 2
    image = None
    rect = None

    @classmethod
    def get_img_rect(cls):
        size = cls.radius * 2 + 1
        if cls.image is None:
            cls.image = pygame.surface.Surface((size, size)).convert_alpha()
            cls.image.fill(pygame.Color(255, 255, 255, 0))
            cls.rect = cls.image.get_rect()
            pygame.draw.circle(cls.image, (0,0,0), cls.rect.center, cls.radius)
        return cls.image, cls.rect.copy()

    def __init__(self, g_pos, target, damage, speed):
        GameObject.__init__(self)
        self.g_pos = Vec(g_pos)
        self.target = target
        self.damage = damage
        self.speed = speed
        self.rect.center = util.game2cscreen(g_pos)

    def update(self, ticks):
        if self.target is None:
            self.kill()
            return

        if not self.target.alive():
            self.kill()
        cur_speed = float(ticks * self.speed) / TICK_PER_SEC
        v = Vec(self.target.g_pos) - Vec(self.g_pos)
        if abs(v) > cur_speed:
            v *= cur_speed / abs(v)
            self.g_pos += v
            self.rect.center = util.game2cscreen(self.g_pos)
        else:
            self.g_pos = self.target.g_pos
            self.rect.center = util.game2cscreen(self.g_pos)
            self.explode()

    def explode(self):
        self.target.hurt(self.damage)
        self.target = None
        

class SimpleTower(GameObject, Tower):
    resource_name = 'simpletower.png'

    damage = 1
    radius = 3
    sqradius = radius ** 2
    recharge_time = 2
    recharge_ticks = recharge_time * TICK_PER_SEC
    bullet_speed = 5
    size = 2
    cost = 5

    def __init__(self, g_lefttop, creeps, missles):
        GameObject.__init__(self)
        self.rect.topleft = util.game2tlscreen(g_lefttop)
        self.g_pos = Vec(util.screen2fgame(self.rect.center))
        self.creeps = creeps
        self.missles = missles
        self.current_recharge = 0

    def update(self, ticks):
        self.current_recharge -= ticks
        if self.current_recharge > 0:
            return

        creep = self._find_target()
        if creep:
            missle = SimpleBullet(
                    self.g_pos, creep, self.damage, self.bullet_speed)
            self.missles.add(missle)
            self.current_recharge = self.recharge_ticks
    
    def _find_target(self):
        for creep in self.creeps:
            distvec = creep.g_pos - self.g_pos
            sqdist = distvec[0] ** 2 + distvec[1] ** 2
            if sqdist <= self.sqradius:
                return creep
        return None
