import pytest
import PyStageLinQ.MessageClasses
import PyStageLinQ.Token
import PyStageLinQ.DataClasses


@pytest.fixture()
def stagelinq_message():
    return PyStageLinQ.MessageClasses.StageLinQMessage()


def test_init_values(stagelinq_message):
    assert stagelinq_message.port_length == 2
    assert stagelinq_message.magic_flag_start == 0
    assert stagelinq_message.magic_flag_length == 4
    assert stagelinq_message.magic_flag_stop == 4
    assert stagelinq_message.network_len_size == 4
    assert stagelinq_message.reference_len == 8


def test_write_network_string(stagelinq_message):
    test_data = "hello"

    test_output = stagelinq_message.write_network_string(test_data)

    assert (10).to_bytes(4, byteorder="big") == test_output[0:4]
    assert test_data.encode(encoding="UTF-16be") == test_output[4:14]


def test_read_network_string_incorrect_length(stagelinq_message):
    test_data = (20).to_bytes(4, byteorder="big") + "hello".encode(encoding="UTF-16be")

    with pytest.raises(Exception):
        stagelinq_message.read_network_string(test_data, 0)


def test_read_network_string_valid_input(stagelinq_message):
    test_data = (
        (10).to_bytes(4, byteorder="big")
        + "hello".encode(encoding="UTF-16be")
        + (14).to_bytes(4, byteorder="big")
        + "goodbye".encode(encoding="UTF-16be")
    )

    test_output = stagelinq_message.read_network_string(test_data, 0)

    assert test_output[0] == 14
    assert test_output[1] == "hello"

    test_output = stagelinq_message.read_network_string(test_data, 14)

    assert test_output[0] == 32
    assert test_output[1] == "goodbye"


def test_verify_get_len(stagelinq_message):
    stagelinq_message.length = 10

    assert stagelinq_message.get_len() == 10
