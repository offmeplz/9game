#!/usr/bin/env python
#vim:fileencoding=utf-8

from itertools import count
from gameobjects import Creep, Wall, SimpleTower, LaserTower

# Set map
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
        dict(creeps=((i * 2, Creep(health=5, speed=2)) for i in count())),
        ]

# Availible towers.
TOWERS = [
        Wall,
        SimpleTower,
        LaserTower,
        ]

INIT_MONEY = 50
LIVES = 20
SELL_FACTOR = 0.6
