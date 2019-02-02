from PIL import Image
import pyglet
from pyglet.gl import *

# Return a pyglet image with just the plain color
def _pil_to_pyglet(pil_image):
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
  return _pil_to_pyglet(sprite)


# Provide PIL image
class ColoredSprite:
  def __init__(self, sprite_normal, mask_normal, color):
    self.tex = shaded_sprite(sprite_normal, mask_normal, color)

    self.width = self.tex.width
    self.height = self.tex.width

  def draw(self, window, x, y):
    # Enable alpha, so transparent sprites work
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    self.tex.blit(x, y)


class ColoredCox(ColoredSprite):
  def __init__(self, color):
    sprite_normal = Image.open("sprites/player_fg_normal.png")
    mask_normal = Image.open("sprites/player_bg_normal.png")
    ColoredSprite.__init__(self,
                           sprite_normal,
                           mask_normal,
                           color)

