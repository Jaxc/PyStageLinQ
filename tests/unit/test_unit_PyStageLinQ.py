import pytest
import PyStageLinQ.PyStageLinQ
from PyStageLinQ.ErrorCodes import *
from unittest.mock import AsyncMock, Mock, MagicMock
from unittest import mock
from socket import AF_INET

import random

name = "unittest"


@pytest.fixture()
def dummy_ip():
    return ".".join(map(str, (random.randint(0, 255) for _ in range(4))))


@pytest.fixture()
def dummy_port():
    return random.randint(1, 65535)


@pytest.fixture()
def dummy_socket():
    return MagicMock()


@pytest.fixture()
def dummy_pystagelinq(dummy_ip):
    return PyStageLinQ.PyStageLinQ.PyStageLinQ(None, name=name, ip=dummy_ip)


@pytest.fixture(autouse=True)
def ensure_cleanup(dummy_socket):
    """Ensure that everything is cleaned up between tests."""
    yield

    # Force garbage collection to trigger __del__ if necessary
    import gc

    gc.collect()


def test_init_values(dummy_pystagelinq, dummy_ip):
    assert dummy_pystagelinq.REQUESTSERVICEPORT == 0
    assert dummy_pystagelinq.name == name
    assert dummy_pystagelinq.OwnToken.get_token() != 0
    assert dummy_pystagelinq.discovery_info.Token is dummy_pystagelinq.OwnToken
    assert dummy_pystagelinq.discovery_info.DeviceName == name
    assert dummy_pystagelinq.discovery_info.ConnectionType is "DISCOVERER_HOWDY_"
    assert dummy_pystagelinq.discovery_info.SwName == "Python"
    assert dummy_pystagelinq.discovery_info.SwVersion == "1.0.0"
    assert (
        dummy_pystagelinq.discovery_info.ReqServicePort
        == dummy_pystagelinq.REQUESTSERVICEPORT
    )

    assert (
        type(dummy_pystagelinq.device_list) is PyStageLinQ.PyStageLinQ.Device.DeviceList
    )
    assert dummy_pystagelinq.ip == [dummy_ip]

    assert dummy_pystagelinq.tasks == set()

    assert dummy_pystagelinq.found_services == []
    assert dummy_pystagelinq.new_services_available is False

    assert dummy_pystagelinq.active_services == []

    assert dummy_pystagelinq.devices_with_services_pending_list == []
    assert dummy_pystagelinq.devices_with_services_pending is False
    assert (
        type(dummy_pystagelinq.devices_with_services_lock)
        == PyStageLinQ.PyStageLinQ.asyncio.Lock
    )

    assert dummy_pystagelinq.new_device_found_callback is None


def test_init_values_ip_none(monkeypatch, dummy_socket):
    class ifutils_net_if_addrs:
        def __init__(self, ip=[]):
            self.address = ip
            self.family = AF_INET

    dummy_psutil = MagicMock()
    dummy_ips = {
        "interface1": [ifutils_net_if_addrs(ip="1.2.3.4")],
        "interface2": [ifutils_net_if_addrs(ip="5.6.7.8")],
        "interface3": [ifutils_net_if_addrs(ip="9.10.11.12")],
    }

    dummy_ips["interface3"][0].family = None

    dummy_psutil.net_if_addrs.return_value = dummy_ips
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "psutil", dummy_psutil)

    dummy_pystagelinq = PyStageLinQ.PyStageLinQ.PyStageLinQ(None, ip=None)

    assert dummy_pystagelinq.ip == ["1.2.3.4", "5.6.7.8"]


def test_start_standalone(dummy_pystagelinq, monkeypatch):
    run_mock = Mock()
    start_stagelinq_mock = Mock()

    monkeypatch.setattr(PyStageLinQ.PyStageLinQ.asyncio, "run", run_mock)
    monkeypatch.setattr(dummy_pystagelinq, "_start_stagelinq", start_stagelinq_mock)

    dummy_pystagelinq.start_standalone()

    start_stagelinq_mock.assert_called_once_with(standalone=True)
    run_mock.assert_called_once_with(start_stagelinq_mock(standalone=True))


def test_start(dummy_pystagelinq, monkeypatch):
    start_stagelinq_mock = Mock()

    monkeypatch.setattr(dummy_pystagelinq, "_start_stagelinq", start_stagelinq_mock)

    dummy_pystagelinq.start()

    start_stagelinq_mock.assert_called_once_with()


def test_internal_stop(dummy_pystagelinq, monkeypatch):
    send_discovery_frame_mock = Mock()
    dummy_discovery = PyStageLinQ.PyStageLinQ.StageLinQDiscovery()

    monkeypatch.setattr(
        dummy_pystagelinq, "_send_discovery_frame", send_discovery_frame_mock
    )

    dummy_pystagelinq._stop()

    send_discovery_frame_mock.assert_called_once_with(
        dummy_discovery.encode_frame(
            PyStageLinQ.PyStageLinQ.StageLinQDiscoveryData(
                Token=dummy_pystagelinq.OwnToken,
                DeviceName=dummy_pystagelinq.name,
                ConnectionType="DISCOVERER_EXIT_",
                SwName="Python",
                SwVersion="1.0.0",
                ReqServicePort=dummy_pystagelinq.REQUESTSERVICEPORT,
            )
        )
    )


def test_announce_self(dummy_pystagelinq, monkeypatch):
    send_discovery_frame_mock = Mock()
    dummy_discovery = PyStageLinQ.PyStageLinQ.StageLinQDiscovery()

    monkeypatch.setattr(
        dummy_pystagelinq, "_send_discovery_frame", send_discovery_frame_mock
    )

    dummy_pystagelinq._announce_self()

    send_discovery_frame_mock.assert_called_once_with(
        dummy_discovery.encode_frame(dummy_pystagelinq.discovery_info)
    )


def test_send_discovery_frame(dummy_pystagelinq, monkeypatch, dummy_socket):

    dummy_discovery_frame = "AAAA"

    discovery_socket = MagicMock()

    dummy_socket.socket.side_effect = discovery_socket

    dummy_socket.getaddrinfo.side_effect = [[["255.255.255.255"]]]

    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "socket", dummy_socket)

    dummy_pystagelinq._send_discovery_frame(dummy_discovery_frame)

    dummy_socket.socket.assert_called_once_with(
        dummy_socket.AF_INET, dummy_socket.SOCK_DGRAM
    )
    discovery_socket.return_value.__enter__.return_value.setsockopt.assert_called_once_with(
        dummy_socket.SOL_SOCKET, dummy_socket.SO_BROADCAST, 1
    )
    discovery_socket.return_value.__enter__.return_value.sendto.assert_called_once_with(
        dummy_discovery_frame,
        ("255.255.255.255", dummy_pystagelinq.StageLinQ_discovery_port),
    )


def test_send_discovery_frame_permission_error(
    dummy_pystagelinq, monkeypatch, dummy_ip, dummy_socket
):
    dummy_discovery_frame = "AAAA"

    discovery_socket = MagicMock()

    dummy_socket.getaddrinfo.side_effect = [[["255.255.255.255"]]]

    dummy_socket.socket.side_effect = discovery_socket
    discovery_socket.return_value.__enter__.return_value.sendto.side_effect = (
        PermissionError
    )

    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "socket", dummy_socket)

    with pytest.raises(PermissionError) as exception:
        dummy_pystagelinq._send_discovery_frame(dummy_discovery_frame)

    dummy_socket.socket.assert_called_once_with(
        dummy_socket.AF_INET, dummy_socket.SOCK_DGRAM
    )
    discovery_socket.return_value.__enter__.return_value.setsockopt.assert_called_once_with(
        dummy_socket.SOL_SOCKET, dummy_socket.SO_BROADCAST, 1
    )


@pytest.mark.asyncio
async def test_discover_stagelinq_device_bind_error(
    dummy_pystagelinq, monkeypatch, dummy_ip, dummy_socket
):
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "socket", dummy_socket)

    dummy_socket.socket.return_value.bind.side_effect = Exception()

    assert (
        await dummy_pystagelinq._discover_stagelinq_device(dummy_ip)
        == PyStageLinQError.CANNOTBINDSOCKET
    )


def test_get_loop_condition(dummy_pystagelinq):
    assert dummy_pystagelinq.get_loop_condition() is True

    dummy_pystagelinq._loopcondition = False

    assert dummy_pystagelinq.get_loop_condition() is False


@pytest.mark.asyncio
async def test_discover_stagelinq_check_initialization(
    dummy_pystagelinq, monkeypatch, dummy_ip, dummy_socket
):
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "socket", dummy_socket)

    get_loop_condition_mock = Mock(side_effect=[False])
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )

    stop_mock = MagicMock()
    monkeypatch.setattr(dummy_pystagelinq, "__del__", stop_mock)

    await dummy_pystagelinq._discover_stagelinq_device(dummy_ip)

    dummy_socket.socket.assert_called_once_with(
        dummy_socket.AF_INET, dummy_socket.SOCK_DGRAM
    )
    dummy_socket.socket.return_value.bind.assert_called_once_with(
        ("255.255.255.255", dummy_pystagelinq.StageLinQ_discovery_port)
    )
    dummy_socket.socket.return_value.setblocking.assert_called_once_with(False)


@pytest.mark.asyncio
async def test_discover_stagelinq_timeout(
    dummy_pystagelinq, monkeypatch, dummy_ip, dummy_socket
):
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "socket", dummy_socket)

    select_mock = MagicMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "select", select_mock)

    time_mock = MagicMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "time", time_mock)

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ.asyncio, "sleep", sleep_mock)

    get_loop_condition_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )

    get_loop_condition_mock.side_effect = [True, False]
    time_mock.time.side_effect = [0, 11]
    select_mock.select.side_effect = [[False]]

    assert (
        await dummy_pystagelinq._discover_stagelinq_device(dummy_ip)
        == PyStageLinQError.DISCOVERYTIMEOUT
    )

    sleep_mock.assert_called_once_with(0.1)
    select_mock.select.assert_called_once_with(
        [dummy_socket.socket.return_value], [], [], 0
    )
    assert time_mock.time.call_count == 2


@pytest.mark.asyncio
async def test_discover_stagelinq_bad_frame(
    dummy_pystagelinq, monkeypatch, dummy_ip, dummy_socket
):
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "socket", dummy_socket)

    select_mock = MagicMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "select", select_mock)

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ.asyncio, "sleep", sleep_mock)

    decode_frame_mock = Mock()
    monkeypatch.setattr(
        PyStageLinQ.PyStageLinQ.StageLinQDiscovery, "decode_frame", decode_frame_mock
    )

    get_loop_condition_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )

    get_loop_condition_mock.side_effect = [True, False]
    select_mock.select.side_effect = [[True]]
    dummy_socket.socket.return_value.recvfrom.side_effect = [
        [None, [dummy_ip, dummy_port]]
    ]
    decode_frame_mock.side_effect = [PyStageLinQError.INVALIDFRAME]

    assert await dummy_pystagelinq._discover_stagelinq_device(dummy_ip) is None

    sleep_mock.assert_called_once_with(0.1)
    select_mock.select.assert_called_once_with(
        [dummy_socket.socket.return_value], [], [], 0
    )
    decode_frame_mock.assert_called_once_with(None)


@pytest.mark.asyncio
async def test_discover_stagelinq_bad_port(
    dummy_pystagelinq, monkeypatch, dummy_ip, dummy_socket
):
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "socket", dummy_socket)

    select_mock = MagicMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "select", select_mock)

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ.asyncio, "sleep", sleep_mock)

    time_mock = MagicMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "time", time_mock)

    class discovery_dummy:
        decode_frame = Mock(side_effect=[PyStageLinQError.STAGELINQOK])
        get = Mock()
        Port = 0

    stagelinq_discovery_mock = discovery_dummy()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "StageLinQDiscovery", discovery_dummy)

    get_loop_condition_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )

    get_loop_condition_mock.side_effect = [True, False]
    select_mock.select.side_effect = [[True]]
    dummy_socket.socket.return_value.recvfrom.side_effect = [[None, [dummy_ip, 0]]]
    time_mock.time.side_effect = [0, 5, 11]

    assert await dummy_pystagelinq._discover_stagelinq_device(dummy_ip) is None

    assert time_mock.time.call_count == 2


@pytest.mark.asyncio
async def test_discover_stagelinq_self_name(
    dummy_pystagelinq, monkeypatch, dummy_ip, dummy_socket, dummy_port
):
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "socket", dummy_socket)

    select_mock = MagicMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "select", select_mock)

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ.asyncio, "sleep", sleep_mock)

    time_mock = MagicMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "time", time_mock)

    class discovery_dummy:
        decode_frame = Mock(side_effect=[PyStageLinQError.STAGELINQOK])
        get = Mock()
        Port = dummy_port
        device_name = name

    stagelinq_discovery_mock = discovery_dummy()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "StageLinQDiscovery", discovery_dummy)

    get_loop_condition_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )

    get_loop_condition_mock.side_effect = [True, False]
    select_mock.select.side_effect = [[True]]
    dummy_socket.socket.return_value.recvfrom.side_effect = [[None, [dummy_ip, 0]]]
    time_mock.time.side_effect = [0, 5, 11]

    assert await dummy_pystagelinq._discover_stagelinq_device(dummy_ip) is None

    assert time_mock.time.call_count == 2


@pytest.mark.asyncio
async def test_discover_stagelinq_device_registered(
    dummy_pystagelinq, monkeypatch, dummy_ip, dummy_socket, dummy_port
):
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "socket", dummy_socket)

    select_mock = MagicMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "select", select_mock)

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ.asyncio, "sleep", sleep_mock)

    time_mock = MagicMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "time", time_mock)

    class discovery_dummy:
        decode_frame = Mock(side_effect=[PyStageLinQError.STAGELINQOK])
        get = Mock()
        Port = dummy_port
        device_name = "AAAA"

    stagelinq_discovery_mock = discovery_dummy()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "StageLinQDiscovery", discovery_dummy)

    get_loop_condition_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )

    get_loop_condition_mock.side_effect = [True, False]
    select_mock.select.side_effect = [[True]]
    dummy_socket.socket.return_value.recvfrom.side_effect = [[None, [dummy_ip, 0]]]
    time_mock.time.side_effect = [0, 5, 11]

    dummy_pystagelinq.device_list = MagicMock()
    dummy_pystagelinq.device_list.find_registered_device.side_effect = [True]

    assert await dummy_pystagelinq._discover_stagelinq_device(dummy_ip) is None

    assert time_mock.time.call_count == 2
    dummy_pystagelinq.device_list.find_registered_device.assert_called_once_with(
        stagelinq_discovery_mock.get()
    )


@pytest.mark.asyncio
async def test_discover_stagelinq(
    dummy_pystagelinq, monkeypatch, dummy_ip, dummy_socket, dummy_port
):
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "socket", dummy_socket)

    select_mock = MagicMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "select", select_mock)

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ.asyncio, "sleep", sleep_mock)

    time_mock = MagicMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "time", time_mock)

    register_device_mock = AsyncMock()
    monkeypatch.setattr(dummy_pystagelinq, "_register_new_device", register_device_mock)

    class discovery_dummy:
        decode_frame = Mock(side_effect=[PyStageLinQError.STAGELINQOK])
        get = Mock()
        Port = dummy_port
        device_name = "AAAA"

    stagelinq_discovery_mock = discovery_dummy()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "StageLinQDiscovery", discovery_dummy)

    get_loop_condition_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )

    get_loop_condition_mock.side_effect = [True, False]
    select_mock.select.side_effect = [[True]]
    dummy_socket.socket.return_value.recvfrom.side_effect = [[None, [dummy_ip, 0]]]
    time_mock.time.side_effect = [0, 5, 11]

    dummy_pystagelinq.device_list = MagicMock()
    dummy_pystagelinq.device_list.find_registered_device.side_effect = [False]

    assert await dummy_pystagelinq._discover_stagelinq_device(dummy_ip) is None

    assert time_mock.time.call_count == 3
    register_device_mock.assert_called_once()


@pytest.mark.asyncio
async def test_register_new_device(dummy_pystagelinq, monkeypatch, dummy_ip):
    class stagelinq_service_dummy:
        def __init__(self, A, B, C, D):
            assert A == dummy_ip
            assert B == "BBBB"
            assert C == dummy_pystagelinq.OwnToken
            assert D is None
            self.device_name = "UnitTest"

        get_tasks = AsyncMock()
        wait_for_services = AsyncMock()

    service_mock = stagelinq_service_dummy(
        dummy_ip, "BBBB", dummy_pystagelinq.OwnToken, None
    )

    monkeypatch.setattr(
        PyStageLinQ.PyStageLinQ, "StageLinQService", stagelinq_service_dummy
    )

    await dummy_pystagelinq._register_new_device("BBBB", dummy_ip)

    service_mock.get_tasks.assert_called_once_with()
    service_mock.wait_for_services.assert_called_once_with(timeout=1)


@pytest.mark.asyncio
async def test_register_new_task(dummy_pystagelinq, monkeypatch, dummy_ip):
    class stagelinq_service_dummy:
        def __init__(self, A, B, C, D):
            assert A == dummy_ip
            assert B == "BBBB"
            assert C == dummy_pystagelinq.OwnToken
            assert D is None
            self.device_name = "UnitTest"

        get_tasks = AsyncMock()
        wait_for_services = AsyncMock()

    service_mock = stagelinq_service_dummy(
        dummy_ip, "BBBB", dummy_pystagelinq.OwnToken, None
    )

    monkeypatch.setattr(
        PyStageLinQ.PyStageLinQ, "StageLinQService", stagelinq_service_dummy
    )

    dummy_task = [MagicMock(), MagicMock()]

    service_mock.get_tasks.side_effect = [dummy_task]

    await dummy_pystagelinq._register_new_device("BBBB", dummy_ip)

    service_mock.get_tasks.assert_called_once_with()
    service_mock.wait_for_services.assert_called_once_with(timeout=1)

    assert dummy_pystagelinq.tasks.difference(dummy_task) == set()


@pytest.mark.asyncio
async def test_register_callback(dummy_pystagelinq, monkeypatch, dummy_ip):
    class stagelinq_service_dummy:
        def __init__(self, A, B, C, D):
            assert A == dummy_ip
            assert B == "BBBB"
            assert C == dummy_pystagelinq.OwnToken
            assert D is None
            self.device_name = "UnitTest"

        get_tasks = AsyncMock()
        wait_for_services = AsyncMock()
        get_services = Mock()

    service_mock = stagelinq_service_dummy(
        dummy_ip, "BBBB", dummy_pystagelinq.OwnToken, None
    )

    monkeypatch.setattr(
        PyStageLinQ.PyStageLinQ, "StageLinQService", stagelinq_service_dummy
    )

    callback_mock = Mock()
    dummy_pystagelinq.new_device_found_callback = callback_mock

    await dummy_pystagelinq._register_new_device("BBBB", dummy_ip)

    service_mock.get_tasks.assert_called_once_with()
    service_mock.wait_for_services.assert_called_once_with(timeout=1)

    service_mock.get_services.assert_called_once_with()
    callback_mock.assert_called_once_with(dummy_ip, "BBBB", service_mock.get_services())


def test_subscribe_to_statemap_wrong_service(dummy_pystagelinq, monkeypatch):
    state_map_service_dummy = PyStageLinQ.PyStageLinQ.EngineServices.ServiceHandle(
        service="AAAA", device=None, ip=None, port=None
    )

    assert (
        dummy_pystagelinq.subscribe_to_statemap(state_map_service_dummy, dict())
        == PyStageLinQError.SERVICENOTRECOGNIZED
    )


def test_subscribe_to_statemap(dummy_pystagelinq, monkeypatch, dummy_ip, dummy_port):
    state_map_service_dummy = PyStageLinQ.PyStageLinQ.EngineServices.ServiceHandle(
        service="StateMap", device="BBBB", ip=dummy_ip, port=dummy_port
    )

    create_task_mock = Mock()
    monkeypatch.setattr(
        PyStageLinQ.PyStageLinQ.asyncio, "create_task", create_task_mock
    )

    subscribe_to_statemap_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "_subscribe_to_statemap", subscribe_to_statemap_mock
    )

    subscription_list_dummy = {"AAAA": "aaaa", "BBBB": "bbbb"}

    assert (
        dummy_pystagelinq.subscribe_to_statemap(
            state_map_service_dummy, subscription_list_dummy
        )
        == PyStageLinQError.STAGELINQOK
    )

    subscribe_to_statemap_mock.assert_called_once_with(
        state_map_service_dummy, subscription_list_dummy, None
    )


@pytest.mark.asyncio
async def test_subscripe_to_statemap(dummy_pystagelinq, monkeypatch):
    def callback_dummy():
        pass

    state_map_service_dummy = "AAAA"
    subscription_list_dummy = "BBBB"

    class state_map_subscription_dummy:
        def __init__(self, A, B, C):
            assert A == state_map_service_dummy
            assert B == subscription_list_dummy
            assert C == callback_dummy

        subscribe = AsyncMock()
        get_task = Mock()

    monkeypatch.setattr(
        PyStageLinQ.PyStageLinQ.EngineServices,
        "StateMapSubscription",
        state_map_subscription_dummy,
    )

    state_map_dummy = state_map_subscription_dummy(
        state_map_service_dummy, subscription_list_dummy, callback_dummy
    )

    await dummy_pystagelinq._subscribe_to_statemap(
        state_map_service_dummy, subscription_list_dummy, callback_dummy
    )

    state_map_dummy.subscribe.assert_awaited_once_with(dummy_pystagelinq.OwnToken)
    state_map_dummy.get_task.assert_called_once_with()
    assert dummy_pystagelinq.tasks.pop() == state_map_dummy.get_task()


@pytest.mark.asyncio
async def test_start_stagelinq(dummy_pystagelinq, monkeypatch):
    create_task_mock = Mock()
    monkeypatch.setattr(
        PyStageLinQ.PyStageLinQ.asyncio, "create_task", create_task_mock
    )

    _periodic_announcement_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "_periodic_announcement", _periodic_announcement_mock
    )

    _py_stagelinq_strapper_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "_py_stagelinq_strapper", _py_stagelinq_strapper_mock
    )

    await dummy_pystagelinq._start_stagelinq()

    assert create_task_mock.call_count == 2
    create_task_mock.assert_any_call(_periodic_announcement_mock.return_value)
    create_task_mock.assert_called_with(_py_stagelinq_strapper_mock.return_value)


@pytest.mark.asyncio
async def test_start_stagelinq_standalone(dummy_pystagelinq, monkeypatch):
    create_task_mock = Mock()
    monkeypatch.setattr(
        PyStageLinQ.PyStageLinQ.asyncio, "create_task", create_task_mock
    )

    _periodic_announcement_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "_periodic_announcement", _periodic_announcement_mock
    )

    _py_stagelinq_strapper_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "_py_stagelinq_strapper", _py_stagelinq_strapper_mock
    )

    wait_for_exit_mock = AsyncMock()
    monkeypatch.setattr(dummy_pystagelinq, "_wait_for_exit", wait_for_exit_mock)

    await dummy_pystagelinq._start_stagelinq(standalone=True)

    assert create_task_mock.call_count == 2
    create_task_mock.assert_any_call(_periodic_announcement_mock.return_value)
    create_task_mock.assert_called_with(_py_stagelinq_strapper_mock.return_value)
    wait_for_exit_mock.assert_called_once_with()


@pytest.mark.asyncio
async def test_wait_for_exit_no_tasks(dummy_pystagelinq, monkeypatch):
    get_loop_condition_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )

    get_loop_condition_mock.side_effect = [True, False]

    await dummy_pystagelinq._wait_for_exit()


@pytest.mark.asyncio
async def test_wait_for_exit_no_tasks(dummy_pystagelinq, monkeypatch):
    get_loop_condition_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ.asyncio, "sleep", sleep_mock)

    get_loop_condition_mock.side_effect = [True, False]

    await dummy_pystagelinq._wait_for_exit()

    sleep_mock.assert_called_with(1)
    assert get_loop_condition_mock.call_count == 2


@pytest.mark.asyncio
async def test_wait_for_exit_task_not_done(dummy_pystagelinq, monkeypatch):
    get_loop_condition_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )

    tasks_mock = MagicMock()
    monkeypatch.setattr(dummy_pystagelinq, "tasks", tasks_mock)

    task_mock = MagicMock()

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ.asyncio, "sleep", sleep_mock)

    tasks_mock.copy.side_effect = [[task_mock]]
    get_loop_condition_mock.side_effect = [True, False]
    task_mock.done.side_effect = [False]

    await dummy_pystagelinq._wait_for_exit()

    sleep_mock.assert_called_with(1)
    assert get_loop_condition_mock.call_count == 2
    tasks_mock.copy.assert_called_once_with()
    task_mock.done.assert_called_once_with()


@pytest.mark.asyncio
async def test_wait_for_exit_task_done(dummy_pystagelinq, monkeypatch):
    get_loop_condition_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )

    tasks_mock = MagicMock()
    monkeypatch.setattr(dummy_pystagelinq, "tasks", tasks_mock)

    task_mock = MagicMock()

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ.asyncio, "sleep", sleep_mock)

    tasks_mock.copy.side_effect = [[task_mock]]
    get_loop_condition_mock.side_effect = [True, False]
    task_mock.done.side_effect = [True]
    task_mock.exception.side_effect = [None]

    await dummy_pystagelinq._wait_for_exit()

    assert get_loop_condition_mock.call_count == 1
    tasks_mock.copy.assert_called_once_with()
    task_mock.done.assert_called_once_with()
    task_mock.exception.assert_called_once_with()


@pytest.mark.asyncio
async def test_wait_for_exit_task_exception(
    dummy_pystagelinq, monkeypatch, dummy_socket
):
    get_loop_condition_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )

    tasks_mock = MagicMock()
    monkeypatch.setattr(dummy_pystagelinq, "tasks", tasks_mock)

    task_mock = MagicMock()

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ.asyncio, "sleep", sleep_mock)

    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "socket", dummy_socket)

    tasks_mock.copy.side_effect = [[task_mock]]
    get_loop_condition_mock.side_effect = [True, False]
    task_mock.done.side_effect = [True]
    # An error as obscure as possible is picket to avoid false positives.
    task_mock.exception.return_value = NotImplementedError
    task_mock.get_coro.return_value = "error task"

    with pytest.raises(NotImplementedError) as exception:
        await dummy_pystagelinq._wait_for_exit()

    assert get_loop_condition_mock.call_count == 1
    tasks_mock.copy.assert_called_once_with()
    task_mock.done.assert_called_once_with()
    assert task_mock.exception.call_count == 3
    assert exception.type is NotImplementedError


@pytest.mark.asyncio
async def test_stop_all_tasks(dummy_pystagelinq, monkeypatch):
    tasks_mock = MagicMock()
    monkeypatch.setattr(dummy_pystagelinq, "tasks", tasks_mock)

    task_mock = MagicMock()
    tasks_mock.copy.side_effect = [[task_mock]]

    dummy_pystagelinq._stop_all_tasks()

    tasks_mock.copy.assert_called_once_with()
    task_mock.cancel.assert_called_once_with()


@pytest.mark.asyncio
async def test_periodic_announcement(dummy_pystagelinq, monkeypatch):
    get_loop_condition_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )
    get_loop_condition_mock.side_effect = [True, False]

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ.asyncio, "sleep", sleep_mock)

    announce_self_mock = Mock()
    monkeypatch.setattr(dummy_pystagelinq, "_announce_self", announce_self_mock)

    await dummy_pystagelinq._periodic_announcement()

    assert get_loop_condition_mock.call_count == 2
    announce_self_mock.assert_called_once_with()
    sleep_mock.assert_called_once_with(0.5)


@pytest.mark.asyncio
async def test_py_stagelinq_strapper(dummy_pystagelinq, monkeypatch, dummy_ip):
    discover_device_mock = AsyncMock()
    monkeypatch.setattr(
        dummy_pystagelinq, "_discover_stagelinq_device", discover_device_mock
    )

    await dummy_pystagelinq._py_stagelinq_strapper()

    discover_device_mock.assert_called_once_with(dummy_ip, timeout=2)


@pytest.mark.asyncio
async def test_py_stagelinq_strapper_loop_condition_false(
    dummy_pystagelinq, monkeypatch, dummy_ip
):
    get_loop_condition_mock = Mock(side_effect=[False])
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )
    discover_device_mock = AsyncMock()
    monkeypatch.setattr(
        dummy_pystagelinq, "_discover_stagelinq_device", discover_device_mock
    )

    await dummy_pystagelinq._py_stagelinq_strapper()

    discover_device_mock.assert_called_once_with(dummy_ip, timeout=2)


@pytest.mark.asyncio
async def test_py_stagelinq_strapper_task_exception(
    dummy_pystagelinq, monkeypatch, dummy_ip
):

    asyncio_create_task_mock = MagicMock()

    asyncio_create_task_mock.return_value = asyncio_create_task_mock

    asyncio_create_task_mock.done.return_value = True
    asyncio_create_task_mock.exception.return_value = RuntimeError

    monkeypatch.setattr(
        PyStageLinQ.PyStageLinQ.asyncio, "create_task", asyncio_create_task_mock
    )

    get_loop_condition_mock = Mock()
    monkeypatch.setattr(
        dummy_pystagelinq, "get_loop_condition", get_loop_condition_mock
    )

    sleep_mock = AsyncMock()
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ.asyncio, "sleep", sleep_mock)

    discover_device_mock = MagicMock()
    monkeypatch.setattr(
        dummy_pystagelinq, "_discover_stagelinq_device", discover_device_mock
    )

    get_loop_condition_mock.side_effect = [True, False]

    with pytest.raises(RuntimeError) as exception:
        await dummy_pystagelinq._py_stagelinq_strapper()
    assert get_loop_condition_mock.call_count == 1

    assert exception.type is RuntimeError


def test_stop(dummy_pystagelinq, monkeypatch):
    stop_mock = Mock()

    monkeypatch.setattr(dummy_pystagelinq, "_stop", stop_mock)

    dummy_pystagelinq.stop()

    stop_mock.assert_called_once_with()


def test___del__(dummy_pystagelinq, monkeypatch):
    stop_mock = MagicMock()
    stop_all_tasks_mock = MagicMock()

    monkeypatch.setattr(dummy_pystagelinq, "_stop", stop_mock)
    monkeypatch.setattr(dummy_pystagelinq, "_stop_all_tasks", stop_all_tasks_mock)

    dummy_pystagelinq.__del__()

    stop_mock.assert_called_once_with()
    stop_all_tasks_mock.assert_called_once_with()
