import pytest
import PyStageLinQ.PyStageLinQ
from PyStageLinQ.ErrorCodes import *
from unittest.mock import AsyncMock, Mock, MagicMock
import ipaddress
from socket import AF_INET

import random


class dummy_net_if_stats:
    def __init__(self):
        self.isup = True


class dummy_net_if_addrs:
    def __init__(self, ip="0.0.0.0"):
        self.family = AF_INET
        self.address = ip
        self.netmask = "255.255.255.0"


class ifutils_net_if_addrs:
    def __init__(self, ip=[], netmask="255.255.255.0"):
        self.address = ip
        self.netmask = netmask
        self.family = AF_INET


@pytest.fixture()
def dummy_socket():
    return MagicMock()


@pytest.fixture(autouse=True)
def ensure_cleanup(dummy_socket):
    """Ensure that everything is cleaned up between tests."""
    yield

    # Force garbage collection to trigger __del__ if necessary
    import gc

    gc.collect()


@pytest.fixture()
def dummy_port():
    return random.randint(1, 65535)


@pytest.fixture()
def dummy_ip():
    return ".".join(map(str, (random.randint(0, 255) for _ in range(4))))


@pytest.fixture()
def dummy_PyStageLinQ_network_interface(dummy_ip, monkeypatch, dummy_port):
    dummy_psutil = MagicMock()
    dummy_psutil.net_if_addrs.return_value = {
        "interface1": [dummy_net_if_addrs(ip=dummy_ip)]
    }
    dummy_psutil.net_if_stats.return_value = {"interface1": dummy_net_if_stats()}
    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "psutil", dummy_psutil)

    return PyStageLinQ.PyStageLinQ.PyStageLinQ_network_interface(dummy_ip, dummy_port)


def test_init_values(dummy_ip, monkeypatch):

    def dummy_get_interface_from_ip(_, ip=None, discovery_port=None):
        assert ip == dummy_ip

    monkeypatch.setattr(
        PyStageLinQ.PyStageLinQ.PyStageLinQ_network_interface,
        "get_interface_from_ip",
        dummy_get_interface_from_ip,
    )

    test_PyStageLinQ_network_interface = (
        PyStageLinQ.PyStageLinQ.PyStageLinQ_network_interface(
            ip=dummy_ip, discovery_port=dummy_port
        )
    )

    assert test_PyStageLinQ_network_interface.discovery_port == dummy_port


def test_init_values_ip_none(monkeypatch, dummy_socket):
    dummy_psutil = MagicMock()
    dummy_ips = {
        "interface1": [ifutils_net_if_addrs(ip="1.2.3.4", netmask="255.0.0.0")],
        "interface2": [ifutils_net_if_addrs(ip="5.6.7.8", netmask="255.255.0.0")],
        "interface3": [ifutils_net_if_addrs(ip="9.10.11.12", netmask="255.255.255.0")],
    }

    dummy_ips["interface3"][0].family = None

    dummy_stats = {
        "interface1": [None],
        "interface2": [None],
        "interface3": [None],
    }

    dummy_psutil.net_if_addrs.return_value = dummy_ips
    dummy_psutil.net_if_stats.return_value = dummy_stats

    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "psutil", dummy_psutil)

    discovery_port = 12345

    dummy_pystagelinq_network_interface = (
        PyStageLinQ.PyStageLinQ.PyStageLinQ_network_interface(
            ip=None, discovery_port=discovery_port
        )
    )

    assert dummy_pystagelinq_network_interface.discovery_port == discovery_port

    assert (
        dummy_pystagelinq_network_interface.target_interfaces[0].addr_str
        == dummy_ips["interface1"][0].address
    )
    assert ipaddress.IPv4Address(
        dummy_pystagelinq_network_interface.target_interfaces[0].addr
    ) == ipaddress.IPv4Address(dummy_ips["interface1"][0].address)
    assert ipaddress.IPv4Address(
        dummy_pystagelinq_network_interface.target_interfaces[0].mask
    ) == ipaddress.IPv4Address(dummy_ips["interface1"][0].netmask)
    assert (
        dummy_pystagelinq_network_interface.target_interfaces[0].status
        is dummy_stats["interface1"]
    )

    assert (
        dummy_pystagelinq_network_interface.target_interfaces[1].addr_str
        == dummy_ips["interface2"][0].address
    )
    assert ipaddress.IPv4Address(
        dummy_pystagelinq_network_interface.target_interfaces[1].addr
    ) == ipaddress.IPv4Address(dummy_ips["interface2"][0].address)
    assert ipaddress.IPv4Address(
        dummy_pystagelinq_network_interface.target_interfaces[1].mask
    ) == ipaddress.IPv4Address(dummy_ips["interface2"][0].netmask)
    assert (
        dummy_pystagelinq_network_interface.target_interfaces[1].status
        is dummy_stats["interface2"]
    )

    assert len(dummy_pystagelinq_network_interface.target_interfaces) == 2


def test_init_values_ip_single(monkeypatch, dummy_socket):
    dummy_psutil = MagicMock()
    dummy_ips = {
        "interface1": [ifutils_net_if_addrs(ip="1.2.3.4", netmask="255.0.0.0")],
        "interface2": [ifutils_net_if_addrs(ip="5.6.7.8", netmask="255.255.0.0")],
        "interface3": [ifutils_net_if_addrs(ip="9.10.11.12", netmask="255.255.255.0")],
    }

    dummy_ips["interface3"][0].family = None

    dummy_stats = {
        "interface1": [None],
        "interface2": [None],
        "interface3": [None],
    }

    dummy_psutil.net_if_addrs.return_value = dummy_ips
    dummy_psutil.net_if_stats.return_value = dummy_stats

    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "psutil", dummy_psutil)

    discovery_port = 12345

    dummy_pystagelinq_network_interface = (
        PyStageLinQ.PyStageLinQ.PyStageLinQ_network_interface(
            ip="1.2.3.4", discovery_port=discovery_port
        )
    )

    assert dummy_pystagelinq_network_interface.discovery_port == discovery_port

    assert (
        dummy_pystagelinq_network_interface.target_interfaces[0].addr_str
        == dummy_ips["interface1"][0].address
    )
    assert ipaddress.IPv4Address(
        dummy_pystagelinq_network_interface.target_interfaces[0].addr
    ) == ipaddress.IPv4Address(dummy_ips["interface1"][0].address)
    assert ipaddress.IPv4Address(
        dummy_pystagelinq_network_interface.target_interfaces[0].mask
    ) == ipaddress.IPv4Address(dummy_ips["interface1"][0].netmask)
    assert (
        dummy_pystagelinq_network_interface.target_interfaces[0].status
        is dummy_stats["interface1"]
    )

    assert len(dummy_pystagelinq_network_interface.target_interfaces) == 1


def test_init_values_ip_multiple(monkeypatch, dummy_socket):
    dummy_psutil = MagicMock()
    dummy_ips = {
        "interface1": [ifutils_net_if_addrs(ip="1.2.3.4", netmask="255.0.0.0")],
        "interface2": [ifutils_net_if_addrs(ip="5.6.7.8", netmask="255.255.0.0")],
        "interface3": [ifutils_net_if_addrs(ip="9.10.11.12", netmask="255.255.255.0")],
        "interface4": [ifutils_net_if_addrs(ip="13.14.15.16", netmask="255.255.255.0")],
    }

    dummy_ips["interface3"][0].family = None

    dummy_stats = {
        "interface1": [None],
        "interface2": [None],
        "interface3": [None],
        "interface4": [None],
    }

    dummy_psutil.net_if_addrs.return_value = dummy_ips
    dummy_psutil.net_if_stats.return_value = dummy_stats

    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "psutil", dummy_psutil)

    discovery_port = 12345

    dummy_pystagelinq_network_interface = (
        PyStageLinQ.PyStageLinQ.PyStageLinQ_network_interface(
            ip=["1.2.3.4", "5.6.7.8", "13.14.15.16"], discovery_port=discovery_port
        )
    )

    assert dummy_pystagelinq_network_interface.discovery_port == discovery_port

    assert (
        dummy_pystagelinq_network_interface.target_interfaces[0].addr_str
        == dummy_ips["interface1"][0].address
    )
    assert ipaddress.IPv4Address(
        dummy_pystagelinq_network_interface.target_interfaces[0].addr
    ) == ipaddress.IPv4Address(dummy_ips["interface1"][0].address)
    assert ipaddress.IPv4Address(
        dummy_pystagelinq_network_interface.target_interfaces[0].mask
    ) == ipaddress.IPv4Address(dummy_ips["interface1"][0].netmask)
    assert (
        dummy_pystagelinq_network_interface.target_interfaces[0].status
        is dummy_stats["interface1"]
    )

    assert (
        dummy_pystagelinq_network_interface.target_interfaces[1].addr_str
        == dummy_ips["interface2"][0].address
    )
    assert ipaddress.IPv4Address(
        dummy_pystagelinq_network_interface.target_interfaces[1].addr
    ) == ipaddress.IPv4Address(dummy_ips["interface2"][0].address)
    assert ipaddress.IPv4Address(
        dummy_pystagelinq_network_interface.target_interfaces[1].mask
    ) == ipaddress.IPv4Address(dummy_ips["interface2"][0].netmask)
    assert (
        dummy_pystagelinq_network_interface.target_interfaces[1].status
        is dummy_stats["interface2"]
    )

    assert (
        dummy_pystagelinq_network_interface.target_interfaces[2].addr_str
        == dummy_ips["interface4"][0].address
    )
    assert ipaddress.IPv4Address(
        dummy_pystagelinq_network_interface.target_interfaces[2].addr
    ) == ipaddress.IPv4Address(dummy_ips["interface4"][0].address)
    assert ipaddress.IPv4Address(
        dummy_pystagelinq_network_interface.target_interfaces[2].mask
    ) == ipaddress.IPv4Address(dummy_ips["interface4"][0].netmask)
    assert (
        dummy_pystagelinq_network_interface.target_interfaces[2].status
        is dummy_stats["interface4"]
    )

    assert len(dummy_pystagelinq_network_interface.target_interfaces) == 3


def test_init_values_ip_invalid(monkeypatch, dummy_socket):
    dummy_psutil = MagicMock()
    dummy_ips = {
        "interface1": [ifutils_net_if_addrs(ip="1.2.3.4", netmask="255.0.0.0")],
        "interface2": [ifutils_net_if_addrs(ip="5.6.7.8", netmask="255.255.0.0")],
        "interface3": [ifutils_net_if_addrs(ip="9.10.11.12", netmask="255.255.255.0")],
        "interface4": [ifutils_net_if_addrs(ip="13.14.15.16", netmask="255.255.255.0")],
    }

    dummy_ips["interface3"][0].family = None

    dummy_stats = {
        "interface1": [None],
        "interface2": [None],
        "interface3": [None],
        "interface4": [None],
    }

    dummy_psutil.net_if_addrs.return_value = dummy_ips
    dummy_psutil.net_if_stats.return_value = dummy_stats

    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "psutil", dummy_psutil)

    discovery_port = 12345

    with pytest.raises(Exception) as exception:
        dummy_pystagelinq_network_interface = (
            PyStageLinQ.PyStageLinQ.PyStageLinQ_network_interface(
                ip=["1.2.3.4", "5.6.7.8", 5], discovery_port=discovery_port
            )
        )
    assert exception.type is TypeError

    with pytest.raises(Exception) as exception:
        dummy_pystagelinq_network_interface = (
            PyStageLinQ.PyStageLinQ.PyStageLinQ_network_interface(
                ip=5, discovery_port=discovery_port
            )
        )
    assert exception.type is TypeError


def test_send_discovery_frame(
    dummy_PyStageLinQ_network_interface, monkeypatch, dummy_socket
):
    dummy_discovery_frame = "AAAA"

    discovery_socket = MagicMock()

    dummy_socket.socket.side_effect = discovery_socket

    dummy_socket.getaddrinfo.side_effect = [[["255.255.255.255"]]]

    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "socket", dummy_socket)

    dummy_PyStageLinQ_network_interface.send_discovery_frame(dummy_discovery_frame)

    dummy_socket.socket.assert_called_once_with(
        dummy_socket.AF_INET, dummy_socket.SOCK_DGRAM
    )
    discovery_socket.return_value.__enter__.return_value.setsockopt.assert_called_once_with(
        dummy_socket.SOL_SOCKET, dummy_socket.SO_BROADCAST, 1
    )
    discovery_socket.return_value.__enter__.return_value.sendto.assert_called_once_with(
        dummy_discovery_frame,
        ("255.255.255.255", dummy_PyStageLinQ_network_interface.discovery_port),
    )


def test_send_discovery_frame_permission_error(
    dummy_PyStageLinQ_network_interface, monkeypatch, dummy_ip, dummy_socket
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
        dummy_PyStageLinQ_network_interface.send_discovery_frame(dummy_discovery_frame)

    dummy_socket.socket.assert_called_once_with(
        dummy_socket.AF_INET, dummy_socket.SOCK_DGRAM
    )
    discovery_socket.return_value.__enter__.return_value.setsockopt.assert_called_once_with(
        dummy_socket.SOL_SOCKET, dummy_socket.SO_BROADCAST, 1
    )


def test_determine_interface_of_remote_ip(monkeypatch, dummy_socket):
    dummy_psutil = MagicMock()
    dummy_ips = {
        "interface1": [ifutils_net_if_addrs(ip="1.2.3.4", netmask="255.0.0.0")],
        "interface2": [ifutils_net_if_addrs(ip="5.6.7.8", netmask="255.255.0.0")],
        "interface3": [ifutils_net_if_addrs(ip="9.10.11.12", netmask="255.255.255.0")],
        "interface4": [ifutils_net_if_addrs(ip="13.14.15.16", netmask="255.255.255.0")],
    }

    dummy_ips["interface3"][0].family = None

    dummy_stats = {
        "interface1": [None],
        "interface2": [None],
        "interface3": [None],
        "interface4": [None],
    }

    dummy_psutil.net_if_addrs.return_value = dummy_ips
    dummy_psutil.net_if_stats.return_value = dummy_stats

    monkeypatch.setattr(PyStageLinQ.PyStageLinQ, "psutil", dummy_psutil)

    discovery_port = 12345

    dummy_pystagelinq_network_interface = (
        PyStageLinQ.PyStageLinQ.PyStageLinQ_network_interface(
            ip=["1.2.3.4", "5.6.7.8", "13.14.15.16"], discovery_port=discovery_port
        )
    )

    # Try valid IPs for each interface
    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip("1.1.1.1")
        == dummy_pystagelinq_network_interface.target_interfaces[0]
    )
    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip("1.2.1.1")
        == dummy_pystagelinq_network_interface.target_interfaces[0]
    )
    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip("1.1.2.1")
        == dummy_pystagelinq_network_interface.target_interfaces[0]
    )
    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip("1.2.3.3")
        == dummy_pystagelinq_network_interface.target_interfaces[0]
    )
    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip(
            "1.255.255.255"
        )
        == dummy_pystagelinq_network_interface.target_interfaces[0]
    )

    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip("5.6.5.5")
        == dummy_pystagelinq_network_interface.target_interfaces[1]
    )
    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip("5.6.6.5")
        == dummy_pystagelinq_network_interface.target_interfaces[1]
    )
    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip(
            "5.6.255.255"
        )
        == dummy_pystagelinq_network_interface.target_interfaces[1]
    )

    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip(
            "13.14.15.5"
        )
        == dummy_pystagelinq_network_interface.target_interfaces[2]
    )
    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip(
            "13.14.15.1"
        )
        == dummy_pystagelinq_network_interface.target_interfaces[2]
    )
    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip(
            "13.14.15.255"
        )
        == dummy_pystagelinq_network_interface.target_interfaces[2]
    )

    # Try some IPs that has no interface
    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip("5.1.1.1")
        is None
    )
    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip(
            "253.196.1.1"
        )
        is None
    )
    assert (
        dummy_pystagelinq_network_interface.determine_interface_of_remote_ip(
            "2.255.255.255"
        )
        is None
    )


def test_send_desc_on_all_if(dummy_PyStageLinQ_network_interface):
    assert dummy_PyStageLinQ_network_interface.send_desc_on_all_if() is False

    dummy_PyStageLinQ_network_interface.target_interfaces[0].n_disc_msg_send = 10

    assert dummy_PyStageLinQ_network_interface.send_desc_on_all_if() is True
