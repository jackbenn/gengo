from browser import document, alert, svg
from browser import websocket
import browser
from browser.html import LI

import json


def on_message(evt):

    games = json.loads(evt.data)
    game_list = document['games']
    for game in games:
        li = LI(game)
        game_list <= li


def on_open(evt):
    ws.send("list games")


ws = websocket.WebSocket("ws://localhost:8765")
ws.bind('open', on_open)
ws.bind('message', on_message)
print("Bound message/open functions to websocket")
print(ws)
