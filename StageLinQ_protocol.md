# StageLinQ protocol
StageLinQ is a protocol for sharing information from Denon DJ equipment 
(at least, maybe it is used by other brands too?). 
The protocol us used to share data between a music source, such as a DJ equipment. This data can be used by a light table
to sync the lightshow to the music, or to read out which track is currently loaded on a deck and show this in a live
stream.

## Preface

### Disclaimer
This information has been gathered from a Denon DJ Prime Go using Wireshark.
The information may differ for other equipment that outputs StageLinQ. 
This also means that this text will float between what I have discovered and derived as requirements of the 
protocol.

### Random info I don't really know where to put

For some reason all ASCII is encoded as 16 bytes, so keep this in mind if when reading data. e.g. every other byte
will be 0x00 when text is written. For python encoding "UTF-16be" seems to work

### Nomenclature
In this document the following words are used as this:

*StageLinQ device*: A device that can communicate on StageLinq, e.g. DJ equipment, stage lightning controller, or 
a computer running the software.

*StageLinQ source*: This is used to describe a device that is the source of StageLinQ information,
examples of this could be a Denon DJ Prime Go.

*StageLinQ sink*: This is used to describe the machine that consumes information from a 
StageLinQ source outputs, i.e. a computer running PyStageLinQ. 
This document is written from the angle of a StageLinQ sink trying to get data from a StageLinQ source.
Note that a StageLinQ device can be both a source and sink.

## Ethernet configuration
The StageLinQ device (based on Prime go behaviour) will pick a random IP in the range 169.254.0.0/16.
You will need to set up your computer to use the same IP range. 
When developing I used the IP 169.254.13.37/16 which seems to work without any issue.

It is very possible that the StageLinQ device can be assigned an IP by DHCP, but I 
have not tested this.



## Device discovery
A StageLinQ device shall send out a discovery frame periodically. 
This frame is used to announce that the StageLinQ device is available and to which port to send a request for services
to.
This frame is a broadcast sent to 255.255.255.255 to UDP port 51337, meaning that any StageLinQ device on the 
network can see which other StageLinQ devices are available.
The source port of this frame seems to be randomized, so any free port could possibly 
be used.
Both StageLinQ sources and StageLinQ sinks need send this frame, even if they do not offer any services.

The StageLinQ Discovery frame is formatted as follows:

| Name                    | Length (bytes)     | Purpose                                           |
|-------------------------|--------------------|---------------------------------------------------|
| Magic flag              | 4                  | Determine if frame is discovery frame: "airD"     |
| Token                   | 16                 | See "Token" section                               |
| Device name length      | 4                  | Length of the device name (uint32)                |
| Device name             | Device name length | UTF16 encoded Device name                         |
| Connection type length  | 4                  | Length of the Connection type(uint32)             |
| Connection type         | Device name length | UTF16 encoded Connection type                     |
| Software name length    | 4                  | Length of the Software name (uint32)              |
| Software name           | Device name length | UTF16 encoded Software name                       |
| Software version length | 4                  | Length of the Software version (uint32)           |
| Software version        | Device name length | UTF16 encoded Software version                    |
| Service request port    | 2                  | Port where a StageLinQ device offers its services |

The connection type has two valid values, one for when the StageLinQ device announcement, i.e. that the StageLinQ device
ready to receive service requests, and one for when a device is disconnecting from the network. The following table have
the values for these two cases:

| Type                 | Value             |
|----------------------|-------------------|
| device ready         | DISCOVERER_HOWDY_ |
| device going offline | DISCOVERER_EXIT_  |

### Prime Go notes

There seems to be two different kinds of discovery frames: one with Software name "Offline Analyzer" and one with 
the Software name "JP11". I'm assuming that "JP11" will change depending on SW on the device. Both these
frames has a periodicity of 1000ms, but are sent with 500ms in between them. When "Offline Analyzer" frame
is sent there are two of them in a very short interval (~50µs).

## Service request
Once a suitable StageLinQ Source has been decided the next step is to request what services the StageLinQ source 
provides. This request is done over TCP (as opposed to the UDP of the discovery frame).
This is done by sending a service request frame to the service request port in the discovery frame. 
The service request frame looks as follows:

| Name         | Length (bytes)     | Purpose                                         |
|--------------|--------------------|-------------------------------------------------|
| Message type | 4                  | Service request frame type (00 00 00 02)        |
| Token        | 16                 | See "Token" section (NOTE: MSb cannot be a '1') |

If everything goes fine the StageLinQ source will reply with its services.
The response frame is as follows:

| Name         |                     | Length (bytes)      | Purpose                                                |
|--------------|---------------------|---------------------|--------------------------------------------------------|
| Message type |                     | 4                   | Service request frame type (00 00 00 02)               |
| Token        |                     | 16                  | See "Token" section (note: same as in discovery frame) |
| Service 1    | Message type        | 4                   | Service announcement frame type (00 00 00 00)          |
| Service 1    | Token               | 16                  | See "Token" section (note: same as in discovery frame) |
| Service 1    | Service name length | 4                   | Length of the service name (uint32)                    |
| Service 1    | Service name        | service name length | name of a service offered                              |
| Service 1    | Service port        | 2                   | Port of the service                                    |
| Service 2    | Message type        | 4                   | Service announcement frame type (00 00 00 00)          |
| Service 2    | Token               | 16                  | See "Token" section (note: same as in discovery frame) |
| Service 2    | Service name length | 4                   | Length of the service name (uint32)                    |
| Service 2    | Service name        | service name length | name of a service offered                              |
| Service 2    | Service port        | 2                   | Port of the service                                    |
| ...          |                     |                     |                                                        |
| Service n    | Message type        | 4                   | Service announcement frame type (00 00 00 00)          |
| Service n    | Token               | 16                  | See "Token" section (note: same as in discovery frame) |
| Service n    | Service name length | 4                   | Length of the service name (uint32)                    |
| Service n    | Service name        | service name length | name of a service offered                              |
| Service n    | Service port        | 2                   | Port of the service                                    |

The response to the service request can contain several service announcements, if the StageLinQ source offers more than
one service. I'm assuming that each of the service names have a specification behind them.
The services supported by my Prime Go is (device name "primego", software name "Jp11"):

| Service               | functionality                                        |
|-----------------------|------------------------------------------------------|
| StateMap              | get information about values of the decks, mixer etc |
| Broadcast             | ?                                                    |
| TimeSynchronization   | ?                                                    |
| BeatInfo              | ?                                                    |
| FileTransfer          | ?                                                    |

## Subscribing to a service
To subscribe to a service, simply establish a TCP connection to the port of the service, then send a service 
announcement frame to the StageLinQ source:

| Name                | Length (bytes)      | Purpose                                       |
|---------------------|---------------------|-----------------------------------------------|
| Message type        | 4                   | Service announcement frame type (00 00 00 00) |
| Token               | 16                  | See "Token" section                           |
| Service name length | 4                   | Length of the service name (uint32)           |
| Service name        | service name length | name of a service offered                     |
| Service port        | 2                   | (For some reason) Port your calling from      |

### StateMap Service
The stateMap service can be used to read out various information from the StageLinQ Source. Examples of this 
information is position of faders, if a deck is playing or not, or information about the loaded track of a deck.

After the service has been subscribed to, the StageLinkQ sink will have to specify which information it wants to 
subscribe to. 
I have not found a way to read out which data is available, so check the lists in EngineServices.py to
find some possible values. The message frame for subscribing to a specific parameter is the following:

| Name                      | Length (bytes)           | Purpose                                                                                            |
|---------------------------|--------------------------|----------------------------------------------------------------------------------------------------|
| Length                    | 4                        | Length of the request                                                                              |
| Magic flag(?)             | 8                        | Seems to me magic flag of some kind, set value to [0x73, 0x6d, 0x61, 0x61, 0x00, 0x00, 0x07, 0xd2] |
| Information path length   | 4                        | Length of the information path                                                                     |
| Information path          | Information path length  | Path to information to subscribe to.                                                               |
| End delimiter             | 4                        | Four bytes of 0s                                                                                   |

Note: several subscription requests can be sent in one frame. It may be possible to also do several requests
with one Length/Magic flag. 

## Tokens
The tokens seem to be a randomly generated 128 bit value, but there also seems to be some constraints on these.
One constraint I have found is that if the most significant bit is '1' when services are requested a StageLinQ source
will not reply with its services, but instead just ignore the request. It is very possible that there are other
undiscovered constraints too. The different frames seems to have unique tokens as this works, 
but this needs to be investigated more.

In PyStageLinQ I have kept the token as randomly generated in hopes of finding more issues when they are incorrect, to
be able to figure out more of the protocol.
