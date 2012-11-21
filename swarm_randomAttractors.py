# Adapted from boids implementation by Stephen Chappell
# Accessed on 11/20/2012 at http://code.activestate.com/recipes/502240/
# Which was in turn motivated by the following pseudocode:
# http://www.vergenet.net/~conrad/boids/pseudocode.html

# This code is a swarm (no velocity matching) with randomly initialized
# attractors.

import random           # FOR RANDOM BEGINNINGS
from Tkinter import *   # ALL VISUAL EQUIPMENT

WIDTH = 1000            # OF SCREEN IN PIXELS
HEIGHT = 500            # OF SCREEN IN PIXELS
BOIDS = 1 + 6 + 12      # IN SIMULATION
ATTRACTORS = 3          # IN SIMULATION
ATTRACTION = 5          # ATTRACTOR INFLUENCE
WALL = 100              # FROM SIDE IN PIXELS
WALL_FORCE = 30         # ACCELERATION PER MOVE
SPEED_LIMIT = 800       # FOR BOID VELOCITY
BOID_RADIUS = 3         # FOR BOIDS IN PIXELS
ATTRACTOR_RADIUS = 3         # FOR BOIDS IN PIXELS
OFFSET_START = 20       # FROM WALL IN PIXELS
FRAMES_PER_SEC = 40     # SCREEN UPDATE RATE
WINDOWED = True         # MOVABLE PROGRAM
DIMENSIONS = 3          # MULTIDIMENSIONAL SWARM SPACE

################################################################################

def main():
    # Start the program.
    initialise()
    mainloop()

def initialise():
    # Setup simulation variables.
    build_boids()
    build_attractors()
    build_graph()

def build_graph():
    # Build GUI environment.
    global graph
    root = Tk()
    if WINDOWED:
        root.resizable(False, False)
        root.title('Boids')
    else:
        root.overrideredirect(True)
    x = (root.winfo_screenwidth() - WIDTH) / 2
    y = (root.winfo_screenheight() - HEIGHT) / 2
    root.geometry('%dx%d+%d+%d' % (WIDTH, HEIGHT, x, y))
    root.bind_all('<Escape>', lambda event: event.widget.quit())
    graph = Canvas(root, width=WIDTH, height=HEIGHT, background='white')
    graph.after(1000 / FRAMES_PER_SEC, update)
    graph.pack()

def update():
    # Main simulation loop.
    graph.after(1000 / FRAMES_PER_SEC, update)
    draw()
    move()

def draw():
    # Draw all boids and attractors.
    graph.delete(ALL)
    for boid in boids:
        x1 = boid.position.x - BOID_RADIUS
        y1 = boid.position.y - BOID_RADIUS
        x2 = boid.position.x + BOID_RADIUS
        y2 = boid.position.y + BOID_RADIUS
        graph.create_oval((x1, y1, x2, y2), fill='red')
    for attractor in attractors:
        x1 = attractor.position.x - ATTRACTOR_RADIUS
        y1 = attractor.position.y - ATTRACTOR_RADIUS
        x2 = attractor.position.x + ATTRACTOR_RADIUS
        y2 = attractor.position.y + ATTRACTOR_RADIUS
        graph.create_oval((x1, y1, x2, y2), fill='blue')
    graph.update()

def move():
    # Move all boids.
    for boid in boids:
        simulate_wall(boid)
        boid.update_velocity(boids)
        boid.move()

def simulate_wall(boid):
    # Create viewing boundaries.
    if boid.position.x < WALL:
        boid.velocity.x += WALL_FORCE
    elif boid.position.x > WIDTH - WALL:
        boid.velocity.x -= WALL_FORCE
    if boid.position.y < WALL:
        boid.velocity.y += WALL_FORCE
    elif boid.position.y > HEIGHT - WALL:
        boid.velocity.y -= WALL_FORCE

def limit_speed(boid):
    # Limit boid speed.
    if boid.velocity.mag() > SPEED_LIMIT:
        boid.velocity /= boid.velocity.mag() / SPEED_LIMIT

def build_boids():
    # Create boids variable.
    global boids
    boids = tuple(Boid(WIDTH, HEIGHT, OFFSET_START, FRAMES_PER_SEC) for boid in xrange(BOIDS))

def build_attractors():
    # Create boids variable.
    global attractors
    attractors = tuple(Attractor(ATTRACTION) for attractor in xrange(ATTRACTORS))

################################################################################

# TWO DIMENTIONAL VECTOR CLASS

class TwoD:

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        return 'TwoD(%s, %s)' % (self.x, self.y)

    def __add__(self, other):
        return TwoD(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return TwoD(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return TwoD(self.x * other, self.y * other)

    def __div__(self, other):
        return TwoD(self.x / other, self.y / other)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        return self

    def __idiv__(self, other):
        self.x /= other
        self.y /= other
        return self

    def mag(self):
        return ((self.x ** 2) + (self.y ** 2)) ** 0.5


################################################################################
# TODO TODO TODO
# MULTIDIMENTIONAL VECTOR CLASS

class TwoD:

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        return 'TwoD(%s, %s)' % (self.x, self.y)

    def __add__(self, other):
        return TwoD(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return TwoD(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return TwoD(self.x * other, self.y * other)

    def __div__(self, other):
        return TwoD(self.x / other, self.y / other)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        return self

    def __idiv__(self, other):
        self.x /= other
        self.y /= other
        return self

    def mag(self):
        return ((self.x ** 2) + (self.y ** 2)) ** 0.5



################################################################################

# BOID RULE IMPLEMENTATION CLASS

class Boid:

    def __init__(self, width, height, offset, move_divider):
        self.velocity = TwoD(0, 0)
        self.position = TwoD(*self.random_start(width, height, offset))
        self.move_divider = move_divider * 5

    def random_start(self, width, height, offset):
        if random.randint(0, 1):
            # along left and right
            y = random.randint(1, height)
            if random.randint(0, 1):
                # along left
                x = -offset
            else:
                # along right
                x = width + offset
        else:
            # along top and bottom
            x = random.randint(1, width)
            if random.randint(0, 1):
                # along top
                y = -offset
            else:
                # along bottom
                y = height + offset
        return x, y


    def update_velocity(self, boids):
        v1 = self.rule1(boids)
        v2 = self.rule2(boids)
        #v3 = self.rule3(boids)     #uncomment for schooling/vel matching
        #self.__temp = v1 + v2 + v3 #uncomment for schooling/vel matching
        v4 = self.rule4(attractors)
        self.__temp = v1 + v2 + v4

    def move(self):
        self.velocity += self.__temp
        limit_speed(self)
        self.position += self.velocity / self.move_divider

    def rule1(self, boids):
        # clumping
        vector = TwoD(0, 0)
        for boid in boids:
            if boid is not self:
                vector += boid.position
        vector /= len(boids) - 1
        return (vector - self.position) / 7.5

    def rule2(self, boids):
        # avoidance
        vector = TwoD(0, 0)
        for boid in boids:
            if boid is not self:
                if (self.position - boid.position).mag() < 30:
                    vector -= (boid.position - self.position)
        return vector * 1.5

    #NOTE: WE DON'T IMPOSE VELOCITY MATCHING
    #    def rule3(self, boids):
    #        # schooling
    #        vector = TwoD(0, 0)
    #        for boid in boids:
    #            if boid is not self:
    #                vector += boid.velocity
    #        vector /= len(boids) - 1
    #        return (vector - self.velocity) / 8

    def rule4(self, attractors):
        # attractors
        vector = TwoD(0, 0)
        for attractor in attractors:
            if (self.position - attractor.position).mag() < 30:
              vector += (attractor.position - self.position) * attractor.attraction
        return vector

################################################################################

# ATTRACTOR CLASS

class Attractor:

    def __init__(self, attract):
        self.position = TwoD(*self.random_start())
        self.attraction = attract

    def random_start(self):
        x = random.randint(1, WIDTH)
        y = random.randint(1, HEIGHT)
        return x, y


################################################################################

# Execute the simulation.
if __name__ == '__main__':
    main()
