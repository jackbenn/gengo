from browser import document, alert
from browser import websocket
import browser
import json
board_size = None


def on_message(evt):
    # board = ast.literal_eval(evt.data)
    # need to fix, but ast not loaded; should parse manually
    board, stones = json.loads(evt.data)
    print(board)
    print(stones)
    for x in range(board_size):
        for y in range(board_size):
            document[f"{x},{y}"].attrs['fill'] = board[x][y]
    stones_div = document['svg']
    blacks, whites = stones
    for stone in blacks:
        circle = document.createElement("circle")
        circle.attrs['cx'] = stone[0] * 30
        circle.attrs['cy'] = stone[1] * 30
        circle.attrs['r'] = "100"
        circle.attrs['stroke'] = 'red'
        circle.attrs['fill'] = 'white'
        alert(circle)
        stones_div <= circle
    for stone in whites:
        circle = document.createElement("circle")
        circle.attrs['cx'] = stone[0]
        circle.attrs['cy'] = stone[1]
        circle.attrs['r'] = 30
        circle.attrs['stroke'] = 'red'
        circle.attrs['fill'] = 'white'
        stones_div <= circle

def on_click(ev):
    document[ev.target.id].attrs['fill'] = "black"
    ws.send(ev.target.id)


def on_open(evt):
    global board_size
    board_size = int(document.select('div#rules')[0].attrs['board_size'])
    ws.send(str(board_size))

    for x in range(board_size):
        for y in range(board_size):
            ident = f"{x},{y}"
            document[ident].bind("click", on_click)


ws = websocket.WebSocket("ws://localhost:8765")
ws.bind('message', on_message)
ws.bind('open', on_open)
