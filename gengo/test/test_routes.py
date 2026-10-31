"""Tests of the Flask pages, through Flask's test client.

The game page carries the game's settings to board.py as attributes of
div#rules, which board.py sends on to the game server; the server compares
the flags against the strings "True" and "False". These tests pin that.
"""
from html.parser import HTMLParser

import pytest

from ..app.routes import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class _RulesFinder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rules = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div' and attrs.get('id') == 'rules':
            self.rules = attrs


def rules_of(response):
    """The attributes of div#rules in a game page, as board.py sees them."""
    finder = _RulesFinder()
    finder.feed(response.get_data(as_text=True))
    assert finder.rules is not None, "no div#rules on the page"
    return finder.rules


def test_index(client):
    response = client.get('/gengo/')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'id="games"' in page            # list_games.py fills this
    assert 'action="/gengo/game"' in page  # the new-game form


@pytest.mark.parametrize("path", ["/gengo/new", "/gengo/join"])
def test_old_pages_redirect_to_index(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/gengo/')


def test_static_files_are_served_under_gengo(client):
    response = client.get('/gengo/static/js/board.py')
    assert response.status_code == 200
    response.close()


def test_new_game_with_every_option(client):
    response = client.get('/gengo/game', query_string={
        'game_name': 'g1', 'board_size': '9', 'action': 'new',
        'allow_suicide': 'on', 'play_in_own_overlap': 'on',
        'play_black': 'on', 'handicap': '3', 'overlap': 'large-n',
        'show_scores': 'on'})
    assert response.status_code == 200
    assert rules_of(response) == {
        'id': 'rules', 'game_name': 'g1', 'board_size': '9',
        'allow_suicide': 'True', 'play_in_own_overlap': 'True',
        'play_black': 'True', 'handicap': '3', 'overlap': 'large-n',
        'show_scores': 'True', 'action': 'new'}


def test_new_game_with_no_options(client):
    """Unchecked boxes are absent from the form; a blank handicap is 1."""
    response = client.get('/gengo/game', query_string={
        'game_name': 'g1', 'board_size': '19', 'action': 'new',
        'handicap': '', 'overlap': 'standard'})
    rules = rules_of(response)
    assert rules['allow_suicide'] == 'False'
    assert rules['play_in_own_overlap'] == 'False'
    assert rules['play_black'] == 'False'
    assert rules['show_scores'] == 'False'
    assert rules['handicap'] == '1'


def test_join_game(client):
    """A joiner's settings come from the creator, so the page sends
    placeholders that the server ignores."""
    response = client.get('/gengo/game', query_string={
        'game_name': 'g1', 'board_size': '11', 'action': 'join'})
    assert response.status_code == 200
    rules = rules_of(response)
    assert rules['action'] == 'join'
    assert rules['game_name'] == 'g1'
    assert rules['board_size'] == '11'


def test_board_has_a_square_per_point(client):
    response = client.get('/gengo/game', query_string={
        'game_name': 'g1', 'board_size': '5', 'action': 'join'})
    page = response.get_data(as_text=True)
    # board.py binds clicks to, and sends, ids of the form "x,y"
    assert 'id="0,0"' in page and 'id="4,4"' in page
    assert 'id="5,5"' not in page
    for button in ('pass', 'undo', 'status'):
        assert f'id="{button}"' in page


@pytest.mark.parametrize("name", ["my game", 'say "hi"', "x onclick=alert(1)"])
def test_game_name_survives_spaces_and_quotes(client, name):
    response = client.get('/gengo/game', query_string={
        'game_name': name, 'board_size': '5', 'action': 'join'})
    rules = rules_of(response)
    assert rules['game_name'] == name
    assert 'onclick' not in rules


@pytest.mark.parametrize("query", [
    {'game_name': 'g1', 'action': 'join'},
    {'game_name': 'g1', 'board_size': 'big', 'action': 'join'},
    {'game_name': 'g1', 'board_size': '0', 'action': 'join'},
    {'game_name': 'g1', 'board_size': '52', 'action': 'join'},
])
def test_bad_board_size_is_a_400(client, query):
    assert client.get('/gengo/game', query_string=query).status_code == 400


def test_largest_board_is_allowed(client):
    response = client.get('/gengo/game', query_string={
        'game_name': 'g1', 'board_size': '51', 'action': 'join'})
    assert response.status_code == 200
