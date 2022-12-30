"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""

from .Token import *
from dataclasses import dataclass


class StageLinQMessageIDs:
    StageLinQServiceAnnouncementData = (0).to_bytes(4, byteorder="big")
    StageLinQReferenceData = (1).to_bytes(4, byteorder="big")
    StageLinQServiceRequestData = (2).to_bytes(4, byteorder="big")


@dataclass
class StageLinQDiscoveryData:
    Token: StageLinQToken
    DeviceName: str
    ConnectionType: str
    SwName: str
    SwVersion: str
    ReqServicePort: int


@dataclass
class StageLinQServiceAnnouncementData:
    Token: StageLinQToken
    Service: str
    Port: int


@dataclass
class StageLinQReferenceData:
    OwnToken: StageLinQToken
    DeviceToken: StageLinQToken
    Reference: int


@dataclass
class StageLinQServiceRequestService:
    Token: StageLinQToken


@dataclass
class StageLinQStateMapData:
    BlockLength: int
    MagicFlag: str
    MagicFlag2: str
    ParameterLength: int
    ParameterName: str
    ValueLength: int
    ParameterValue: str
