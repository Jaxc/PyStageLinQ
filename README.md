[![Build Status](https://img.shields.io/circleci/build/github/Jaxc/PyStageLinQ/main?style=plastic)](https://app.circleci.com/pipelines/github/Jaxc/PyStageLinQ?branch=main)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/PyStageLinQ?style=plastic)](https://pypi.org/project/PyStageLinQ/)
<picture>
  <img alt="PyPi version" src="https://img.shields.io/pypi/v/PyStageLinQ?style=plastic">
</picture>
[![PyPI - License](https://img.shields.io/pypi/l/PyStageLinQ?style=plastic)](https://en.wikipedia.org/wiki/MIT_License)
[![Read the Docs](https://img.shields.io/readthedocs/pystagelinq?style=plastic)](https://pystagelinq.readthedocs.io/en/latest/)
[![Codecov](https://img.shields.io/codecov/c/github/Jaxc/PyStageLinQ?style=plastic)](https://app.codecov.io/gh/Jaxc/PyStageLinQ)
[![CodeFactor](https://www.codefactor.io/repository/github/jaxc/pystagelinq/badge/main?style=plastic)](https://www.codefactor.io/repository/github/jaxc/pystagelinq/overview/main)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
# Overview
This Python module decodes part of the StageLinQ protocol used by Denon DJ equipment. In its current state it is
possible to read out information like track information, fader position (Crossfader, channel volume, pitchfader), BPM 
etc. The project also includes [a description of how StageLinQ works](https://github.com/Jaxc/PyStageLinQ/blob/main/StageLinQ_protocol.md) taking from my findings
as well as other code available.

This module can be used to receive this information from a device via a callback when data is available.

There is also a Wireshark Dissector that I made during my trials.

# Status
An initial implementation of parts of the protocol has been done, but there is still much left to do. As the code should
be at least somewhat functional I've decided to release this as is and add functionality along the way. Since I'm unsure
where this is heading there is a possibility that there will be a future (major) version that will reimagine the 
functions completely.

The next few versions will probably be patched to bring the documentation up to date.

# Documentation
Documentation is available on [readthedocs.io](https://pystagelinq.readthedocs.io/en/latest/)

# Installation
`pip install PyStageLinQ`


# Issue tracking
If you find an issue, please report check known issues, and if the issue is not mentioned please report it 
[here](https://github.com/Jaxc/PyStageLinQ)

# Example usage
Here follow an example of how PyStageLinQ can be used:

```python
from PyStageLinQ import EngineServices, PyStageLinQ
PrimeGo = None

# Callback for when PyStageLinQ as found a StageLinQ device. This will print out information about the found device
# and if lets the user decide if they want to subscribe to a service or not.

def new_device_found_callback(ip, discovery_frame, service_list):
    # Print device info and supplied services
    print(
        f"Found new Device on ip {ip}: Device name: {discovery_frame.device_name}, ConnectionType: {discovery_frame.connection_type}, SwName: {discovery_frame.sw_name}, "
        f"SwVersion: {discovery_frame.sw_version}, port: {discovery_frame.Port}")

    if len(service_list) > 0:
        print("Services found in device:")
    else:
        print("No services found")

    for service in service_list:
         print(f"\t{service.service} on port {service.port}")


    # Request StateMap service
    for service in service_list:
        if service.service == "StateMap":
            PrimeGo.subscribe_to_statemap(service, EngineServices.prime_go, state_map_data_print)

            
# Callback for when data has arrived from a StageLinQ device. It is up to the user what to do with this information.
            
def state_map_data_print(data):
    for message in data:
        print(message)

# Example main function, starting PyStageLinQ.
if __name__ == "__main__":
    global PrimeGo
    
    # Run PyStageLinQ on all available network interfaces
    PrimeGo = PyStageLinQ.PyStageLinQ(new_device_found_callback, name="Jaxcie StagelinQ")
    PrimeGo.start()
```

# Wireshark dissector
When I developed this code I made a WireShark Dissector, it is included in this repo. Do note that this dissector 
isn't properly tested and may cause unexpected issues. As this file is not part of the Pythoncode in PyStageLinQ it can
be found on [GitHub](https://github.com/Jaxc/PyStageLinQ/blob/main/tools/StageLinQ.lua)

# Compatability
PyStageLinQ has been tested with a Denon DJ Prime Go on Windows 10 and Linux (Mint 20.3) with Python 3.10. 

# Acknowledgements
Big thanks to icedream for his implementation of StageLinQ in go:
https://github.com/icedream/go-stagelinq
