import pytest
import random

import PyStageLinQ.Device
import PyStageLinQ.Network
import PyStageLinQ.MessageClasses
import PyStageLinQ.DataClasses
import PyStageLinQ.Token

device_name = "AAAA"
ConnectionType = "BBBB"
SwName = "CCCC"
SwVersion = "DDDD"


class StageLinQService_dummy:
    device_name = ""
    sw_name = ""
    Port = -1


@pytest.fixture()
def dummy_device(discovery_dummy, monkeypatch):
    monkeypatch.setattr(PyStageLinQ.Network, "StageLinQService", StageLinQService_dummy)

    return StageLinQService_dummy()


@pytest.fixture()
def dummy_device_2(monkeypatch):
    monkeypatch.setattr(PyStageLinQ.Network, "StageLinQService", StageLinQService_dummy)

    return StageLinQService_dummy()


@pytest.fixture()
def port_dummy():
    return random.randint(1, 65535)


@pytest.fixture()
def discovery_data_dummy():
    token = PyStageLinQ.Token.StageLinQToken()

    return PyStageLinQ.DataClasses.StageLinQDiscoveryData(
        token, device_name, ConnectionType, SwName, SwVersion, port_dummy
    )


@pytest.fixture()
def discovery_dummy():
    return PyStageLinQ.MessageClasses.StageLinQDiscovery()


@pytest.fixture()
def DeviceList():
    return PyStageLinQ.Device.DeviceList()


def test_init_value(DeviceList):
    assert DeviceList.device_list == []


def test_register_device_wrong_type(DeviceList):
    assert DeviceList.register_device(1) is False
    assert DeviceList.register_device(None) is False
    assert DeviceList.register_device("1") is False


def test_register_device(DeviceList, dummy_device, dummy_device_2):
    DeviceList.register_device(dummy_device)

    assert len(DeviceList.device_list) == 1
    assert DeviceList.device_list[0] == dummy_device

    DeviceList.register_device(dummy_device_2)

    assert len(DeviceList.device_list) == 2
    assert DeviceList.device_list[0] == dummy_device
    assert DeviceList.device_list[1] == dummy_device_2


def test_find_registered_device_bad_main_interface(
    DeviceList, discovery_data_dummy, monkeypatch
):
    def find_main_interface_dummy(_):
        return False

    discovery_data_dummy.SwName = "OfflineAnalyzer"

    monkeypatch.setattr(DeviceList, "find_main_interface", find_main_interface_dummy)

    assert DeviceList.find_registered_device(discovery_data_dummy) is True


def test_find_registered_device_ok_main_interface(
    DeviceList, discovery_data_dummy, monkeypatch
):
    def find_main_interface_dummy(_):
        return True

    discovery_data_dummy.SwName = "OfflineAnalyzer"

    monkeypatch.setattr(DeviceList, "find_main_interface", find_main_interface_dummy)

    assert DeviceList.find_registered_device(discovery_data_dummy) is False


def test_find_registered_device_bad_device_name(
    DeviceList, dummy_device, port_dummy, discovery_data_dummy, monkeypatch
):
    dummy_device.Port = port_dummy

    DeviceList.device_list.append(dummy_device)

    assert DeviceList.find_registered_device(discovery_data_dummy) is False


def test_find_registered_device_bad_port(
    DeviceList, dummy_device, discovery_data_dummy, monkeypatch
):
    dummy_device.device_name = discovery_data_dummy.DeviceName

    DeviceList.device_list.append(dummy_device)

    assert DeviceList.find_registered_device(discovery_data_dummy) is False


def test_find_registered_device_valid_input(
    DeviceList, dummy_device, discovery_data_dummy, monkeypatch
):
    dummy_device.device_name = discovery_data_dummy.DeviceName
    dummy_device.Port = discovery_data_dummy.ReqServicePort

    DeviceList.device_list.append(dummy_device)

    assert DeviceList.find_registered_device(discovery_data_dummy) is True


def test_find_main_interface_no_entries(DeviceList, discovery_data_dummy):
    assert DeviceList.find_main_interface(discovery_data_dummy) is False


def test_find_main_interface_bad_device_name(
    dummy_device, DeviceList, discovery_data_dummy
):
    DeviceList.device_list.append(dummy_device)

    assert DeviceList.find_main_interface(discovery_data_dummy) is False


def test_find_main_interface_bad_sw_name(
    dummy_device, DeviceList, discovery_data_dummy
):
    dummy_device.device_name = discovery_data_dummy.DeviceName
    dummy_device.sw_name = "OfflineAnalyzer"

    DeviceList.device_list.append(dummy_device)

    assert DeviceList.find_main_interface(discovery_data_dummy) is False


def test_find_main_interface_valid_input(
    dummy_device, DeviceList, discovery_data_dummy
):
    dummy_device.device_name = discovery_data_dummy.DeviceName

    DeviceList.device_list.append(dummy_device)

    assert DeviceList.find_main_interface(discovery_data_dummy) is True
