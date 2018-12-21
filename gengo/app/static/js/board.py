from browser import document, alert
from browser import websocket
import browser
board_size = None


def on_message(evt):
    # board = ast.literal_eval(evt.data)
    # need to fix, but ast not loaded; should parse manually
    board = eval(evt.data)

    for x in range(board_size):
        for y in range(board_size):
            document[f"{x},{y}"].attrs['fill'] = board[x][y]


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
