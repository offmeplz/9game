#!/usr/bin/env python
#vim:fileencoding=utf-8

from itertools import count
from gameobjects import Creep, Wall, SimpleTower, LightningTower

# Set map (Unsupported for now)
# > -- enter
# ^ -- exit
# X -- obstacle
# . -- empty cell

MAP = """
>....................^
>....................^
>....................^
>....................^
>....................^
>....................^
>....................^
>....................^
>....................^
>....................^
>....................^
"""

# Image that will be used for background.
BACKGROUND = None

# Waves of creeps.
CREEP_WAVES = [
        # (StartTime, WaveDescription)

        # 10 creeps, spawn each 2 seconds.
        (0, dict(creeps=((i * 2, Creep(health=5, speed=2)) for i in xrange(10)))),
        # infinite number of creeps, spawn each second.
        (20, dict(creeps=((i, Creep(health=10, speed=1.5, money=2)) for i in count()))),
        ]


# Balance tower parameters
Wall.cost = 2

SimpleTower.cost = 5
SimpleTower.damage = 1
SimpleTower.radius = 4
SimpleTower.recharge_time = 2
SimpleTower.bullet_speed = 5

LightningTower.cost = 10
LightningTower.damage = 3
LightningTower.radius = 3
LightningTower.recharge_time = 3
LightningTower.fire_cost = 1

# Availible towers.
TOWERS = [
        Wall,
        SimpleTower,
        LightningTower,
        ]

INIT_MONEY = 50
LIVES = 20
SELL_FACTOR = 0.6
