#!/usr/bin/env python
#vim:fileencoding=utf-8

import collections
import math
import random
import pygame

import util
import interface
from util import Vec, signum


from cfg import *

def draw_lightning(surface, a, b):
    color = pygame.Color(0,0,100)
    a = Vec(a)
    b = Vec(b)
    for i in xrange(3):
        sections = random.randrange(3,7)
        points = [a]
        ab = b - a
        ls = [random.random() for i in xrange(sections)]
        ls.sort()
        for l in ls:
            p = a + ab * l
            p += ab.perpendicular() * 0.2 * (random.random() - 0.5)
            points.append((int(p[0]), int(p[1])))
        points.append(b)
        pygame.draw.aalines(surface, color, False, points)


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

    @classmethod
    def load_cached_image(cls, filename):
        if not hasattr(cls, 'img') or cls.img is None:
            cls.img, img_rect = util.load_image(cls.resource_name)
        return cls.img

    @classmethod
    def load_cached_image_list(cls, filename):
        if not hasattr(cls, 'image_list') or cls.image_list is None:
            cls.image_list = util.load_image_array(filename)
        return cls.image_list

    def update(self, ticks):
        pass

class Blood(GameObject):
    resource_name = 'blood.png'

    def __init__(self, obj):
        pygame.sprite.Sprite.__init__(self)
        images = self.load_cached_image_list(self.resource_name)
        self.image = random.choice(images)
        self.rect = self.image.get_rect().copy()
        self.rect.center = obj.rect.center
        angle = random.choice([0, 90, 180, 270])
        self.image = pygame.transform.rotate(self.image, angle)

class Message(pygame.sprite.Sprite):
    speed = 1.
    def __init__(self, text, lifetime, g_pos, color):
        pygame.sprite.Sprite.__init__(self)
        self.lifeticks = lifetime * TICK_PER_SEC
        font = interface.get_font()
        if isinstance(color, tuple):
            color = pygame.Color(*color)
        else:
            color = pygame.Color(color)
        self.image = font.render(text, True, color)
        self.g_pos = g_pos
        self.rect = self.image.get_rect()
        self.rect.center = util.game2cscreen(g_pos)

    def update(self, ticks):
        self.lifeticks -= ticks
        if self.lifeticks <= 0:
            self.kill()
            return

        self.g_pos -= Vec(0, self.speed / TICK_PER_SEC)
        self.rect.center = util.game2cscreen(self.g_pos)


class Starter(object):
    @staticmethod
    def defaultcallback(arg):
        raise NotImplementedError, "Callback is not set."

    def __init__(self, iargs, func, start=True):
        self.iargs = iter(iargs)
        self.started = start
        if self.started:
            self.next()

        if func is None:
            func = Starter.defaultcallback
        self.func = func
        self.curtime = 0

    def next(self):
        try:
            self.nexttime, self.arg = next(self.iargs)
        except StopIteration:
            self.nexttime, self.arg = None, None

    def start(self):
        if not self.started:
            self.started = True
            self.next()

    def alive(self):
        return self.started and self.nexttime is not None

    def update(self, ticks):
        if not self.started:
            return
        self.curtime += float(ticks) / TICK_PER_SEC
        while self.nexttime is not None and self.curtime > self.nexttime:
            self.func(self.arg)
            self.next()

class Creep(GameObject):
    resource_name = 'creep.png'
    speed = 2.
    health = 3
    money = 1
    
    def __init__(self, health=None, speed=None, money=None):
        pygame.sprite.Sprite.__init__(self)
        images = self.load_cached_image_list(self.resource_name)
        self.image = images[0]
        self.rect = self.image.get_rect().copy()
        self.direction = Vec(0,1)
        if money is not None:
            self.money = money
        if health is not None:
            self.health = health
        if speed is not None:
            self.speed = speed

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
        if degrees % 90 == 0:
            self.image = pygame.transform.rotate(self.image_list[0], degrees)
        else:
            self.image = pygame.transform.rotate(self.image_list[1], degrees - 45)
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
    def __init__(self, g_lefttop, world):
        GameObject.__init__(self)
        self.rect.center = util.game2cscreen(g_lefttop)
        self.g_pos = Vec(util.screen2fgame(self.rect.center))

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


class Lightning(pygame.sprite.Sprite):
    def __init__(self, g_pos, target, damagepersec, g_radius):
        pygame.sprite.Sprite.__init__(self)

        self.g_pos = Vec(g_pos)
        self.target = target
        self.damagepersec = float(damagepersec)
        self.curdamage = 0

        s_radius = GAME_CELL_SIZE * g_radius
        rect_size = s_radius * 2 + 1
        self.rect = pygame.Rect((0,0), (rect_size, rect_size))
        self.rect.center = util.game2cscreen(g_pos)
        self.beam_start = Vec(self.rect.center) - Vec(self.rect.topleft)
        self.image = pygame.surface.Surface((rect_size, rect_size))
        self.image = self.image.convert_alpha()
        self.g_radius = g_radius


    def update(self, ticks):
        target = self.target
        if target is None or not target.alive():
            self.kill()
            return

        distance = abs(Vec(target.g_pos) - Vec(self.g_pos))
        if distance > self.g_radius:
            self.kill()
            return

        self.curdamage += self.damagepersec * ticks / TICK_PER_SEC
        if self.curdamage >= 1:
            curdamage = int(math.floor(self.curdamage))
            self.curdamage -= curdamage
            target.hurt(curdamage)

        # draw
        beam_end = Vec(util.game2cscreen(target.g_pos)) - Vec(self.rect.topleft)
        self.image.fill((0,0,0,0))
        draw_lightning(self.image, self.beam_start, beam_end)
        

class SimpleTower(GameObject, Tower):
    resource_name = 'simpletower.png'

    damage = 1
    radius = 3
    recharge_time = 0.2
    bullet_speed = 5
    size = 2
    cost = 5

    def __init__(self, g_lefttop, world):
        GameObject.__init__(self)
        self.rect.topleft = util.game2tlscreen(g_lefttop)
        self.g_pos = Vec(util.screen2fgame(self.rect.center))
        self.creeps = world.creeps
        self.missles = world.missles
        self.current_recharge = 0
        self.recharge_ticks = self.recharge_time * TICK_PER_SEC

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
            if abs(distvec) <= self.radius:
                return creep
        return None

class LightningTower(GameObject, Tower):
    resource_name = 'lasertower.png'

    damage = 1.5
    radius = 3
    recharge_time = 2
    bullet_speed = 5
    size = 2
    cost = 5
    fire_cost = 1

    def __init__(self, g_lefttop, world):
        GameObject.__init__(self)
        self.rect.topleft = util.game2tlscreen(g_lefttop)
        self.g_pos = Vec(util.screen2fgame(self.rect.center))
        self.creeps = world.creeps
        self.missles = world.missles
        self.messages = world.messages
        self.current_recharge = 0
        self.world = world
        self.curmissle = None
        self.recharge_ticks = self.recharge_time * TICK_PER_SEC

    def update(self, ticks):
        if self.curmissle is None:
            self.current_recharge -= ticks
        elif not self.curmissle.alive():
            self.curmissle = None
            return
        if self.current_recharge > 0:
            return

        if self.world.money < self.fire_cost:
            return

        creep = self._find_target()
        if creep:
            self._fire(creep)

    def _fire(self, target):
        laser = Lightning(
                self.g_pos, target, self.damage, self.radius)
        self.missles.add(laser)
        self.curmissle = laser
        self.world.money -= self.fire_cost
        msg = '-%d' % self.fire_cost
        self.messages.add(Message(msg, 1, Vec(self.g_pos), GOLD_COLOR))
        self.current_recharge = self.recharge_ticks
    
    def _find_target(self):
        for creep in self.creeps:
            distvec = creep.g_pos - self.g_pos
            if abs(distvec) <= self.radius:
                return creep
        return None

