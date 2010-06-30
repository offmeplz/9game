#!/usr/bin/env python
#vim:fileencoding=utf-8

import pygame

import util
from util import Vec

from cfg import *

class Creep(pygame.sprite.Sprite):
    img, img_rect = None, None
    resource_name = 'creep.png'
    speed = 0.5
    
    def __init__(self, g_pos, field):
        pygame.sprite.Sprite.__init__(self)
        self.g_pos = Vec(float(g_pos[0]), float(g_pos[1]))
        self.field = field
        self.image, self.rect = self.get_img_rect()
        self.rect.center = util.game2cscreen(g_pos)
        self.curdst = None
        self.cursrc = None

    @classmethod
    def get_img_rect(cls):
        if cls.img is None:
            cls.img, cls.img_rect = util.load_image(cls.resource_name)
        return cls.img, cls.img_rect

    def update(self, ticks):
        g_pos = Vec(int(self.g_pos[0]), int(self.g_pos[1]))
        cur_cell = self.field._get_cell(g_pos)
        if self.curdst is None:
            if cur_cell.is_exit:
                self.finish()
                return
            dst = self.field.get_next_pos(g_pos)
            self.curdst = Vec(dst)
            self.cursrc = Vec(g_pos)
        dstvec = self.curdst - self.g_pos
        g_dpos = self.curdst - self.cursrc
        g_dpos /= abs(g_dpos)
        g_dpos *= ticks * self.speed / float(TICK_PER_SEC)
        if abs(g_dpos) >= abs(dstvec):
            g_dpos = dstvec
            self.curdst = None
        self.g_pos += g_dpos
        self.rect.center = util.game2cscreen(self.g_pos)

    def finish(self):
        pass
