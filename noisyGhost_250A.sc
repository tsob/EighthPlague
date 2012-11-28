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
~scale = Scale.chromatic;
~minFreq = 10;  // in midi notes
~maxFreq = 120; // in midi notes
~minAmp = 0;
~maxAmp = 0.5;
~minDur = 0.1;
~maxDur = 3.0;
~minPan = -1.0;
~maxPan = 1.0;
~rangeFreq = ~maxFreq - ~minFreq;
~rangeAmp = ~maxAmp - ~minAmp;
~rangeDur = ~maxDur - ~minDur;
~rangePan = ~maxPan - ~minPan;
n = NetAddr("127.0.0.1", 57120); // local machine
OSCdef.newMatching(\incoming, {|msg, time, addr, recvPort| \matching.postln}, '/swarmNote', n); // path matching
a = OSCdef(\incomingNotePrint,
      {|msg, time, addr, recvPort|
      time.postln;   // post time
      msg.do({arg i; i.postln}); // post each part of the msg
      ~freq = ((~rangeFreq * msg[1]) + ~minFreq).round;
      ~amp = ((~rangeAmp * msg[2]) + ~minAmp);
      ~dur = ((~rangeDur * msg[3]) + ~minDur);
      ~pan = ((~rangePan * msg[4]) + ~minPan);
      ~degree = (~freq % 12) + (7 * ((~freq / 12).round - 6) );

      //FM
      Pbind(
        \instrument,  \simpFM,
        \freq,        Pseq([~freq.midicps],1),
        \amp,         ~amp,
        \dur,         ~dur,
        \pan,         ~pan
      ).play;

      Pbind(
        \instrument,  \envio,
        //\freq,        Pseq([~freq.midicps],1),
        \degree,      Pseq([~degree],1),
        \scale,       Pfunc({ ~scale }, inf),
        \amp,         ~amp,
        \dur,         ~dur,
        \pan,         ~pan
      ).play;


      //drums
      Pbind(
        \instrument,  \natalQuinto,
        //\freq,       Pseq([msg[1].midicps.round],1),
        #[\bufnum, \sampdur],
                      Prand(Array.fill(~paths.size, { arg i; [b[i],b[i].duration] } ), 2.rand),
        \amp,         ~amp*4,
        \dur,         Prand([0.1,0.2,0.5,1], inf),
        \pan,         ([-1,-0.5,0,0.5,1] * ~pan).min(1).max(-1).choose //random panning
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
// register to receive messages from jar
//---------------------------------------------------------
// port 7000
// /piezo float
// /accel float float float
// jerk
( 
~jarlist = (
  \piezo: List(),
  \accx: List(),
  \accy: List(),
  \accz: List(),
  \jerk: List()
);
~numvals = 200;     //will hold the last 2 seconds at 10ms/msg 
var started=false; 
~piezo = OSCdef(\newPiezoMsg,
      {|msg, time, addr, recvPort|		
	      if(started,{	
          ~jarlist[\piezo].addFirst(msg[1]);
        	//remove oldest val if over size ~numvals
        	if(~jarlist[\piezo].size>~numvals,
        	    { ~jarlist[\piezo].pop; }
        	); 
	
      	},{started = true;}); 
      },
      '/piezo', nil);
~acc = OSCdef(\newAccMsg,
      {|msg, time, addr, recvPort|		
	      if(started,{	
          ~jarlist[\accx].addFirst(msg[1]);
          ~jarlist[\accy].addFirst(msg[2]);
          ~jarlist[\accz].addFirst(msg[3]);
        	//remove oldest val if over size ~numvals
        	if(~jarlist[\accx].size>~numvals,
        	    { ~jarlist[\accx].pop;
          	    ~jarlist[\accy].pop;
          	    ~jarlist[\accz].pop; }
        	); 
      	},{started = true;}); 
      },
      '/accel', nil);
~jerk = OSCdef(\newJerkMsg,
      {|msg, time, addr, recvPort|		
      	m = NetAddr("127.0.0.1", 9000); // python
      	//set attractor position
        m.sendMsg("/attr",
              //freq,
              (~jarlist[\piezo]).max(0).min(1), //amp
              (~jarlist[\accx]).max(0).min(1), //dur
              (~jarlist[\accx]).max(0).min(1), //mod freq
              (~jarlist[\accy]).max(0).min(1), //dur
              (~jarlist[\accz]).max(0).min(1), //ioi
        );
      },
      'jerk', nil);
)
//---------------------------------------------------------
// register to receive note message from scsynth server
//---------------------------------------------------------
// Send tracked notes to python script to modify attractors
//---------------------------------------------------------
( 
n = NetAddr("127.0.0.1", 57120); // local machine
OSCdef.newMatching(\incoming, {|msg, time, addr, recvPort| \matching.postln}, '/swarmNote', n); // path matching
var lasttime, started=false; 
var maxlength=50.0;
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
          m.sendMsg("/attr",
                ((msg[4].cpsmidi - ~minFreq) / ~rangeFreq).max(0).min(1),
                ((msg[3] - ~minAmp) / ~rangeAmp).max(0).min(1),
                (time - lasttime).min(~maxDur)/~maxDur,
                ((msg[4].cpsmidi*[0.5,1.0,1.2,1.4,1.5,1.6,1.8,2.0].choose - ~minFreq) / ~rangeFreq).max(0).min(1), // mod freq
                1.0.rand, //random panning
                (time - lasttime).min(~maxDur)/~maxDur, //ioi
          );
	
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


