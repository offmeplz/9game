#!/usr/bin/env python
#vim:fileencoding=utf-8

import math
import os
import pygame

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

def game2cscreen(game_pos):
    screen = game2screen(game_pos)
    return (int(screen[0] + GAME_CELL_SIZE / 2),
            int(screen[1] + GAME_CELL_SIZE / 2))

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
    rect should be Rect object.
    line should be a pair of points.
    """
    p1, p2 = line
    if p1 == p2:
        return rect.collidepoint(p1)

    # Check if rect with (p1,p2) as diagonal collides rect.
    linerect = Rect(
            (min(p1[0], p2[0]), min(p1[1], p2[1])),
            (abs(p1[0] - p2[0]), abs(p1[1] - p2[1])))
    if not rect.collide(linerect):
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


class Vec(object):
    def __init__(self, x, y=None):
        if y is None:
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
