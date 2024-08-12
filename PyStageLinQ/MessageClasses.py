"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""

from .DataClasses import *


class ConnectionTypes:
    HOWDY = "DISCOVERER_HOWDY_"
    EXIT = "DISCOVERER_EXIT_"


class StageLinQMessage:
    port_length = 2
    magic_flag_start = 0
    magic_flag_length = 4
    magic_flag_stop = magic_flag_start + magic_flag_length

    network_len_size = 4
    reference_len = 8

    length: int | type(None)

    def write_network_string(self, string: str) -> bytes:
        # Note: 2 bytes are needed for every char as it is UTF16 encoded
        ret = (2 * len(string)).to_bytes(self.network_len_size, byteorder="big")
        ret += string.encode(encoding="UTF-16be")

        return ret

    def read_network_string(self, frame, start_offset):
        # Only uint32 length supported
        size_stop = start_offset + self.network_len_size
        data_start = size_stop

        data_length = int.from_bytes(frame[start_offset:size_stop], byteorder="big")
        data_stop = data_start + data_length

        if data_stop > len(frame):
            # Out of bounds
            raise Exception(PyStageLinQError.INVALIDLENGTH)

        return data_stop, frame[data_start:data_stop].decode(encoding="UTF-16be")

    def get_len(self):
        return self.length


class StageLinQDiscovery(StageLinQMessage):
    token: StageLinQToken
    deviceName: str
    connectionType: str
    sw_name: str | type(None)
    sw_version: str | type(None)
    stagelinq_magic_flag = bytes("airD".encode(encoding="ASCII"))

    def __init__(self):
        self.Port = None
        self.sw_version = None
        self.sw_name = None
        self.device_name = None
        self.connection_type = None
        self.token = StageLinQToken()
        self.length = 0
        self.min_length = (
            self.magic_flag_length + StageLinQToken.TOKENLENGTH + self.network_len_size
        )

    def encode_frame(self, discovery_data: StageLinQDiscoveryData) -> bytes:
        if self.verify_discovery_data(discovery_data) != PyStageLinQError.STAGELINQOK:
            return PyStageLinQError.INVALIDDISCOVERYDATA

        discovery_frame = self.stagelinq_magic_flag
        discovery_frame += discovery_data.Token.get_token().to_bytes(
            StageLinQToken.TOKENLENGTH, byteorder="big"
        )
        discovery_frame += self.write_network_string(discovery_data.DeviceName)
        discovery_frame += self.write_network_string(discovery_data.ConnectionType)
        discovery_frame += self.write_network_string(discovery_data.SwName)
        discovery_frame += self.write_network_string(discovery_data.SwVersion)
        discovery_frame += discovery_data.ReqServicePort.to_bytes(
            self.port_length, byteorder="big"
        )

        return discovery_frame

    @staticmethod
    def verify_discovery_data(discovery_data) -> StageLinQDiscoveryData:
        ret = PyStageLinQError.STAGELINQOK
        if (0 > discovery_data.ReqServicePort) or (
            65535 < discovery_data.ReqServicePort
        ):
            ret = PyStageLinQError.INVALIDDISCOVERYDATA
        return ret

    def get(self):
        return StageLinQDiscoveryData(
            self.token,
            self.device_name,
            self.connection_type,
            self.sw_name,
            self.sw_version,
            self.Port,
        )

    def decode_frame(self, frame):
        if len(frame) < self.min_length:
            return PyStageLinQError.INVALIDFRAME

        # Local Constants
        token_start = self.magic_flag_stop
        token_length = StageLinQToken.TOKENLENGTH
        token_stop = token_start + token_length
        device_name_size_start = token_stop

        # Check if Frame contains Magic flag
        if (
            self.stagelinq_magic_flag
            != frame[self.magic_flag_start : self.magic_flag_stop]
        ):
            return PyStageLinQError.MAGICFLAGNOTFOUND

        self.token.set_token(
            int.from_bytes(frame[token_start:token_stop], byteorder="big")
        )

        try:
            connection_type_start, self.device_name = self.read_network_string(
                frame, device_name_size_start
            )

            sw_name_start, self.connection_type = self.read_network_string(
                frame, connection_type_start
            )

            sw_version_start, self.sw_name = self.read_network_string(
                frame, sw_name_start
            )
            port_start, self.sw_version = self.read_network_string(
                frame, sw_version_start
            )

        except Exception as e:
            if str(e) == str(PyStageLinQError.INVALIDLENGTH):
                return PyStageLinQError.INVALIDLENGTH
            else:
                raise e

        port_stop = port_start + self.port_length

        if len(frame) < port_stop:
            return PyStageLinQError.INVALIDLENGTH

        self.Port = int.from_bytes(frame[port_start:port_stop], byteorder="big")
        self.length = port_stop
        return PyStageLinQError.STAGELINQOK


class StageLinQServiceAnnouncement(StageLinQMessage):
    Token: StageLinQToken | type(None)
    Service: str | type(None)
    Port: int | type(None)

    def __init__(self):
        self.Token = StageLinQToken()
        self.Service = None
        self.Port = None
        self.length = None

        self.min_length = (
            self.magic_flag_length + StageLinQToken.TOKENLENGTH + self.network_len_size
        )

    def encode_frame(
        self, service_announcement_data: StageLinQServiceAnnouncementData
    ) -> bytes:
        request_frame = StageLinQMessageIDs.StageLinQServiceAnnouncementData
        request_frame += service_announcement_data.Token.get_token().to_bytes(
            StageLinQToken.TOKENLENGTH, byteorder="big"
        )
        request_frame += self.write_network_string(service_announcement_data.Service)
        request_frame += service_announcement_data.Port.to_bytes(2, byteorder="big")
        return request_frame

    def decode_frame(self, frame):
        if len(frame) < self.min_length:
            return PyStageLinQError.INVALIDLENGTH

        # Verify frame type
        if (
            frame[self.magic_flag_start : self.magic_flag_stop]
            != StageLinQMessageIDs.StageLinQServiceAnnouncementData
        ):
            return PyStageLinQError.INVALIDFRAME

        token_start = self.magic_flag_stop
        token_stop = token_start + StageLinQToken.TOKENLENGTH
        service_name_start = token_stop

        self.Token.set_token(
            (0).from_bytes(frame[token_start:token_stop], byteorder="big")
        )

        try:
            port_start, self.Service = self.read_network_string(
                frame, service_name_start
            )
        except Exception as e:
            if str(e) == str(PyStageLinQError.INVALIDLENGTH):
                return PyStageLinQError.INVALIDLENGTH
            else:
                raise e

        port_stop = port_start + self.port_length

        if len(frame) < port_stop:
            return PyStageLinQError.INVALIDLENGTH

        self.Port = int.from_bytes(frame[port_start:port_stop], byteorder="big")
        self.length = port_stop
        return PyStageLinQError.STAGELINQOK

    def get(self):
        return StageLinQServiceAnnouncementData(
            Token=self.Token, Service=self.Service, Port=self.Port
        )


class StageLinQReference(StageLinQMessage):
    OwnToken: StageLinQToken | type(None)
    DeviceToken: StageLinQToken | type(None)
    Reference: int | type(None)

    def __init__(self):
        self.OwnToken = StageLinQToken()
        self.DeviceToken = StageLinQToken()
        self.Reference = None
        self.length = (
            self.magic_flag_length + StageLinQToken.TOKENLENGTH * 2 + self.reference_len
        )

    @staticmethod
    def encode_frame(reference_data) -> StageLinQReferenceData:
        request_frame = StageLinQMessageIDs.StageLinQReferenceData
        request_frame += reference_data.OwnToken.get_token().to_bytes(
            StageLinQToken.TOKENLENGTH, byteorder="big"
        )
        request_frame += 0x00.to_bytes(StageLinQToken.TOKENLENGTH, byteorder="big")
        request_frame += reference_data.Reference.to_bytes(8, byteorder="big")
        return request_frame

    def decode_frame(self, frame):
        if len(frame) < self.length:
            return PyStageLinQError.INVALIDLENGTH

        # Verify frame type
        if (
            frame[self.magic_flag_start : self.magic_flag_stop]
            != StageLinQMessageIDs.StageLinQReferenceData
        ):
            return PyStageLinQError.INVALIDFRAME

        own_token_start = self.magic_flag_stop
        own_token_stop = own_token_start + StageLinQToken.TOKENLENGTH
        device_token_start = own_token_stop
        device_token_stop = device_token_start + StageLinQToken.TOKENLENGTH
        reference_start = device_token_stop
        reference_stop = reference_start + self.reference_len

        self.OwnToken.set_token(
            (0).from_bytes(frame[own_token_start:own_token_stop], byteorder="big")
        )

        token_id = (0).from_bytes(
            frame[device_token_start:device_token_stop], byteorder="big"
        )

        if token_id != 0:
            self.DeviceToken.set_token(token_id)
        self.Reference = int.from_bytes(
            frame[reference_start:reference_stop], byteorder="big"
        )
        return PyStageLinQError.STAGELINQOK

    def get(self):
        return StageLinQReferenceData(
            OwnToken=self.OwnToken,
            DeviceToken=self.DeviceToken,
            Reference=self.Reference,
        )


class StageLinQRequestServices(StageLinQMessage):
    Token: StageLinQToken

    length = 4 + StageLinQToken.TOKENLENGTH

    def __init__(self):
        self.Token = StageLinQToken()

    @staticmethod
    def encode_frame(service_request_data) -> StageLinQServiceRequestService:
        request_frame = StageLinQMessageIDs.StageLinQServiceRequestData
        request_frame += service_request_data.Token.get_token().to_bytes(
            StageLinQToken.TOKENLENGTH, byteorder="big"
        )
        return request_frame

    def decode_frame(self, frame):
        # Verify frame
        if len(frame) < self.length:
            return PyStageLinQError.INVALIDLENGTH
        if (
            frame[self.magic_flag_start : self.magic_flag_stop]
            != StageLinQMessageIDs.StageLinQServiceRequestData
        ):
            return PyStageLinQError.INVALIDFRAME

        token_start = self.magic_flag_stop
        token_stop = token_start + StageLinQToken.TOKENLENGTH

        self.Token = frame[token_start:token_stop]
        return PyStageLinQError.STAGELINQOK

    def get(self):
        return StageLinQServiceRequestService(Token=self.Token)
