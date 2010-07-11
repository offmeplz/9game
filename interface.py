#!/usr/bin/env python
#vim:fileencoding=utf-8

import pygame

from cfg import *

from util import Vec

font = None

def get_font():
    global font
    if font is None:
        fontpath = pygame.font.match_font(FONT_FAMILY, bold=True)
        font = pygame.font.Font(fontpath, FONT_SIZE)
    return font

class PanelHolder(object):
    def __init__(self, surface, rect):
        self.rect = rect
        self.surface = surface.subsurface(rect)
        self.subpanels = []

    def addsubpanel(self, subpanel, rect):
        self.subpanels.append((rect, subpanel))

    def removepanel(self, panel):
        idx = None
        for i, item in enumerate(self.subpanels):
            if panel == item[1]:
                idx = i
                break
        if i is None:
            raise ValueError, "Can't find such panel"
        self.subpanels[i] = self.subpanels[-1]
        self.subpanels.pop()

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

class TowerButton(object):
    def __init__(self, surface, img, pushfunc):
        self.surface = surface
        self.image = img
        self.selected = False
        self.pushfunc = pushfunc

    def redraw(self, rect=None):
        if self.selected:
            color = (200,200,200)
        else:
            color = (255,255,255)

        self.surface.fill(color)
        self.surface.blit(self.image, (0,0))

    def onclick(self, pos, button):
        self.pushfunc()

    def onrelease(self, pos, button):
        pass

    def update(self):
        pass

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


class Slot(object):
    def __init__(self, surface):
        self.surface = surface
        self.set_panel(None)
    
    def onclick(self, pos, button):
        if self.panel is not None:
            return self.panel.onclick(pos, button)

    def onrelease(self, pos, button):
        if self.panel is not None:
            return self.panel.onrelease(pos, button)

    def update(self):
        if self.panel is not None:
            return self.panel.update()

    def set_panel(self, panel):
        self.panel = panel
        self.update()
        self.redraw()

    def redraw(self, rect=None):
        if self.panel is not None:
            return self.panel.redraw(rect)
        else:
            self.surface.fill((200,200,200))


class TowerInfo(object):
    def __init__(self, surface, tower):
        self.surface = surface
        self.tower = tower
        self.info = None
        self.font = get_font()

    def onclick(self, pos, button):
        pass

    def onrelease(self, pos, button):
        pass

    def redraw(self, rect=None):
        if self.info is not None:
            self.surface.fill((200,200,200))
            name, damage, radius = self.info
            name_surface = self.font.render(name, True, (0,0,0))
            damage_text = 'damage: %d' % damage
            damage_surface = self.font.render(damage_text, True, (0,0,0))
            radius_text = 'radius: %d' % radius
            radius_surface = self.font.render(radius_text, True, (0,0,0))
            self.surface.blit(name_surface, (0,0))
            self.surface.blit(damage_surface, (0,20))
            self.surface.blit(radius_surface, (0,40))

    def update(self, rect=None):
        info = (self.tower.__class__.__name__,
                self.tower.damage, self.tower.radius)
        if self.info != info:
            self.info = info
            self.redraw()

class CreepInfo(object):
    def __init__(self, surface, creep):
        self.surface = surface
        self.creep = creep
        self.info = None
        self.font = get_font()

    def onclick(self, pos, button):
        pass

    def onrelease(self, pos, button):
        pass

    def redraw(self, rect=None):
        if self.info is not None:
            self.surface.fill((200,200,200))
            name, health, maxhealth = self.info
            name_surface = self.font.render(name, True, (0,0,0))
            health_text = 'health: %d/%d' % (health, maxhealth)
            health_surface = self.font.render(health_text, True, (0,0,0))
            self.surface.blit(name_surface, (0,0))
            self.surface.blit(health_surface, (0,20))

    def update(self, rect=None):
        info = (self.creep.__class__.__name__,
                self.creep.health, self.creep.maxhealth)
        if self.info != info:
            self.info = info
            self.redraw()

class TextInfo(object):
    def __init__(self, surface, rect, textgetter, picture=None):
        self.surface = surface.subsurface(rect)
        self.rect = rect.copy()
        self.curtext = None
        self.font = get_font()
        self.textgetter = textgetter
        self.picture = picture

    def onclick(self, pos, button):
        pass

    def onrelease(self, pos, button):
        pass

    def redraw(self, rect=None):
        self.surface.fill((200,200,200))
        if self.picture is not None:
            self.surface.blit(self.picture, (0,0))
        if self.curtext is not None:
            textsurface = self.font.render(self.curtext, True, (0,0,0))
            draw_rect = textsurface.get_rect().copy()
            draw_rect.center = self.surface.get_rect().center
            self.surface.blit(textsurface, draw_rect.topleft)

    def update(self):
        curtext = self.textgetter()
        if curtext != self.curtext:
            self.curtext = curtext
            self.redraw()
