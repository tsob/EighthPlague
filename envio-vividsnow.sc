//«envio» by vividsnow
//http://sccode.org/1-4Qw


( // synth
SynthDef(\envio, {| out=0, freq=80, dur=1, atk=0.1, amp=0.8, curve= #[2,-3], blend=0.1, from=1, to=0, rot=0, rot_freq=0.5 |
	var ha = Harmonics((3,5..13).choose.debug('sub freq size'));
	var i = 6.exprand(26).asInteger.debug('oscillators');
	var sig = Pan2.ar(
		EnvGen.ar(
			Env(
				[0] ++ SinOsc.kr(
					NamedControl.kr(\in_freq, Array.exprand(i-2,0.1,10)),
					NamedControl.kr(\in_phase, Array.rand(i-2,0,pi)),
					NamedControl.kr(\in_mul, Array.rand(i-2,0,1)),
					NamedControl.kr(\in_add, 0!(i-2)),
				) ++ [0],
				NamedControl.kr(\in_step, Array.exprand(i-1, 0.1,1.0).normalizeSum),
				\sin
			).circle,
			timeScale: freq.reciprocal
			* NamedControl.kr(\sub_freq, ha.formant(ha.size - 1 / 2, ha.size).pow(1.exprand(2))).reciprocal,
			levelScale: AmpCompA.kr(NamedControl.kr(\sub_freq) * freq)
			* NamedControl.kr(\sub_amp, ha.formant(ha.size - 1 / 2, ha.size).pow(1.0.exprand(3)).normalizeSum) // * Line.kr()
		),
		NamedControl.kr(\sub_pan, Array.interpolation(ha.size,-1,1))
		* Line.kr(from,to,dur)
	).sum * EnvGen.kr(Env.perc(atk, dur-atk, amp, curve).blend(Env.sine(dur), blend), doneAction:2);
	sig = Rotate2.ar(sig[0],sig[1],rot*LFSaw.kr(rot_freq));
	Out.ar(out, LPF.ar(HPF.ar(sig,20),2e4));
}).add.play
)
