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
def stagelinq_request_services():
    return PyStageLinQ.MessageClasses.StageLinQRequestServices()


def test_init_values(stagelinq_request_services):
    assert type(stagelinq_request_services.Token) is PyStageLinQ.Token.StageLinQToken
    assert stagelinq_request_services.Token.get_token() == 0
    assert stagelinq_request_services.length == 20
    assert stagelinq_request_services.port_length == 2
    assert stagelinq_request_services.magic_flag_start == 0
    assert stagelinq_request_services.magic_flag_length == 4
    assert stagelinq_request_services.magic_flag_stop == 4
    assert stagelinq_request_services.network_len_size == 4
    assert stagelinq_request_services.reference_len == 8


def test_encode_frame(stagelinq_request_services, dummy_token):
    test_data = PyStageLinQ.DataClasses.StageLinQServiceRequestService(dummy_token)

    test_output = stagelinq_request_services.encode_frame(test_data)

    assert (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceRequestData
        == test_output[0:4]
    )
    assert dummy_token.get_token().to_bytes(16, byteorder="big") == test_output[4:20]


def test_decode_frame_invalid_length(stagelinq_request_services):
    assert (
        stagelinq_request_services.decode_frame(random.randbytes(3))
        == PyStageLinQError.INVALIDLENGTH
    )


def test_decode_frame_invalid_frame_id(stagelinq_request_services):
    assert (
        stagelinq_request_services.decode_frame("airJ".encode() + random.randbytes(16))
        == PyStageLinQError.INVALIDFRAME
    )


def test_decode_frame_valid_input(stagelinq_request_services, dummy_token):
    dummy_frame = (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceRequestData
        + dummy_token.get_token().to_bytes(16, byteorder="big")
    )

    assert (
        stagelinq_request_services.decode_frame(dummy_frame)
        == PyStageLinQError.STAGELINQOK
    )

    assert stagelinq_request_services.Token == dummy_token.get_token().to_bytes(
        16, byteorder="big"
    )


def test_verify_get_data(stagelinq_request_services, dummy_token):
    stagelinq_request_services.Token = dummy_token.get_token().to_bytes(
        16, byteorder="big"
    )

    data = stagelinq_request_services.get()

    assert data.Token == dummy_token.get_token().to_bytes(16, byteorder="big")
