from browser import document, alert, svg
from browser import websocket
from browser import window
import browser
from browser.html import LI, A, EM
import logging

import json


def on_message(evt):
    games = json.loads(evt.data)
    game_list = document['games']
    game_list.text = ''
    if not games:
        li = LI()
        li <= EM("(no active games)")
        game_list <= li
    else:
        for game_data in games:
            logging.info("Game data:", game_data)
            game_name = game_data["game_name"]
            board_size = int(game_data["board_size"])
            li = LI()
            a = A(game_name)
            a.attrs["href"] = f"/gengo/game?game_name={game_name}&board_size={board_size}&action=join"
            li <= a
            game_list <= li


def on_open(evt):
    ws.send("list games")


def websocket_url():
    """Connect through nginx's /gengo/ws proxy, matching the page's protocol
    (browsers block ws:// from an https:// page). A bare `flask run` on port
    5000 has no proxy, so go straight to the game server there."""
    if window.location.port == "5000":
        return f"ws://{window.location.hostname}:8765"
    proto = "wss" if window.location.protocol == "https:" else "ws"
    return f"{proto}://{window.location.host}/gengo/ws"


ws = websocket.WebSocket(websocket_url())
ws.bind('open', on_open)
ws.bind('message', on_message)
print("Bound message/open functions to websocket")
print(ws)
