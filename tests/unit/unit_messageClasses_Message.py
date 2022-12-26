import pytest
import PyStageLinQ.MessageClasses
import PyStageLinQ.Token
import PyStageLinQ.DataClasses
import random

from PyStageLinQ.ErrorCodes import PyStageLinQError
from pytest import MonkeyPatch



@pytest.fixture()
def StageLinQMessage():
    return PyStageLinQ.MessageClasses.StageLinQMessage()


def test_init_values(StageLinQMessage):
    assert StageLinQMessage.port_length == 2
    assert StageLinQMessage.magic_flag_start == 0
    assert StageLinQMessage.magic_flag_length == 4
    assert StageLinQMessage.magic_flag_stop == 4
    assert StageLinQMessage.network_len_size == 4
    assert StageLinQMessage.reference_len == 8


def test_writeNetworkString(StageLinQMessage):

    testData = "hello"

    testOutput = StageLinQMessage.WriteNetworkString(testData)

    assert (10).to_bytes(4, byteorder='big') == testOutput[0:4]
    assert testData.encode(encoding='UTF-16be') == testOutput[4:14]


def test_ReadNetworkString_incorrect_length(StageLinQMessage):

    testData = (20).to_bytes(4, byteorder='big') + "hello".encode(encoding='UTF-16be')

    assert StageLinQMessage.ReadNetworkString(testData, 0) is None

def test_ReadNetworkString_valid_input(StageLinQMessage):

    testData = (10).to_bytes(4, byteorder='big') + "hello".encode(encoding='UTF-16be') + \
               (14).to_bytes(4, byteorder='big') + "goodbye".encode(encoding='UTF-16be')

    testOutput = StageLinQMessage.ReadNetworkString(testData, 0)

    assert testOutput[0] == 14
    assert testOutput[1] == "hello"


    testOutput = StageLinQMessage.ReadNetworkString(testData, 14)

    assert testOutput[0] == 32
    assert testOutput[1] == "goodbye"

def test_verify_get_len(StageLinQMessage):
    StageLinQMessage.length = 10

    assert StageLinQMessage.get_len() == 10