#!/usr/bin/env python

# WS server example

import asyncio
import websockets
import json
import ast

from ..src.gengo import Board, GridBoard, Rules, Player, Game, InvalidMove

connections = {}


async def run_game(game_name):
    print("Waiting for first connection")
    websocket1 = await connections[game_name].get()
    print(websocket1)
    print("Waiting for second connection")
    websocket2 = await connections[game_name].get()
    print(websocket2)
    print("Got both connections")

    board_size = int(await websocket1.recv())

    print(f"creating a board of size {board_size}")

    # this should be the same.
    connection2_board_size = int(await websocket2.recv())
    assert(board_size == connection2_board_size)

    rules = Rules([(0, 0), (1, 0), (0, 1), (1, 1)],
                  [(2, 0), (0, 2), (2, 1), (1, 2)],
                  board_size)

    p1 = Player("X", "X", "black", 1)
    p2 = Player("O", "O", "white", 2)

    game = Game((p1, p2), rules)

    while True:

        for websocket in [websocket1, websocket2]:
            # first, send the current board,
            # plus that it's your turn
            response = json.dumps(game.board.colors() + (True,))
            print(f">json ({response})")
            await websocket.send(response)

            # second, wait for a move
            move = await websocket.recv()
            print(f"< ({move})")
            if move == "pass":
                move = None
                game.move(move)
            elif move == "undo":
                game = game.create_replay()
            else:
                move = ast.literal_eval(move)
                try:
                    game.move(move)
                except InvalidMove as e:
                    print(e)
                    game = game.create_replay()
            print(game)

            # third, send the results of the move,
            # plus that it's not your turn anymore
            response = json.dumps(game.board.colors() + (False,))
            print(f">json ({response})")

            await websocket.send(response)


async def get_connection(websocket, path):
    game_name = await websocket.recv()
    if game_name not in connections:
        # can shorted in python 3.7
        task = asyncio.get_event_loop().create_task(run_game(game_name))
        # we should probably save the tasks somewhere??
        connections[game_name] = asyncio.Queue()

        await connections[game_name].put(websocket)
        await task
    else:
        await connections[game_name].put(websocket)
    while True:
        print("sleeping a little in connection")
        await asyncio.sleep(60)

start_server = websockets.serve(get_connection, 'localhost', 8765)

loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()
