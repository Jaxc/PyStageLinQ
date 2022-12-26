import pytest
import PyStageLinQ.MessageClasses
import PyStageLinQ.Token
import PyStageLinQ.DataClasses
import random

from PyStageLinQ.ErrorCodes import PyStageLinQError
from pytest import MonkeyPatch


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
    device_token = PyStageLinQ.Token.StageLinQToken()
    device_token.generate_token()
    return device_token

@pytest.fixture()
def StageLinQReference():
    return PyStageLinQ.MessageClasses.StageLinQReference()


def test_init_values(StageLinQReference):
    assert StageLinQReference.OwnToken is None
    assert StageLinQReference.DeviceToken is None
    assert StageLinQReference.Reference is None
    assert StageLinQReference.length == 44
    assert StageLinQReference.port_length == 2
    assert StageLinQReference.magic_flag_start == 0
    assert StageLinQReference.magic_flag_length == 4
    assert StageLinQReference.magic_flag_stop == 4
    assert StageLinQReference.network_len_size == 4
    assert StageLinQReference.reference_len == 8


def test_encodeFrame(StageLinQReference, owntoken, devicetoken):

    testData = PyStageLinQ.DataClasses.StageLinQReferenceData(owntoken, devicetoken, 313)

    test_output = StageLinQReference.encodeFrame(testData)

    assert PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQReferenceData == test_output[0:4]
    assert owntoken.get_token().to_bytes(16, byteorder='big') == test_output[4:20]
    assert devicetoken.get_token().to_bytes(16, byteorder='big') == test_output[20:36]
    assert (313).to_bytes(8, byteorder='big') == test_output[36:44]


def test_decodeFrame_invalid_magic_flag_length(StageLinQReference):

    assert StageLinQReference.decodeFrame(random.randbytes(3)) == PyStageLinQError.INVALIDFRAME

def test_decodeFrame_invalid_frame_ID(StageLinQReference):
    assert StageLinQReference.decodeFrame("airJ".encode()) == PyStageLinQError.INVALIDFRAME


def test_decodeFrame_valid_input(StageLinQReference, owntoken, devicetoken):




    dummy_frame = PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQReferenceData + \
                  owntoken.get_token().to_bytes(16, byteorder='big') + \
                  devicetoken.get_token().to_bytes(16, byteorder='big') + (313).to_bytes(8, byteorder='big')

    assert StageLinQReference.decodeFrame(dummy_frame) == PyStageLinQError.STAGELINQOK

    assert StageLinQReference.OwnToken == owntoken.get_token().to_bytes(16, byteorder='big')
    assert StageLinQReference.DeviceToken == devicetoken.get_token().to_bytes(16, byteorder='big')
    assert StageLinQReference.Reference == (313)


def test_verify_get_data(StageLinQReference, owntoken, devicetoken):

    StageLinQReference.OwnToken = owntoken.get_token().to_bytes(16, byteorder='big')
    StageLinQReference.DeviceToken = devicetoken.get_token().to_bytes(16, byteorder='big')
    StageLinQReference.Reference = (313)


    data = StageLinQReference.get()

    assert data.OwnToken == owntoken.get_token().to_bytes(16, byteorder='big')
    assert data.DeviceToken == devicetoken.get_token().to_bytes(16, byteorder='big')
    assert data.Reference == (313)