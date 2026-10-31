"""Tests of the game server's websocket protocol, against the real server.

These pin the messages the browser client (`app/static/js/board.py` and
`list_games.py`) sends and expects, so a rewrite of the client can be checked
against the same contract:

- "list games" -> a JSON list of {"game_name", "board_size"} for games that
  are waiting for a second player.
- "new game", then the game name, then a JSON object of settings, all strings
  except board_size, as board.py sends them.
- "join game", then the game name.
- During play, the player to move is sent a board with is_my_turn true, and
  answers with "x,y", "pass" or "undo". Both players are then sent the result.
"""
import contextlib
import json
import time

import pytest
from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect

TIMEOUT = 5

BOARD_KEYS = {'board', 'stones', 'pairs', 'area_scores', 'stone_scores',
              'is_my_turn', 'show_scores'}


def settings(**overrides):
    """Settings as board.py sends them: board_size an int, the rest strings."""
    result = {
        'board_size': 5,
        'allow_suicide': 'True',
        'play_in_own_overlap': 'False',
        'play_black': 'True',
        'handicap': '1',
        'overlap': 'go',   # plain go: one-point overlap, orthogonal neighbours
        'show_scores': 'False',
    }
    result.update(overrides)
    return result


@pytest.fixture
def open_ws(ws_url):
    """Return a function that opens a client connection to the game server;
    every connection it opens is closed when the test ends."""
    with contextlib.ExitStack() as stack:
        yield lambda: stack.enter_context(connect(ws_url))


def recv_json(ws, timeout=TIMEOUT):
    return json.loads(ws.recv(timeout=timeout))


def assert_silent(ws, timeout=0.3):
    """Nothing more arrives on ws within the timeout."""
    with pytest.raises(TimeoutError):
        ws.recv(timeout=timeout)


def list_games(url):
    with connect(url) as ws:
        ws.send("list games")
        return recv_json(ws)


def wait_for_listing(url, predicate):
    """Poll "list games" until predicate(listing) holds; the server registers
    a game asynchronously after it receives the settings."""
    deadline = time.monotonic() + TIMEOUT
    while True:
        listing = list_games(url)
        if predicate(listing) or time.monotonic() > deadline:
            return listing
        time.sleep(0.02)


def create_game(open_ws, url, name="g1", **overrides):
    ws = open_ws()
    ws.send("new game")
    ws.send(name)
    ws.send(json.dumps(settings(**overrides)))
    wait_for_listing(url, lambda games: any(g['game_name'] == name
                                            for g in games))
    return ws


def join_game(open_ws, name="g1"):
    ws = open_ws()
    ws.send("join game")
    ws.send(name)
    return ws


def start_game(open_ws, url, name="g1", **overrides):
    """Create and join a game; return (black, white) connections."""
    creator = create_game(open_ws, url, name, **overrides)
    joiner = join_game(open_ws, name)
    if overrides.get('play_black', 'True') == 'True':
        return creator, joiner
    return joiner, creator


def play(mover, other, move):
    """Take one turn: mover is told it is their turn, sends move, and both
    are sent the result. Returns (mover's result, other's result)."""
    prompt = recv_json(mover)
    assert prompt['is_my_turn'] is True
    assert 'done' not in prompt
    mover.send(move)
    return recv_json(mover), recv_json(other)


def stones(msg):
    """The stones in a board message, as (black, white) sets of tuples."""
    black, white = msg['stones']
    return {tuple(s) for s in black}, {tuple(s) for s in white}


# --- list games ------------------------------------------------------------

def test_list_games_empty(ws_url):
    assert list_games(ws_url) == []


def test_list_games_shows_waiting_game_then_hides_started_one(ws_url, open_ws):
    black = create_game(open_ws, ws_url, "waiting", board_size=7)
    assert list_games(ws_url) == [{'game_name': 'waiting', 'board_size': 7}]

    white = join_game(open_ws, "waiting")
    recv_json(black)   # the game has started once black is prompted
    assert list_games(ws_url) == []


# --- play ------------------------------------------------------------------

def test_first_prompt_goes_to_black_with_an_empty_board(ws_url, open_ws):
    black, white = start_game(open_ws, ws_url)
    prompt = recv_json(black)
    assert BOARD_KEYS <= prompt.keys()
    assert prompt['is_my_turn'] is True
    assert prompt['board'] == [['empty'] * 5 for _ in range(5)]
    assert prompt['stones'] == [[], []]
    assert_silent(white)


def test_creator_plays_white_when_play_black_unchecked(ws_url, open_ws):
    creator = create_game(open_ws, ws_url, play_black='False')
    joiner = join_game(open_ws)
    assert recv_json(joiner)['is_my_turn'] is True
    assert_silent(creator)


def test_move_is_sent_to_both_players(ws_url, open_ws):
    black, white = start_game(open_ws, ws_url)
    to_black, to_white = play(black, white, "2,3")

    for msg in (to_black, to_white):
        assert stones(msg) == ({(2, 3)}, set())
        assert msg['board'][2][3] == 'overlap'
        assert 'warning' not in msg
    assert to_black['is_my_turn'] is False
    assert to_white['is_my_turn'] is True

    to_white, to_black = play(white, black, "0,0")
    assert stones(to_black) == ({(2, 3)}, {(0, 0)})
    assert to_black['is_my_turn'] is True


def test_capture(ws_url, open_ws):
    black, white = start_game(open_ws, ws_url)
    play(black, white, "0,1")
    play(white, black, "0,0")
    to_black, to_white = play(black, white, "1,0")
    assert stones(to_white) == ({(0, 1), (1, 0)}, set())
    assert to_white['stone_scores'] == [2, 0]


def test_invalid_move_warns_only_the_mover_who_moves_again(ws_url, open_ws):
    black, white = start_game(open_ws, ws_url)
    play(black, white, "2,2")
    to_white, to_black = play(white, black, "2,2")

    assert 'warning' in to_white
    assert 'warning' not in to_black
    assert to_white['is_my_turn'] is True
    assert to_black['is_my_turn'] is False
    assert stones(to_white) == ({(2, 2)}, set())

    to_white, to_black = play(white, black, "1,1")
    assert stones(to_black) == ({(2, 2)}, {(1, 1)})


@pytest.mark.parametrize("move", ["9,9", "-1,0", "1", "foo", "1,2,3", "'a','b'"])
def test_malformed_move_warns_and_the_game_goes_on(ws_url, open_ws, move):
    black, white = start_game(open_ws, ws_url)
    play(black, white, "2,2")
    play(white, black, "3,3")
    to_black, to_white = play(black, white, move)
    assert 'warning' in to_black
    assert 'warning' not in to_white
    assert to_black['is_my_turn'] is True
    # the earlier moves are untouched
    assert stones(to_black) == ({(2, 2)}, {(3, 3)})

    to_black, to_white = play(black, white, "0,0")
    assert stones(to_white) == ({(2, 2), (0, 0)}, {(3, 3)})


def test_undo_takes_back_the_opponents_last_move(ws_url, open_ws):
    """Only the player to move can undo, and it removes the opponent's last
    move: you cannot take back your own move unless your opponent agrees."""
    black, white = start_game(open_ws, ws_url)
    play(black, white, "1,1")
    play(white, black, "3,3")
    to_black, to_white = play(black, white, "undo")

    for msg in (to_black, to_white):
        assert stones(msg) == ({(1, 1)}, set())
    assert to_white['is_my_turn'] is True
    assert to_black['is_my_turn'] is False

    to_white, to_black = play(white, black, "2,2")
    assert stones(to_black) == ({(1, 1)}, {(2, 2)})


def test_pass(ws_url, open_ws):
    black, white = start_game(open_ws, ws_url)
    to_black, to_white = play(black, white, "pass")
    assert stones(to_white) == (set(), set())
    assert to_white['is_my_turn'] is True
    assert 'done' not in to_white


def test_three_passes_end_the_game_and_nothing_follows(ws_url, open_ws):
    black, white = start_game(open_ws, ws_url, show_scores='True')
    play(black, white, "0,0")
    play(white, black, "pass")
    play(black, white, "pass")
    to_white, to_black = play(white, black, "pass")

    for msg in (to_black, to_white):
        assert msg['done'] is True
        assert msg['is_my_turn'] is False
        assert msg['area_scores'] == [25, 0]
        assert msg['stone_scores'] == [1, 0]
    # The board page would show "Click on the board to move" again if the
    # server went on to prompt anyone.
    assert_silent(black)
    assert_silent(white)


def test_show_scores_is_passed_through(ws_url, open_ws):
    black, white = start_game(open_ws, ws_url, show_scores='True')
    assert recv_json(black)['show_scores'] is True


def test_handicap_gives_black_extra_moves(ws_url, open_ws):
    black, white = start_game(open_ws, ws_url, handicap='3')
    play(black, white, "0,0")
    play(black, white, "2,2")
    to_black, to_white = play(black, white, "4,4")
    assert to_white['is_my_turn'] is True
    assert stones(to_white) == ({(0, 0), (2, 2), (4, 4)}, set())


# --- bad requests ----------------------------------------------------------

@pytest.mark.parametrize("bad", [{'overlap': 'hexagonal'},
                                 {'board_size': 52},
                                 {'board_size': 0}])
def test_bad_settings_close_the_connection_and_list_nothing(ws_url, open_ws, bad):
    ws = open_ws()
    ws.send("new game")
    ws.send("bad")
    ws.send(json.dumps(settings(**bad)))
    with pytest.raises(ConnectionClosed) as excinfo:
        ws.recv(timeout=TIMEOUT)
    assert excinfo.value.rcvd.code == 1008
    assert list_games(ws_url) == []


@pytest.mark.xfail(strict=True, raises=TimeoutError,
                   reason="GENGO-8: the server has no error reply")
def test_join_unknown_game_gets_an_error(ws_url, open_ws):
    ws = join_game(open_ws, "no-such-game")
    assert 'error' in recv_json(ws, timeout=1)


@pytest.mark.xfail(strict=True, raises=TimeoutError,
                   reason="GENGO-8: the server has no error reply")
def test_new_game_with_a_taken_name_gets_an_error(ws_url, open_ws):
    create_game(open_ws, ws_url, "taken")
    ws = open_ws()
    ws.send("new game")
    ws.send("taken")
    ws.send(json.dumps(settings()))
    assert 'error' in recv_json(ws, timeout=1)


@pytest.mark.xfail(strict=True, raises=TimeoutError,
                   reason="GENGO-8: the server has no error reply")
def test_join_started_game_gets_an_error(ws_url, open_ws):
    black, white = start_game(open_ws, ws_url, "full")
    recv_json(black)
    third = join_game(open_ws, "full")
    assert 'error' in recv_json(third, timeout=1)
