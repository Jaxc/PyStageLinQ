"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""

from PyStageLinQ import PyStageLinQ
import asyncio


is_running = True

async def periodic_announcement(PyStageLinQClass) -> PyStageLinQ:
    #Temp import here just to get the code running
    import asyncio
    while True:
        PyStageLinQClass.announceSelf()
        await asyncio.sleep(1)
        if not is_running:
            return


async def PyStageLinQStrapper(PyStageLinQClass) -> PyStageLinQ:
    global is_running
    await asyncio.sleep(1)

    PyStageLinQClass.discoverStageLinQDevice(timeout=2)
    is_running = False
"""
Processes needed for StageLinQ:
1. Announce: Send discovery frame every 1 s
2. Negotiation: Reading Device discovery messages and request services.
3. Service Server: Open TCP socket ? 
"""

async def main():
    # Init non parallel functions.

    #server = await asyncio.start_server(StageLinQ.HandleRequestService, '', PyStageLinQ.REQUESTSERVICEPORT)

    #addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    #print(f'Serving on {addrs}')

    StageLinQ = PyStageLinQ(name="Jaxcie StagelinQ")


    # Start up server sockets
    await asyncio.gather(
        periodic_announcement(StageLinQ),
        PyStageLinQStrapper(StageLinQ),
        #StageLinQ.discoverStageLinQDevice(timeout=5)
    )




if __name__ == "__main__":
    asyncio.run(main())
    #StageLinQ = PyStageLinQ(name="Jaxcie StagelinQ")
    #StageLinQ.StartPyStageLinQ()
    #StageLinQ.discoverStageLinQDevice(timeout=2)
    #StageLinQ.leave()

