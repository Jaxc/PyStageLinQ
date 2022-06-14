"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""
import select
import socket
import time
from PyStageLinQMessageClasses import *
from PyStageLinQDataClasses import *
from ErrorCodes import PyStageLinQError
from EngineServices import DenonDjServices


class ConnectionTypes:
    HOWDY = "DISCOVERER_HOWDY_"
    EXIT = "DISCOVERER_EXIT_"


class PyStageLinQ:

    FRAMEIDLENGTH = 4
    REQUESTSERVICEPORT = 0 # If set to anything but 0 other StageLinQ devices will try to request services
    # Message ID's:
    serviceAnnouncementMessageID = 0
    referenceMessageID = 1
    servicesRequestMessage = 2
    deviceName = "PyStageLinQ"

    def __init__(self, name="Hello StageLinQ World"):
        self.name = name
        self.OwnToken = StageLinQToken()
        self.discovery_info = None
        self.OwnToken.generate_token()
        self.discovery_info = StageLinQDiscoveryData(Token=self.OwnToken, DeviceName=self.name,
                                                     ConnectionType=ConnectionTypes.HOWDY, SwName="Python",
                                                     SwVersion="1.0.0", ReqServicePort=self.REQUESTSERVICEPORT)

    def announceSelf(self):
        Discovery = StageLinQDiscovery()
        discovery_frame = Discovery.encode(self.discovery_info)

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as opened_socket:
            opened_socket.sendto(discovery_frame, ("169.254.255.255", 51337))


    def leave(self):
        Discovery = StageLinQDiscovery()
        discovery_frame = Discovery.encode(StageLinQDiscoveryData(Token=self.OwnToken, DeviceName=self.name,
                                                     ConnectionType=ConnectionTypes.EXIT, SwName="Python",
                                                     SwVersion="1.0.0", ReqServicePort=self.REQUESTSERVICEPORT))

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
        match (int.from_bytes(frame[0:4], byteorder='big')) :
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

    def discoverStageLinQDevice(self, timeout=10):
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
            dataAvailable = select.select([discoverSocket], [], [], loop_timeout - time.time())
            if dataAvailable[0]:
                data, addr = discoverSocket.recvfrom(DiscoverBufferSize)
                discovery_frame = StageLinQDiscovery()
                if PyStageLinQError.STAGELINQOK != discovery_frame.decode(data):
                    continue
                service_list = self.RequestStageLinQDeviceServices(addr[0], discovery_frame)
                if service_list is None:
                    continue
                StateMapService = self.SearchForService(service_list, "StateMap")
                if StateMapService is None:
                    continue

                self.SubscribeToStateMap(addr[0], StateMapService[1])
                return PyStageLinQError.STAGELINQOK

            if time.time() > loop_timeout:
                return PyStageLinQError.DISCOVERYTIMEOUT

    def SearchForService(self, service_list, wanted_service):
        for service in service_list:
            if service[0] == wanted_service:
                return service
        return None

    def SubscribeToStateMap(self, ip, Port):

        StateAnnounce = StageLinQServiceAnnouncement()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as StateMapSocket:
            StateMapSocket.connect((ip, Port))
            StateMapSocket.getsockname()
            StateMapSocket.send(StateAnnounce.encode(StageLinQServiceAnnouncementData(Token=self.OwnToken, Service="StateMap", Port=StateMapSocket.getsockname()[1])))
            for service in ["/Engine/Deck1/Play"]:
                msg = StateAnnounce.WriteNetworkString(service)
                msg += (0).to_bytes(4,byteorder='big')
                StateMapSocket.send(msg)

            time.sleep(3)
        pass

    def RequestStageLinQDeviceServices(self, ip, discovery_frame):

        if discovery_frame.sw_name != 'OfflineAnalyzer':

            RequestPort = discovery_frame.get_data().ReqServicePort

            out_data = StageLinQRequestServices()
            out_token = self.OwnToken
            reference_message = out_data.encode(StageLinQServiceRequestData(Token=out_token))
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as StageLinQSocket :
                StageLinQSocket.connect((ip, RequestPort))
                StageLinQSocket.send(reference_message)
                response = StageLinQSocket.recvfrom(1024)

            service_list = self.DecodeMultiframe(response[0])
            if len(service_list) > 0:
                return service_list

            return None

    def DecodeMultiframe(self, frame):
        service_list = []
        while(len(frame) > 4):
            match (int.from_bytes(frame[0:4], byteorder='big')):
                case 0:
                    data = StageLinQServiceAnnouncement()
                    data.decode(frame)
                    service = data.get()
                    service_list.append([service.Service, service.Port])
                case 1:
                    data = StageLinQReference()
                case 2:
                    data = StageLinQRequestServices()
                case _:
                    # invalid data, return
                    return
            frame = frame[data.get_len():]
        return service_list