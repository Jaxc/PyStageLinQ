"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""
from PyStageLinQ import EngineServices, PyStageLinQ

"""
Processes needed for StageLinQ:
1. Announce: Send discovery frame every 1 s
2. Negotiation: Reading Device discovery messages and request services.
3. Service Server: Open TCP socket ? 
"""
PrimeGo = None


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

def state_map_data_print(data):
    for message in data:
        print(message)


def main():
    global PrimeGo
    PrimeGo = PyStageLinQ.PyStageLinQ(new_device_found_callback, name="Jaxcie StagelinQ")
    PrimeGo.start()


if __name__ == "__main__":
    main()
