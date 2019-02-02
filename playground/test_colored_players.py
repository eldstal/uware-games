#!/usr/bin/env python3

from PIL import Image
import pyglet
from pyglet.gl import *
from shaded_sprite import ColoredCox



window = pyglet.window.Window()

player_1 = ColoredCox((0xce, 0x39, 0x10, 255))
player_2 = ColoredCox((0xef, 0xef, 0x32, 255))

@window.event
def on_draw():
  window.clear()

  player_1.draw(window, 20, 20)
  player_2.draw(window, 50, 20)

pyglet.app.run()
