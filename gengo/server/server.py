#!/usr/bin/env python

# WS server example

import asyncio
import websockets
import json
import ast

from ..src.gengo import Board, GridBoard, Rules, Player, Game, InvalidMove

import logging
logger = logging.getLogger('websockets')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

connections = {}

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

        response = json.dumps(game.board.colors())
        print(f">json ({response})")

        await websocket.send(response)

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
        print("inside loop")
        print(game)

        for websocket in [websocket1, websocket2]:
            print("waiting for move")
            if websocket1.open:
                print("1 is open")
            if websocket1.closed:
                print("1 is closed")
            if websocket2.open:
                print("2 is open")
            if websocket2.closed:
                print("2 is closed")
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

            response = json.dumps(game.board.colors())
            print(f">json ({response})")

            await websocket.send(response)
        print("DONE WITH ONE ROUND")
    print("DONE WITH INFINITE LOOP")

async def get_connection(websocket, path):
    game_name = await websocket.recv()
    if game_name not in connections:
        # can shorted in python 3.7
        print("creating task")
        task = asyncio.get_event_loop().create_task(run_game(game_name))
        print("task created")
        # we should probably save the tasks somewhere??
        connections[game_name] = asyncio.Queue()
    
        print("awaiting put")
        await connections[game_name].put(websocket)
        print("awaiting task")
        await task
        print("TASK COMPLETE")
    else:
        print("awaiting 2nd put")
        await connections[game_name].put(websocket)
        print("done with 2nd put")
    while True:
        print("sleeping a little in connection")
        await asyncio.sleep(10)

start_server = websockets.serve(get_connection, 'localhost', 8765)

loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()
