from browser import document, alert, svg
from browser import websocket
import browser
from browser.html import LI

import json
import logging
game_name = None
board_size = None
is_my_turn = None


def trans(position):
    return position * 30 + 15


def on_message(evt):
    # board = ast.literal_eval(evt.data)
    # need to fix, but ast not loaded; should parse manually
    global is_my_turn
    board, stones, scores, pairs, is_my_turn = json.loads(evt.data)

    for x in range(board_size):
        for y in range(board_size):
            document[f"{x},{y}"].attrs['class'] = board[x][y]
    stones_div = document['stones']
    stones_div.clear()
    blacks, whites = stones
    for stone in blacks:
        circle = svg.circle(fill="black",
                            cx=trans(stone[0]),
                            cy=trans(stone[1]), r="15")
        stones_div <= circle
    for stone in whites:
        circle = svg.circle(fill="white",
                            cx=trans(stone[0]),
                            cy=trans(stone[1]), r="15")
        stones_div <= circle
    for pair in pairs[0]:
        line = svg.line(stroke="black",
                        x1=trans(pair[0][0]),
                        x2=trans(pair[1][0]),
                        y1=trans(pair[0][1]),
                        y2=trans(pair[1][1]))
        stones_div <= line
    for pair in pairs[1]:
        line = svg.line(stroke="white",
                        x1=trans(pair[0][0]),
                        x2=trans(pair[1][0]),
                        y1=trans(pair[0][1]),
                        y2=trans(pair[1][1]))
        stones_div <= line
    document['black-score'].text = scores[0]
    document['white-score'].text = scores[1]


def on_click(ev):
    global is_my_turn
    if is_my_turn:
        ws.send(ev.target.id)
        is_my_turn = False


def on_open(evt):
    logging.info("Opened connection; creating initial board")
    global game_name
    global board_size
    game_name = document.select('div#rules')[0].attrs['game_name']
    board_size = int(document.select('div#rules')[0].attrs['board_size'])
    ws.send(game_name)
    ws.send(str(board_size))

    logging.debug("Binding events to board squares and buttons")
    for x in range(board_size):
        for y in range(board_size):
            ident = f"{x},{y}"
            document[ident].bind("click", on_click)
    document['undo'].bind("click", on_click)
    document['pass'].bind("click", on_click)
    logging.info("Binding complete")


ws = websocket.WebSocket("ws://localhost:8765")
ws.bind('open', on_open)
ws.bind('message', on_message)
logging.info("Bound message/open functions to websocket")
logging.info(ws)
