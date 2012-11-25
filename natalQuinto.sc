// All SuperCollider code by Tim O'Brien.
// We use Natal Quinto percussion sample pack
// by ramjac ( http://www.freesound.org/people/ramjac/ )
// You can find this pack online at: http://www.freesound.org/people/ramjac/packs/1302/
// Available under CC Attribution license
// http://creativecommons.org/licenses/by/3.0/

//NOTE: Change ~paths to point to the right directory on your machine!
//      Requires absolute path.

//instantiate buffers, read in samples, and create synthdef
(
~paths = "/home/tim/EighthPlague/1302__ramjac__natal-quinto/*.aif".pathMatch;
b = Array.newClear(~paths.size); //init buffers for samples
for(0, ~paths.size-1,
   {arg i; b[i] = Buffer.read(s,PathName(~paths[i]).asAbsolutePath);}
);

SynthDef(\natalQuinto, { arg out = 0, bufnum, sampdur, amp=1, pan=0;
    var env;
    env = EnvGen.kr(Env.linen(sampdur*0.001,sampdur*0.9,sampdur*0.0999,amp),doneAction: 2);
    Out.ar( out,
        Pan2.ar( env * PlayBuf.ar(1, bufnum, BufRateScale.kr(bufnum)), pan)
    )
}).add;
)

// to create an array of the sample buffers:
// Array.fill(~paths.size, { arg i; b[i] } )

// play a random rhythm
(
Pbind(
  \instrument, \natalQuinto,
  #[\bufnum, \sampdur],
      Pxrand(Array.fill(~paths.size, { arg i; [b[i],b[i].duration] } ), 50),
  \dur, Prand([0.075,0.1,0.1,0.1,0.2,0.2,0.2,0.166667,0.333333,0.5,1], inf),
  \pan, Prand([-1,-0.5,0,0.5,1], inf),
  \amp, Prand([0.7,1.2], inf)
).play;
)
s.meter

// free buffers when done
b.free;


s.queryAllNodes
s.freeAll

