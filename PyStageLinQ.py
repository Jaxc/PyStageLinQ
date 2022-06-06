
"""
License TBD
"""
import select
import socket
import time
from random import randbytes

class PyStageLinQ:

    # PyStageLinQ Error codes
    STAGELINQOK         = 0

    DISCOVERYTIMEOUT    = 100

    INVALIDFRAME        = 200
    MAGICFLAGNOTFOUND   = 201


    TOKENLENGTH                     = 16
    FRAMEIDLENGTH                   = 4
    # Message ID's:
    serviceAnnouncementMessageID    = 0
    referenceMessageID              = 1
    servicesRequestMessage          = 2


    def __init__(self):
        self.ownToken = randbytes(self.TOKENLENGTH)
        pass

    def announceSelf(self):
        

    def discoverStageLinQDevice(self, timeout = 10):
        """
        This function can be used to find StageLinQ devices.
        """

        # Local Constants
        StageLinQPort = 51337
        DiscoverBufferSize = 8192

        # Create socket
        discoverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discoverSocket.bind(("", StageLinQPort)) # bind socket to all interfaces
        discoverSocket.setblocking(0)

        loop_timeout = time.time() + timeout

        while True:
            dataAvailable = select.select([discoverSocket], [], [], loop_timeout - time.time() )
            if dataAvailable[0]:
                data, addr = discoverSocket.recvfrom(DiscoverBufferSize)
                if self.STAGELINQOK != self.decodeDiscoveryFrame(data) :
                    continue
                print(addr[1])
                self.connectToStageLinQDevice(addr[0])


            if time.time() > loop_timeout:
                return self.DISCOVERYTIMEOUT


    def decodeDiscoveryFrame(self, Frame):

        # Local Constants
        StageLinQMagicFlag = bytes('airD'.encode(encoding="ASCII"))
        MagicFlagStart          = 0
        MagicFlagLength         = 4
        MagicFlagStop           = MagicFlagStart + MagicFlagLength
        TokenStart              = MagicFlagStop
        TokenLength             = self.TOKENLENGTH
        TokenStop               = TokenStart + TokenLength
        DeviceNameSizeStart     = TokenStop
        PortLength              = 2



        if len(Frame) < 4:
            return self.INVALIDFRAME

        # Check if Frame contains Magic flag
        if StageLinQMagicFlag != Frame[MagicFlagStart:MagicFlagStop]:
            return self.MAGICFLAGNOTFOUND

        self.token = Frame[TokenStart:TokenStop]

        ConnectionTypeStart, DeviceName = self.ReadBytesFromFrame(Frame, DeviceNameSizeStart)
        SwNameStart, ConnectionType = self.ReadBytesFromFrame(Frame, ConnectionTypeStart)
        SwVersionStart, SwName = self.ReadBytesFromFrame(Frame, SwNameStart)
        PortStart, SwVersion = self.ReadBytesFromFrame(Frame, SwVersionStart)
        PortStop = PortStart + PortLength
        self.Port = int.from_bytes(Frame[PortStart:PortStop], byteorder='big')

        print(f"Found Device: {DeviceName}, ConnectionType: {ConnectionType}, SwName: {SwName}, SwVersion: {SwVersion}, Port: {self.Port}")
        return self.STAGELINQOK

    def ReadBytesFromFrame(self, Frame, StartOffset):

        # Only uint32 length supported
        SizeLength    = 4
        SizeStop      = StartOffset + SizeLength
        DataStart     = SizeStop

        DataLength = int.from_bytes(Frame[StartOffset:SizeStop], byteorder='big')
        DataStop = DataStart + DataLength

        if DataStop > len(Frame):
            # Out of bounds
            return

        return DataStop, Frame[DataStart:DataStop].decode(encoding='UTF-16be')

    def connectToStageLinQDevice(self, ip):


        self.StageLinQSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.StageLinQSocket.connect((ip, self.Port))
        reference_message = self.servicesRequestMessage.to_bytes(self.FRAMEIDLENGTH, byteorder='big')
        reference_message += self.token
        self.StageLinQSocket.send(reference_message)
        self.StageLinQSocket.recvfrom(1024)

        pass


        pass


if __name__ == "__main__":
    # Test code for class
    StageLinQ = PyStageLinQ()
    StageLinQ.discoverStageLinQDevice(timeout=5)
