#!/usr/bin/env python

# WS server example

import asyncio
import websockets

from ..src.gengo import Board, GridBoard, Rules, Player, Game

async def start_game(websocket, path):
    print("is this working?")
    rules = Rules([(0, 0), (1, 0), (0, 1), (1, 1)],
                  [(2, 0), (0, 2), (2, 1), (1, 2)],
                  11)
    gb = GridBoard(rules)

    p1 = Player("X", "X", 1)
    p2 = Player("O", "O", 2)

    game = Game((p1, p2), gb)


    while True:
        print("inside loop")
        print(game)

        move = await websocket.recv()
        print(f"< ({move})")
        move = eval(move)
        game.move(move)
        print(game)

        response = str(game)

        await websocket.send(response)
        print(f"> ({response})")



start_server = websockets.serve(start_game, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()