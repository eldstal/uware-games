#!/usr/bin/env python3

import math
import pyglet

from physics import Entity

class Player(Entity):
  def __init__(self, sprite):
    self.sprite = sprite

    Entity.__init__(self, 0, 0, sprite.width, sprite.height, "Player")

    #
    # Instantaneous state
    #
    self.vx_target = 0    # When accelerating, this is the target velocity

    self.jumping = False
    self.jump_strength = 0


    #
    # Static parameters (tuning the player's movement)
    #

    self.ay = -2.5        # Gravity
    self.vy_max_fall = -10 # Terminal velocity
    self.ax_move = 8      # Run acceleration
    self.ax_stop = 3      # Ground friction
    self.ax_move_air = 4  # Air control
    self.ax_stop_air = 1  # Stopping ability in air

    self.vx_max = 6
    self.vy_jump = 12
    self.jump_strength_max = 10   # Frames/ticks of jump push


  def _clamp(self, v, mn,mx):
    v = max(v, mn)
    v = min(v, mx)
    return v

  def _jump(self):

    # Bumped your head
    if (self.bump_up):
      self.jump_strength = 0

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
      self.vy = max(self.vy, self.vy_max_fall)

    self._jump()
    self._move()
    self._bump()

    self.x += self.vx
    self.y += self.vy


  def draw(self, window):
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
      pass
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

