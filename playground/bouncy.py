#!/usr/bin/env python3

import pyglet
from pyglet.gl import *
import random

def clamp(a, lower, upper):
  if (a > upper): return upper
  if (a < lower): return lower
  return a

class Cox:
  def __init__(self, x=20, y=20):
    self.sprite_normal = pyglet.resource.image("sprites/player_normal.png")
    self.sprite_ouch = pyglet.resource.image("sprites/player_ouch.png")

    self.x = x
    self.y = y
    self.vx = random.randrange(-500, 500)
    self.vy = random.randrange(-500, 500)

    self.w = self.sprite_normal.width
    self.h = self.sprite_normal.width

    self.ouch_ticks = 20
    self.ticks_since_bounce = 0

    self.time = 0

  def draw(self, window):
    sprite = self.sprite_normal
    if self.ticks_since_bounce <= self.ouch_ticks:
      sprite = self.sprite_ouch

    # Enable alpha, so transparent sprites work
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    sprite.blit(self.x, self.y)


  def tick(self, window, dt):
    dx = self.vx * dt
    dy = self.vy * dt

    self.x += dx
    self.y += dy

    bx = clamp(self.x, 0, window.width - self.w)
    if self.x != bx:
      self.x = bx
      self.vx *= -1
      self.ticks_since_bounce = 0

    by = clamp(self.y, 0, window.height - self.h)
    if self.y != by:
      self.y = by
      self.vy *= -1
      self.ticks_since_bounce = 0

    self.ticks_since_bounce += 1



window = pyglet.window.Window()

n_coxes = 40
coxes = []
for c in range(n_coxes):
  coxes += [Cox(
               x=random.randrange(32, window.height-32),
               y=random.randrange(32, window.height-32)
              )]

@window.event
def on_draw():
  window.clear()

  for p in coxes:
    p.draw(window)


def tick(dt):
  for p in coxes:
    p.tick(window, dt)


# 60FPS animations
pyglet.clock.schedule_interval(tick, 1/60)


pyglet.app.run()
