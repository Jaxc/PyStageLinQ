"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""
import select
import socket
import time
import asyncio

from PyStageLinQMessageClasses import *
from PyStageLinQDataClasses import *
from ErrorCodes import PyStageLinQError
from PyStageLinQNetwork import StageLinQService
import EngineServices


class ConnectionTypes:
    HOWDY = "DISCOVERER_HOWDY_"
    EXIT = "DISCOVERER_EXIT_"


class PyStageLinQ:
    FRAMEIDLENGTH = 4
    REQUESTSERVICEPORT = 0  # If set to anything but 0 other StageLinQ devices will try to request services

    deviceName = "PyStageLinQ"

    reference_message_list = []

    def __init__(self, name="Hello StageLinQ World"):
        self.name = name
        self.OwnToken = StageLinQToken()
        self.discovery_info = None
        self.OwnToken.generate_token()
        self.discovery_info = StageLinQDiscoveryData(Token=self.OwnToken, DeviceName=self.name,
                                                     ConnectionType=ConnectionTypes.HOWDY, SwName="Python",
                                                     SwVersion="1.0.0", ReqServicePort=self.REQUESTSERVICEPORT)
        self.device_list = []

        self.is_running = True
        self.tasks = set()
        self.found_services = []
        self.new_services_available = False

        self.active_services = []

        self.devices_with_services_pending_list = []
        self.devices_with_services_pending = False
        self.devices_with_services_lock = asyncio.Lock()

        asyncio.run(self.start_StageLinQ())

    def announceSelf(self):
        Discovery = StageLinQDiscovery()
        discovery_frame = Discovery.encode(self.discovery_info)

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as opened_socket:
            opened_socket.sendto(discovery_frame, ("169.254.255.255", 51337))

    def leave(self):
        Discovery = StageLinQDiscovery()
        discovery_frame = Discovery.encode(StageLinQDiscoveryData(Token=self.OwnToken, DeviceName=self.name,
                                                                  ConnectionType=ConnectionTypes.EXIT, SwName="Python",
                                                                  SwVersion="1.0.0",
                                                                  ReqServicePort=self.REQUESTSERVICEPORT))

        opened_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        opened_socket.sendto(discovery_frame, ("169.254.255.255", 51337))

        opened_socket.close()

    def OpenRequestServiceSocket(self):
        request_service_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        request_service_socket.bind(('', self.REQUESTSERVICEPORT))
        request_service_socket.listen(5)

    #        while True:
    #            (client_socket, client_address) = await request_service_socket.accept()

    def HandleRequestService(self, reader, writer):
        frame = reader.read(100)

        if len(frame) < 4:
            # Invalid frame, to short to determine type
            return
        match (int.from_bytes(frame[0:4], byteorder='big')):
            case 0:
                data = StageLinQServiceAnnouncementData()
            case 1:
                data = StageLinQServiceAnnouncementData()
            case 2:
                data = StageLinQRequestServices()
            case _:
                return
        data.decode(frame)

        addr = writer.get_extra_info('peername')

        print(f"Received {data.get()!r} from {addr!r}")

        writer.close()

        pass

    async def discoverStageLinQDevice(self, timeout=10):
        """
        This function can be used to find StageLinQ devices.
        """

        # Local Constants
        StageLinQPort = 51337
        DiscoverBufferSize = 8192

        # Create socket
        discoverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discoverSocket.bind(("", StageLinQPort))  # bind socket to all interfaces
        discoverSocket.setblocking(False)

        loop_timeout = time.time() + timeout

        while True:
            await asyncio.sleep(0.1)
            dataAvailable = select.select([discoverSocket], [], [], loop_timeout - time.time())
            if dataAvailable[0]:
                data, addr = discoverSocket.recvfrom(DiscoverBufferSize)
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

                if "OfflineAnalyzer" == discovery_frame.sw_name:
                    # Temp just to reduce bloat in analyzing
                    continue

                device_registered = await self.find_registered_device(discovery_frame)
                if device_registered:
                    continue


                print(
                    f"Found new Device: {discovery_frame.device_name}, ConnectionType: {discovery_frame.connection_type}, SwName: {discovery_frame.sw_name}, "
                    f"SwVersion: {discovery_frame.sw_version}, port: {discovery_frame.Port}")

                stagelinq_device = StageLinQService(addr[0], discovery_frame, self.OwnToken, self.service_found_callback)
                service_tasks = await stagelinq_device.get_tasks()
                for task in service_tasks:
                    self.tasks.add(task)

                self.device_list.append(stagelinq_device)
                await stagelinq_device.wait_for_services(timeout=1)

            if time.time() > loop_timeout:
                return PyStageLinQError.DISCOVERYTIMEOUT


    async def find_registered_device(self, discovery_frame):
        for device in self.device_list:
            if discovery_frame.Port == device.Port:
                # Device already registered
                return True
        return False


    async def service_found_callback(self, device_service):

        async with self.devices_with_services_lock:
            self.devices_with_services_pending_list.append(device_service)
            self.devices_with_services_pending = True


    async def state_map_process(self):
        while True:
            devices_with_services_pending_list_int = None
            self.new_services_available = False
            async with self.devices_with_services_lock:
                if self.devices_with_services_pending:
                    devices_with_services_pending_list_int = self.devices_with_services_pending_list.copy()
                    self.devices_with_services_pending_list = []

            if devices_with_services_pending_list_int is not None:

                for device in devices_with_services_pending_list_int:
                    service_list = device.get_services()

                    if service_list is None:
                        continue
                    if len(service_list[2]) < 1:
                        continue

                    for service in service_list[2]:

                        self.found_services.append([service_list[0], service_list[1], service[0], service[1]])
                        self.new_services_available = True

            if self.new_services_available:
                StateMapService = self.SearchForService(self.found_services, "StateMap")

                if StateMapService is None:
                    continue

                self.active_services.append(StateMapService)
                self.tasks.add(asyncio.create_task(self.SubscribeToStateMap(StateMapService)))

            await asyncio.sleep(0.1)

    def SearchForService(self, service_list, wanted_service):
        for service in service_list:
            if service[2] == wanted_service:
                return service
        return None

    async def SubscribeToStateMap(self, service_handle):
        StateAnnounce = StageLinQServiceAnnouncement()
        reader, writer = await asyncio.open_connection(service_handle[1], service_handle[3])
        writer.write(StateAnnounce.encode(
            StageLinQServiceAnnouncementData(Token=self.OwnToken, Service="StateMap",
                                             Port=writer.transport.get_extra_info('sockname')[1])))
        await writer.drain()

        for service in EngineServices.common_functions.values():
            msg = (len(service)*2 + 8*2).to_bytes(4, byteorder='big')
            msg += bytearray([0x73, 0x6d, 0x61, 0x61])
            msg += bytearray([0x00, 0x00, 0x07, 0xd2])
            msg += StateAnnounce.WriteNetworkString(service)
            msg += (0).to_bytes(4, byteorder='big')
            writer.write(msg)
            await writer.drain()
        # small sleep to actually send frame
        await asyncio.sleep(0.001)

        while True:

            data = await reader.read(8192*2)

            print(len(data))

            if len(data) == 0:
                return

            while len(data) > 4:
                block_len = int.from_bytes(data[0:4], byteorder='big') + 4
                block_string = data[16:block_len].decode(encoding='UTF-16be')
                print(block_string)
                data = data[block_len:]
            print("-----------")
            """            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as StateMapSocket:
                StateMapSocket.connect((ip, Port))
                StateMapSocket.getsockname()
                StateMapSocket.send(StateAnnounce.encode(
                    StageLinQServiceAnnouncementData(Token=self.OwnToken, Service="StateMap",
                                                     Port=StateMapSocket.getsockname()[1])))
                msg = bytearray()
                for service in EngineServices.prime_go.values():
                    msg += StateAnnounce.WriteNetworkString(service)
                    msg += (0).to_bytes(4, byteorder='big')
                StateMapSocket.send(msg)

                while True:
                    data = StateMapSocket.recv(8192)
                    print(data)
            pass"""

            await asyncio.sleep(1)



    def send_reference_messages(self):
        for device in self.device_list:
            device.send_reference_message()


    async def start_StageLinQ(self):

        self.tasks.add(asyncio.create_task(self.periodic_announcement()))
        self.tasks.add(asyncio.create_task(self.PyStageLinQStrapper()))
        self.tasks.add(asyncio.create_task(self.state_map_process()))


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
            self.announceSelf()
            await asyncio.sleep(1)
            if not self.is_running:
                return

    async def PyStageLinQStrapper(self):
        await asyncio.sleep(1)

        await self.discoverStageLinQDevice(timeout=2)
        while True:
            await asyncio.sleep(0.5)
        self.is_running = False

    def __del__(self):
        self.leave()
