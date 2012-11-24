EighthPlague
============

An environment for human/computer improvisation.

A SuperCollider synth applies machine learning algorithms to extract frequency, amplitude, and onsets of note events from incoming audio data. It then sends those notes to the Python swarm simulation, which become attractor elements in the multidimensional swarm space (as described in, e.g., Blackwell2004). The swarm algorithm sends note events back to SuperCollider, which sonifies them with a simple FM synth.

Reference:
Blackwell, T., & Young, M. (2004). Self-organised music. Organised Sound, 9(02). doi:10.1017/S1355771804000214
