"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""

import select
import socket
import time
import asyncio
import logging
import psutil
import ipaddress
from typing import Callable

from . import Device
from .MessageClasses import *
from .DataClasses import *
from .ErrorCodes import PyStageLinQError
from .Network import StageLinQService
from . import EngineServices

logger = logging.getLogger("PyStageLinQ")


@dataclass
class PyStageLinQ_interface_info:
    name: str
    id: int
    addr: int
    addr_str: str
    mask: int
    status: psutil._common.snicstats
    n_disc_msg_send: int


class PyStageLinQ_network_interface:
    def __init__(self, ip=None, discovery_port=51337):
        self.target_interfaces = []
        self.discovery_port = discovery_port
        self.get_interface_from_ip(ip)

    def get_interface_from_ip(self, ip):
        if ip is None:
            ip_list = ["any"]
        elif type(ip) is str:
            ip_list = [ip]
        elif type(ip) is list:
            for entry in ip:
                if type(entry) is not str:
                    raise TypeError
            ip_list = ip
        else:
            raise TypeError

        for interface in psutil.net_if_stats().items():
            for interface_info in psutil.net_if_addrs()[interface[0]]:
                # Only look for IPV4 binds
                if socket.AF_INET == interface_info.family and (
                    interface_info.address in ip_list or ip_list[0] == "any"
                ):
                    self.target_interfaces.append(
                        PyStageLinQ_interface_info(
                            interface[0],
                            len(self.target_interfaces),
                            int(ipaddress.IPv4Address(interface_info.address)),
                            interface_info.address,
                            int(ipaddress.IPv4Address(interface_info.netmask)),
                            interface[1],
                            0,
                        )
                    )

    def send_discovery_frame(self, discovery_frame):
        for interface in self.target_interfaces:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as discovery_socket:
                discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                discovery_socket.bind((interface.addr_str, 0))
                try:
                    discovery_socket.sendto(
                        discovery_frame,
                        ("255.255.255.255", self.discovery_port),
                    )
                    self.target_interfaces[interface.id].n_disc_msg_send += 1
                except PermissionError:
                    logger.warning(
                        f"Cannot send message on interface {interface.name}, "
                        f"this error could be due to that there is no network interface set up with this IP range"
                    )
                    raise PermissionError

    def determine_interface_of_remote_ip(self, ip):
        for interface in self.target_interfaces:
            if (int(ipaddress.IPv4Address(ip)) & interface.mask) == (
                interface.mask & interface.addr
            ):
                return interface

        return None

    def send_desc_on_all_if(self):
        for interface in self.target_interfaces:
            # Wait until a few discovery frames have been sent to make sure the other devices have seen us. If they have
            # not and we are asking for services it will be denied.
            if interface.n_disc_msg_send < 3:
                return False

        return True


class PyStageLinQ:
    """
    The main object for PyStageLinQ. Use this object to first initialize and then start PyStageLinq

    :param new_device_found_callback: This callback is used to report back to the application when a StageLinQ
    device has been detected on the network. It is then up to the application to determine what device has been
    and how if it wants to connect to it.

    :param name: This is the name which PyStageLinQ will announce itself with on the StageLinQ protocol. If not
    set it defaults to "Hello StageLinQ World".

    :param ip: This is the ip of the interface you want to bind the sockets to, e.g. your local ethernet IP. If set to
    None all interfaces will be used.

    """

    REQUESTSERVICEPORT = 0  # If set to anything but 0 other StageLinQ devices will try to request services at said port
    StageLinQ_discovery_port = 51337

    _loopcondition = True

    def __init__(
        self,
        new_device_found_callback: Callable[
            [str, StageLinQDiscovery, EngineServices.ServiceHandle], None
        ],
        name: str = "Hello StageLinQ World",
        ip=None,
    ):
        self.name = name
        self.OwnToken = StageLinQToken()
        self.OwnToken.generate_token()
        self.discovery_info = StageLinQDiscoveryData(
            Token=self.OwnToken,
            DeviceName=self.name,
            ConnectionType=ConnectionTypes.HOWDY,
            SwName="Python",
            SwVersion="0.0.1",
            ReqServicePort=self.REQUESTSERVICEPORT,
        )

        self.device_list = Device.DeviceList()

        self.network_interface = PyStageLinQ_network_interface(ip)

        self.tasks = set()

        self.active_services = []

        self.new_device_found_callback = new_device_found_callback

        logger.debug(f"Initialized!")

    def start_standalone(self):
        """
        Function for starting PyStageLinq in standalone mode. In this mode this function will not return, but
        instead start asyncio and que up tasks. This function shall be called once the PyStageLinQ object has been
        initialized.
        """
        logger.debug(f"Starting in standalone mode.")
        asyncio.run(self._start_stagelinq(standalone=True))

    def start(self):
        """
        Function for starting PyStageLinq as part of a bigger asyncio program. The function will start the required
        tasks and then return to its caller. It is then up to the called to make sure that the asyncio tasks gets
        time to execute. This function shall be called once the PyStageLinQ object has been initialized.
        """
        logger.debug(f"Starting in asyncio mode.")
        self._start_stagelinq()

    def _stop(self):
        logger.info(f"Stop requested, trying graceful shutdown")
        try:
            discovery = StageLinQDiscovery()
            discovery_info = self.discovery_info
            discovery_info.ConnectionType = ConnectionTypes.EXIT
            discovery_frame = discovery.encode_frame(discovery_info)

            self.network_interface.send_discovery_frame(discovery_frame)
            logger.info(f"Gracefully shutdown complete")
        except Exception as e:
            logger.debug('Could not send "EXIT" discovery frame during shutdown')
            raise e

    def _announce_self(self):
        discovery = StageLinQDiscovery()
        discovery_frame = discovery.encode_frame(self.discovery_info)
        self.network_interface.send_discovery_frame(discovery_frame)

    def get_loop_condition(self) -> bool:
        return self._loopcondition

    async def _discover_stagelinq_device(self, host_ip, timeout=10):
        """
        This function is used to find StageLinQ device announcements.
        """

        logger.info(f"Trying to discover StageLinQ devices.")

        # Local Constants
        discover_buffer_size = 8192

        # Create socket
        discover_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            discover_socket.bind(
                (host_ip, self.StageLinQ_discovery_port)
            )  # bind socket to broadcast
        except Exception as e:
            # Cannot bind to socket, check if IP is correct and link is up
            logger.warning(
                f"Cannot bind to IP socket: {host_ip} on port {self.StageLinQ_discovery_port}"
            )
            raise e
        discover_socket.setblocking(False)

        loop_timeout = time.time() + timeout

        logger.debug(
            f"Socket bound to IP {host_ip} and Port {self.StageLinQ_discovery_port} successfully. Starting to look for "
            f"discovery frames"
        )

        while self.get_loop_condition():
            data_available = select.select([discover_socket], [], [], 0)
            if data_available[0]:
                data, addr = discover_socket.recvfrom(discover_buffer_size)
                device_ip = addr[0]
                discovery_frame = StageLinQDiscovery()

                if PyStageLinQError.STAGELINQOK != discovery_frame.decode_frame(data):
                    # something went wrong
                    continue

                if self.name == discovery_frame.device_name:
                    # Ourselves, ignore message
                    continue

                if 0 == discovery_frame.Port:
                    # If port is 0 there are no services to request, and for our use an invalid device
                    continue

                # External Device present, setting new timeout
                loop_timeout = time.time() + timeout

                # Check if we have already registered this device, and if so ignore it for now
                device_registered = self.device_list.find_registered_device(
                    discovery_frame.get()
                )
                if device_registered is True:
                    continue

                logger.info(f"Found new StageLinq device at IP {device_ip}")
                await self._register_new_device(discovery_frame, device_ip)

            if time.time() > loop_timeout:
                # No devices found within timeout
                logger.info(
                    f"No discovery frames found on {host_ip} last {timeout} seconds."
                )
                return PyStageLinQError.DISCOVERYTIMEOUT
            await asyncio.sleep(0.1)

    async def _register_new_device(self, discovery_frame, ip):
        stagelinq_device = StageLinQService(ip, discovery_frame, self.OwnToken, None)
        service_tasks = await stagelinq_device.get_tasks()
        for task in service_tasks:
            self.tasks.add(task)
        self.device_list.register_device(stagelinq_device)
        logging.debug(f"Device found! Name: {stagelinq_device.device_name}")
        await stagelinq_device.wait_for_services(timeout=1)
        if self.new_device_found_callback is not None:
            self.new_device_found_callback(
                ip, discovery_frame, stagelinq_device.get_services()
            )

    def subscribe_to_statemap(
        self,
        state_map_service: EngineServices.ServiceHandle,
        subscription_list: dict,
        data_available_callback: Callable[[list[StageLinQStateMapData]], None] = None,
    ) -> int:
        """
        This function is used to subscribe to a statemap service provided by a StageLinQ device.
                :param state_map_service: This parameter is used to determine if
                :param subscription_list: list of serivces that the application wants to subscribe to
                :param data_available_callback: Callback for when data is available from StageLinQ device
        """
        if state_map_service.service != "StateMap":
            logger.warning(f'{state_map_service.service} is not of type "Statemap"')
            return PyStageLinQError.SERVICENOTRECOGNIZED

        # Defer task creation to avoid blocking the calling function
        asyncio.create_task(
            self._subscribe_to_statemap(
                state_map_service, subscription_list, data_available_callback
            )
        )
        return PyStageLinQError.STAGELINQOK

    # beat_info_service """: EngineBeatInfo.BeatInfoHandle""", subscription_list: dict, data_available_callback: Callable[[list[StageLinQStateMapData]], None] = None
    def subscribe_to_beatinfo(self, beat_info_service: EngineServices.ServiceHandle, data_available_callback) -> int:
        if beat_info_service.service != "BeatInfo":
            logger.warning(f'{beat_info_service.service} is not of type "BeatInfo"')
            return PyStageLinQError.SERVICENOTRECOGNIZED

        # Defer task creation to avoid blocking the calling function
        asyncio.create_task(
            self._subscribe_to_beatinfo(
                beat_info_service, data_available_callback
            )
        )
        return PyStageLinQError.STAGELINQOK



    async def _subscribe_to_statemap(
        self, state_map_service, subscription_list, data_available_callback
    ):
        state_map = EngineServices.StateMapSubscription(
            state_map_service, subscription_list, data_available_callback
        )
        await state_map.subscribe(self.OwnToken)

        self.tasks.add(state_map.get_task())
        logger.debug(f"Subscription to StateMap successful.")

    async def _subscribe_to_beatinfo(
        self, state_map_service, data_available_callback
    ):
        beat_info = EngineServices.beatinfoSubscription(
            state_map_service, data_available_callback
        )
        await beat_info.subscribe(self.OwnToken)

        self.tasks.add(beat_info.get_task())
        logger.debug(f"Subscription to BeatInfo successful, sending flag to start receiving data.")

        await beat_info.start()


    async def _start_stagelinq(self, standalone=False):
        # Start the initial tasks of the library
        self.tasks.add(asyncio.create_task(self._periodic_announcement()))

        # wait for discovery message to be send on all interfaces
        while not self.network_interface.send_desc_on_all_if():
            await asyncio.sleep(0.1)

        self.tasks.add(asyncio.create_task(self._py_stagelinq_strapper()))

        if standalone:
            await self._wait_for_exit()

    async def _wait_for_exit(self):
        while self.get_loop_condition():
            for task in self.tasks.copy():
                if task.done():
                    if task.exception() is not None:
                        logger.warning(
                            f"Exception: {task.exception()} occured in task: {task.get_coro()}, stopping "
                            f"PyStageLinQ."
                        )
                        logger.debug(f"Stacktrace to error: {task.print_stack()}")
                        self.stop()
                        raise task.exception()
                    return
            await asyncio.sleep(1)

    def _stop_all_tasks(self):
        logger.info(f"Stop all PyStageLinQ AsyncIO tasks requested")
        for task in self.tasks.copy():
            task.cancel()

    async def _periodic_announcement(self):
        while self.get_loop_condition():
            self._announce_self()
            await asyncio.sleep(0.5)

    async def _py_stagelinq_strapper(self):
        strapper_tasks = set()
        logger.info(f"Starting to look for StageLinQ discovery frames:")

        strapper_tasks.add(
            asyncio.create_task(self._discover_stagelinq_device("", timeout=2))
        )

        while self.get_loop_condition():
            all_tasks_done = True
            for task in strapper_tasks.copy():
                all_tasks_done = all_tasks_done and task.done()
                if task.done():
                    if task.exception() is not None:
                        raise task.exception()

            if all_tasks_done:
                logger.debug("Timeout occurred on all interfaces.")
                return
            await asyncio.sleep(1)

    def stop(self):
        self._stop()

    def __del__(self):
        self._stop_all_tasks()
        self._stop()
