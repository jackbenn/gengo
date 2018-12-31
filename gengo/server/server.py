#!/usr/bin/env python

# WS server example

import asyncio
import websockets
import ast

from ..src.gengo import Board, GridBoard, Rules, Player, Game, InvalidMove

async def start_game(websocket, path):

    board_size = int(await websocket.recv())

    print(f"creating a board of size {board_size}")

    rules = Rules([(0, 0), (1, 0), (0, 1), (1, 1)],
                  [(2, 0), (0, 2), (2, 1), (1, 2)],
                  board_size)

    p1 = Player("X", "X", "black", 1)
    p2 = Player("O", "O", "white", 2)

    game = Game((p1, p2), rules)

    while True:
        print("inside loop")
        print(game)

        move = await websocket.recv()
        print(f"< ({move})")
        move = ast.literal_eval(move)

        try:
            game.move(move)
        except InvalidMove as e:
            print(e)
            game = game.create_replay()
        print(game)

        response = str(game.board.colors())

        await websocket.send(response)
        print(f"> ({response})")



start_server = websockets.serve(start_game, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()