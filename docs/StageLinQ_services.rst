StageLinQ Services
******************
StageLinQ supports many different services, but since the standard isn't open I cannot tell if these are standardized
Denon DJ specific. Here follows a short description of the services supported by PyStageLinQ.

Depending on your needs you may need one or several of the services in parallel.

State Map
~~~~~~~~~
State map is a way to read out the status of the device. It can be things like positions of the faders and knobs,
The name and artist of the current track loaded, or the current BPM of a deck playing.

It is limited in that it does not provide any information that can be used to track the playback of a deck.
This includes things like current time, time until end etc.

The service itself works by PyStageLinQ sending which parameters it wants to be sent.
The StageLinQ device that receives this request will then send out the current value of these parameters.
The StageLinQ device will then continue to send update if the parameter changes,
e.g. a new track is loaded or a knob is turned.

The parameters that can be read out are highly depending on the device,
and at least so far I have not found a way to make a StageLinQ device output all available parameters.

Beat Info
~~~~~~~~~
As opposed to State Map, Beat Info seems to be intended to be used for high accuracy work.
It has supplies information like where in the track a deck is currently playing, as well as the length of the track.

This can then in turn be used to synch things to the music, allowing VJs to sync stage lightning etc to the beat!

The PyStageLinQ implementation of Beat Info also has a bit of more work to do to make it more user friendly
