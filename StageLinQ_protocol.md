# StageLinQ protocol
StageLinQ is a protocol for sharing information from Denon DJ equipment. 
This can be used to display information about playing tracks, if deck is playing or not.

## Preface

### Disclaimer
This information has been gathered from a Denon DJ Prime Go using Wireshark.
The information may differ for other equipment that outputs StageLinQ.

### Nomenclature
In this document the following words are used as this:

*StageLinQ device*: This is used to describe a device that output StageLinQ information,
examples of this could be a Denon DJ Prime Go.
*Host*: This is used to describe the machine that uses the information that the 
StageLinQ device outputs, i.e. a computer running PyStageLinQ

## Ethernet configuration
The StageLinQ device will pick a random IP in the range 169.254.0.0/16.
You will need to set up your computer to use the same IP range. 
When developing I used the IP 169.254.1.10/16.

It is very possible that the StageLinQ device can be assigned an IP by DHCP, but I 
have not tested this.

## Device discovery
When no connection with a host has been established the DJ device will send out a broadcast message to 
IP 255.255.255.255.
These requests are sent to UDP port 51337. The source port of these request seems 
to be randomized. A StageLinQ device seems to output several discovery 
frames each second.

The StageLinQ Discovery frame is formatted as follows:

| Name                    | Length (bytes)     | Purpose                                 |
|-------------------------|--------------------|-----------------------------------------|
| Magic flag              | 4                  | Determine if frame is discovery frame   |
| token                   | 16                 | ?                                       |
| Device name length      | 4                  | Length of the device name (uint32)      |
| Device name             | Device name length | UTF16 encoded Device name               |
| Connection type length  | 4                  | Length of the Connection type(uint32)   |
| Connection type         | Device name length | UTF16 encoded Connection typee          |
| Software name length    | 4                  | Length of the Software name (uint32)    |
| Software name           | Device name length | UTF16 encoded Software name             |
| Software version length | 4                  | Length of the Software version (uint32) |
| Software version        | Device name length | UTF16 encoded Software version          |
| Port                    | 2                  | ? (Not same as source port of frame)    |

There seems to be two different kinds of discovery frames: one with Software name "Offline Analyzer" and one with 
the Software name "JP11". I'm assuming that "JP11" will change depending on SW on the device. Both these
frames has a periodicity of 1000ms, but are sent with 500ms in between them. When "Offline Analyzer" frame
is sent there are two of them in a very short interval (~50µs).
