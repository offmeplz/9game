#!/usr/bin/env python
#vim:fileencoding=utf-8

import itertools
import math
import os
import pygame

from pygame import Rect

from cfg import *

def load_image(name):
    '''Return: image, image rectangle pair.'''
    fullpath = os.path.join(RESOURCE_PATH, name)
    image = pygame.image.load(fullpath)
    if image.get_alpha() is None:
        image = image.convert()
    else:
        image = image.convert_alpha()
    return image, image.get_rect()

def screen2game(screen_pos):
    s_x, s_y = screen_pos
    g_x, g_y = s_x / GAME_CELL_SIZE, s_y / GAME_CELL_SIZE
    return g_x, g_y

def screen2fgame(screen_pos):
    s_x, s_y = screen_pos
    g_x, g_y = s_x / float(GAME_CELL_SIZE), s_y / float(GAME_CELL_SIZE)
    return g_x, g_y

def game2screen(game_pos):
    g_x, g_y = game_pos
    s_x, s_y = g_x * GAME_CELL_SIZE, g_y * GAME_CELL_SIZE
    return int(s_x), int(s_y)

game2tlscreen = game2screen

def game2cscreen(game_pos):
    screen = game2screen(game_pos)
    return (int(screen[0] + GAME_CELL_SIZE / 2),
            int(screen[1] + GAME_CELL_SIZE / 2))

def game2screencellrect(g_rect):
    s_rect = g_rect.copy()
    s_rect.top *= GAME_CELL_SIZE
    s_rect.left *= GAME_CELL_SIZE
    s_rect.width *= GAME_CELL_SIZE
    s_rect.heght *= GAME_CELL_SIZE
    return s_rect

def screen2gamecellrect(s_rect):
    if s_rect.top % GAME_CELL_SIZE or \
       s_rect.left % GAME_CELL_SIZE or \
       s_rect.width % GAME_CELL_SIZE or \
       s_rect.height % GAME_CELL_SIZE:
           raise ValueError, "Rect %s is not cellrect" % s_rect

    g_rect = s_rect.copy()
    g_rect.top /= GAME_CELL_SIZE
    g_rect.left /= GAME_CELL_SIZE
    g_rect.width /= GAME_CELL_SIZE
    g_rect.heght /= GAME_CELL_SIZE
    return g_rect

def addvec(pos1, pos2):
    return pos1[0] + pos2[0], pos1[1] + pos2[1]
 
def mulvec(pos, x):
    return pos[0] * x, pos[1] * x

def divvec(pos, x):
    return pos[0] / x, pos[1] / x

def signum(num):
    if num > 0:
        return 1
    elif num < 0:
        return -1
    else:
        return 0


def collideline(rect, line):
    """
    Check if line collide rectangle.

    rect - Rect object.
    line - a pair of points.
    """
    p1, p2 = line
    if p1 == p2:
        return rect.collidepoint(p1)

    # Check if rect with (p1,p2) as diagonal collides rect.
    linerect = Rect(
            (min(p1[0], p2[0]), min(p1[1], p2[1])),
            (abs(p1[0] - p2[0]), abs(p1[1] - p2[1])))
    if not rect.colliderect(linerect):
        return False

    # Check if both half planes (formed by line) have at least one rect corner.
    sides = [False, False]
    for p in (rect.topleft, rect.topright, rect.bottomleft, rect.bottomright):
        v = (p2[0] - p1[0]) * (p[1] - p1[1]) - (p2[1] - p1[1]) * (p[0] - p1[0])
        if v >= 0:
            sides[0] = True
        if v <= 0:
            sides[1] = True

    return sides[0] and sides[1]


def anycollideline(rects, line):
    '''
    Check if any of rectangles collides line.

    rects - iterable of Rect.
    line - a pair of points.
    '''
    p1, p2 = line
    if p1 == p2:
        return any(r.collidepoint(p1) for r in rects)

    linerect = Rect(
            (min(p1[0], p2[0]), min(p1[1], p2[1])),
            (abs(p1[0] - p2[0]), abs(p1[1] - p2[1])))

    for rect in rects:
        if rect.colliderect(linerect):
            sides = [False, False]
            for p in (rect.topleft, rect.topright, rect.bottomleft, rect.bottomright):
                v = (p2[0] - p1[0]) * (p[1] - p1[1]) - (p2[1] - p1[1]) * (p[0] - p1[0])
                if v >= 0:
                    sides[0] = True
                if v <= 0:
                    sides[1] = True
            if sides[0] and sides[1]:
                return True
    return False


def is_walkable(begin, end, radius, sprites):
    if begin == end:
        raise ValueError, 'begin and end are the same'
    begin = Vec(begin)
    end = Vec(end)
    linevec = end - begin
    shift = linevec.perpendicular()
    shift *= radius / abs(shift)
    line1 = (begin + shift, end + shift)
    if anycollideline((s.rect for s in sprites), line1):
        return False
    line2 = (begin - shift, end - shift)
    if anycollideline((s.rect for s in sprites), line2):
        return False
    return True

def placeintsegment(approxcenter, size):
    size = int(size)
    if size % 2 == 0:
        return int(round(approxcenter)) - size / 2
    else:
        return int(approxcenter) - size / 2

def placeintrect(approxcenter, sizes):
    xcorner = placeintsegment(approxcenter[0], sizes[0])
    ycorner = placeintsegment(approxcenter[1], sizes[1])
    return (xcorner, ycorner)

def iterpoints(x, y=None):
    if y == None:
        rect = x
        return itertools.product(
                xrange(rect.left, rect.left + rect.width + 1),
                xrange(rect.top, rect.top + rect.height + 1))
    else:
        return itertools.product(
                xrange(x[0], x[0] + y[0]), xrange(x[1], x[1] + y[1]))

class Vec(object):
    __slots__ = ['x', 'y']
    def __init__(self, x, y=None):
        if y is None:
            if isinstance(x, Vec):
                self.x = x.x
                self.y = x.y
            else:
                self.x, self.y = x
        else:
            self.x, self.y = x, y

    def __add__(self, other):
        return Vec(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vec(self.x - other.x, self.y - other.y)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        return self

    def __mul__(self, a):
        return Vec(self.x * a, self.y * a)

    def __imul__(self, a):
        self.x *= a
        self.y *= a
        return self

    def __div__(self, a):
        return Vec(self.x / a, self.y / a)

    def __idiv__(self, a):
        self.x /= a
        self.y /= a
        return self

    def __neg__(self):
        return Vec(-self.x, -self.y)

    def __len__(self):
        return 2

    def __iter__(self):
        return iter((self.x, self.y))

    def __getitem__(self, i):
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        else:
            raise IndexError, "Index is out of range."

    def __setitem__(self, i, x):
        if i == 0:
            self.x = x
        elif i == 1:
            self.y = x
        else:
            raise IndexError, "Index is out of range."

    def __str__(self):
        return "Vec(%s,%s)" % (str(self.x), str(self.y))
    
    def __repr__(self):
        return str(self)

    def __abs__(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def __eq__(self, other):
        if hasattr(other, '__getitem__') and len(other) == 2:
            return self.x == other[0] and self.y == other[1]
        else:
            return False

    def __ne__(self, other):
        return not self == other

    def perpendicular(self):
        return Vec(self.y, -self.x)
