from browser import document, alert
from browser import websocket

def on_message(evt):
    alert(f"Message received: {evt.data}")

ws = websocket.WebSocket("ws://localhost:8765")
ws.bind('message', on_message)

def on_click(ev):
    document[ev.target.id].attrs['fill'] = "black"
    ws.send('foobar')



for x in [1,2,3,4,5]:
    for y in [1,2,3,4,5]:
        ident = "space_{}_{}".format(x,y)
        document[ident].bind("click", on_click)

