#!/usr/bin/env python3

from PIL import Image
import pyglet
import json
import math
from threading import Lock

# Our own little support library
from platforming import Player
from shaded_sprite import ColoredCox

from pyglet.gl import *

import input_mapper


class PlayerController:

  def __init__(self, p1):
    self.p1 = p1

  def on_input(self, controller, event, value):
    if controller == "controller1":
      self.move_player(self.p1, event, value)
    elif controller == "controller2":
      #self.move_player(self.p2, event, value)
      pass
    else:
      if (event == "quit"):
        pyglet.app.exit()
      return


  def move_player(self, player, event, value):
    # Map dpad to the same thing as the analog axis
    if (event == "dpad-left"):
      event = "axis-X1"
      value = -1 * value

    if (event == "dpad-right"):
      event = "axis-X1"
      value = 1 * value

    if (event == "axis-X1"):
      # Dead zone
      if (-0.1 <= value <= 0.1): value = 0
      player.move(value)

    if (event == "button-A"):
      player.jump(value == 1)



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
