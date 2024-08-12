import pytest
import PyStageLinQ.Network
import PyStageLinQ.DataClasses
from unittest.mock import AsyncMock, Mock, MagicMock
from PyStageLinQ.ErrorCodes import PyStageLinQError

import random

# initialize random values as init
ip_dummy = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))


@pytest.fixture()
def token_dummy():
    token = PyStageLinQ.Network.Token.StageLinQToken()
    token.generate_token()
    return token


@pytest.fixture()
def discovery_dummy():
    return MagicMock()


@pytest.fixture()
def dummy_stagelinq_service(discovery_dummy, token_dummy, monkeypatch):
    receive_data_mock = Mock()
    monkeypatch.setattr(
        PyStageLinQ.Network.StageLinQService, "start_receive_data", receive_data_mock
    )

    create_task_mock = Mock()
    monkeypatch.setattr(PyStageLinQ.Network.asyncio, "create_task", create_task_mock)

    return PyStageLinQ.Network.StageLinQService(
        ip_dummy, discovery_dummy, token_dummy, None
    )


def test_init_values(
    dummy_stagelinq_service, discovery_dummy, token_dummy, monkeypatch
):
    assert dummy_stagelinq_service.Socket is None
    assert dummy_stagelinq_service.reference_task is None
    assert dummy_stagelinq_service.reader is None
    assert dummy_stagelinq_service.writer is None
    assert dummy_stagelinq_service.Ip == ip_dummy
    assert dummy_stagelinq_service.Port == discovery_dummy.get().ReqServicePort
    assert dummy_stagelinq_service.OwnToken == token_dummy
    assert type(dummy_stagelinq_service.DeviceToken) is type(
        PyStageLinQ.Token.StageLinQToken()
    )
    assert dummy_stagelinq_service.service_list == []
    assert dummy_stagelinq_service.device_name == discovery_dummy.device_name
    assert dummy_stagelinq_service.device_token == discovery_dummy.token
    assert dummy_stagelinq_service.sw_name == discovery_dummy.sw_name

    dummy_stagelinq_service.receive_task.assert_not_called()

    assert dummy_stagelinq_service.init_complete is False
    assert dummy_stagelinq_service.services_available is False

    assert dummy_stagelinq_service.service_found_callback is None


def test_get_services_no_services(dummy_stagelinq_service):
    assert dummy_stagelinq_service.get_services() is None


def test_get_services_service_list_empty(dummy_stagelinq_service):
    dummy_stagelinq_service.services_available = True
    assert dummy_stagelinq_service.get_services() == []


def test_get_services_service_list_empty(dummy_stagelinq_service):
    service1 = ["AAAA", 1234]
    service2 = ["BBBB", 56789]

    device_name = "CCCC"

    dummy_stagelinq_service.services_available = True
    dummy_stagelinq_service.service_list = [service1, service2]
    dummy_stagelinq_service.device_name = device_name

    test_output = dummy_stagelinq_service.get_services()

    assert test_output[0].device == device_name
    assert test_output[0].ip == ip_dummy
    assert test_output[0].service == service1[0]
    assert test_output[0].port == service1[1]

    assert test_output[1].device == device_name
    assert test_output[1].ip == ip_dummy
    assert test_output[1].service == service2[0]
    assert test_output[1].port == service2[1]


def test_get_init_complete(dummy_stagelinq_service):
    assert dummy_stagelinq_service.get_init_complete() is False

    dummy_stagelinq_service.init_complete = True

    assert dummy_stagelinq_service.get_init_complete() is True


@pytest.mark.asyncio
async def test_get_tasks(dummy_stagelinq_service, monkeypatch):
    get_init_complete = Mock(side_effect=[False, False, True])
    monkeypatch.setattr(dummy_stagelinq_service, "get_init_complete", get_init_complete)

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.Network.asyncio, "sleep", sleep_mock)

    dummy_stagelinq_service.reference_task = Mock()

    test_output = await dummy_stagelinq_service.get_tasks()

    assert test_output[0] == dummy_stagelinq_service.reference_task
    assert test_output[1] == dummy_stagelinq_service.receive_task

    assert sleep_mock.call_count == 2
    assert sleep_mock.mock_calls[0].args[0] == 0.1
    assert sleep_mock.mock_calls[1].args[0] == 0.1


def test_get_services_available(dummy_stagelinq_service):
    assert dummy_stagelinq_service.get_services_available() is False

    dummy_stagelinq_service.services_available = True

    assert dummy_stagelinq_service.get_services_available() is True


@pytest.mark.asyncio
async def test_wait_for_services(dummy_stagelinq_service, monkeypatch):
    get_services_available_mock = Mock(side_effect=[False, False, True])
    monkeypatch.setattr(
        dummy_stagelinq_service, "get_services_available", get_services_available_mock
    )

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.Network.asyncio, "sleep", sleep_mock)

    await dummy_stagelinq_service.wait_for_services()


@pytest.mark.asyncio
async def test_wait_for_services_timeout(dummy_stagelinq_service, monkeypatch):
    get_services_available_mock = Mock(side_effect=[False, False, False, False])
    monkeypatch.setattr(
        dummy_stagelinq_service, "get_services_available", get_services_available_mock
    )

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.Network.asyncio, "sleep", sleep_mock)

    with pytest.raises(RuntimeError) as exception:
        await dummy_stagelinq_service.wait_for_services(timeout=0.02)

    assert exception.value.args[0] == "Timeout occurred before services were received"


@pytest.mark.asyncio
async def test_send_request_frame(dummy_stagelinq_service, monkeypatch, token_dummy):
    class writer_dummy:
        write = Mock()
        drain = AsyncMock()

    writer = writer_dummy()
    monkeypatch.setattr(dummy_stagelinq_service, "writer", writer)

    await dummy_stagelinq_service.send_request_frame()

    writer.write.assert_called_once_with(
        b"\0\0\0\2" + token_dummy.get_token().to_bytes(16, "big")
    )
    writer.drain.assert_called_once()


@pytest.mark.asyncio
async def test_start_receive_data(dummy_stagelinq_service, monkeypatch):
    monkeypatch.undo()

    class reader:
        read = AsyncMock()

    class writer:
        write = Mock()
        transport = MagicMock()
        drain = AsyncMock()

    writer_mock = writer()
    open_connection_mock = AsyncMock(side_effect=[[reader, writer_mock]])
    create_task_mock = Mock()
    receive_data_loop_mock = AsyncMock()
    send_reference_message_periodically_mock = Mock()
    send_request_frame_mock = Mock()

    monkeypatch.setattr(
        PyStageLinQ.EngineServices.asyncio, "open_connection", open_connection_mock
    )
    monkeypatch.setattr(
        PyStageLinQ.EngineServices.asyncio, "create_task", create_task_mock
    )
    monkeypatch.setattr(
        dummy_stagelinq_service, "_receive_data_loop", receive_data_loop_mock
    )
    monkeypatch.setattr(
        dummy_stagelinq_service,
        "send_reference_message_periodically",
        send_reference_message_periodically_mock,
    )
    monkeypatch.setattr(
        dummy_stagelinq_service, "send_request_frame", send_request_frame_mock
    )

    test_port = 1337
    test_ip = "169.254.13.37"

    dummy_stagelinq_service.Ip = test_ip
    dummy_stagelinq_service.Port = test_port

    await dummy_stagelinq_service.start_receive_data()

    open_connection_mock.assert_called_once_with(test_ip, test_port)
    assert create_task_mock.call_count == 2
    assert dummy_stagelinq_service.init_complete is True
    receive_data_loop_mock.assert_awaited_once()


def test_get_loop_condition(dummy_stagelinq_service):
    assert dummy_stagelinq_service.get_loop_condition() is True

    dummy_stagelinq_service._loopcondition = False

    assert dummy_stagelinq_service.get_loop_condition() is False


@pytest.mark.asyncio
async def test_receive_data_loop(dummy_stagelinq_service, monkeypatch):
    Frame_data = "AAAA"

    receive_frames_mock = AsyncMock(side_effect=[False, Frame_data, False, False])
    handle_frames_mock = AsyncMock(side_effect=[False, Frame_data])
    loop_condition_mock = Mock(side_effect=[True, True, False])

    monkeypatch.setattr(dummy_stagelinq_service, "_receive_frames", receive_frames_mock)
    monkeypatch.setattr(dummy_stagelinq_service, "_handle_frames", handle_frames_mock)
    monkeypatch.setattr(
        dummy_stagelinq_service, "get_loop_condition", loop_condition_mock
    )

    await dummy_stagelinq_service._receive_data_loop()

    assert receive_frames_mock.await_count == 2
    handle_frames_mock.assert_awaited_once_with(Frame_data)
    assert loop_condition_mock.call_count == 3


@pytest.mark.asyncio
async def test_receive_frames_no_response(dummy_stagelinq_service, monkeypatch):
    test_port = 1337
    test_ip = "169.254.13.37"

    class reader:
        read = AsyncMock(side_effect=[[]])

    reader_dummy = reader()

    dummy_stagelinq_service.reader = reader_dummy
    dummy_stagelinq_service.Ip = test_ip
    dummy_stagelinq_service.Port = test_port

    with pytest.raises(RuntimeError) as exception:
        await dummy_stagelinq_service._receive_frames()

    assert (
        exception.value.args[0]
        == f"Remote socket for IP:{test_ip} Port:{test_port} closed!"
    )


@pytest.mark.asyncio
async def test_receive_frames_no_frames(dummy_stagelinq_service, monkeypatch):
    response_data = b"AAAA"

    class reader:
        read = AsyncMock(side_effect=[response_data])

    reader_dummy = reader()
    dummy_stagelinq_service.reader = reader_dummy

    decode_multiframe_mock = Mock(side_effect=[[None, None]])
    monkeypatch.setattr(
        dummy_stagelinq_service, "decode_multiframe", decode_multiframe_mock
    )

    assert await dummy_stagelinq_service._receive_frames() is False
    decode_multiframe_mock.assert_called_once_with(response_data)


@pytest.mark.asyncio
async def test_receive_frames_valid_data(dummy_stagelinq_service, monkeypatch):
    response_data = b"AAAA"
    frames_data = b"BBBB"

    class reader:
        read = AsyncMock(side_effect=[response_data])

    reader_dummy = reader()
    dummy_stagelinq_service.reader = reader_dummy

    decode_multiframe_mock = Mock(side_effect=[[frames_data, None]])
    monkeypatch.setattr(
        dummy_stagelinq_service, "decode_multiframe", decode_multiframe_mock
    )

    assert await dummy_stagelinq_service._receive_frames() == frames_data

    assert dummy_stagelinq_service.last_frame == response_data


@pytest.mark.asyncio
async def test_receive_frames_valid_data_multiframe(
    dummy_stagelinq_service, monkeypatch
):
    response_data = b"AAAA"
    frames_data = b"BBBB"
    remaining_data = b"CCCC"

    class reader:
        read = AsyncMock(side_effect=[response_data])

    reader_dummy = reader()
    dummy_stagelinq_service.reader = reader_dummy

    decode_multiframe_mock = Mock(side_effect=[[frames_data, None]])
    monkeypatch.setattr(
        dummy_stagelinq_service, "decode_multiframe", decode_multiframe_mock
    )

    dummy_stagelinq_service.remaining_data = remaining_data

    assert await dummy_stagelinq_service._receive_frames() == frames_data

    assert dummy_stagelinq_service.last_frame == b"".join(
        [remaining_data, response_data]
    )


@pytest.mark.asyncio
async def test_handle_frames_AnnouncementData(
    dummy_stagelinq_service, monkeypatch, token_dummy
):
    test_service = "AAAA"
    test_port = 1337

    handle_new_services_mock = AsyncMock()
    set_device_token_mock = Mock()

    monkeypatch.setattr(
        dummy_stagelinq_service, "_set_device_token", set_device_token_mock
    )
    monkeypatch.setattr(
        dummy_stagelinq_service, "_handle_new_services", handle_new_services_mock
    )

    test_frame = PyStageLinQ.DataClasses.StageLinQServiceAnnouncementData(
        token_dummy, test_service, test_port
    )
    await dummy_stagelinq_service._handle_frames([test_frame])

    assert dummy_stagelinq_service.service_list == [[test_service, test_port]]

    handle_new_services_mock.assert_called_once()
    set_device_token_mock.assert_called_once_with(test_frame)


@pytest.mark.asyncio
async def test_handle_frames_request_service(
    dummy_stagelinq_service, token_dummy, monkeypatch
):
    handle_new_services_mock = AsyncMock()
    set_device_token_mock = Mock()

    monkeypatch.setattr(
        dummy_stagelinq_service, "_set_device_token", set_device_token_mock
    )
    monkeypatch.setattr(
        dummy_stagelinq_service, "_handle_new_services", handle_new_services_mock
    )

    test_frame = PyStageLinQ.DataClasses.StageLinQServiceRequestService(token_dummy)
    await dummy_stagelinq_service._handle_frames([test_frame])

    assert dummy_stagelinq_service.service_list == []

    set_device_token_mock.assert_called_once_with(test_frame)
    assert handle_new_services_mock.call_count == 0


@pytest.mark.asyncio
async def test_handle_frames_reference_own_frame(
    dummy_stagelinq_service, token_dummy, monkeypatch
):
    handle_new_services_mock = AsyncMock()
    set_device_token_mock = Mock()
    create_task_mock = Mock()
    send_reference_message_mock = Mock()

    monkeypatch.setattr(PyStageLinQ.Network.asyncio, "create_task", create_task_mock)
    monkeypatch.setattr(
        dummy_stagelinq_service, "_set_device_token", set_device_token_mock
    )
    monkeypatch.setattr(
        dummy_stagelinq_service, "_handle_new_services", handle_new_services_mock
    )
    monkeypatch.setattr(
        dummy_stagelinq_service, "send_reference_message", send_reference_message_mock
    )

    test_frame = PyStageLinQ.DataClasses.StageLinQReferenceData(
        token_dummy, token_dummy, 12345
    )
    await dummy_stagelinq_service._handle_frames([test_frame])

    assert dummy_stagelinq_service.service_list == []

    assert set_device_token_mock.call_count == 0
    assert handle_new_services_mock.call_count == 0
    create_task_mock.assert_not_called()


@pytest.mark.asyncio
async def test_handle_frames_reference_other_frame(
    dummy_stagelinq_service, token_dummy, monkeypatch
):
    handle_new_services_mock = AsyncMock()
    set_device_token_mock = Mock()
    create_task_mock = Mock()
    send_reference_message_mock = Mock()

    other_token = PyStageLinQ.Network.Token.StageLinQToken()
    other_token.generate_token()

    monkeypatch.setattr(PyStageLinQ.Network.asyncio, "create_task", create_task_mock)
    monkeypatch.setattr(
        dummy_stagelinq_service, "_set_device_token", set_device_token_mock
    )
    monkeypatch.setattr(
        dummy_stagelinq_service, "_handle_new_services", handle_new_services_mock
    )
    monkeypatch.setattr(
        dummy_stagelinq_service, "send_reference_message", send_reference_message_mock
    )

    test_frame = PyStageLinQ.DataClasses.StageLinQReferenceData(
        other_token, token_dummy, 12345
    )
    await dummy_stagelinq_service._handle_frames([test_frame])

    assert dummy_stagelinq_service.service_list == []

    assert set_device_token_mock.call_count == 0
    assert handle_new_services_mock.call_count == 0
    create_task_mock.assert_called_once_with(send_reference_message_mock())


@pytest.mark.asyncio
async def test_handle_no_frames(dummy_stagelinq_service, token_dummy, monkeypatch):
    handle_new_services_mock = AsyncMock()
    set_device_token_mock = Mock()
    create_task_mock = Mock()
    send_reference_message_mock = Mock()

    monkeypatch.setattr(PyStageLinQ.Network.asyncio, "create_task", create_task_mock)
    monkeypatch.setattr(
        dummy_stagelinq_service, "_set_device_token", set_device_token_mock
    )
    monkeypatch.setattr(
        dummy_stagelinq_service, "_handle_new_services", handle_new_services_mock
    )
    monkeypatch.setattr(
        dummy_stagelinq_service, "send_reference_message", send_reference_message_mock
    )

    test_frame = bytes()
    await dummy_stagelinq_service._handle_frames([test_frame])

    assert dummy_stagelinq_service.service_list == []

    assert set_device_token_mock.call_count == 0
    assert handle_new_services_mock.call_count == 0
    assert create_task_mock.call_count == 0
    assert send_reference_message_mock.call_count == 0


@pytest.mark.asyncio
async def test_handle_new_services_no_callback(dummy_stagelinq_service):
    assert await dummy_stagelinq_service._handle_new_services() is None

    assert dummy_stagelinq_service.services_available is True


@pytest.mark.asyncio
async def test_handle_new_services_callback(dummy_stagelinq_service):
    callback_mock = AsyncMock()

    dummy_stagelinq_service.service_found_callback = callback_mock

    assert await dummy_stagelinq_service._handle_new_services() is None

    assert dummy_stagelinq_service.services_available is True
    callback_mock.assert_called_once_with(dummy_stagelinq_service)


def test_set_device_token_announcement_data(dummy_stagelinq_service, monkeypatch):
    test_service = "AAAA"
    test_port = 1337
    token_value = 64
    token = token_value.to_bytes(16, "big")

    set_device_token_mock = Mock()
    monkeypatch.setattr(
        dummy_stagelinq_service.DeviceToken, "set_token", set_device_token_mock
    )

    test_frame = PyStageLinQ.DataClasses.StageLinQServiceAnnouncementData(
        token, test_service, test_port
    )

    dummy_stagelinq_service._set_device_token(test_frame)

    set_device_token_mock.assert_called_once_with(token_value)


def test_set_device_token_request_service(dummy_stagelinq_service, monkeypatch):
    set_device_token_mock = Mock()
    monkeypatch.setattr(
        dummy_stagelinq_service.DeviceToken, "set_token", set_device_token_mock
    )

    token_value = 64
    token = token_value.to_bytes(16, "big")
    test_frame = PyStageLinQ.DataClasses.StageLinQServiceRequestService(token)

    dummy_stagelinq_service._set_device_token(test_frame)
    set_device_token_mock.assert_called_once_with(token_value)


def test_set_device_token_token_already_set(dummy_stagelinq_service, monkeypatch):
    dummy_stagelinq_service.DeviceToken.token = 1

    set_device_token_mock = Mock()
    monkeypatch.setattr(
        dummy_stagelinq_service.DeviceToken, "set_token", set_device_token_mock
    )

    token_value = 64
    token = token_value.to_bytes(16, "big")
    test_frame = PyStageLinQ.DataClasses.StageLinQServiceRequestService(token)

    dummy_stagelinq_service._set_device_token(test_frame)
    assert set_device_token_mock.call_count == 0


def test_set_device_token_wrong_class(
    dummy_stagelinq_service, monkeypatch, token_dummy
):
    set_device_token_mock = Mock()
    monkeypatch.setattr(
        dummy_stagelinq_service.DeviceToken, "set_token", set_device_token_mock
    )

    test_frame = PyStageLinQ.DataClasses.StageLinQReferenceData(
        token_dummy, token_dummy, 12345
    )

    dummy_stagelinq_service._set_device_token(test_frame)
    assert set_device_token_mock.call_count == 0


@pytest.mark.asyncio
async def test_send_reference_message_periodically_service_not_ready(
    dummy_stagelinq_service, monkeypatch
):
    loop_condition_mock = Mock(side_effect=[True, True, False])
    send_reference_message_mock = AsyncMock()
    sleep_mock = AsyncMock()

    monkeypatch.setattr(
        dummy_stagelinq_service, "get_loop_condition", loop_condition_mock
    )
    monkeypatch.setattr(
        dummy_stagelinq_service, "send_reference_message", send_reference_message_mock
    )
    monkeypatch.setattr(PyStageLinQ.Network.asyncio, "sleep", sleep_mock)

    await dummy_stagelinq_service.send_reference_message_periodically()

    assert send_reference_message_mock.call_count == 0
    assert sleep_mock.await_count == 2


@pytest.mark.asyncio
async def test_send_reference_message_periodically(
    dummy_stagelinq_service, monkeypatch
):
    loop_condition_mock = Mock(side_effect=[True, True, False])
    send_reference_message_mock = AsyncMock()
    sleep_mock = AsyncMock()

    monkeypatch.setattr(
        dummy_stagelinq_service, "get_loop_condition", loop_condition_mock
    )
    monkeypatch.setattr(
        dummy_stagelinq_service, "send_reference_message", send_reference_message_mock
    )
    monkeypatch.setattr(PyStageLinQ.Network.asyncio, "sleep", sleep_mock)
    dummy_stagelinq_service.services_available = True

    await dummy_stagelinq_service.send_reference_message_periodically()

    assert send_reference_message_mock.call_count == 2
    assert sleep_mock.await_count == 2


@pytest.mark.asyncio
async def test_send_refence_message(dummy_stagelinq_service, monkeypatch, token_dummy):
    class writer_dummy:
        write = Mock()
        drain = AsyncMock()

    writer = writer_dummy()
    monkeypatch.setattr(dummy_stagelinq_service, "writer", writer)

    await dummy_stagelinq_service.send_reference_message()

    expected_value = (
        (1).to_bytes(4, byteorder="big")
        + token_dummy.get_token().to_bytes(16, "big")
        + (0).to_bytes(16, byteorder="big")
        + (0).to_bytes(8, byteorder="big")
    )

    writer.write.assert_called_once_with(expected_value)
    writer.drain.assert_called_once()


def test_decode_multiframe_no_frame(dummy_stagelinq_service):
    assert dummy_stagelinq_service.decode_multiframe(bytes()) == ([], None)


def test_decode_multiframe_short_frame(dummy_stagelinq_service):
    assert dummy_stagelinq_service.decode_multiframe(b"0000") == None


def test_decode_multiframe_service_announcement(dummy_stagelinq_service, monkeypatch):
    service = (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceAnnouncementData
        + b"56778"
    )

    frame_data = b"1234"

    class service_announcement_dummy:
        decode_frame = Mock(side_effect=[0])
        get = Mock(side_effect=[frame_data])
        get_len = Mock(side_effect=[10])

    service_announcement_mock = service_announcement_dummy()

    monkeypatch.setattr(
        PyStageLinQ.Network, "StageLinQServiceAnnouncement", service_announcement_dummy
    )

    assert dummy_stagelinq_service.decode_multiframe(service) == ([frame_data], None)

    service_announcement_mock.decode_frame.assert_called_once_with(service)
    service_announcement_mock.get.assert_called_once()
    service_announcement_mock.get_len.assert_called_once()


def test_decode_multiframe_reference(dummy_stagelinq_service, monkeypatch):
    service = (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQReferenceData + b"56778"
    )

    frame_data = b"1234"

    class service_announcement_dummy:
        decode_frame = Mock(side_effect=[0])
        get = Mock(side_effect=[frame_data])
        get_len = Mock(side_effect=[10])

    service_announcement_mock = service_announcement_dummy()

    monkeypatch.setattr(
        PyStageLinQ.Network, "StageLinQReference", service_announcement_dummy
    )

    assert dummy_stagelinq_service.decode_multiframe(service) == ([frame_data], None)

    service_announcement_mock.decode_frame.assert_called_once_with(service)
    service_announcement_mock.get.assert_called_once()
    service_announcement_mock.get_len.assert_called_once()


def test_decode_multiframe_request_service(dummy_stagelinq_service, monkeypatch):
    service = (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceRequestData
        + b"56778"
    )

    frame_data = b"1234"

    class service_announcement_dummy:
        decode_frame = Mock(side_effect=[0])
        get = Mock(side_effect=[frame_data])
        get_len = Mock(side_effect=[10])

    service_announcement_mock = service_announcement_dummy()

    monkeypatch.setattr(
        PyStageLinQ.Network, "StageLinQRequestServices", service_announcement_dummy
    )

    assert dummy_stagelinq_service.decode_multiframe(service) == ([frame_data], None)

    service_announcement_mock.decode_frame.assert_called_once_with(service)
    service_announcement_mock.get.assert_called_once()
    service_announcement_mock.get_len.assert_called_once()


def test_decode_multiframe_invalid_frame_type(dummy_stagelinq_service, monkeypatch):
    service = (-1).to_bytes(4, byteorder="big", signed=True) + b"56778"

    frame_data = b"1234"

    class service_announcement_dummy:
        decode_frame = Mock(side_effect=[0])
        get = Mock(side_effect=[frame_data])
        get_len = Mock(side_effect=[10])

    service_announcement_mock = service_announcement_dummy()

    monkeypatch.setattr(
        PyStageLinQ.Network, "StageLinQRequestServices", service_announcement_dummy
    )

    assert dummy_stagelinq_service.decode_multiframe(service) == None

    assert service_announcement_mock.decode_frame.call_count == 0
    assert service_announcement_mock.get.call_count == 0
    assert service_announcement_mock.get_len.call_count == 0


def test_decode_multiframe_decoding_failed(dummy_stagelinq_service, monkeypatch):
    service = (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceRequestData
        + b"56778"
    )

    frame_data = b"1234"

    class service_announcement_dummy:
        decode_frame = Mock(side_effect=[1])
        get = Mock(side_effect=[frame_data])
        get_len = Mock(side_effect=[10])

    service_announcement_mock = service_announcement_dummy()

    monkeypatch.setattr(
        PyStageLinQ.Network, "StageLinQRequestServices", service_announcement_dummy
    )

    assert dummy_stagelinq_service.decode_multiframe(service) == None

    assert service_announcement_mock.decode_frame.call_count == 1
    assert service_announcement_mock.get.call_count == 0
    assert service_announcement_mock.get_len.call_count == 0


def test_decode_multiframe_decoding_too_short(dummy_stagelinq_service, monkeypatch):
    service = (
        PyStageLinQ.DataClasses.StageLinQMessageIDs.StageLinQServiceRequestData
        + b"56778"
    )

    frame_data = b"1234"

    class service_announcement_dummy:
        decode_frame = Mock(side_effect=[PyStageLinQError.INVALIDLENGTH])
        get = Mock(side_effect=[frame_data])
        get_len = Mock(side_effect=[10])

    service_announcement_mock = service_announcement_dummy()

    monkeypatch.setattr(
        PyStageLinQ.Network, "StageLinQRequestServices", service_announcement_dummy
    )

    assert dummy_stagelinq_service.decode_multiframe(service) == ([], service)

    assert service_announcement_mock.decode_frame.call_count == 1
    assert service_announcement_mock.get.call_count == 0
    assert service_announcement_mock.get_len.call_count == 0
