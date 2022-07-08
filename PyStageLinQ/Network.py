"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""

import asyncio
from . import EngineServices
from .MessageClasses import *
from . import Token


class StageLinQService:
    def __init__(self, ip, discovery_frame, own_token, service_found_callback):
        self.reference_task = None
        self.reader = None
        self.writer = None
        self.Ip = ip
        self.Port = discovery_frame.get_data().ReqServicePort
        self.OwnToken = own_token
        self.DeviceToken = Token.StageLinQToken()
        self.service_list = []
        self.device_name = discovery_frame.device_name
        self.device_token = discovery_frame.token
        self.sw_name = discovery_frame.sw_name

        self.receive_task = asyncio.create_task(self.receive_data())

        self.init_complete = False
        self.services_available = False

        self.service_found_callback = service_found_callback

    def get_services(self):
        if self.services_available:
            return_list = []
            for service in self.service_list:
                return_list.append(EngineServices.ServiceHandle(device=self.device_name, ip=self.Ip, service=service[0],
                                                                port=service[1]))
            return return_list

    async def get_tasks(self):
        while not self.init_complete:
            await asyncio.sleep(0.1)
        return [self.reference_task, self.receive_task]

    async def wait_for_services(self, timeout=-1):
        timestep = 0.01
        n = 0
        while True:
            if self.services_available:
                return
            elif timeout >= 0 and n > timeout / timestep:
                raise Exception("Timeout occurred before services were received")
            n = n + 1
            await asyncio.sleep(timestep)

    async def send_request_frame(self, delay=0):

        await asyncio.sleep(delay)

        out_data = StageLinQRequestServices()
        service_request_message = out_data.encode(StageLinQServiceRequestService(Token=self.OwnToken))

        self.writer.write(service_request_message)
        await self.writer.drain()

        await asyncio.sleep(0.1)

        if not self.services_available:
            # try a second time after 100ms if Device did not reply the first time
            await self.send_reference_message()

            await asyncio.sleep(0.2)

            self.writer.write(service_request_message)
            await self.writer.drain()

    async def receive_data(self):
        # Send first message

        self.reader, self.writer = await asyncio.open_connection(self.Ip, self.Port)
        self.reference_task = asyncio.create_task(self.send_reference_message_periodically())
        asyncio.create_task(self.send_request_frame(0))
        # asyncio.create_task(self.send_request_frame(0.2))

        self.init_complete = True

        while True:
            response = await self.reader.read(1024)

            if len(response) == 0:
                # Socket closed
                raise Exception(f"Remote socket for IP:{self.Ip} Port:{self.Port} closed!")

            frames = self.DecodeMultiframe(response)

            adding_services = False
            for frame in frames:
                if type(frame) is StageLinQServiceAnnouncementData:
                    self.service_list.append([frame.Service, frame.Port])
                    adding_services = True

                if self.DeviceToken.get_token() == 0:
                    if type(frame) is StageLinQServiceAnnouncementData or type(frame) is StageLinQServiceRequestService:
                        self.DeviceToken.set_token(int.from_bytes(frame.Token, byteorder='big'))

                if type(frame) is StageLinQReference:
                    asyncio.create_task(self.send_reference_message())

            if adding_services:
                self.services_available = True
                if self.service_found_callback is not None:
                    await self.service_found_callback(self)

    async def send_reference_message_periodically(self):
        while True:
            # Really simple way of knowing if a link has been established, and initial handshake is done
            if self.services_available:
                await self.send_reference_message()
            await asyncio.sleep(0.250)

    async def send_reference_message(self):
        reference_data = StageLinQReferenceData(OwnToken=self.OwnToken, DeviceToken=self.DeviceToken, Reference=0)
        reference_message = StageLinQReference()
        reference_message.encode(reference_data)

        self.writer.write(reference_message.encode(reference_data))
        await self.writer.drain()

    def DecodeMultiframe(self, frame):
        subframes = []
        while (len(frame) > 4):
            match (int.from_bytes(frame[0:4], byteorder='big')):
                case 0:
                    data = StageLinQServiceAnnouncement()
                case 1:
                    data = StageLinQReference()
                case 2:
                    data = StageLinQRequestServices()
                case _:
                    # invalid data, return
                    return
            data.decode(frame)
            subframes.append(data.get())
            frame = frame[data.get_len():]

        return subframes

    def __del__(self):

        try:
            print("Closing Network sockets for services")
            self.Socket.close()
        except AttributeError:
            print("Failed to close network, possible it was not initalized")
            # Socket not inited, nothing to close
            pass
