#!/usr/bin/env python

# WS server example

import asyncio
import websockets

from ..src.gengo import Board

async def hello(websocket, path):

    while True:
        name = await websocket.recv()
        print(f"< {name}")

        greeting = f"Clicked in {name}!"

        await websocket.send(greeting)
        print(f"> {greeting}")

start_server = websockets.serve(hello, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()