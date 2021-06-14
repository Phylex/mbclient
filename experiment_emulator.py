import mbdatatypes as mbd
import websockets as ws
import numpy as np
import asyncio
import sys

async def send_out_data(websocket, path):
    with open(sys.argv[1]) as f:
        _ = f.readline()
        while True:
            linecount = np.random.randint(100)
            lines = f.readlines(20*linecount)
            if len(lines) == 0:
                websocket.send(None)
            for line in lines:
                await websocket.send(line)

start_server = ws.serve(send_out_data, "localhost", 8080)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
