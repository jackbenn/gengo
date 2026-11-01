from browser import document
from browser import websocket
from browser import window
from browser.html import LI, A, EM

import json


received = False


def on_message(evt):
    global received
    received = True
    games = json.loads(evt.data)
    game_list = document['games']
    game_list.classList.remove('error')
    game_list.text = ''
    if not games:
        li = LI()
        li <= EM("(no active games)")
        game_list <= li
    else:
        for game_data in games:
            game_name = game_data["game_name"]
            board_size = int(game_data["board_size"])
            li = LI()
            a = A(game_name)
            a.attrs["href"] = ("/gengo/game?game_name=" +
                               window.encodeURIComponent(game_name) +
                               f"&board_size={board_size}&action=join")
            li <= a
            game_list <= li


def on_open(evt):
    ws.send("list games")


def on_close(evt):
    # The server closes the connection once it has sent the list; closing
    # before that means something went wrong.
    if not received:
        game_list = document['games']
        game_list.text = "Couldn\u2019t reach the game server. Reload the page to try again."
        game_list.classList.add('error')


def websocket_url():
    """The page's data-ws-url if the app sets one (local development, where
    the game server is reached directly); otherwise nginx's /gengo/ws proxy,
    matching the page's protocol (browsers block ws:// from an https://
    page)."""
    url = document.body.attrs.get('data-ws-url', '')
    if url:
        return url
    proto = "wss" if window.location.protocol == "https:" else "ws"
    return f"{proto}://{window.location.host}/gengo/ws"



ws = websocket.WebSocket(websocket_url())
ws.bind('open', on_open)
ws.bind('message', on_message)
ws.bind('close', on_close)
