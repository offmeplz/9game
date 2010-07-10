#!/usr/bin/env python
#vim:fileencoding=utf-8

import pygame

from cfg import *

from util import Vec

class PanelHolder(object):
    def __init__(self, surface, rect):
        self.rect = rect
        self.surface = surface.subsurface(rect)
        self.subpanels = []

    def addsubpanel(self, subpanel, rect):
        self.subpanels.append((rect, subpanel))

    def onclick(self, pos, button):
        for rect, subpanel in self.subpanels:
            if rect.collidepoint(pos):
                pos = Vec(pos) - Vec(rect.topleft)
                subpanel.onclick(pos, button)

    def onrelease(self, pos, button):
        for rect, subpanel in self.subpanels:
            if rect.collidepoint(pos):
                pos = Vec(pos) - Vec(rect.topleft)
                subpanel.onrelease(pos, button)

    def redraw(self, rect=None):
        for r, subpanel in self.subpanels:
            if rect is None:
                subpanel.redraw()
            elif rect.collide(r):
                subpanel.redraw(rect.clip(r))


class MenuButton(object):
    def __init__(self, surface, rect):
        self.surface = surface.subsurface(rect)
        self.rect = rect.copy()

        # creating text
        fontpath = pygame.font.match_font('arial')
        font = pygame.font.Font(fontpath, FONT_SIZE)
        self.text = font.render('Menu', True, (0,0,0))
        self.clicking = False

    def redraw(self, rect=None):
        draw_rect = self.text.get_rect().copy()
        draw_rect.center = self.rect.center
        if self.clicking:
            self.surface.fill((100,100,100))
        else:
            self.surface.fill((200,200,200))
        self.surface.blit(self.text, draw_rect.topleft)

    def onclick(self, pos, button):
        self.clicking = True
        self.redraw()

    def onrelease(self, pos, button):
        self.clicking = False
        self.redraw()
