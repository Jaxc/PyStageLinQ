"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""
import select
import socket
import time
import asyncio
from typing import Callable

from . import Device
from .MessageClasses import *
from .DataClasses import *
from .ErrorCodes import PyStageLinQError
from .Network import StageLinQService
from . import EngineServices


class PyStageLinQ:
    """
        The main object for PyStageLinQ. Use this object to first initialize and then start PyStageLinq

        :param new_device_found_callback: This callback is used to report back to the application when a StageLinQ \
        device has been detected on the network. It is then up to the application to determine what device has been \
        and how if it wants to connect to it.

        :param name: This is the name which PyStageLinQ will announce itself with on the StageLinQ protocol. If not set \
        it defaults to "Hello StageLinQ World".

    """
    REQUESTSERVICEPORT = 0  # If set to anything but 0 other StageLinQ devices will try to request services at said port
    StageLinQ_discovery_port = 51337

    ANNOUNCE_IP = "169.254.255.255"

    def __init__(self, new_device_found_callback: Callable[[str, StageLinQDiscovery, EngineServices.ServiceHandle], None],
                 name: str = "Hello StageLinQ World"):
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
        """
Function for starting PyStageLinq. This function shall be called once the PyStageLinQ object has been initialized and
will start a bunch of subprocesses.
        """
        asyncio.run(self._start_StageLinQ())

    def _stop(self):
        discovery = StageLinQDiscovery()
        discovery_frame = discovery.encode(StageLinQDiscoveryData(Token=self.OwnToken, DeviceName=self.name,
                                                                  ConnectionType=ConnectionTypes.EXIT, SwName="Python",
                                                                  SwVersion="1.0.0",
                                                                  ReqServicePort=self.REQUESTSERVICEPORT))

        self._send_discovery_frame(discovery_frame)

    def _announce_self(self):
        discovery = StageLinQDiscovery()
        discovery_frame = discovery.encode(self.discovery_info)
        self._send_discovery_frame(discovery_frame)

    def _send_discovery_frame(self, discovery_frame):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as discovery_socket:
            discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            try:

                discovery_socket.sendto(discovery_frame, (self.ANNOUNCE_IP, 51337))
            except PermissionError:
                raise Exception(
                    f"Cannot write to IP {self.ANNOUNCE_IP}, this error could be due to that there is no network cart set up with this IP range")

    async def _discover_StageLinQ_device(self, timeout=10):
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

    def subscribe_to_statemap(self, state_map_service: EngineServices.ServiceHandle, subscription_list: dict,
                              data_available_callback: Callable[[list[StageLinQStateMapData]], None] = None) -> None:
        """
This function is used to subscribe to a statemap service provided by a StageLinQ device.
        :param state_map_service: This parameter is used to determine if
        :param subscription_list: list of serivces that the application wants to subscribe to
        :param data_available_callback: Callback for when data is available from StageLinQ device
        """
        if state_map_service.service != "StateMap":
            raise Exception("Service is not StateMap!")

        # Defer task creation to avoid blocking the calling function
        asyncio.create_task(self._subscribe_to_statemap(state_map_service, subscription_list, data_available_callback))

    async def _subscribe_to_statemap(self, StateMapService, subscription_list, data_available_callback):

        state_map = EngineServices.StateMapSubscription(StateMapService, data_available_callback, subscription_list)
        await state_map.Subscribe(self.OwnToken)

        self.tasks.add(state_map.get_task())

    async def _start_StageLinQ(self):

        self.tasks.add(asyncio.create_task(self._periodic_announcement()))
        self.tasks.add(asyncio.create_task(self._PyStageLinQStrapper()))

        await self._wait_for_exit()

        pass

    async def _wait_for_exit(self):
        while True:
            for task in self.tasks.copy():
                if task.done():
                    if task.exception():
                        raise task.exception()
                    return
            await asyncio.sleep(1)

    async def _periodic_announcement(self):
        while True:
            self._announce_self()
            await asyncio.sleep(0.5)

    async def _PyStageLinQStrapper(self):
        await asyncio.sleep(0.5)

        await self._discover_StageLinQ_device(timeout=2)

    def __del__(self):
        self._stop()
