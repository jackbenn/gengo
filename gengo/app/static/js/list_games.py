from browser import document, alert, svg
from browser import websocket
from browser import window
import browser
from browser.html import LI, A
import logging

import json


def on_message(evt):
    games = json.loads(evt.data)
    game_list = document['games']
    for game_data in games:
        logging.info("Game data:", game_data)
        game_name = game_data["game_name"]
        board_size = int(game_data["board_size"])
        li = LI()
        a = A(game_name)
        a.attrs["href"] = f"/game?game_name={game_name}&board_size={board_size}&action=join"
        li <= a
        game_list <= li


def on_open(evt):
    ws.send("list games")


ws = websocket.WebSocket(f"ws://{window.location.hostname}:8765")
ws.bind('open', on_open)
ws.bind('message', on_message)
print("Bound message/open functions to websocket")
print(ws)
