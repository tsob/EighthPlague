// a simple FM synth

(
SynthDef(\simpFM,
{ | outbus=0, freq=200, modfreq=290, modamp=0.5, amp=0.3, dur=0.5, pan=0 |
  var sig, mod, env, atk, dec, sus, rel;
  atk = dur*0.01;
  dec = dur*0.5;
  sus = dur*0.02;
  rel = dur*0.47;
  mod = SinOsc.ar(modfreq, 0, 0.5);
  sig = SinOsc.ar(freq + (freq * mod), 0, 1.0);
  env = Env([0, 1, 0.6, 0.4, 0]*amp, [atk, dec, sus, rel], curve: \squared);
  Out.ar(outbus,Pan2.ar(sig * EnvGen.kr(env, doneAction: 2),pan));
}).add;
)
