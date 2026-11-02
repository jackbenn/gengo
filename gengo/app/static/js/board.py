from browser import document, alert, svg
from browser import websocket
from browser import window
from browser.html import A, BR

import json
import logging
game_name = None
board_size = None
is_my_turn = None
show_scores = False
game_over = False    # the game ended, or the server refused it

# for testing
# logging.basicConfig(level=logging.DEBUG)


def trans(position):
    return position * 30 + 15


def set_button_enabled(btn_id, enabled):
    btn = document[btn_id]
    if enabled:
        if 'disabled' in btn.attrs:
            del btn.attrs['disabled']
    else:
        btn.attrs['disabled'] = ''


def show_error(message):
    """Replace the status with message and a link back to the game list,
    and stop play."""
    global is_my_turn
    is_my_turn = False
    status = document['status']
    status.text = message
    status <= BR()
    status <= A("Back to the game list", href="/gengo/")
    status.classList.add('error')
    set_button_enabled('pass', False)
    set_button_enabled('undo', False)


def on_message(evt):
    global is_my_turn, show_scores, game_over
    data = json.loads(evt.data)
    logging.info(f"Got message with data {data}")
    if 'error' in data:
        # the server refused the request and is closing the connection
        game_over = True
        show_error(data['error'])
        return
    board = data['board']
    stones = data['stones']
    pairs = data['pairs']
    is_my_turn = data['is_my_turn']
    if 'show_scores' in data:
        show_scores = data['show_scores']

    if is_my_turn:
        document['status'].text = "Click on the board to move"
    else:
        document['status'].text = "Waiting for opponent to play"
    set_button_enabled('pass', is_my_turn)
    set_button_enabled('undo', is_my_turn)

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
    if show_scores or 'done' in data:
        document['black-area-score'].text = data['area_scores'][0]
        document['white-area-score'].text = data['area_scores'][1]
        document['black-stone-score'].text = data['stone_scores'][0]
        document['white-stone-score'].text = data['stone_scores'][1]
    if 'done' in data:
        game_over = True
        document['status'].text = "Game complete"

    if 'warning' in data:
        alert('Invalid move: ' + data['warning'])


def on_click(ev):
    global is_my_turn
    if is_my_turn and ev.target.id:
        ws.send(ev.target.id)
        is_my_turn = False


def on_close(evt):
    if not game_over:
        show_error("Lost the connection to the game server. "
                   "Reload the page to try again.")


def on_open(evt):
    logging.info("Opened connection; creating initial board")
    global game_name
    global board_size
    global show_scores
    div_rules = document.select('div#rules')[0]
    game_name = div_rules.attrs['game_name']
    board_size = int(div_rules.attrs['board_size'])
    allow_suicide = div_rules.attrs['allow_suicide']
    play_in_own_overlap = div_rules.attrs['play_in_own_overlap']
    play_black = div_rules.attrs['play_black']
    handicap = div_rules.attrs['handicap']
    overlap = div_rules.attrs['overlap']
    show_scores = div_rules.attrs['show_scores'] == 'True'
    action = div_rules.attrs['action']

    logging.info(f"action = {action}")
    if action == "new":
        document['status'].text = "Waiting for opponent to join"
        ws.send("new game")
        ws.send(game_name)
        ws.send(json.dumps({
            'board_size': board_size,
            'allow_suicide': allow_suicide,
            'play_in_own_overlap': play_in_own_overlap,
            'play_black': play_black,
            'handicap': handicap,
            'overlap': overlap,
            'show_scores': str(show_scores),
        }))
    elif action == "join":
        document['status'].text = "Waiting for opponent to play"
        ws.send("join game")
        ws.send(game_name)
    else:
        logging.error(f"Invalid action {action}")

    logging.debug("Binding events to board squares and buttons")
    for x in range(board_size):
        for y in range(board_size):
            ident = f"{x},{y}"
            document[ident].bind("click", on_click)
    document['undo'].bind("click", on_click)
    document['pass'].bind("click", on_click)
    logging.info("Binding complete")


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
logging.info("Bound message/open functions to websocket")
logging.info(ws)
