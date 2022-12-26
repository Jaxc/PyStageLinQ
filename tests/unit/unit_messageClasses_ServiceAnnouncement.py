import pytest
import PyStageLinQ.MessageClasses
import PyStageLinQ.Token
import PyStageLinQ.DataClasses
import random

from PyStageLinQ.ErrorCodes import PyStageLinQError
from pytest import MonkeyPatch

@pytest.fixture()
def dummyToken():
    token = PyStageLinQ.Token.StageLinQToken()
    token.generate_token()
    return token

@pytest.fixture()
def dummyPort():
    return random.randint(1, 65535)

@pytest.fixture()
def StageLinQServiceAnnouncement():
    return PyStageLinQ.MessageClasses.StageLinQServiceAnnouncement()


def test_init_values(StageLinQServiceAnnouncement):
    assert StageLinQServiceAnnouncement.Token is None
    assert StageLinQServiceAnnouncement.Service is None
    assert StageLinQServiceAnnouncement.Port is None
    assert StageLinQServiceAnnouncement.length is None
    assert StageLinQServiceAnnouncement.port_length == 2
    assert StageLinQServiceAnnouncement.magic_flag_start == 0
    assert StageLinQServiceAnnouncement.magic_flag_length == 4
    assert StageLinQServiceAnnouncement.magic_flag_stop == 4
    assert StageLinQServiceAnnouncement.network_len_size == 4
    assert StageLinQServiceAnnouncement.reference_len == 8


def test_encodeFrame_valid_input(StageLinQServiceAnnouncement, dummyToken, dummyPort, monkeypatch):

    def WriteNetworkString_mock(string):
        return string.encode()

    monkeypatch.setattr(StageLinQServiceAnnouncement, 'WriteNetworkString', WriteNetworkString_mock)

    service = "Yes please!"
    testData = PyStageLinQ.DataClasses.StageLinQServiceAnnouncementData(dummyToken, service, dummyPort)

    test_output = StageLinQServiceAnnouncement.encodeFrame(testData)

    assert PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceAnnouncementData == test_output[0:4]
    assert dummyToken.get_token().to_bytes(16,byteorder='big') == test_output[4:20]
    assert service.encode() == test_output[20:31]
    assert dummyPort.to_bytes(2, byteorder='big') == test_output[31:33]

def test_decodeFrame_invalid_magic_flag_length(StageLinQServiceAnnouncement):
    assert StageLinQServiceAnnouncement.decodeFrame(random.randbytes(3)) == PyStageLinQError.INVALIDFRAME

def test_decodeFrame_invalid_frame_ID(StageLinQServiceAnnouncement):
    assert StageLinQServiceAnnouncement.decodeFrame("airJ".encode()) == PyStageLinQError.INVALIDFRAME

def test_decodeFrame_valid_input(StageLinQServiceAnnouncement, dummyToken, dummyPort, monkeypatch):

    testString = "hello"

    def ReadNetworkString_mock(frame, start_offset):
        fields = [dummyToken.get_token(), testString, dummyPort]
        return start_offset + 10, fields[start_offset-20]


    monkeypatch.setattr(StageLinQServiceAnnouncement, 'ReadNetworkString', ReadNetworkString_mock)

    dummy_frame = PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceAnnouncementData + \
                  dummyToken.get_token().to_bytes(16, byteorder='big') + \
                  testString.encode(encoding='UTF-16be') + \
                  dummyPort.to_bytes(2, byteorder='big')

    assert StageLinQServiceAnnouncement.decodeFrame(dummy_frame) == PyStageLinQError.STAGELINQOK

    assert StageLinQServiceAnnouncement.Token == dummyToken.get_token().to_bytes(16, byteorder='big')
    assert StageLinQServiceAnnouncement.Port.to_bytes(2, byteorder='big') == dummyPort.to_bytes(2, byteorder='big')

    assert StageLinQServiceAnnouncement.get_len() == 32

def test_verify_get_data(StageLinQServiceAnnouncement, dummyToken, dummyPort):
    testString = "hello"

    StageLinQServiceAnnouncement.Token = dummyToken.get_token().to_bytes(16, byteorder='big')
    StageLinQServiceAnnouncement.Service = testString
    StageLinQServiceAnnouncement.Port = dummyPort


    data = StageLinQServiceAnnouncement.get()

    assert data.Token == dummyToken.get_token().to_bytes(16, byteorder='big')
    assert data.Service == testString
    assert data.Port == dummyPort