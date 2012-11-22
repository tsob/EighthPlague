// @author Tim O'Brien
// @name noisyGhost.sc
// @desc Note event transcription and pattern-based resynthesis.
// @note Adapted from Nick Collins' Machine Listening Chapter in the SuperCollider book.
// @note See also «envio» synth by vividsnow, http://sccode.org/1-4Qw

//------------------------------------------------------
// Set up machine listening on server
//------------------------------------------------------
(

s.waitForBoot({

b = Buffer.alloc(s, 512); //buffer for FFT

SynthDef(\pitchandonsets, //this SynthDef makes no sound, just analyzes input
{
	var in, amp, freq, hasFreq, chain, onsets, trigger, trigval;
	
	in = SoundIn.ar(0);
	amp = Amplitude.kr(in);
	# freq, hasFreq = Pitch.kr(in, maxFreq: 1000); 
		
	chain = FFT(b, in);
	
	// - move the mouse left/right to change the threshold:
	onsets = Onsets.kr(chain, MouseX.kr(0,1), \complex);
	
  // send amplitude and freq
	trigval = [ RunningSum.kr(amp,512)*(s.options.blockSize/512),
	            freq,
	            hasFreq ];

	trigger = SendReply.kr(onsets,'/newNote',trigval);

//  SendReply.kr((hasFreq == 0)&&(2.rand),'/playNotes',\go);

}).add;
});
)

//------------------------------------------------------
// For debugging
//------------------------------------------------------
(
//test out receiving the OSC note messages 
n = NetAddr("127.0.0.1", 57120); // local machine
OSCdef.newMatching(\incoming, {|msg, time, addr, recvPort| \matching.postln}, '/swarmNote', n); // path matching
c = OSCdef(\incomingNotePrint,
      {|msg, time, addr, recvPort|
      time.postln;   // time
      msg[0].postln; // /swarmNote
      msg[1].postln; // freq (Hz)
      msg[2].postln; // amp (between 0 and 1)
      msg[3].postln; // dur (ms)
    //msg[4].postln; // not used yet
    //msg[5].postln; // not used yet
      },
      '/swarmNote',nil);
)
c.free
(
//test out note tracking      
b = OSCdef(\newNoteMsg,
      {|msg, time, addr, recvPort|
      time.postln;   // time
      msg[0].postln; // /newNote
      msg[1].postln; // 1000
      msg[2].postln; // -1
      msg[3].postln; // 
      msg[4].postln; // 
      msg[5].postln; // 
      },
      '/newNote');
)
b.free

OSCFunc.trace(true); // Turn posting on
OSCFunc.trace(false); // Turn posting off
SwingOSC.quitAll
//------------------------------------------------------
(
z = Synth(\default,[freq: 440, amp: 0]);
//Receiving output notes from swarm via OSC 
n = NetAddr("127.0.0.1", 57120); // local machine
OSCdef.newMatching(\incoming, {|msg, time, addr, recvPort| \matching.postln}, '/swarmNote', n); // path matching
a = OSCdef(\incomingNotePrint,
      {|msg, time, addr, recvPort|
      time.postln;   // time
      msg[0].postln; // /swarmNote
      msg[1].postln; // freq (Hz)
      msg[2].postln; // amp (between 0 and 1)
      msg[3].postln; // dur (ms)
    //msg[4].postln; // not used yet
    //msg[5].postln; // not used yet
      z.set(
        \freq, msg[1],
        \amp, msg[2],
        \dur, msg[3]/1000,
        \pan, [-1,-0.5,0,0.5,1].choose //random panning
      );
      },
      '/swarmNote',nil);
)
a.free



//------------------------------------------------------
// register to receive note message from scsynth server
//------------------------------------------------------
( 
var lasttime, started=false; 
var maxlength=1.0;
~notelist = (
  \dur: List(),
  \freq: List(),
  \amp: List()
);
~numnotes = 10;     //will hold the last 10 notes 
a = OSCdef(\newNoteMsg,
      {|msg, time, addr, recvPort|
        var newnote, midinote;
		
	      if(started,{	

          ~notelist[\dur].addFirst((time - lasttime).min(maxlength));

          ~notelist[\freq].addFirst(msg[4]);
          midinote = msg[4].cpsmidi.round.midicps; //round to midi notes
          //~notelist[\freq].addFirst(midinote); 

          ~notelist[\amp].addFirst(msg[3]);

          //...

	
        	//remove oldest note if over size ~numnotes
        	if(~notelist[\dur].size>~numnotes,
        	    { ~notelist[\dur].pop;
          	    ~notelist[\freq].pop;
          	    ~notelist[\amp].pop; }
        	); 
	
      	},{started = true;}); 
	
      	//reset lists for collection
      	lasttime = time;
      },
      '/newNote', s.addr);
   
x = Synth(\pitchandonsets); 
)

s.meter;

//------------------------------------------------------
// Send tracked notes to python script to modify attractors
//------------------------------------------------------


// note yet sending tracked notes, but can change the freq/amp position
// of a random attractor
m = NetAddr("127.0.0.1", 9000); // python
m.sendMsg("/attr",100,100); //attractor position


//------------------------------------------------------
// Play tracked notes as patterns
//------------------------------------------------------

(
q = Pbind(
  \instrument, \default,
  \freq, Pseq(~notelist[\freq].reverse),
  \dur, Pseq(~notelist[\dur].reverse),
  \amp, Pseq(~notelist[\amp].reverse),
  \pan, Prand([-1,-0.5,0,0.5,1],10) //random panning
);
q.play;
)

(  // scrambled notes
q = Pbind(
  \instrument, \default,
  \freq, Pseq(~notelist[\freq].scramble),
  \dur, Pseq(~notelist[\dur].scramble),
  \amp, Pseq(~notelist[\amp].scramble),
  \pan, Prand([-1,-0.5,0,0.5,1],10) //random panning
);
q.play;
)


(  // play back stuttered notes
q = Pbind(
  \instrument, \default,
  \freq, Pseq(~notelist[\freq].stutter),
  \dur, Pseq(~notelist[\dur].stutter),
  \amp, Pseq(~notelist[\amp].stutter),
  \pan, Pseq([-1,1],inf) //panning l-r for stutter
);
q.play;
)


(  // play back scrambled and stuttered notes
q = Pbind(
  \instrument, \default,
  \freq, Pseq(~notelist[\freq].scramble.stutter),
  \dur, Pseq(~notelist[\dur].scramble.stutter),
  \amp, Pseq(~notelist[\amp].scramble.stutter),
  \pan, Prand([-1,-0.5,0,0.5,1],inf) //random panning
);
q.play;
)


(  // play back mirrored notes (3x) (reverses to beginning once it gets to the end)
q = Pbind(
  \instrument, \default,
  \freq, Pseq(~notelist[\freq].mirror1, 3),
  \dur, Pseq(~notelist[\dur].mirror1, inf),
  \amp, Pseq(~notelist[\amp].mirror1, inf),
  \pan, Pseq([-1,-0.75,-0.5,-0.25,0,0.25,0.5,0.75,1].mirror,inf) //random panning
);
q.play;
)





//------------------------------------------------
// Using the envio instrument
// see ~/Projects/SuperCollider/envio-vividsnow.sc
//------------------------------------------------

(  // play back the buffer of notes
q = Pbind(
  \instrument, \envio,
  \freq, Pseq(~notelist[\freq].reverse),
  \dur, Pseq(~notelist[\dur].reverse),
  \amp, Pseq(~notelist[\amp].reverse),
);
q.play;
)


(  // play back stuttered notes
q = Pbind(
  \instrument, \envio,
  \freq, Pseq(~notelist[\freq].stutter),
  \dur, Pseq(~notelist[\dur].stutter),
  \amp, Pseq(~notelist[\amp].stutter),
  \pan, Pseq([-1,1],inf) //panning l-r for stutter
);
q.play;
)


(  // play back scrambled and stuttered notes
q = Pbind(
  \instrument, \envio,
  \freq, Pseq(~notelist[\freq].scramble.stutter),
  \dur, Pseq(~notelist[\dur].scramble.stutter),
  \amp, Pseq(~notelist[\amp].scramble.stutter),
  \pan, Prand([-1,-0.5,0,0.5,1],inf) //random panning
);
q.play;
)


(  // play back mirrored notes (3x) (reverses to beginning once it gets to the end)
q = Pbind(
  \instrument, \envio,
  \freq, Pseq(~notelist[\freq].mirror1, 3),
  \dur, Pseq(~notelist[\dur].mirror1, inf),
  \amp, Pseq(~notelist[\amp].mirror1, inf),
  \pan, Pseq([-1,-0.75,-0.5,-0.25,0,0.25,0.5,0.75,1].mirror,inf) //random panning
);
q.play;
)




//in progress----------------
(
b = OSCdef(\playNoteMsg,
      {|msg, time, addr, recvPort|
      q = Pbind(
        \instrument, \default,
        \freq, Pseq(~notelist[\freq].reverse),
        \dur, Pseq(~notelist[\dur].reverse),
        \amp, Pseq(~notelist[\amp].reverse)
      );
      q.play;
      },
      '/playNotes', s.addr);
)



// Free transcription variables
(
  a.remove; //Free the OSCresponder
  x.free; // Free the synth
  b.free; // Free the buffer
)


