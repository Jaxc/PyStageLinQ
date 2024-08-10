"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""

from __future__ import annotations
import asyncio
import logging
from . import EngineServices
from .DataClasses import (
    StageLinQServiceAnnouncementData,
    StageLinQReferenceData,
    StageLinQServiceRequestService,
)
from .MessageClasses import *
from . import Token
from typing import Callable, Tuple, List, Any

logger = logging.getLogger("PyStageLinQ")


class StageLinQService:
    _loopcondition = True

    def __init__(
        self,
        ip: str,
        discovery_frame: StageLinQDiscovery,
        own_token: StageLinQToken,
        service_found_callback: Callable[[StageLinQService], None],
    ) -> None:
        self.Socket = None
        self.reference_task = None
        self.reader = None
        self.writer = None
        self.Ip = ip
        self.Port = discovery_frame.get().ReqServicePort
        self.OwnToken = own_token
        self.DeviceToken = Token.StageLinQToken()
        self.service_list = []
        self.device_name = discovery_frame.device_name
        self.device_token = discovery_frame.token
        self.sw_name = discovery_frame.sw_name

        self.receive_task = asyncio.create_task(self.start_receive_data())

        self.init_complete = False
        self.services_available = False

        self.service_found_callback = service_found_callback

        self.remaining_data = None

        self.debug = []

    def get_services(self) -> list[EngineServices]:
        if self.services_available:
            return_list = []
            for service in self.service_list:
                return_list.append(
                    EngineServices.ServiceHandle(
                        device=self.device_name,
                        ip=self.Ip,
                        service=service[0],
                        port=service[1],
                    )
                )
            return return_list

    def get_init_complete(self) -> bool:
        return self.init_complete

    async def get_tasks(self) -> [asyncio.Task, asyncio.Task]:
        while self.get_init_complete() is False:
            await asyncio.sleep(0.1)
        return [self.reference_task, self.receive_task]

    def get_services_available(self) -> bool:
        return self.services_available

    async def wait_for_services(self, timeout: float = -1.0) -> None:
        timestep = 0.01
        n = 0
        while True:
            if self.get_services_available() is True:
                return
            elif timeout >= 0 and n > timeout / timestep:
                raise RuntimeError("Timeout occurred before services were received")
            n = n + 1
            await asyncio.sleep(timestep)

    async def send_request_frame(self) -> None:
        out_data = StageLinQRequestServices()
        service_request_message = out_data.encode_frame(
            StageLinQServiceRequestService(Token=self.OwnToken)
        )

        self.writer.write(service_request_message)
        await self.writer.drain()

    async def start_receive_data(self) -> None:
        # Send first message

        self.reader, self.writer = await asyncio.open_connection(self.Ip, self.Port)
        self.reference_task = asyncio.create_task(
            self.send_reference_message_periodically()
        )
        asyncio.create_task(self.send_request_frame())

        self.init_complete = True

        await self._receive_data_loop()

    def get_loop_condition(self) -> bool:
        return self._loopcondition

    async def _receive_data_loop(self) -> None:
        while self.get_loop_condition() is True:
            frames = await self._receive_frames()

            if frames is False:
                continue

            await self._handle_frames(frames)

    async def _receive_frames(
        self,
    ) -> (
        bool
        | list[
            StageLinQServiceAnnouncementData
            | StageLinQReferenceData
            | StageLinQServiceRequestService
        ]
    ):
        response = await self.reader.read(1024)
        if len(response) == 0:
            # Socket closed
            raise RuntimeError(
                f"Remote socket for IP:{self.Ip} Port:{self.Port} closed!"
            )

        if self.remaining_data is not None:
            response = b"".join([self.remaining_data, response])
        frames, self.remaining_data = self.decode_multiframe(response)
        if frames is None:
            # Something went wrong during decoding, lets throw away the frame and hope it doesn't happen again
            logger.debug(f"Error while decoding the frame")
            return False
        self.last_frame = response
        return frames

    async def _handle_frames(self, frames: bytes) -> None:
        adding_services = False
        for frame in frames:
            if type(frame) is StageLinQServiceAnnouncementData:
                self.service_list.append([frame.Service, frame.Port])
                adding_services = True
                self._set_device_token(frame)

            elif type(frame) is StageLinQServiceRequestService:
                self._set_device_token(frame)

            elif type(frame) is StageLinQReferenceData:
                # Do not send a new frame if read frame is from ourselves.
                if frame.OwnToken.get_token() != self.OwnToken.get_token():
                    asyncio.create_task(self.send_reference_message())

        if adding_services:
            await self._handle_new_services()

    async def _handle_new_services(self) -> None:
        self.services_available = True
        if self.service_found_callback is not None:
            await self.service_found_callback(self)

    def _set_device_token(
        self,
        data_class: StageLinQServiceAnnouncementData | StageLinQServiceRequestService,
    ) -> None:
        if (type(data_class) is StageLinQServiceAnnouncementData) or (
            type(data_class) is StageLinQServiceRequestService
        ):
            if self.DeviceToken.get_token() == 0:
                self.DeviceToken.set_token(
                    int.from_bytes(data_class.Token, byteorder="big")
                )

    async def send_reference_message_periodically(self) -> None:
        while self.get_loop_condition():
            # Checking services_available is a really simple way of knowing if a link has been established, and initial
            # handshake is done
            if self.services_available:
                await self.send_reference_message()
            await asyncio.sleep(0.250)

    async def send_reference_message(self) -> None:
        reference_data = StageLinQReferenceData(
            OwnToken=self.OwnToken, DeviceToken=self.DeviceToken, Reference=0
        )
        reference_message = StageLinQReference()
        reference_message.encode_frame(reference_data)

        self.writer.write(reference_message.encode_frame(reference_data))
        await self.writer.drain()

    @staticmethod
    def decode_multiframe(
        frame: bytes,
    ) -> tuple[list[Any], None | bytes] | None:
        subframes = []
        while len(frame) >= 4:
            match (int.from_bytes(frame[0:4], byteorder="big")):
                case 0:
                    data = StageLinQServiceAnnouncement()
                case 1:
                    data = StageLinQReference()
                case 2:
                    data = StageLinQRequestServices()
                case _:
                    # invalid data, return
                    return None
            decode_status = data.decode_frame(frame)

            if decode_status != PyStageLinQError.STAGELINQOK:
                if decode_status == PyStageLinQError.INVALIDLENGTH:
                    return subframes, frame
                else:
                    return None

            subframes.append(data.get())
            frame = frame[data.get_len() :]

        return subframes, None
