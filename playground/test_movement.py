#!/usr/bin/env python3

from PIL import Image
import pyglet
import json
import math
from threading import Lock

# Our own little support library
from platforming import Player, PlayerController
from shaded_sprite import ColoredCox

from pyglet.gl import *

import input_mapper


window = pyglet.window.Window()

p1_sprite = ColoredCox((0xce, 0x39, 0x10, 255))
player1 = Player(p1_sprite)

player1.x = 20
player1.y = 20

@window.event
def on_draw():
  window.clear()
  player1.draw(window)


def tick(dt):
  player1.tick(dt)

  collide_world(player1)

def collide_world(actor):

  actor.bump_up = False
  actor.bump_down = False
  actor.bump_left = False
  actor.bump_right = False

  # Ground
  if (actor.y <= 20):
    actor.y = 20
    actor.bump_down = True
  else:
    actor.bump_down = False

  # Walls
  if (actor.x <= 0):
    actor.x = 0
    actor.bump_left = True

  if (actor.x + actor.width >= window.width):
    actor.x = window.width - actor.width
    actor.bump_right = True


controller = PlayerController(player1)
controls = json.loads(open("../game_config.json").read())
input_mapper.setup(controller, controls)

input_mapper.start()


# 60FPS animations
pyglet.clock.schedule_interval(tick, 1/60)

pyglet.app.run()

input_mapper.stop()
input_mapper.shutdown()
