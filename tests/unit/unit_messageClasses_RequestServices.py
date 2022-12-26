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
def StageLinQRequestServices():
    return PyStageLinQ.MessageClasses.StageLinQRequestServices()


def test_init_values(StageLinQRequestServices):
    assert type(StageLinQRequestServices.Token) is PyStageLinQ.Token.StageLinQToken
    assert StageLinQRequestServices.Token.get_token() == 0
    assert StageLinQRequestServices.length == 20
    assert StageLinQRequestServices.port_length == 2
    assert StageLinQRequestServices.magic_flag_start == 0
    assert StageLinQRequestServices.magic_flag_length == 4
    assert StageLinQRequestServices.magic_flag_stop == 4
    assert StageLinQRequestServices.network_len_size == 4
    assert StageLinQRequestServices.reference_len == 8


def test_encodeFrame(StageLinQRequestServices, dummyToken):
    testData = PyStageLinQ.DataClasses.StageLinQServiceRequestService(dummyToken)

    test_output = StageLinQRequestServices.encodeFrame(testData)

    assert PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceRequestData == test_output[0:4]
    assert dummyToken.get_token().to_bytes(16, byteorder='big') == test_output[4:20]


def test_decodeFrame_invalid_magic_flag_length(StageLinQRequestServices):
    assert StageLinQRequestServices.decodeFrame(random.randbytes(3)) == PyStageLinQError.INVALIDFRAME


def test_decodeFrame_invalid_frame_ID(StageLinQRequestServices):
    assert StageLinQRequestServices.decodeFrame("airJ".encode() + random.randbytes(16)) == PyStageLinQError.INVALIDFRAME


def test_decodeFrame_valid_input(StageLinQRequestServices, dummyToken):
    dummy_frame = PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceRequestData + \
                  dummyToken.get_token().to_bytes(16, byteorder='big')

    assert StageLinQRequestServices.decodeFrame(dummy_frame) == PyStageLinQError.STAGELINQOK

    assert StageLinQRequestServices.Token == dummyToken.get_token().to_bytes(16, byteorder='big')


def test_verify_get_data(StageLinQRequestServices, dummyToken):
    StageLinQRequestServices.Token = dummyToken.get_token().to_bytes(16, byteorder='big')

    data = StageLinQRequestServices.get()

    assert data.Token == dummyToken.get_token().to_bytes(16, byteorder='big')
