// @author Tim O'Brien
// @name noisyGhost.sc
// @desc Note event transcription and swarm-based resynthesis.
// @note Adapted from Nick Collins' Machine Listening Chapter in the SuperCollider book.
// @note See also «envio» synth by vividsnow, http://sccode.org/1-4Qw

//------------------------------------------------------
// 1. Set up machine listening on server ---------------
(
s.waitForBoot({

b = Buffer.alloc(s, 512); //buffer for FFT

//this SynthDef makes no sound, just analyzes input
SynthDef(\pitchandonsets,
{
	var in, amp, freq, hasFreq, chain, onsets, trigger, trigval;
	in = SoundIn.ar(0);
	amp = Amplitude.kr(in);
	# freq, hasFreq = Pitch.kr(in, maxFreq: 1000); 
		
	chain = FFT(b, in);
	
	// move the mouse left/right to change the threshold:
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
// 2. Start to receive notes from python swarm
//------------------------------------------------------
(
//z = Synth(\default,[freq: 440, amp: 0]);

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
    
    
//      z.set(
//        \freq, msg[1].midicps.round,
//        \amp, msg[2],
//        \dur, msg[3]/1000,
//        \pan, [-1,-0.5,0,0.5,1].choose //random panning
//      );
      
      Pbind(
        \instrument,  \envio,
        \freq,        Pseq([msg[1].midicps.round],1),
        \amp,         msg[2],
        \dur,         msg[3]/50,
        \pan,         [-1,-0.5,0,0.5,1].choose //random panning
      ).play;
      
      
      },
      '/swarmNote',nil);
)
a.free

//------------------------------------------------------
// For debugging
//------------------------------------------------------
s.meter;
OSCFunc.trace(true); // Turn posting on
OSCFunc.trace(false); // Turn posting off
SwingOSC.quitAll

//---------------------------------------------------------
// register to receive note message from scsynth server
//---------------------------------------------------------
// Send tracked notes to python script to modify attractors
//---------------------------------------------------------
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

        	//remove oldest note if over size ~numnotes
        	if(~notelist[\dur].size>~numnotes,
        	    { ~notelist[\dur].pop;
          	    ~notelist[\freq].pop;
          	    ~notelist[\amp].pop; }
        	); 
        	
        	m = NetAddr("127.0.0.1", 9000); // python
        	//set attractor position
          m.sendMsg("/attr",msg[4].cpsmidi,msg[3],(time - lasttime).min(maxlength)*1000);
	
      	},{started = true;}); 
	
      	//reset lists for collection
      	lasttime = time;
      },
      '/newNote', s.addr);

x = Synth(\pitchandonsets); 
)


//------------------------------------------------------
// Free variables
(
  a.remove; //Free the OSCresponder
  x.free; // Free the synth
  b.free; // Free the buffer
)


