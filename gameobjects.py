#!/usr/bin/env python
#vim:fileencoding=utf-8

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


class Creep(GameObject):
    resource_name = 'creep.png'
    speed = 1.
    
    def __init__(self, g_pos, health, field):
        GameObject.__init__(self)

        self.g_pos = Vec(float(g_pos[0]), float(g_pos[1]))
        self.field = field
        self.rect.center = util.game2cscreen(g_pos)
        self.curdst = None
        self.cursrc = None
        self.direction = Vec(0,1)
        self.health = health
        self.maxhealth = health

    @classmethod
    def get_img_rect(cls):
        if cls.img is None:
            cls.img, cls.img_rect = util.load_image(cls.resource_name)
        return cls.img, cls.img_rect.copy()

    def update(self, ticks):
        g_pos = self.current_cell()
        cur_cell = self.field._get_cell(g_pos)
        if self.curdst is None:
            if cur_cell.is_exit:
                self.finish()
                return
            dst = self.field.get_next_pos(g_pos)
            self.curdst = Vec(dst)
            self.cursrc = Vec(g_pos)
        dstvec = self.curdst - self.g_pos
        vecnorm = self.speed / float(TICK_PER_SEC)
        if abs(dstvec) <= vecnorm:
            self.curdst = None
        else:
            dstvec *= vecnorm / abs(dstvec)
        self.g_pos += dstvec
        self.change_direction(dstvec)
        self.rect.center = util.game2cscreen(self.g_pos)

    def forget_way(self):
        self.curdst, self.cursrc = None, None

    def finish(self):
        self.kill()

    def current_cell(self):
        return int(round(self.g_pos[0])), int(round(self.g_pos[1]))

    def change_direction(self, new_direction):
        direction = new_direction
        if abs(direction[0]) < abs(direction[1]):
            direction[0] = 0
            direction[1] = signum(direction[1])
        else:
            direction[1] = 0
            direction[0] = signum(direction[0])
        if direction == self.direction:
            return
        self.direction = direction
        degrees = {
                (0,0) : 0,
                (0,-1) : 0,
                (-1,0) : 90,
                (0, 1) : 180,
                (1, 0) : 270}[tuple(self.direction)]
        self.image = pygame.transform.rotate(self.img, degrees)

    def hurt(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.kill()

class Wall(GameObject):
    resource_name = 'wall.png'
    def __init__(self, g_pos):
        GameObject.__init__(self)
        self.rect.center = util.game2cscreen(g_pos)

class SimpleBullet(GameObject):
    radius = 3
    image = None
    rect = None

    @classmethod
    def get_img_rect(cls):
        size = cls.radius * 2 - 1
        if cls.image is None:
            cls.image = pygame.surface.Surface((size, size)).convert_alpha()
            cls.image.fill(pygame.Color(255, 255, 255, 0))
            cls.rect = cls.image.get_rect()
            pygame.draw.circle(cls.image, (0,0,0), cls.rect.center, cls.radius)
        return cls.image, cls.rect

    def __init__(self, g_pos, target, damage, speed=None):
        GameObject.__init__(self)
        self.g_pos = Vec(g_pos)
        self.target = target
        self.damage = damage
        self.speed = speed
        rect_size = self.radius * 2 - 1
        self.rect.center = util.game2cscreen(g_pos)

    def update(self, ticks):
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
        self.kill()
        

class SimpleTower(GameObject):
    resource_name = 'wall.png'
    damage = 1
    radius = 3
    recharge_time = 2

    def __init__(self, g_pos):
        GameObject.__init__(self)
        self.rect.center = util.game2cscreen(g_pos)
        self.recharge = 0
        s_radius = self.radius * GAME_CELL_SIZE
        self.s_reach_rect = Rect(0, 0, s_radius, s_radius)
        self.s_reach_rect.center = game2screen(g_pos)

    def target(self, creeps):
        if self.recharge_time > 0:
            return None

        creep_rects = (c.rect for c in creeps)
        collision_idx = self.s_reach_rect.collidelist(creep_rects)
        if collision_idx == -1:
            return None
        else:
            pass
