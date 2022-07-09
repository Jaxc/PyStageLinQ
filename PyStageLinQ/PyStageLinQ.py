"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""
import select
import socket
import time
import asyncio

from . import Device
from .MessageClasses import *
from .DataClasses import *
from .ErrorCodes import PyStageLinQError
from .Network import StageLinQService
from . import EngineServices


class PyStageLinQ:
    REQUESTSERVICEPORT = 0  # If set to anything but 0 other StageLinQ devices will try to request services at said port
    StageLinQ_discovery_port = 51337

    ANNOUNCE_IP ="169.254.255.255"

    def __init__(self, new_device_found_callback, name="Hello StageLinQ World", ):
        self.name = name
        self.OwnToken = StageLinQToken()
        self.discovery_info = None
        self.OwnToken.generate_token()
        self.discovery_info = StageLinQDiscoveryData(Token=self.OwnToken, DeviceName=self.name,
                                                     ConnectionType=ConnectionTypes.HOWDY, SwName="Python",
                                                     SwVersion="1.0.0", ReqServicePort=self.REQUESTSERVICEPORT)

        self.device_list = Device.DeviceList()

        self.tasks = set()
        self.found_services = []
        self.new_services_available = False

        self.active_services = []

        self.devices_with_services_pending_list = []
        self.devices_with_services_pending = False
        self.devices_with_services_lock = asyncio.Lock()

        self.new_device_found_callback = new_device_found_callback

    def start(self):
        asyncio.run(self.start_StageLinQ())

    def stop(self):
        discovery = StageLinQDiscovery()
        discovery_frame = discovery.encode(StageLinQDiscoveryData(Token=self.OwnToken, DeviceName=self.name,
                                                                  ConnectionType=ConnectionTypes.EXIT, SwName="Python",
                                                                  SwVersion="1.0.0",
                                                                  ReqServicePort=self.REQUESTSERVICEPORT))

        self.send_discovery_frame(discovery_frame)

    def announce_self(self):
        Discovery = StageLinQDiscovery()
        discovery_frame = Discovery.encode(self.discovery_info)
        self.send_discovery_frame(discovery_frame)

    def send_discovery_frame(self, discovery_frame):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as discovery_socket:
            try:
                discovery_socket.sendto(discovery_frame, (self.ANNOUNCE_IP, 51337))
            except PermissionError:
                raise Exception(
                    f"Cannot write to IP {self.ANNOUNCE_IP}, this error could be due to that there is no network cart set up with this IP range")

    async def discover_StageLinQ_device(self, timeout=10):
        """
        This function is used to find StageLinQ device announcements.
        """
        # Local Constants
        DiscoverBufferSize = 8192

        # Create socket
        discoverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discoverSocket.bind(("", self.StageLinQ_discovery_port))  # bind socket to all interfaces
        discoverSocket.setblocking(False)

        loop_timeout = time.time() + timeout

        while True:
            await asyncio.sleep(0.1)
            dataAvailable = select.select([discoverSocket], [], [], 0)
            if dataAvailable[0]:
                data, addr = discoverSocket.recvfrom(DiscoverBufferSize)
                ip = addr[0]
                discovery_frame = StageLinQDiscovery()

                if PyStageLinQError.STAGELINQOK != discovery_frame.decode(data):
                    # something went wrong
                    continue

                # Devices found, setting new timeout
                loop_timeout = time.time() + timeout

                if 0 == discovery_frame.Port:
                    # If port is 0 there are no services to request
                    continue

                if self.name == discovery_frame.device_name:
                    # Ourselves, ignore
                    continue

                device_registered = self.device_list.find_registered_device(discovery_frame.get_data())
                if device_registered:
                    continue
                print(discovery_frame.sw_name)
                stagelinq_device = StageLinQService(ip, discovery_frame, self.OwnToken, None)
                service_tasks = await stagelinq_device.get_tasks()

                for task in service_tasks:
                    self.tasks.add(task)

                self.device_list.register_device(stagelinq_device)
                await stagelinq_device.wait_for_services(timeout=1)

                if self.new_device_found_callback is not None:
                    self.new_device_found_callback(ip, discovery_frame, stagelinq_device.get_services())

            if time.time() > loop_timeout:
                print("No devices found within timeout")
                return PyStageLinQError.DISCOVERYTIMEOUT





    def subscribe_to_statemap(self, StateMapService, subscription_list, data_available_callback=None):

        if StateMapService.service != "StateMap":
            raise Exception("Service is not StateMap!")

        # Defer task creation to avoid blocking the calling function
        asyncio.create_task(self._subscribe_to_statemap(StateMapService, subscription_list, data_available_callback))

    async def _subscribe_to_statemap(self, StateMapService, subscription_list, data_available_callback):

        state_map = EngineServices.StateMapSubscription(StateMapService, data_available_callback, subscription_list)
        await state_map.Subscribe(self.OwnToken)

        self.tasks.add(state_map.get_task())

    def SearchForService(self, service_list, wanted_service):
        for service in service_list:
            if service.service == wanted_service:
                return service
        return None

    async def start_StageLinQ(self):

        self.tasks.add(asyncio.create_task(self.periodic_announcement()))
        self.tasks.add(asyncio.create_task(self.PyStageLinQStrapper()))


        await self.wait_for_exit()

        pass


    async def wait_for_exit(self):
        while True:
            for task in self.tasks.copy():
                if task.done():
                    if task.exception():
                        raise task.exception()
                    return
            await asyncio.sleep(1)

    async def periodic_announcement(self):
        while True:
            self.announce_self()
            await asyncio.sleep(0.5)

    async def PyStageLinQStrapper(self):
        await asyncio.sleep(0.5)

        await self.discover_StageLinQ_device(timeout=2)

    def __del__(self):
        self.stop()
