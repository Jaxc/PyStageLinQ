"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""

import PyStageLinQ
import asyncio


"""
Processes needed for StageLinQ:
1. Announce: Send discovery frame every 1 s
2. Negotiation: Reading Device discovery messages and request services.
3. Service Server: Open TCP socket ? 
"""

def main():
    # Init non parallel functions.

    #server = await asyncio.start_server(StageLinQ.HandleRequestService, '', PyStageLinQ.REQUESTSERVICEPORT)

    #addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    #print(f'Serving on {addrs}')
    PyStageLinQ.PyStageLinQ(name="Jaxcie StagelinQ")




if __name__ == "__main__":
    main()
    #StageLinQ = PyStageLinQ(name="Jaxcie StagelinQ")
    #StageLinQ.StartPyStageLinQ()
    #StageLinQ.discoverStageLinQDevice(timeout=2)
    #StageLinQ.leave()

