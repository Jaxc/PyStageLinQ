PyStageLinQ is a Python library for ineracting with StageLinQ devices over IP. It is distributed over PyPi and currently
supports the StateMap functionality.

# Installation
`pip install PyStageLinQ`

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