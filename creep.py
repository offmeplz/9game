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

    @classmethod
    def get_img_rect(cls):
        if cls.img is None:
            cls.img, cls.img_rect = util.load_image(cls.resource_name)
        return cls.img, cls.img_rect

    def update(self, ticks):
        g_pos = Vec(int(self.g_pos[0]), int(self.g_pos[1]))
        cur_cell = self.field._get_cell(g_pos)
        if cur_cell.is_exit:
            self.finish()
        else:
            g_next_pos = self.field.get_next_pos(g_pos)
            g_next_pos = Vec(g_next_pos)
            g_dpos = g_next_pos - g_pos
            g_dpos *= ticks * self.speed / float(TICK_PER_SEC)
            self.g_pos += g_dpos
            self.rect.center = util.game2cscreen(self.g_pos)

    def finish(self):
        pass
