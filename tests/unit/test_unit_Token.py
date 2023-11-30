import pytest
import PyStageLinQ.Token

from PyStageLinQ.ErrorCodes import PyStageLinQError


@pytest.fixture()
def token():
    return PyStageLinQ.Token.StageLinQToken()


def test_init_value(token):
    assert token.get_token() == 0


def test__get_randomized_bytes_length(token):
    test_lengths = [16, 8, 1, 100, 3, 24, 4]

    for length in test_lengths:
        rand_bytes = token._get_randomized_bytes(length)
        assert len(rand_bytes) == length


def test_generate_token_zero(token, monkeypatch):
    def mock_random_0(length):
        return bytearray((0).to_bytes(length, "big"))

    monkeypatch.setattr(token, "_get_randomized_bytes", mock_random_0)

    token.generate_token()
    assert token.get_token() == 0


def test_generate_token_msb1(token, monkeypatch):
    def mock_random_msb1(length):
        return bytearray(
            int("80000000000000000000000000000001", length).to_bytes(length, "big")
        )

    monkeypatch.setattr(token, "_get_randomized_bytes", mock_random_msb1)

    token.generate_token()
    assert token.get_token() == 1


def test_set_token_wrong_input_type(token):
    # test type
    testValue = None
    with pytest.raises(Exception):
        token.set_token(testValue)


def test_set_token_valid_input(token, monkeypatch):
    def ret_ok(_):
        return PyStageLinQError.STAGELINQOK

    monkeypatch.setattr(token, "validate_token", ret_ok)
    testValue = 0
    token.set_token(testValue)
    assert token.get_token() == testValue


def test_set_token_invalid_input_value(token, monkeypatch):
    def ret_nok(_):
        return PyStageLinQError.INVALIDTOKEN

    testValue = 0
    monkeypatch.setattr(token, "validate_token", ret_nok)
    with pytest.raises(Exception):
        assert token.set_token(testValue)


def test_validate_token_ok(token):
    token.generate_token()
    good_value = token.get_token()

    goodResult = token.validate_token(good_value)

    assert goodResult == PyStageLinQError.STAGELINQOK


def test_validate_token_invalid_length(token):
    badValue = int("800000000000000000000000000000000", 17)
    badResult = token.validate_token(badValue)

    assert badResult == PyStageLinQError.INVALIDTOKENLENGTH


def test_validate_token_invalid_value(token, monkeypatch):
    badValue = int("-1", 16)
    badResult = token.validate_token(badValue)

    assert badResult == PyStageLinQError.INVALIDTOKEN
