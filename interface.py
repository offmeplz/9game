#!/usr/bin/env python
#vim:fileencoding=utf-8

import pygame

from cfg import *

from util import Vec

font = None

def get_font():
    global font
    if font is None:
        fontpath = pygame.font.match_font('arial')
        font = pygame.font.Font(fontpath, FONT_SIZE)
    return font

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

    def update(self):
        for r, subpanel in self.subpanels:
            subpanel.update()


class MenuButton(object):
    def __init__(self, surface, rect):
        self.surface = surface.subsurface(rect)
        self.rect = rect.copy()

        # creating text
        font = get_font()
        self.text = font.render('Menu', True, (0,0,0))
        self.clicking = False

    def redraw(self, rect=None):
        draw_rect = self.text.get_rect().copy()
        draw_rect.center = self.surface.get_rect().center
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

    def update(self):
        pass


class MoneyInfo(object):
    def __init__(self, surface, rect, moneygetter):
        self.surface = surface.subsurface(rect)
        self.rect = rect.copy()
        self.curmoney = None
        self.font = get_font()
        self.moneygetter = moneygetter

    def onclick(self, pos, button):
        pass

    def onrelease(self, pos, button):
        pass

    def redraw(self, rect=None):
        self.surface.fill((200,200,200))
        if self.curmoney is not None:
            text = '%d$' % int(self.curmoney)
            textsurface = self.font.render(text, True, (0,0,0))
            draw_rect = textsurface.get_rect().copy()
            draw_rect.center = self.surface.get_rect().center
            self.surface.blit(textsurface, draw_rect.topleft)

    def update(self):
        money = self.moneygetter()
        if money != self.curmoney:
            self.curmoney = money
            self.redraw()
