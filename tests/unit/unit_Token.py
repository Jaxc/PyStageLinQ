import pytest
import PyStageLinQ.Token

from PyStageLinQ.ErrorCodes import PyStageLinQError
from pytest import MonkeyPatch

@pytest.fixture()
def Token():
    return PyStageLinQ.Token.StageLinQToken()



def test_init_value(Token):
    assert Token.get_token() == 0

def test__get_randomized_bytes_length(Token):
    test_lengths = [16, 8, 1, 100, 3, 24, 4]

    for length in test_lengths:
        rand_bytes = Token._get_randomized_bytes(length)
        assert len(rand_bytes) == length

def test_generate_token_zero(Token, monkeypatch):

    def mock_random_0(length):
        return bytearray((0).to_bytes(length,'big'))

    monkeypatch.setattr(Token, "_get_randomized_bytes", mock_random_0)

    Token.generate_token()
    assert Token.get_token() == 0

def test_generate_token_MSb1(Token, monkeypatch):

    def mock_random_MSb1(length):
        return bytearray(int("80000000000000000000000000000001", length).to_bytes(length,'big'))

    monkeypatch.setattr(Token, "_get_randomized_bytes", mock_random_MSb1)

    Token.generate_token()
    assert Token.get_token() == 1

def test_validate_token_ok(Token):

    Token.generate_token()
    goodValue = Token.get_token()

    goodResult = Token.validate_token(goodValue)

    assert goodResult == PyStageLinQError.STAGELINQOK

def test_validate_token_invalid(Token):

    badValue = int("800000000000000000000000000000000", 17)
    badResult = Token.validate_token(badValue)

    assert badResult == PyStageLinQError.INVALIDTOKEN

def test_set_token_wrong_input_type(Token):
    # test type
    testValue = None
    assert Token.set_token((testValue)) == PyStageLinQError.INVALIDTOKENTYPE

def test_set_token_valid_input(Token, monkeypatch):

    def ret_ok(token):
        return PyStageLinQError.STAGELINQOK

    monkeypatch.setattr(Token, "validate_token", ret_ok)
    testValue = 0
    assert Token.set_token((testValue)) == PyStageLinQError.STAGELINQOK
    assert Token.get_token() == testValue

def test_set_token_invalid_input_value(Token, monkeypatch):

    def ret_nok(token):
        return PyStageLinQError.INVALIDTOKEN

    testValue = 0
    monkeypatch.setattr(Token, "validate_token", ret_nok)
    assert Token.set_token((testValue)) == PyStageLinQError.INVALIDTOKEN

