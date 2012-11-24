# Adapted from boids implementation by Stephen Chappell
# Accessed on 11/20/2012 at http://code.activestate.com/recipes/502240/
# Which was in turn motivated by the following pseudocode:
# http://www.vergenet.net/~conrad/boids/pseudocode.html

# This code is a swarm (no velocity matching) with random attractors.

# NOTE: Use OSC to set a random attactor position
# In Supercollider, execute this code, for example:
# m = NetAddr("127.0.0.1", 9000); // python address
# m.sendMsg("/attr",300,300,...); //attractor position for correct number of dimensions

import random           # FOR RANDOM BEGINNINGS
from Tkinter import *   # ALL VISUAL EQUIPMENT
import socket, OSC      # OSC COMMUNICATION
import time, threading
import math

DIMLIMIT = 700          # LIMIT OF DIMENSION VALUES
WIDTH = DIMLIMIT        # OF SCREEN IN PIXELS
HEIGHT = DIMLIMIT       # OF SCREEN IN PIXELS
BOIDS = 1 + 6 + 12      # IN SIMULATION
BOIDMASS = 2            # IN SIMULATION
BLIMIT = 30             # LIMIT FOR BOID PERCEPTION
ATTRACTORS = 9          # IN SIMULATION
ATTRACTION = 3          # ATTRACTOR INFLUENCE
WALL = 100              # FROM SIDE IN PIXELS
WALL_FORCE = 30         # ACCELERATION PER MOVE
SPEED_LIMIT = 1000      # FOR BOID VELOCITY
BOID_RADIUS = 3         # FOR BOIDS IN PIXELS
ATTRACTOR_RADIUS = 5    # FOR BOIDS IN PIXELS
OFFSET_START = 20       # FROM WALL IN PIXELS
FRAMES_PER_SEC = 40     # SCREEN UPDATE RATE
UPDATE_TIME = 500 / FRAMES_PER_SEC
WINDOWED = True         # MOVABLE PROGRAM
NDIMS = 5               # MULTIDIMENSIONAL SWARM SPACE

# FOR OSC
RECEIVE_ADDRESS = ('127.0.0.1', 9000) # tupple with ip, port.
SEND_ADDRESS = ('127.0.0.1', 57120) # SuperCollider on local machine.

# FOR CREATING/SENDING NOTE EVENTS
MAXFREQ = 90 #MIDI FREQ
MINFREQ = 20
MAXAMP = 0.9
MAXDUR = 100
MINDUR = 10
MAXIOI = 100
MINIOI = 10
FREQSCALER = float(MAXFREQ - MINFREQ) / float(DIMLIMIT)
AMPSCALER = float(MAXAMP) / float(DIMLIMIT)
DURSCALER = float(MAXDUR - MINDUR) / float(DIMLIMIT)
IOISCALER = float(MAXIOI - MINIOI) / float(DIMLIMIT)

################################################################################

def main():
    # Start the program.
    initialise()
    mainloop()

def initialise():
    # Setup simulation variables.
    global sim_time  # discreet simulation time variable
    sim_time = 0     # start at 0
    global note_time # time of next note
    note_time = 0    # start at zero - see makesound()
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
    graph = Canvas(root, width=WIDTH, height=HEIGHT, background='black')
    graph.after(1000 / FRAMES_PER_SEC, update)
    graph.pack()

def update():
    # Main simulation loop.
    graph.after(UPDATE_TIME, update)
    draw()
    move()
    makesound()
    global sim_time #necessary to prevent UnboundLocalError
    sim_time += 1 # iterate discreet time variable
    if not (sim_time % 50): print "%d\n" % (sim_time) #keep track of time
    #if not (sim_time % 500): #randomly move attractors every once in a while
    #    for attractor in attractors:
    #        attractor.rand_update()

def draw():
    # Draw boids and attractors.
    # Shows only first 2 dimensions
    graph.delete(ALL)
    for boid in boids:
        x1 = boid.position.x[0] - BOID_RADIUS
        y1 = boid.position.x[1] - BOID_RADIUS
        x2 = boid.position.x[0] + BOID_RADIUS
        y2 = boid.position.x[1] + BOID_RADIUS
        graph.create_oval((x1, y1, x2, y2), fill='white')
    for attractor in attractors:
        x1 = attractor.position.x[0] - ATTRACTOR_RADIUS
        y1 = attractor.position.x[1] - ATTRACTOR_RADIUS
        x2 = attractor.position.x[0] + ATTRACTOR_RADIUS
        y2 = attractor.position.x[1] + ATTRACTOR_RADIUS
        graph.create_oval((x1, y1, x2, y2), fill='red')
    graph.update()

def move():
    # Move all boids.
    for boid in boids:
        simulate_wall(boid)
        boid.update_velocity(boids)
        boid.move()

#TODO - in progress
def makesound():
    global note_time
    global sim_time
    if not note_time:
        note_time = random.randint(10,100) #time of first note, in sim_time units
    #check to see if it's time to output a note
    if (note_time < sim_time):
        freq = 0
        amp = 0
        dur = 0
        ioi = 0
        # get dimension centroids
        for boid in boids:
            freq += boid.position.x[0]
            amp  += boid.position.x[1]
            dur  += boid.position.x[2]
#            print "ioi component: %d\n" % boid.position.x[3]
            ioi  += boid.position.x[3]
        freq = (freq / len(boids)) * FREQSCALER + MINFREQ
        amp = (amp / len(boids)) * AMPSCALER              #0 IS MIN AMP
        dur = (dur / len(boids)) * DURSCALER + MINDUR
        ioi = (ioi / len(boids)) * IOISCALER + MINIOI
        # send them via osc as a note event
        sendMsg('/swarmNote',[freq,amp,dur]) # send OSC to SuperCollider
        # assign next note time
        note_time = sim_time + ioi
        print "\nCurrent time: %d" % (sim_time)
        print "Freq=%f, amp=%f, dur=%f, IOI=%f" % (freq, amp, dur, ioi)
        print "Next note time: %d\n" % (note_time)
    

def simulate_wall(boid):
    # Create viewing boundaries.
    for dim in range(NDIMS):
        if boid.position.x[dim] < WALL:
            boid.velocity.x[dim] += WALL_FORCE
        elif boid.position.x[dim] > WIDTH - WALL:
            boid.velocity.x[dim] -= WALL_FORCE

def limit_speed(boid):
    # Limit boid speed.
    for dim in range(NDIMS):
        if abs(boid.velocity.x[dim]) > SPEED_LIMIT:
            boid.velocity.x[dim] /= abs(boid.velocity.x[dim]) / SPEED_LIMIT

def build_boids():
    # Create boids variable.
    global boids
    boids = tuple(Boid([DIMLIMIT]*NDIMS, OFFSET_START, FRAMES_PER_SEC) for boid in xrange(BOIDS))

def build_attractors():
    # Create boids variable.
    global attractors
    attractors = tuple(Attractor(ATTRACTION) for attractor in xrange(ATTRACTORS))


################################################################################
# MULTIDIMENTIONAL SPACE

# DIMENSIONS: not all will be used at first...
# Event Parameters:
#   Frequency
#   Amplitude
#   Chord Number
#   Sequence Number
#   Mode
#   Tonic
#   PANNING TODO TODO
# Timing functions:
#   Duration
#   Inter-Onset-Interval (can be different!)

# Note: we'll implement dimensional decoupling!! Makes more sense musically.


class MultiD:

    def __init__(self, x):
        self.x = [float(i) for i in x]

    def __repr__(self):
        return 'MultiD:\n'
        for dim in range(NDIMS):
            return '$s, ' % (self.x[dim])
        return '\n'

    def __add__(self, other):
        return MultiD((self.x[i] + other.x[i]) for i in range(NDIMS))

    def __sub__(self, other):
        return MultiD((self.x[i] - other.x[i]) for i in range(NDIMS))

    def __mul__(self, other):
        return MultiD((self.x[i] * other) for i in range(NDIMS))

    def __div__(self, other):
        return MultiD((self.x[i] / other) for i in range(NDIMS))

    def __iadd__(self, other):
        for dim in range(NDIMS):
            self.x[dim] += other.x[dim]
        return self

    def __isub__(self, other):
        for dim in range(NDIMS):
            self.x[dim] -= other.x[dim]
        return self

    def __idiv__(self, other):
        for dim in range(NDIMS):
            self.x[dim] /= other
        return self

################################################################################
# BOID RULE IMPLEMENTATION CLASS

class Boid:

    def __init__(self, lims, offset, move_divider):
        self.velocity = MultiD([0]*NDIMS)
        self.position = MultiD([0]*NDIMS)
        #random starting position
        for dim in range(NDIMS):
            #random start
            self.position.x[dim] = random.randint(0,DIMLIMIT)
#            if random.randint(0, 1):
#                start less than min val for dim
#                self.position.x[dim] = -offset
#            else:
#                #start greater than max val for dim
#                self.position.x[dim] = lims[dim] + offset
        self.move_divider = move_divider * 5

#    def random_start(self, lims, offset):
#        for dim in range(NDIMS):
#            if random.randint(0, 1):
#                #start less than min val for dim
#                x[dim] = -offset
#            else:
#                #start greater than max val for dim
#                x[dim] = lims[dim] + offset
#        return x

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
        vector = MultiD([0]*NDIMS)
        for boid in boids:
            if boid is not self:
                vector += boid.position
        vector /= len(boids) - 1
        return (vector - self.position) / BOIDMASS

    def rule2(self, boids):
        # avoidance
        vector = MultiD([0]*NDIMS)
        for boid in boids:
            if boid is not self:
                for dim in range(NDIMS):
                    if abs(self.position.x[dim] - boid.position.x[dim]) < BLIMIT:
                        vector.x[dim] -= (boid.position.x[dim] - self.position.x[dim])
        return vector * 1.5

    #NOTE: NO rule3 BECAUSE WE DON'T IMPOSE VELOCITY MATCHING/SCHOOLING

    def rule4(self, attractors):
        # attractors
        vector = MultiD([0]*NDIMS)
        for attractor in attractors:
            for dim in range(NDIMS):
                if abs(self.position.x[dim] - attractor.position.x[dim]) < 30:
                  vector.x[dim] += (attractor.position.x[dim] - self.position.x[dim]) * attractor.attraction
        return vector

################################################################################
# ATTRACTOR CLASS

class Attractor:

    def __init__(self, attract):
        self.position = MultiD([0]*NDIMS)
        for dim in range(NDIMS):
            self.position.x[dim] = random.randint(1, DIMLIMIT)
        self.attraction = attract

    def rand_update(self):
        #self.position = MultiD([0]*NDIMS)
        for dim in range(NDIMS):
            self.position.x[dim] = random.randint(1, DIMLIMIT)


################################################################################
# RECEIVING OSC

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
    global attractors
    attractor = random.choice(attractors) #modify a random attractor
    for item in stuff:
      print "data %f" % item
    #Freq dimension value
    attractor.position.x[0] = int(min(max(stuff[0]-float(MINFREQ),0), MAXFREQ)/float(FREQSCALER))
    print "freq dim val: %d" % (attractor.position.x[0])
    #Amp dimension value
    attractor.position.x[1] = int(min(max(stuff[1],0),MAXAMP)/float(AMPSCALER))
    print "amp dim val: %d" % (attractor.position.x[1])
    #Dur dimension value
    attractor.position.x[2] = int(min(max(stuff[2]-float(MINDUR),0),MAXDUR)/float(DURSCALER))
    print "dur dim val: %d" % (attractor.position.x[2])
    print "---"
s.addMsgHandler("/attr", attractor_handler) # adding our function

# FOR DEBUGGING TODO: remove
def note_handler(addr, tags, stuff, source):
    print "---"
    print "received new osc msg from %s" % OSC.getUrlStr(source)
    print "with addr : %s" % addr
    print "typetags %s" % tags
    for item in stuff:
        print "data %f" % item
    print "---"
s.addMsgHandler("/swarmNote", note_handler) # adding our function


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
# SENDING OSC

client = OSC.OSCClient()
client.connect( SEND_ADDRESS ) # note that the argument is a tupple and not two arguments
#client.connect( RECEIVE_ADDRESS ) # debugging

def sendMsg(addr,val):
    msg = OSC.OSCMessage() #  we reuse the same variable msg used above overwriting it
    msg.setAddress(addr)   # something like "/note"
    msg.append(val)        # the corresponding value
    client.send(msg)       # now we dont need to tell the client the address anymore

################################################################################

# Execute the simulation.
if __name__ == '__main__':
    main()
