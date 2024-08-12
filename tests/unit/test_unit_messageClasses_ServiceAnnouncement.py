import pytest
import PyStageLinQ.MessageClasses
import PyStageLinQ.Token
import PyStageLinQ.DataClasses
import random

from PyStageLinQ.ErrorCodes import PyStageLinQError


@pytest.fixture()
def dummy_token():
    token = PyStageLinQ.Token.StageLinQToken()
    token.generate_token()
    return token


@pytest.fixture()
def dummy_port():
    return random.randint(1, 65535)


@pytest.fixture()
def stagelinq_service_announcement():
    return PyStageLinQ.MessageClasses.StageLinQServiceAnnouncement()


def test_init_values(stagelinq_service_announcement):
    assert (
        type(stagelinq_service_announcement.Token) is PyStageLinQ.Token.StageLinQToken
    )
    assert stagelinq_service_announcement.Service is None
    assert stagelinq_service_announcement.Port is None
    assert stagelinq_service_announcement.length is None
    assert stagelinq_service_announcement.port_length == 2
    assert stagelinq_service_announcement.magic_flag_start == 0
    assert stagelinq_service_announcement.magic_flag_length == 4
    assert stagelinq_service_announcement.magic_flag_stop == 4
    assert stagelinq_service_announcement.network_len_size == 4
    assert stagelinq_service_announcement.reference_len == 8


def test_encode_frame_valid_input(
    stagelinq_service_announcement, dummy_token, dummy_port, monkeypatch
):
    def write_network_string_mock(string):
        return string.encode()

    monkeypatch.setattr(
        stagelinq_service_announcement,
        "write_network_string",
        write_network_string_mock,
    )

    service = "Yes please!"
    test_data = PyStageLinQ.DataClasses.StageLinQServiceAnnouncementData(
        dummy_token, service, dummy_port
    )

    test_output = stagelinq_service_announcement.encode_frame(test_data)

    assert (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceAnnouncementData
        == test_output[0:4]
    )
    assert dummy_token.get_token().to_bytes(16, byteorder="big") == test_output[4:20]
    assert service.encode() == test_output[20:31]
    assert dummy_port.to_bytes(2, byteorder="big") == test_output[31:33]


def test_decode_frame_invalid_length(stagelinq_service_announcement):
    assert (
        stagelinq_service_announcement.decode_frame(random.randbytes(3))
        == PyStageLinQError.INVALIDLENGTH
    )


def test_decode_frame_invalid_frame_id(stagelinq_service_announcement):
    assert (
        stagelinq_service_announcement.decode_frame(("airJ" * 20).encode())
        == PyStageLinQError.INVALIDFRAME
    )


def test_decode_frame_invalid_network_string_length(
    stagelinq_service_announcement, monkeypatch, dummy_token, dummy_port
):
    def read_invalid_network_string(arg1, arg2):
        raise Exception(PyStageLinQError.INVALIDLENGTH)

    test_string = "hello"

    dummy_frame = (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceAnnouncementData
        + dummy_token.get_token().to_bytes(16, byteorder="big")
        + test_string.encode(encoding="UTF-16be")
        + dummy_port.to_bytes(2, byteorder="big")
    )

    monkeypatch.setattr(
        stagelinq_service_announcement,
        "read_network_string",
        read_invalid_network_string,
    )

    assert (
        stagelinq_service_announcement.decode_frame(dummy_frame)
        == PyStageLinQError.INVALIDLENGTH
    )


def test_decode_frame_network_string_length_error(
    stagelinq_service_announcement, monkeypatch, dummy_token, dummy_port
):
    def read_invalid_network_string(arg1, arg2):
        raise ValueError

    test_string = "hello"

    dummy_frame = (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceAnnouncementData
        + dummy_token.get_token().to_bytes(16, byteorder="big")
        + test_string.encode(encoding="UTF-16be")
        + dummy_port.to_bytes(2, byteorder="big")
    )

    monkeypatch.setattr(
        stagelinq_service_announcement,
        "read_network_string",
        read_invalid_network_string,
    )

    with pytest.raises(Exception):
        stagelinq_service_announcement.decode_frame(dummy_frame)


def test_decode_frame_valid_input(
    stagelinq_service_announcement, dummy_token, dummy_port, monkeypatch
):
    test_string = "hello"

    def read_network_string_mock(_, start_offset):
        fields = [dummy_token.get_token(), test_string, dummy_port]
        return start_offset + 10, fields[start_offset - 20]

    monkeypatch.setattr(
        stagelinq_service_announcement, "read_network_string", read_network_string_mock
    )

    dummy_frame = (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceAnnouncementData
        + dummy_token.get_token().to_bytes(16, byteorder="big")
        + test_string.encode(encoding="UTF-16be")
        + dummy_port.to_bytes(2, byteorder="big")
    )

    assert (
        stagelinq_service_announcement.decode_frame(dummy_frame)
        == PyStageLinQError.STAGELINQOK
    )

    assert stagelinq_service_announcement.Token.get_token() == dummy_token.get_token()
    assert stagelinq_service_announcement.Port.to_bytes(
        2, byteorder="big"
    ) == dummy_port.to_bytes(2, byteorder="big")

    assert stagelinq_service_announcement.get_len() == 32


def test_decode_port_to_short(
    stagelinq_service_announcement, dummy_token, dummy_port, monkeypatch
):
    test_string = "hello"

    def read_network_string_mock(_, start_offset):
        fields = [dummy_token.get_token(), test_string, dummy_port]
        return start_offset + 10, fields[start_offset - 20]

    monkeypatch.setattr(
        stagelinq_service_announcement, "read_network_string", read_network_string_mock
    )

    dummy_frame = (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceAnnouncementData
        + dummy_token.get_token().to_bytes(16, byteorder="big")
        + test_string.encode(encoding="UTF-16be")
        + (20).to_bytes(1, byteorder="big")
    )

    assert (
        stagelinq_service_announcement.decode_frame(dummy_frame)
        == PyStageLinQError.INVALIDLENGTH
    )


def test_verify_get_data(stagelinq_service_announcement, dummy_token, dummy_port):
    test_string = "hello"

    stagelinq_service_announcement.Token = dummy_token.get_token().to_bytes(
        16, byteorder="big"
    )
    stagelinq_service_announcement.Service = test_string
    stagelinq_service_announcement.Port = dummy_port

    data = stagelinq_service_announcement.get()

    assert data.Token == dummy_token.get_token().to_bytes(16, byteorder="big")
    assert data.Service == test_string
    assert data.Port == dummy_port
