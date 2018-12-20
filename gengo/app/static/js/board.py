from browser import document, alert
from browser import websocket
#import ast
size = 11

def on_message(evt):
    #board = ast.literal_eval(evt.data)
    # need to fix, but ast not loaded; should parse manually
    board = eval(evt.data)
    for x in range(size):
        for y in range(size):
            document[f"{x},{y}"].attrs['fill'] = board[x][y]

    #alert(f"Message received: {evt.data}")

ws = websocket.WebSocket("ws://localhost:8765")
ws.bind('message', on_message)

def on_click(ev):
    document[ev.target.id].attrs['fill'] = "black"
    ws.send(ev.target.id)


for x in range(size):
    for y in range(size):
        ident = f"{x},{y}"
        document[ident].bind("click", on_click)

