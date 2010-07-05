#!/usr/bin/env python
#vim:fileencoding=utf-8

import pygame

import util
from util import Vec

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


class Creep(GameObject):
    resource_name = 'creep.png'
    speed = 1.
    
    def __init__(self, g_pos, field):
        GameObject.__init__(self)

        self.g_pos = Vec(float(g_pos[0]), float(g_pos[1]))
        self.field = field
        self.rect.center = util.game2cscreen(g_pos)
        self.curdst = None
        self.cursrc = None

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
        self.rect.center = util.game2cscreen(self.g_pos)

    def forget_way(self):
        self.curdst, self.cursrc = None, None

    def finish(self):
        self.kill()

    def current_cell(self):
        return int(round(self.g_pos[0])), int(round(self.g_pos[1]))

class Wall(GameObject):
    resource_name = 'wall.png'
    def __init__(self, g_pos):
        GameObject.__init__(self)
        self.rect.center = util.game2cscreen(g_pos)
