import asyncio
import websockets

async def hello():
    uri = "ws://localhost:8080"
    async with websockets.connect(uri) as websocket:
        while True:
            line = await websocket.recv()
            print(type(line))
            print(line)

asyncio.get_event_loop().run_until_complete(hello())
