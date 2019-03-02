from pyglet.gl import *


class Entity:
  def __init__(self, x, y, width, height, name="Entity"):

    #
    # Instantaneous state
    #

    self.x = x
    self.y = y
    self.vx = 0
    self.vy = 0
    self.width = width
    self.height = height

    self.bump_up    = False
    self.bump_down  = False
    self.bump_left  = False
    self.bump_right = False

    self.name = name

  @property
  def right(self):
    return self.x + self.width

  @property
  def top(self):
    return self.y + self.height


  # Set the bumps of either entity if the two collide.
  # self should be the moving entity and ent a static one, ideally.
  # If snap is set, keeps the objects apart.
  # Returns True if there is any collision
  def collide(self, ent, snap=False):
    overlap_v = (
                 (ent.y  <= self.y <= ent.top) or
                 (self.y <= ent.y  <= self.top)
                )
    overlap_h = (
                 (ent.x  <= self.x <= ent.right) or
                 (self.x <= ent.x  <= self.right)
                )

    collision = False

    if overlap_h:
      # Check for up or down bump
      top = ent.y <= self.top <= ent.top
      bottom = ent.y <= self.y <= ent.top

      move_top = self.vy > 0 or ent.vy < 0
      #move_bottom = self.vy < 0 or ent.vy > 0

      if (move_top and top and not bottom):
        #print("{} U to {}".format(self.name, ent.name))
        self.bump_up = True
        ent.bump_down = True
        if (snap): self.y = ent.y-self.height
        collision = True

      if (bottom and not top):
        #print("{} D to {} at {}".format(self.name, ent.name, self.y))
        self.bump_down = True
        ent.bump_up = True
        if (snap): self.y = ent.top
        collision = True

    if (collision): return collision

    if overlap_v:
      left  = ent.x <= self.x <= ent.right
      right = ent.x <= self.right <= ent.right

      move_right = self.vx > 0 or ent.vx < 0
      move_left = self.vx < 0 or ent.vx > 0

      # Check for left or right bump
      if (move_left and left and not right):
        #print("{} L to {} at {}".format(self.name, ent.name, self.x))
        self.bump_left = True
        ent.bump_right = True
        if (snap): self.x = ent.right
        collision = True

      if (move_right and right and not left):
        #print("{} R to {}".format(self.name, ent.name))
        self.bump_right = True
        ent.bump_left = True
        if (snap): self.x = ent.x-self.width
        collision = True


    return collision

  def draw(self, window):
    print("Entity not being drawn...")


class ColoredBlock(Entity):
  def __init__(self, x, y, width, height, color, name="Block"):
    Entity.__init__(self, x, y, width, height, name)

    self.color = color
    self.points = ( x, y,
                    self.right, y,
                    self.right, self.top,
                    x, self.top
                  )

  def draw(self, window):
    pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                        ('v2f', self.points))
