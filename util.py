#!/usr/bin/env python
#vim:fileencoding=utf-8

import pygame
import os

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

def game2screen(game_pos):
    g_x, g_y = game_pos
    s_x, s_y = g_x * GAME_CELL_SIZE, g_y * GAME_CELL_SIZE
    return s_x, s_y

def addvec(pos1, pos2):
    return pos1[0] + pos2[0], pos1[1] + pos2[1]

def mulvec(pos, x):
    return pos[0] * x, pos[1] * x

def divvec(pos, x):
    return pos[0] / x, pos[1] / x
