#!/usr/bin/env python3

from PIL import Image
import pyglet
from pyglet.gl import *

# Return a pyglet image with just the plain color
def pil_to_pyglet(pil_image):
  w,h = pil_image.size
  return pyglet.image.ImageData(w, h, 'RGBA', pil_image.tobytes(), pitch=-4*w)

# Generate a single texture which is the sprite with
# the correct background color.
# bg_color is the base color of the clothes
# bg_mask is the shape of the clothes (for example)
# fg_sprite is anything to draw on top of the clothes
def shaded_sprite(fg_sprite, bg_mask, bg_color):
  sprite = Image.new('RGBA', fg_sprite.size)

  # A plain color sheet
  colored_bg = Image.new('RGBA', fg_sprite.size, color=bg_color)

  # Cut the color sheet to the right shape
  sprite = Image.composite(colored_bg, sprite, bg_mask)

  # Add the foreground on top of the sheet
  sprite = Image.alpha_composite(sprite, fg_sprite)
  return pil_to_pyglet(sprite)


class ColoredCox:
  def __init__(self, color, x=20, y=20):
    sprite_normal = Image.open("sprites/player_fg_normal.png")
    mask_normal = Image.open("sprites/player_bg_normal.png")

    self.tex = shaded_sprite(sprite_normal, mask_normal, color)

    self.x = x
    self.y = y

    self.w = self.tex.width
    self.h = self.tex.width

  def draw(self, window):
    # Enable alpha, so transparent sprites work
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    self.tex.blit(self.x, self.y)



window = pyglet.window.Window()

player_1 = ColoredCox((0xce, 0x39, 0x10, 255), 20, 20)
player_2 = ColoredCox((0xef, 0xef, 0x32, 255), 50, 20)

@window.event
def on_draw():
  window.clear()

  player_1.draw(window)
  player_2.draw(window)

pyglet.app.run()
