import pytest
import PyStageLinQ.Network


from PyStageLinQ.ErrorCodes import PyStageLinQError
from pytest import MonkeyPatch

import random

# initialize random values as init
ip_dummy = ".".join(map(str, (random.randint(0, 255)
                        for _ in range(4))))


def somecallback():
    pass


@pytest.fixture()
def StageLinQService():
    """discovery_frame = "airD"
    discovery_frame += "1234567890123456"
    discovery_frame += "airD"
    discovery_frame += "airD"
    discovery_frame += "airD"
    discovery_frame += "airD"
    discovery_frame += "airD"
    """
    """
    discovery_frame += WriteNetworkString(discovery_data.DeviceName)
    discovery_frame += WriteNetworkString(discovery_data.ConnectionType)
    discovery_frame += WriteNetworkString(discovery_data.SwName)
    discovery_frame += WriteNetworkString(discovery_data.SwVersion)
    discovery_frame += ReqServicePort.to_bytes(self.port_length, byteorder='big')"""

    #return PyStageLinQ.Network.StageLinQService(ip_dummy, discovery_frame, random.randbytes(16), somecallback)

