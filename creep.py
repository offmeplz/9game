#!/usr/bin/env python
#vim:fileencoding=utf-8

import pygame

import util

from cfg import *

class Creep(pygame.sprite.Sprite):
    img, img_rect = None, None
    resource_name = 'creep.png'
    speed = 0.5
    
    def __init__(self, s_pos, field):
        pygame.sprite.Sprite.__init__(self)
        self.s_pos = s_pos
        self.field = field
        self.image, self.rect = self.get_img_rect()
        self.rect.center = s_pos

    @classmethod
    def get_img_rect(cls):
        if cls.img is None:
            cls.img, cls.img_rect = util.load_image(cls.resource_name)
        return cls.img, cls.img_rect

    def update(self, ticks):
        g_pos = util.screen2game(self.s_pos)
        cur_cell = self.field._get_cell(g_pos)
        if cur_cell.is_exit:
            self.finish()
        else:
            g_next_pos = self.field.get_next_pos(g_pos)
            g_dpos = g_next_pos[0] - g_pos[0], g_next_pos[1] - g_pos[1]
            s_dpos = util.game2screen(g_dpos)
            s_dpos = util.divvec(s_dpos, TICK_PER_SEC)
            s_dpos = util.mulvec(s_dpos, ticks * self.speed)
            s_dpos = int(s_dpos[0]), int(s_dpos[1])
            self.s_pos = util.addvec(self.s_pos, s_dpos)
            self.rect.move_ip(s_dpos)

    def finish(self):
        pass
