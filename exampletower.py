#!/usr/bin/env python
#vim:fileencoding=utf-8

from gameobjects import *

class ExampleTower(GameObject, Tower):
    resource_name = 'exampletower.png'

    # can be changed
    damage = 5
    radius = 15
    cost = 5
    recharge_time = 2
    bullet_speed = 5

    # do not change
    size = 2

    def __init__(self, g_lefttop, world):
        GameObject.__init__(self)
        self.rect.topleft = util.game2tlscreen(g_lefttop)
        self.g_pos = Vec(util.screen2fgame(self.rect.center))
        self.creeps = world.creeps
        self.missles = world.missles
        self.current_recharge = 0
        self.recharge_ticks = self.recharge_time * TICK_PER_SEC

    def update(self, ticks):
        self.current_recharge -= ticks
        if self.current_recharge > 0:
            return

        creep = self._find_target()
        if creep:
            missle = SimpleBullet(
                    self.g_pos, creep, self.damage, self.bullet_speed)
            self.missles.add(missle)
            self.current_recharge = self.recharge_ticks
    
    def _find_target(self):
        for creep in self.creeps:
            distvec = creep.g_pos - self.g_pos
            if abs(distvec) <= self.radius:
                return creep
        return None
