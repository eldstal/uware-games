#!/usr/bin/env python3

from PIL import Image
import pyglet
import json
import math

from threading import Lock

# Our own little support library
from platforming import Player,PlayerController
from shaded_sprite import ColoredCox
from physics import ColoredBlock

from pyglet.gl import *

import input_mapper


def tick(dt):
  player1.tick(dt)

  collide_world(player1, world)

def make_world(window):
  world = [ ]
  # Floor
  world += [ ColoredBlock(-32, -32, window.width+64, 40, None, "Floor") ]
  world += [ ColoredBlock(-32, -32, 40, window.height+64, None, "LeftWall") ]
  world += [ ColoredBlock(window.width-8, -32, 48, window.height+64, None, "RightWall") ]
  world += [ ColoredBlock(-32, window.height-8, window.width+64, 40, None, "RightWall") ]
  return world

def collide_world(actor, world):
  actor.bump_up = False
  actor.bump_down = False
  actor.bump_left = False
  actor.bump_right = False

  for ent in world:
    actor.collide(ent, True)


window = pyglet.window.Window()

@window.event
def on_draw():
  window.clear()
  for ent in world:
    ent.draw(window)
  player1.draw(window)


p1_sprite = ColoredCox((0xce, 0x39, 0x10, 255))
player1 = Player(p1_sprite)

player1.x = 20
player1.y = 300

world = make_world(window)

controller = PlayerController(player1)
controls = json.loads(open("../game_config.json").read())
input_mapper.setup(controller, controls)

input_mapper.start()


# 60FPS animations
pyglet.clock.schedule_interval(tick, 1/60)

pyglet.app.run()

input_mapper.stop()
input_mapper.shutdown()
