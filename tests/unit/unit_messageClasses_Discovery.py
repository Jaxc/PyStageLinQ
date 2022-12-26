import pytest
import PyStageLinQ.MessageClasses
import PyStageLinQ.Token
import PyStageLinQ.DataClasses
import random

from PyStageLinQ.ErrorCodes import PyStageLinQError
from pytest import MonkeyPatch


device_name_dummy = "AAAA"
connection_type_dummy = "BBBB"
sw_name_dummy = "CCCC"
sw_version_dummy = "DDDD"

@pytest.fixture()
def dummyPort():
    return random.randint(1, 65535)

@pytest.fixture()
def dummyToken():
    return PyStageLinQ.Token.StageLinQToken()


@pytest.fixture()
def StageLinQDiscovery():
    return PyStageLinQ.MessageClasses.StageLinQDiscovery()


def test_init_values(StageLinQDiscovery):
    assert StageLinQDiscovery.Port is None
    assert StageLinQDiscovery.sw_version is None
    assert StageLinQDiscovery.sw_name is None
    assert StageLinQDiscovery.device_name is None
    assert StageLinQDiscovery.connection_type is None
    assert type(StageLinQDiscovery.token) is PyStageLinQ.Token.StageLinQToken
    assert StageLinQDiscovery.token.get_token() == 0
    assert StageLinQDiscovery.length == 0
    assert StageLinQDiscovery.port_length == 2
    assert StageLinQDiscovery.magic_flag_start == 0
    assert StageLinQDiscovery.magic_flag_length == 4
    assert StageLinQDiscovery.magic_flag_stop == 4
    assert StageLinQDiscovery.network_len_size == 4
    assert StageLinQDiscovery.reference_len == 8


def test_encodeFrame_invalid_port(StageLinQDiscovery, dummyToken, monkeypatch):

    def verify_discovery_data_mock(string):
        return PyStageLinQError.INVALIDDISCOVERYDATA

    testData = PyStageLinQ.DataClasses.StageLinQDiscoveryData(dummyToken, "", "", "", "",
                                                              -1)
    monkeypatch.setattr(StageLinQDiscovery, 'verify_discovery_data', verify_discovery_data_mock)
    assert StageLinQDiscovery.encodeFrame(testData) == PyStageLinQError.INVALIDDISCOVERYDATA


def test_encodeFrame_valid_input(StageLinQDiscovery, dummyToken, dummyPort, monkeypatch):
    def WriteNetworkString_mock(string):
        return string.encode()

    def verify_discovery_data_mock(string):
        return PyStageLinQError.STAGELINQOK

    monkeypatch.setattr(StageLinQDiscovery, 'WriteNetworkString', WriteNetworkString_mock)
    monkeypatch.setattr(StageLinQDiscovery, 'verify_discovery_data', verify_discovery_data_mock)
    testData = PyStageLinQ.DataClasses.StageLinQDiscoveryData(dummyToken, device_name_dummy, connection_type_dummy, sw_name_dummy, sw_version_dummy,
                                                              dummyPort)
    test_output = StageLinQDiscovery.encodeFrame(testData)

    assert "airD".encode() == test_output[0:4]
    assert dummyToken.get_token().to_bytes(16,byteorder='big') == test_output[4:20]
    assert device_name_dummy.encode() == test_output[20:24]
    assert connection_type_dummy.encode() == test_output[24:28]
    assert sw_name_dummy.encode() == test_output[28:32]
    assert sw_version_dummy.encode() == test_output[32:36]
    assert dummyPort.to_bytes(2,byteorder='big') == test_output[36:38]

def test_verify_discovery_data_wrong_port(StageLinQDiscovery):
    testData = PyStageLinQ.DataClasses.StageLinQDiscoveryData(dummyToken, "", "", "", "",
                                                              -1)

    assert StageLinQDiscovery.verify_discovery_data(testData) == PyStageLinQError.INVALIDDISCOVERYDATA


def test_verify_discovery_data_ok(StageLinQDiscovery, dummyPort):
    testData = PyStageLinQ.DataClasses.StageLinQDiscoveryData(dummyToken, "", "", "", "",
                                                              dummyPort)

    assert StageLinQDiscovery.verify_discovery_data(testData) == PyStageLinQError.STAGELINQOK


def test_verify_get_data(StageLinQDiscovery, dummyPort):

    StageLinQDiscovery.device_name = device_name_dummy
    StageLinQDiscovery.connection_type = connection_type_dummy
    StageLinQDiscovery.sw_name = sw_name_dummy
    StageLinQDiscovery.sw_version = sw_version_dummy
    StageLinQDiscovery.Port = dummyPort


    data = StageLinQDiscovery.get()

    assert type(data.Token) is PyStageLinQ.Token.StageLinQToken
    assert data.Token.get_token() == 0

    assert data.DeviceName == device_name_dummy
    assert data.ConnectionType == connection_type_dummy
    assert data.SwName == sw_name_dummy
    assert data.SwVersion == sw_version_dummy
    assert data.ReqServicePort == dummyPort

def test_decodeFrame_invalid_magic_flag_length(StageLinQDiscovery):

    assert StageLinQDiscovery.decodeFrame(random.randbytes(3)) == PyStageLinQError.INVALIDFRAME

def test_decodeFrame_invalid_magic_flag(StageLinQDiscovery):
    assert StageLinQDiscovery.decodeFrame("airJ".encode()) == PyStageLinQError.MAGICFLAGNOTFOUND

def test_decodeFrame_invalid_token_type(StageLinQDiscovery, monkeypatch):

    def set_token_invalid_type(token):
        return PyStageLinQError.INVALIDTOKENTYPE

    monkeypatch.setattr(StageLinQDiscovery.token, "set_token", set_token_invalid_type)

    assert StageLinQDiscovery.decodeFrame("airD".encode()) == PyStageLinQError.INVALIDTOKENTYPE

def test_decodeFrame_invalid_token_length(StageLinQDiscovery, monkeypatch):

    def set_token_invalid(token):
        return PyStageLinQError.INVALIDTOKEN

    monkeypatch.setattr(StageLinQDiscovery.token, "set_token", set_token_invalid)

    assert StageLinQDiscovery.decodeFrame("airD".encode()) == PyStageLinQError.INVALIDTOKEN

def test_decodeFrame_valid_input(StageLinQDiscovery, monkeypatch, dummyPort):

    def ReadNetworkString(frame, start_offset):
        fields = [device_name_dummy, connection_type_dummy, sw_name_dummy, sw_version_dummy, dummyPort]
        return start_offset + 1, fields[start_offset-20]

    def set_token_valid(token):
        return PyStageLinQError.STAGELINQOK

    monkeypatch.setattr(StageLinQDiscovery.token, "set_token", set_token_valid)
    monkeypatch.setattr(StageLinQDiscovery, "ReadNetworkString", ReadNetworkString)

    dummy_frame = bytearray("airD".encode()) + random.randbytes(20) + dummyPort.to_bytes(2, byteorder='big')

    assert StageLinQDiscovery.decodeFrame(dummy_frame) == PyStageLinQError.STAGELINQOK

    assert StageLinQDiscovery.Port == dummyPort
    assert StageLinQDiscovery.sw_version == sw_version_dummy
    assert StageLinQDiscovery.sw_name == sw_name_dummy
    assert StageLinQDiscovery.device_name == device_name_dummy
    assert StageLinQDiscovery.connection_type == connection_type_dummy
    assert type(StageLinQDiscovery.token) is PyStageLinQ.Token.StageLinQToken
    assert StageLinQDiscovery.token.get_token() == 0
    assert StageLinQDiscovery.length == 26

