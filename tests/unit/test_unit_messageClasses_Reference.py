import pytest
import PyStageLinQ.MessageClasses
import PyStageLinQ.Token
import PyStageLinQ.DataClasses
import random

from PyStageLinQ.ErrorCodes import PyStageLinQError


service_dummy = "AAAA"
own_token = "BBBB"
device_token = "CCCC"


@pytest.fixture()
def owntoken():
    owntoken = PyStageLinQ.Token.StageLinQToken()
    owntoken.generate_token()
    return owntoken


@pytest.fixture()
def devicetoken():
    devicetoken = PyStageLinQ.Token.StageLinQToken()
    devicetoken.generate_token()
    return devicetoken


@pytest.fixture()
def stagelinq_reference():
    return PyStageLinQ.MessageClasses.StageLinQReference()


def test_init_values(stagelinq_reference):
    assert type(stagelinq_reference.OwnToken) is PyStageLinQ.Token.StageLinQToken
    assert type(stagelinq_reference.DeviceToken) is PyStageLinQ.Token.StageLinQToken
    assert stagelinq_reference.Reference is None
    assert stagelinq_reference.length == 44
    assert stagelinq_reference.port_length == 2
    assert stagelinq_reference.magic_flag_start == 0
    assert stagelinq_reference.magic_flag_length == 4
    assert stagelinq_reference.magic_flag_stop == 4
    assert stagelinq_reference.network_len_size == 4
    assert stagelinq_reference.reference_len == 8


def test_encode_frame(stagelinq_reference, owntoken, devicetoken):
    test_data = PyStageLinQ.DataClasses.StageLinQReferenceData(
        owntoken, devicetoken, 313
    )

    test_output = stagelinq_reference.encode_frame(test_data)

    assert (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQReferenceData
        == test_output[0:4]
    )
    assert owntoken.get_token().to_bytes(16, byteorder="big") == test_output[4:20]
    assert (0).to_bytes(16, byteorder="big") == test_output[20:36]
    assert (313).to_bytes(8, byteorder="big") == test_output[36:44]


def test_decode_frame_invalid_magic_flag_length(stagelinq_reference):
    assert (
        stagelinq_reference.decode_frame(random.randbytes(3))
        == PyStageLinQError.INVALIDLENGTH
    )


def test_decode_frame_invalid_frame_id(stagelinq_reference):
    assert (
        stagelinq_reference.decode_frame(("airJ" * 20).encode())
        == PyStageLinQError.INVALIDFRAME
    )


def test_decode_frame_invalid_token_id(stagelinq_reference, owntoken, devicetoken):
    dummy_frame = (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQReferenceData
        + owntoken.get_token().to_bytes(16, byteorder="big")
        + (0).to_bytes(16, byteorder="big")
        + (313).to_bytes(8, byteorder="big")
    )

    assert stagelinq_reference.decode_frame(dummy_frame) == PyStageLinQError.STAGELINQOK

    assert stagelinq_reference.OwnToken.get_token() == owntoken.get_token()
    assert stagelinq_reference.DeviceToken.get_token() == 0
    assert stagelinq_reference.Reference == 313


def test_decode_frame_valid_input(stagelinq_reference, owntoken, devicetoken):
    dummy_frame = (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQReferenceData
        + owntoken.get_token().to_bytes(16, byteorder="big")
        + devicetoken.get_token().to_bytes(16, byteorder="big")
        + (313).to_bytes(8, byteorder="big")
    )

    assert stagelinq_reference.decode_frame(dummy_frame) == PyStageLinQError.STAGELINQOK

    assert stagelinq_reference.OwnToken.get_token() == owntoken.get_token()
    assert stagelinq_reference.DeviceToken.get_token() == devicetoken.get_token()
    assert stagelinq_reference.Reference == 313


def test_verify_get_data(stagelinq_reference, owntoken, devicetoken):
    stagelinq_reference.OwnToken = owntoken.get_token().to_bytes(16, byteorder="big")
    stagelinq_reference.DeviceToken = devicetoken.get_token().to_bytes(
        16, byteorder="big"
    )
    stagelinq_reference.Reference = 313

    data = stagelinq_reference.get()

    assert data.OwnToken == owntoken.get_token().to_bytes(16, byteorder="big")
    assert data.DeviceToken == devicetoken.get_token().to_bytes(16, byteorder="big")
    assert data.Reference == 313
