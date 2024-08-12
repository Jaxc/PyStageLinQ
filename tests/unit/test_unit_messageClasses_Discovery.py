import pytest
import PyStageLinQ.MessageClasses
import PyStageLinQ.Token
import PyStageLinQ.DataClasses
import random

from PyStageLinQ.ErrorCodes import PyStageLinQError

device_name_dummy = "AAAA"
connection_type_dummy = "BBBB"
sw_name_dummy = "CCCC"
sw_version_dummy = "DDDD"


@pytest.fixture()
def dummy_port():
    return random.randint(1, 65535)


@pytest.fixture()
def dummy_token():
    return PyStageLinQ.Token.StageLinQToken()


@pytest.fixture()
def stagelinq_discovery():
    return PyStageLinQ.MessageClasses.StageLinQDiscovery()


def test_init_values(stagelinq_discovery):
    assert stagelinq_discovery.Port is None
    assert stagelinq_discovery.sw_version is None
    assert stagelinq_discovery.sw_name is None
    assert stagelinq_discovery.device_name is None
    assert stagelinq_discovery.connection_type is None
    assert type(stagelinq_discovery.token) is PyStageLinQ.Token.StageLinQToken
    assert stagelinq_discovery.token.get_token() == 0
    assert stagelinq_discovery.length == 0
    assert stagelinq_discovery.port_length == 2
    assert stagelinq_discovery.magic_flag_start == 0
    assert stagelinq_discovery.magic_flag_length == 4
    assert stagelinq_discovery.magic_flag_stop == 4
    assert stagelinq_discovery.network_len_size == 4
    assert stagelinq_discovery.reference_len == 8


def test_encode_frame_invalid_port(stagelinq_discovery, dummy_token, monkeypatch):
    def verify_discovery_data_mock(_):
        return PyStageLinQError.INVALIDDISCOVERYDATA

    test_data = PyStageLinQ.DataClasses.StageLinQDiscoveryData(
        dummy_token, "", "", "", "", -1
    )
    monkeypatch.setattr(
        stagelinq_discovery, "verify_discovery_data", verify_discovery_data_mock
    )
    assert (
        stagelinq_discovery.encode_frame(test_data)
        == PyStageLinQError.INVALIDDISCOVERYDATA
    )


def test_encode_frame_valid_input(
    stagelinq_discovery, dummy_token, dummy_port, monkeypatch
):
    def write_network_string_mock(string):
        return string.encode()

    def verify_discovery_data_mock(_):
        return PyStageLinQError.STAGELINQOK

    monkeypatch.setattr(
        stagelinq_discovery, "write_network_string", write_network_string_mock
    )
    monkeypatch.setattr(
        stagelinq_discovery, "verify_discovery_data", verify_discovery_data_mock
    )
    test_data = PyStageLinQ.DataClasses.StageLinQDiscoveryData(
        dummy_token,
        device_name_dummy,
        connection_type_dummy,
        sw_name_dummy,
        sw_version_dummy,
        dummy_port,
    )
    test_output = stagelinq_discovery.encode_frame(test_data)

    assert "airD".encode() == test_output[0:4]
    assert dummy_token.get_token().to_bytes(16, byteorder="big") == test_output[4:20]
    assert device_name_dummy.encode() == test_output[20:24]
    assert connection_type_dummy.encode() == test_output[24:28]
    assert sw_name_dummy.encode() == test_output[28:32]
    assert sw_version_dummy.encode() == test_output[32:36]
    assert dummy_port.to_bytes(2, byteorder="big") == test_output[36:38]


def test_verify_discovery_data_wrong_port(stagelinq_discovery, dummy_token):
    test_data = PyStageLinQ.DataClasses.StageLinQDiscoveryData(
        dummy_token, "", "", "", "", -1
    )

    assert (
        stagelinq_discovery.verify_discovery_data(test_data)
        == PyStageLinQError.INVALIDDISCOVERYDATA
    )


def test_verify_discovery_data_ok(stagelinq_discovery, dummy_token, dummy_port):
    test_data = PyStageLinQ.DataClasses.StageLinQDiscoveryData(
        dummy_token, "", "", "", "", dummy_port
    )

    assert (
        stagelinq_discovery.verify_discovery_data(test_data)
        == PyStageLinQError.STAGELINQOK
    )


def test_verify_get_data(stagelinq_discovery, dummy_port):
    stagelinq_discovery.device_name = device_name_dummy
    stagelinq_discovery.connection_type = connection_type_dummy
    stagelinq_discovery.sw_name = sw_name_dummy
    stagelinq_discovery.sw_version = sw_version_dummy
    stagelinq_discovery.Port = dummy_port

    data = stagelinq_discovery.get()

    assert type(data.Token) is PyStageLinQ.Token.StageLinQToken
    assert data.Token.get_token() == 0

    assert data.DeviceName == device_name_dummy
    assert data.ConnectionType == connection_type_dummy
    assert data.SwName == sw_name_dummy
    assert data.SwVersion == sw_version_dummy
    assert data.ReqServicePort == dummy_port


def test_decode_frame_invalid_magic_flag_length(stagelinq_discovery):
    assert (
        stagelinq_discovery.decode_frame(random.randbytes(3))
        == PyStageLinQError.INVALIDFRAME
    )


def test_decode_frame_invalid_magic_flag(stagelinq_discovery):
    assert (
        stagelinq_discovery.decode_frame(
            "airJ<just some text to fill the frame>".encode()
        )
        == PyStageLinQError.MAGICFLAGNOTFOUND
    )


def test_decode_frame_invalid_network_string_length(stagelinq_discovery, monkeypatch):
    def read_invalid_network_string(arg1, arg2):
        raise Exception(PyStageLinQError.INVALIDLENGTH)

    monkeypatch.setattr(
        stagelinq_discovery, "read_network_string", read_invalid_network_string
    )

    assert (
        stagelinq_discovery.decode_frame(
            "airDtest_decode_frame_invalid_token_length".encode()
        )
        == PyStageLinQError.INVALIDLENGTH
    )


def test_decode_frame_network_string_length_error(stagelinq_discovery, monkeypatch):
    def read_invalid_network_string(arg1, arg2):
        raise ValueError

    monkeypatch.setattr(
        stagelinq_discovery, "read_network_string", read_invalid_network_string
    )

    with pytest.raises(Exception):
        stagelinq_discovery.decode_frame(
            "airDtest_decode_frame_invalid_token_length".encode()
        )


def test_decode_frame_valid_input(stagelinq_discovery, monkeypatch, dummy_port):
    def read_network_string(_, start_offset):
        fields = [
            device_name_dummy,
            connection_type_dummy,
            sw_name_dummy,
            sw_version_dummy,
            dummy_port,
        ]
        return start_offset + 1, fields[start_offset - 20]

    def set_token_valid(_):
        return PyStageLinQError.STAGELINQOK

    monkeypatch.setattr(stagelinq_discovery.token, "set_token", set_token_valid)
    monkeypatch.setattr(stagelinq_discovery, "read_network_string", read_network_string)

    dummy_frame = (
        bytearray("airD".encode())
        + random.randbytes(20)
        + dummy_port.to_bytes(2, byteorder="big")
    )

    assert stagelinq_discovery.decode_frame(dummy_frame) == PyStageLinQError.STAGELINQOK

    assert stagelinq_discovery.Port == dummy_port
    assert stagelinq_discovery.sw_version == sw_version_dummy
    assert stagelinq_discovery.sw_name == sw_name_dummy
    assert stagelinq_discovery.device_name == device_name_dummy
    assert stagelinq_discovery.connection_type == connection_type_dummy
    assert type(stagelinq_discovery.token) is PyStageLinQ.Token.StageLinQToken
    assert stagelinq_discovery.token.get_token() == 0
    assert stagelinq_discovery.length == 26


def test_decode_frame_port_too_short(stagelinq_discovery, monkeypatch, dummy_port):
    def read_network_string(_, start_offset):
        fields = [
            device_name_dummy,
            connection_type_dummy,
            sw_name_dummy,
            sw_version_dummy,
            dummy_port,
        ]
        return start_offset + 1, fields[start_offset - 20]

    def set_token_valid(_):
        return PyStageLinQError.STAGELINQOK

    monkeypatch.setattr(stagelinq_discovery.token, "set_token", set_token_valid)
    monkeypatch.setattr(stagelinq_discovery, "read_network_string", read_network_string)

    dummy_frame = (
        bytearray("airD".encode())
        + random.randbytes(20)
        + (20).to_bytes(1, byteorder="big")
    )

    assert (
        stagelinq_discovery.decode_frame(dummy_frame) == PyStageLinQError.INVALIDLENGTH
    )
