#!/usr/bin/env python3

from PIL import Image
import pyglet
import json
import math
from threading import Lock

from pyglet.gl import *

import input_mapper

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
  def __init__(self, color):
    sprite_normal = Image.open("sprites/player_fg_normal.png")
    mask_normal = Image.open("sprites/player_bg_normal.png")

    self.tex = shaded_sprite(sprite_normal, mask_normal, color)

    self.w = self.tex.width
    self.h = self.tex.width

  def draw(self, window, x, y):
    # Enable alpha, so transparent sprites work
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    self.tex.blit(x, y)


class Player:
  def __init__(self, sprite):
    self.sprite = sprite

    #
    # Instantaneous state
    #
    self.x = 0
    self.y = 0

    self.vx = 0
    self.vy = 0

    self.vx_target = 0    # When accelerating, this is the target velocity

    self.bump_up    = False
    self.bump_down  = False
    self.bump_left  = False
    self.bump_right = False

    self.jumping = False
    self.jump_strength = 0


    #
    # Static parameters (tuning the player's movement
    #

    self.ay = -2.5        # Gravity
    self.ax_move = 8    # Run acceleration
    self.ax_stop = 3    # Ground friction
    self.ax_move_air = 4 # Air control
    self.ax_stop_air = 1 # Stopping ability in air

    self.vx_max = 14
    self.vy_jump = 12
    self.jump_strength_max = 10   # Frames/ticks of jump push


  def _clamp(self, v, mn,mx):
    v = max(v, mn)
    v = min(v, mx)
    return v

  def _jump(self):
    # Player has held long enough for a maximum jump
    if (self.jump_strength == 0):
      self.jumping = False

    if (self.jumping):
      self.jump_strength -= 1
      self.vy = self.vy_jump

  def _move(self):
    # Max change in velocity
    dv = self.vx_target - self.vx

    # Directions
    dir_x = math.copysign(1, self.vx)
    dir_target = math.copysign(1, self.vx_target)
    dir_dv = math.copysign(1, dv)

    # Retardation, either due to stopping
    # or turning around
    is_decrease = self.vx != 0 and dir_dv != dir_x

    # The acceleration we apply this tick
    ax = 0

    if is_decrease:
      if self.bump_down:
        # Apply ground friction to slow down
        ax = self.ax_stop
      else:
        ax = self.ax_stop_air

    else:
      if self.bump_down:
        # Accelerate toward target speed
        ax = self.ax_move
      else:
        ax = self.ax_move_air

    # Clamp to prevent overshoot
    ax = dir_dv * min(ax, abs(dv))

    self.vx += ax
    self.vx = self._clamp(self.vx, -self.vx_max, self.vx_max)

  def _collide(self):

    # Ground
    if (self.y <= 20):
      self.bump_down = True
      self.y = 20
    else:
      self.bump_down = False

  def _bump(self):
    if (self.bump_up and self.vy > 0):
      self.vy = 0
    if (self.bump_down and self.vy < 0):
      self.vy = 0
    if (self.bump_left and self.vx < 0):
      self.vx = 0
    if (self.bump_right and self.vx > 0):
      self.vx = 0


  def tick(self, dt):

    # Gravity
    if (not self.bump_down):
      self.vy += self.ay

    self._jump()
    self._move()
    self._collide()
    self._bump()

    self.x += self.vx
    self.y += self.vy


  def draw(self, window):
    self._collide()
    self.sprite.draw(window, self.x, self.y)

  # value is -1 (full left) to 1 (full right)
  # 0 stops.
  def move(self, value):
    target_speed = value * self.vx_max
    self.vx_target = target_speed

  def jump(self, active):
    # Abort a jump early
    if (self.jumping):
      if (not active):
        self.jumping = False
      return

    # Start a new jump
    if (self.bump_down):
      if (active):
        self.jumping = True
        self.jump_strength = self.jump_strength_max

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


controller = PlayerController(player1)
controls = json.loads(open("../game_config.json").read())
input_mapper.setup(controller, controls)

input_mapper.start()


# 60FPS animations
pyglet.clock.schedule_interval(tick, 1/60)

pyglet.app.run()

input_mapper.stop()
input_mapper.shutdown()