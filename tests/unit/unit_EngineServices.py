import pytest
import PyStageLinQ.EngineServices
from unittest.mock import AsyncMock, Mock, MagicMock

device = "AAAA"
service = "BBBB"
state_map_task = "CCCC"
ip = "0.0.0.0"
port = -1
dummy_subscription_list = [0, 1]


@pytest.fixture()
def dummy_engine_services():
    return PyStageLinQ.EngineServices.StateMapSubscription(
        PyStageLinQ.EngineServices.ServiceHandle(device, ip, service, port),
        dummy_subscription_list,
        None,
    )


def set_up_read_mock(dummy_engine_services):
    read_mock = AsyncMock()

    class reader_dummy:
        read = read_mock

    dummy_engine_services.reader = reader_dummy


def test_init_value(dummy_engine_services):
    assert dummy_engine_services.service_handle.device == device
    assert dummy_engine_services.service_handle.ip == ip
    assert dummy_engine_services.service_handle.service == service
    assert dummy_engine_services.service_handle.port == port
    assert dummy_engine_services._callback is None
    assert dummy_engine_services._subscription_list == dummy_subscription_list
    assert dummy_engine_services.reader is None
    assert dummy_engine_services.writer is None
    assert dummy_engine_services.state_map_task is None


def test_get_task(dummy_engine_services):
    dummy_engine_services.state_map_task = state_map_task

    assert dummy_engine_services.get_task() == state_map_task


@pytest.mark.asyncio
async def test_read_state_map_nothing_read(dummy_engine_services):
    read_mock = AsyncMock()

    class reader_dummy:
        read = read_mock

    dummy_engine_services.reader = reader_dummy

    # test for no data:

    read_mock.return_value = bytes()

    assert await dummy_engine_services.read_frame(bytes()) == bytes()
    read_mock.assert_called_once()
    read_mock.assert_awaited_once_with(8192 * 4)

    # test for appending data

    read_value = "Hello"
    trailing_data = " world"

    read_mock.return_value = read_value.encode()

    assert (
        await dummy_engine_services.read_frame(trailing_data.encode())
        == (trailing_data + read_value).encode()
    )


@pytest.mark.asyncio
async def test_read_state_map_no_data_read(dummy_engine_services, monkeypatch):
    read_frame_mock = AsyncMock()

    monkeypatch.setattr(dummy_engine_services, "read_frame", read_frame_mock)

    read_frame_mock.return_value = bytes()

    assert await dummy_engine_services.read_state_map() is None


@pytest.mark.asyncio
async def test_read_state_map_one_entry(dummy_engine_services, monkeypatch):
    trailing_data_value = b"world"

    def decode_frame_side_effect(frame):
        if len(frame.split(None, 1)):
            blocks = frame
        else:
            blocks, frame = frame.split(None, 1)
        trailing_data = trailing_data_value

        return blocks, trailing_data

    read_frame_mock = AsyncMock()
    decode_frame_mock = Mock(side_effect=decode_frame_side_effect)
    handle_data_mock = Mock()

    monkeypatch.setattr(dummy_engine_services, "read_frame", read_frame_mock)
    monkeypatch.setattr(dummy_engine_services, "decode_frame", decode_frame_mock)
    monkeypatch.setattr(dummy_engine_services, "handle_data", handle_data_mock)

    read_frame_mock.side_effect = [b"hello", bytes()]

    assert await dummy_engine_services.read_state_map() is None
    read_frame_mock.assert_awaited()
    assert read_frame_mock.await_count == 2
    assert read_frame_mock.await_args_list[-1].args[0] == trailing_data_value
    decode_frame_mock.assert_called_once()
    handle_data_mock.assert_called_once()


def test_decode_frame_propagate_input_data(dummy_engine_services, monkeypatch):
    decode_multi_block_mock = Mock()
    monkeypatch.setattr(
        dummy_engine_services, "decode_multi_block", decode_multi_block_mock
    )

    input_value = b"hello"

    decode_multi_block_mock.return_value = [bytes()]

    dummy_engine_services.decode_frame(input_value)

    assert decode_multi_block_mock.call_args_list[-1].args[0] == input_value


def test_decode_frame_no_data(dummy_engine_services, monkeypatch):
    decode_multi_block_mock = Mock()
    monkeypatch.setattr(
        dummy_engine_services, "decode_multi_block", decode_multi_block_mock
    )

    decode_multi_block_mock.return_value = [bytes()]

    assert dummy_engine_services.decode_frame(bytes()) == ([], bytes())


def test_decode_frame_short_data(dummy_engine_services, monkeypatch):
    decode_multi_block_mock = Mock()
    monkeypatch.setattr(
        dummy_engine_services, "decode_multi_block", decode_multi_block_mock
    )

    input_data = b"123"

    decode_multi_block_mock.return_value = [input_data]

    assert dummy_engine_services.decode_frame(bytes()) == ([], input_data)


def test_decode_frame_incomplete_frame(dummy_engine_services, monkeypatch):
    decode_multi_block_mock = Mock()
    monkeypatch.setattr(
        dummy_engine_services, "decode_multi_block", decode_multi_block_mock
    )

    input_data = (64).to_bytes(4, "big") + b"hello world"

    decode_multi_block_mock.return_value = [input_data]

    assert dummy_engine_services.decode_frame(bytes()) == ([], input_data)


def test_decode_frame_complete_frame(dummy_engine_services, monkeypatch):
    decode_multi_block_mock = Mock()
    monkeypatch.setattr(
        dummy_engine_services, "decode_multi_block", decode_multi_block_mock
    )

    input_data = (11).to_bytes(4, "big") + b"hello world"

    decode_multi_block_mock.return_value = [input_data]

    assert dummy_engine_services.decode_frame(bytes()) == ([input_data], bytearray())


def test_handle_data_no_blocks_no_callback(dummy_engine_services, monkeypatch):
    verify_block_mock = Mock()
    monkeypatch.setattr(dummy_engine_services, "verify_block", verify_block_mock)

    dummy_engine_services.handle_data([])
    assert verify_block_mock.call_count == 0


def test_handle_data_no_blocks(dummy_engine_services, monkeypatch):
    verify_block_mock = Mock()
    callback_mock = Mock()
    monkeypatch.setattr(dummy_engine_services, "verify_block", verify_block_mock)

    dummy_engine_services._callback = callback_mock

    dummy_engine_services.handle_data([])
    assert verify_block_mock.call_count == 0
    callback_mock.assert_called_once_with([])


def test_handle_data_no_callback(dummy_engine_services, monkeypatch):
    verify_block_mock = Mock()
    monkeypatch.setattr(dummy_engine_services, "verify_block", verify_block_mock)

    input_data = ["aaa", "bbb"]

    dummy_engine_services.handle_data(input_data)
    assert verify_block_mock.call_count == 2
    assert verify_block_mock.call_args_list[0].args[0] == input_data[0]
    assert verify_block_mock.call_args_list[1].args[0] == input_data[1]


def test_handle_data_blocks_and_callback(dummy_engine_services, monkeypatch):
    output_data = ["ccc", "ddd"]

    verify_block_mock = Mock(side_effect=output_data)
    callback_mock = Mock()
    monkeypatch.setattr(dummy_engine_services, "verify_block", verify_block_mock)
    dummy_engine_services._callback = callback_mock

    input_data = ["aaa", "bbb"]

    dummy_engine_services.handle_data(input_data)
    callback_mock.assert_called_once()
    assert callback_mock.call_args_list[0].args[0] == output_data


def test_handle_data_runtime_error_and_callback(dummy_engine_services, monkeypatch):
    output_data = "AAAA"

    verify_block_mock = Mock(side_effect=RuntimeError(output_data))
    callback_mock = Mock()
    monkeypatch.setattr(dummy_engine_services, "verify_block", verify_block_mock)
    dummy_engine_services._callback = callback_mock

    input_data = ["aaa", "bbb"]

    dummy_engine_services.handle_data(input_data)
    callback_mock.assert_called_once()
    assert type(callback_mock.call_args_list[0].args[0]) == type(
        RuntimeError(output_data)
    )
    assert (
        callback_mock.call_args_list[0].args[0].args == RuntimeError(output_data).args
    )


def test_handle_data_runtime_error_and_no_callback(dummy_engine_services, monkeypatch):
    output_data = "BBBB"

    verify_block_mock = Mock(side_effect=RuntimeError(output_data))
    monkeypatch.setattr(dummy_engine_services, "verify_block", verify_block_mock)

    input_data = ["aaa", "bbb"]

    with pytest.raises(RuntimeError) as exception:
        dummy_engine_services.handle_data(input_data)

    assert exception.value.args[0] == output_data


def test_decode_multi_block_no_data(dummy_engine_services):
    assert dummy_engine_services.decode_multi_block(bytes()) == []


def test_decode_multi_block_short_data(dummy_engine_services):
    assert dummy_engine_services.decode_multi_block(bytes("A", "utf-8")) == [
        bytes("A", "utf-8")
    ]


def test_decode_multi_block_valid_data(dummy_engine_services):
    input_data = (
        (11).to_bytes(4, "big") + b"hello world" + (3).to_bytes(4, "big") + b"Bye"
    )
    assert dummy_engine_services.decode_multi_block(input_data) == [
        (11).to_bytes(4, "big") + b"hello world",
        (3).to_bytes(4, "big") + b"Bye",
    ]


def test_verify_block_short_length(dummy_engine_services):
    with pytest.raises(
        RuntimeError,
    ) as exception:
        dummy_engine_services.verify_block(b"123")

    assert exception.value.args[0] == "Block is to short to contain length"


def test_verify_block_length_zero(dummy_engine_services):
    assert dummy_engine_services.verify_block(b"\0\0\0\0") is None


def test_verify_block_invalid_length(dummy_engine_services):
    input_data = bytearray((3).to_bytes(4, "big") + b"smab")

    with pytest.raises(
        RuntimeError,
    ) as exception:
        dummy_engine_services.verify_block(input_data)

    assert (
        exception.value.args[0]
        == "Block invalid: Block length inconsistent with its header"
    )


def test_verify_block_invalid_magic_flag(dummy_engine_services):
    input_data = bytearray((4).to_bytes(4, "big") + b"smab")

    with pytest.raises(
        RuntimeError,
    ) as exception:
        dummy_engine_services.verify_block(input_data)

    assert exception.value.args[0] == "Block invalid: Could not find magic flag"


def test_verify_block_valid_data(dummy_engine_services, monkeypatch):
    magic_flag = b"smaa"
    magic_flag2 = b"\0\0\0\0"
    path = "/test/data".encode(encoding="UTF-16be")
    path_len = len(path).to_bytes(4, "big")
    value = "on".encode(encoding="UTF-16be")
    value_len = len(value).to_bytes(4, "big")

    input_data_blocks = magic_flag + magic_flag2 + path_len + path + value_len + value
    total_len = len(input_data_blocks).to_bytes(4, "big")

    json_load_mock = Mock(side_effect=[value.decode(encoding="UTF-16be")])
    monkeypatch.setattr(PyStageLinQ.EngineServices.json, "loads", json_load_mock)

    input_data = bytearray(total_len + input_data_blocks)

    output_data = dummy_engine_services.verify_block(input_data)

    assert len(input_data_blocks) == output_data.BlockLength
    assert magic_flag.decode() == output_data.MagicFlag
    assert magic_flag2 == output_data.MagicFlag2
    assert (0).from_bytes(path_len, "big") == output_data.ParameterLength
    assert path.decode(encoding="UTF-16be") == output_data.ParameterName
    assert (0).from_bytes(value_len, "big") == output_data.ValueLength
    assert value.decode(encoding="UTF-16be") == output_data.ParameterValue


@pytest.mark.asyncio
async def test_subscribe(dummy_engine_services, monkeypatch):
    class reader:
        read = AsyncMock()

    class writer:
        write = Mock()
        transport = MagicMock()
        drain = AsyncMock()

    writer_mock = writer()

    open_connection_mock = AsyncMock(side_effect=[[reader, writer_mock]])
    create_task_mock = Mock()
    encode_frame_mock = Mock()
    send_subscription_requests_mock = AsyncMock()
    read_state_map_mock = Mock()

    token = MagicMock()

    test_port = 1337
    test_ip = "169.254.13.37"

    dummy_engine_services.service_handle.ip = test_ip
    dummy_engine_services.service_handle.port = test_port
    dummy_engine_services.service_handle.Service = service

    monkeypatch.setattr(
        PyStageLinQ.EngineServices.asyncio, "open_connection", open_connection_mock
    )
    monkeypatch.setattr(
        PyStageLinQ.EngineServices.asyncio, "create_task", create_task_mock
    )
    monkeypatch.setattr(
        dummy_engine_services,
        "_send_subscription_requests",
        send_subscription_requests_mock,
    )
    monkeypatch.setattr(
        dummy_engine_services,
        "read_state_map",
        read_state_map_mock,
    )

    monkeypatch.setattr(
        PyStageLinQ.EngineServices.StageLinQServiceAnnouncement,
        "encode_frame",
        encode_frame_mock,
    )

    await dummy_engine_services.subscribe(token)

    open_connection_mock.assert_called_once_with(test_ip, test_port)
    encode_frame_mock.assert_called_once()
    writer_mock.transport.get_extra_info.assert_called_once_with("sockname")
    encode_frame_mock.assert_called_once_with(
        PyStageLinQ.EngineServices.StageLinQServiceAnnouncementData(
            token, service, writer_mock.transport.get_extra_info().__getitem__()
        )
    )

    writer_mock.drain.assert_awaited_once()
    create_task_mock.assert_called_once()

    send_subscription_requests_mock.assert_called_once()
    read_state_map_mock.assert_called_once()


@pytest.mark.asyncio
async def test_send_subscription_requests(dummy_engine_services, monkeypatch):
    class writer:
        write = Mock()
        drain = AsyncMock()

    writer_mock = writer()

    monkeypatch.setattr(dummy_engine_services, "writer", writer_mock)

    dummy_service_list = {"RootTest1": "/root/test1", "Test2": "/test2"}

    dummy_engine_services._subscription_list = dummy_service_list

    await dummy_engine_services._send_subscription_requests()

    assert writer_mock.write.call_count == 2
    assert writer_mock.drain.call_count == 2

    assert (
        writer_mock.write.mock_calls[0].args[0]
        == b"\x00\x00\x00&smaa\x00\x00\x07\xd2\x00\x00\x00\x16\x00/\x00r\x00o\x00o\x00t\x00/\x00t\x00e\x00s\x00t\x001\x00\x00\x00\x00"
    )
    assert (
        writer_mock.write.mock_calls[1].args[0]
        == b"\x00\x00\x00\x1csmaa\x00\x00\x07\xd2\x00\x00\x00\x0c\x00/\x00t\x00e\x00s\x00t\x002\x00\x00\x00\x00"
    )
