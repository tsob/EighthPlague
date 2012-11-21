# Adapted from boids implementation by Stephen Chappell
# Accessed on 11/20/2012 at http://code.activestate.com/recipes/502240/
# Which was in turn motivated by the following pseudocode:
# http://www.vergenet.net/~conrad/boids/pseudocode.html

# This code is a swarm (no velocity matching) with randomly initialized
# attractors.

# NOTE: Use OSC to set a random attactor position
# In Supercollider, execute this code, for example:
# m = NetAddr("127.0.0.1", 9000); // python address
# m.sendMsg("/attr",300,300); //attractor position

import random           # FOR RANDOM BEGINNINGS
from Tkinter import *   # ALL VISUAL EQUIPMENT
import socket, OSC      # OSC COMMUNICATION
import time, threading

WIDTH = 1000            # OF SCREEN IN PIXELS
HEIGHT = 500            # OF SCREEN IN PIXELS
BOIDS = 1 + 6 + 12      # IN SIMULATION
ATTRACTORS = 4          # IN SIMULATION
ATTRACTION = 5          # ATTRACTOR INFLUENCE
WALL = 100              # FROM SIDE IN PIXELS
WALL_FORCE = 30         # ACCELERATION PER MOVE
SPEED_LIMIT = 1000       # FOR BOID VELOCITY
BOID_RADIUS = 3         # FOR BOIDS IN PIXELS
ATTRACTOR_RADIUS = 3         # FOR BOIDS IN PIXELS
OFFSET_START = 20       # FROM WALL IN PIXELS
FRAMES_PER_SEC = 40     # SCREEN UPDATE RATE
WINDOWED = True         # MOVABLE PROGRAM
DIMENSIONS = 3          # MULTIDIMENSIONAL SWARM SPACE

################################################################################

RECEIVE_ADDRESS = ('127.0.0.1', 9000) # tupple with ip, port.
SEND_ADDRESS = ('127.0.0.1', 57120)

# OSC Server. there are three different types of server.
s = OSC.OSCServer(RECEIVE_ADDRESS) # basic
##s = OSC.ThreadingOSCServer(receive_address) # threading
##s = OSC.ForkingOSCServer(receive_address) # forking

# this registers a 'default' handler (for unmatched messages),
# an /'error' handler, an '/info' handler.
# And, if the client supports it, a '/subscribe' & '/unsubscribe' handler
s.addDefaultHandlers()

# define a message-handler function for the server to call.
def attractor_handler(addr, tags, stuff, source):
    print "---"
    print "received new osc msg from %s" % OSC.getUrlStr(source)
    print "with addr : %s" % addr
    print "typetags %s" % tags
    attractor = random.choice(attractors) #modify a random attractor
    for item in stuff:
      print "data %d" % item
    (attractor.position.x, attractor.position.y) = stuff
    print "---"

s.addMsgHandler("/attr", attractor_handler) # adding our function

def startOSC():
  # Start OSCServer
  print "\nStarting OSCServer.\n"
  global st
  st = threading.Thread( target = s.serve_forever )
  st.start()

def quit_handler():
  # close OSC server
  print "Closing OSCServer."
  s.close()
  print "Waiting for Server-thread to finish."
  st.join() ##!!!
  print "Done."
  graph.quit()

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
    startOSC()

def build_graph():
    # Build GUI environment.
    global graph
    root = Tk()
    if WINDOWED:
        root.resizable(False, False)
        root.title('Swarm')
    else:
        root.overrideredirect(True)
    x = (root.winfo_screenwidth() - WIDTH) / 2
    y = (root.winfo_screenheight() - HEIGHT) / 2
    root.geometry('%dx%d+%d+%d' % (WIDTH, HEIGHT, x, y))
    root.protocol("WM_DELETE_WINDOW", quit_handler)
    #root.bind_all('<Escape>', lambda event: event.widget.quit())
    graph = Canvas(root, width=WIDTH, height=HEIGHT, background='black')
    graph.after(1000 / FRAMES_PER_SEC, update)
    graph.pack()

def update():
    # Main simulation loop.
    #graph.after(1000 / FRAMES_PER_SEC, update)
    graph.after(500 / FRAMES_PER_SEC, update)
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
        graph.create_oval((x1, y1, x2, y2), fill='white')
    for attractor in attractors:
        x1 = attractor.position.x - ATTRACTOR_RADIUS
        y1 = attractor.position.y - ATTRACTOR_RADIUS
        x2 = attractor.position.x + ATTRACTOR_RADIUS
        y2 = attractor.position.y + ATTRACTOR_RADIUS
        graph.create_oval((x1, y1, x2, y2), fill='red')
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
# PROBABLY USE NUMPY


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

    #NOTE: NO rule3 BECAUSE WE DON'T IMPOSE VELOCITY MATCHING/SCHOOLING

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

    #TODO
    #def update(self):



################################################################################

# OSC STUFF



################################################################################

# Execute the simulation.
if __name__ == '__main__':
    main()
