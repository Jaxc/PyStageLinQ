from . import DataClasses

class DeviceList:

    device_list : DataClasses.StageLinQDiscoveryData

    def __init__(self):
        self.device_list = []

    def register_device(self, device):
        self.device_list.append(device)

    def find_registered_device(self, discovery_frame) -> DataClasses.StageLinQDiscoveryData:
        # Check if main link has been established for Offline analyzers
        if discovery_frame.SwName == "OfflineAnalyzer":
            if not self.find_main_interface(discovery_frame):
                return True

        # Check if device is registered
        for device in self.device_list:
            if discovery_frame.DeviceName == device.device_name:
                if discovery_frame.ReqServicePort == device.Port:
                    # Device already registered
                    return True
        return False

    def find_main_interface(self, discovery_frame) -> DataClasses.StageLinQDiscoveryData:
        for device in self.device_list:
            if device.device_name == discovery_frame.DeviceName:
                if device.sw_name != "OfflineAnalyzer":
                    return True

        return False
