#!/usr/bin/env python
import asyncio
import websockets
import json
import ast
import logging

from ..src.gengo import Board, GridBoard, Rules, Player, Game, InvalidMove

# for testing
#logging.basicConfig(level=logging.DEBUG)

games = {}


async def run_game(game_name):
    logging.info("Waiting for first connection")
    websocket1 = await games[game_name]['connections'].get()

    board_size = int(await websocket1.recv())
    allow_suicide = (await websocket1.recv()) == "True"
    play_black = (await websocket1.recv()) == "True"
    handicap = await websocket1.recv()
    handicap = int(handicap) if handicap.isdigit() else 1
    overlap = await websocket1.recv()
    if overlap == "standard":
        overlap_lists = ([(0, 0), (1, 0), (0, 1), (1, 1)],
                         [(2, 0), (0, 2), (2, 1), (1, 2)])
    elif overlap == "go":
        overlap_lists = ([(0, 0)],
                         [(1, 0)])
    elif overlap == "expanded":
        overlap_lists = ([(0, 0), (1, 0), (0, 1), (1, 1)],
                         [(2, 0), (0, 2), (2, 1), (1, 2), (2,2), (3,0), (0,3), (3,1), (1,3)])

    logging.info(f"creating a board of size {board_size}")
    logging.info(f"allow_suicide {allow_suicide}")
    logging.info(f"play_black {play_black}")
    logging.info(f"handicap {handicap}")
    games[game_name]['board_size'] = board_size

    logging.info("Waiting for second connection")
    websocket2 = await games[game_name]['connections'].get()
    logging.info("Got both connections")

    rules = Rules(*overlap_lists,
                  size=board_size,
                  allow_suicide=allow_suicide,
                  handicap=handicap)

    p1 = Player("X", "X", "black", 1)
    p2 = Player("O", "O", "white", 2)

    game = Game((p1, p2), rules)

    if play_black:
        websockets = [websocket1, websocket2]
    else:
        websockets = [websocket2, websocket1]
    
    while True:
        this_player = game.next_player
        websocket = websockets[this_player]

        # first, send the current board,
        # plus that it's your turn
        game_data = game.board.get_game_data()
        game_data['is_my_turn'] = True
        response = json.dumps(game_data)
        logging.info(f">json ({response})")
        await websocket.send(response)

        # second, wait for a move
        move = await websocket.recv()
        logging.info(f"< ({move})")
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
                logging.warning(e)
                game = game.create_replay()
        logging.info(game)

        # third, send the results of the move,
        # plus that it's not your turn anymore
        game_data = game.board.get_game_data()
        game_data['is_my_turn'] = this_player == game.next_player
        response = json.dumps(game_data)
        logging.info(f">json ({response})")

        await websocket.send(response)


async def get_connection(websocket, path):
    action = await websocket.recv()
    print(action)
    if action == "list games":
        games_data = []
        for game_name in games:
            games_data.append({'game_name': game_name, 'board_size': games[game_name]['board_size']})
        game_names = json.dumps(list(games_data))
        logging.info(game_names)
        print("games: ", game_names)
        await websocket.send(game_names)

    if action == "new game":
        game_name = await websocket.recv()
        if game_name not in games:
            # can shorted in python 3.7
            task = asyncio.get_event_loop().create_task(run_game(game_name))
            # we should probably save the tasks somewhere??
            games[game_name] = {}
            games[game_name]['connections'] = asyncio.Queue()

            await games[game_name]['connections'].put(websocket)
            await task
        else:
            # give some sort of error
            pass
        while True:
            logging.info("sleeping a little in connection")
            await asyncio.sleep(60)
    elif action == "join game":
        game_name = await websocket.recv()
        if game_name not in games:
            # give some sort of error
            pass
        else:
            await games[game_name]['connections'].put(websocket)
        while True:
            logging.info("sleeping a little in connection")
            await asyncio.sleep(60)

start_server = websockets.serve(get_connection, None, 8765)

loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()
