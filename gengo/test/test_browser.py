"""Browser tests: the real pages, Brython client and game server together.

Opt-in, because they take a while and need Playwright and its browsers:

    pip install -r requirements-dev.txt
    python -m playwright install chromium firefox
    pytest --browser-tests

GENGO_BROWSERS picks the browsers (default "chromium,firefox"). WebKit, which
stands in for Safari, is left out by default: Playwright's WebKit build for
macOS 14 launches but hangs opening a page. Where it works, add it with
GENGO_BROWSERS=chromium,firefox,webkit; otherwise check Safari by hand.
"""
import os
import threading

import pytest

pytestmark = pytest.mark.browser
sync_api = pytest.importorskip("playwright.sync_api")
expect = sync_api.expect

from werkzeug.serving import make_server  # noqa: E402

from ..app.routes import app  # noqa: E402

# Brython compiles the scripts on first load, which takes a few seconds in a
# fresh browser profile.
LOAD_TIMEOUT = 30_000
TIMEOUT = 10_000

BROWSERS = os.environ.get("GENGO_BROWSERS", "chromium,firefox").split(",")


def serve_app():
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_port}"


@pytest.fixture
def site(ws_url, monkeypatch):
    """The web app on a free port, pointed straight at the test game server."""
    monkeypatch.setenv("GENGO_WS_URL", ws_url)
    server, url = serve_app()
    yield url
    server.shutdown()


@pytest.fixture(scope="module")
def playwright():
    with sync_api.sync_playwright() as p:
        yield p


@pytest.fixture(params=BROWSERS)
def browser(request, playwright):
    browser = getattr(playwright, request.param).launch()
    yield browser
    browser.close()


class Player:
    """One browser context (its own profile) with a page, recording
    script errors and every URL requested."""

    def __init__(self, browser):
        self.context = browser.new_context()
        self.page = self.context.new_page()
        self.errors = []
        self.requests = []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.on("request", lambda r: self.requests.append(r.url))
        self.page.on("dialog", self._dialog)
        self.dialogs = []

    def _dialog(self, dialog):
        self.dialogs.append(dialog.message)
        dialog.accept()

    def status(self):
        return expect(self.page.locator("#status"))

    def click_point(self, x, y):
        # Click the middle of the square, where the grid lines cross: the
        # click must still reach the square.
        self.page.locator(f'[id="{x},{y}"]').click()

    def stones(self):
        return self.page.locator("#stones circle")


def test_create_join_and_play_a_game(site, browser):
    black, white = Player(browser), Player(browser)

    black.page.goto(f"{site}/gengo/")
    expect(black.page.locator("#games")).to_have_text(
        "(no active games)", timeout=LOAD_TIMEOUT)

    # A name with a space and an ampersand: it has to survive the form, the
    # rules attributes, the game list and the join link.
    name = "Jack & Jill"
    black.page.fill("#game_name", name)
    black.page.fill("#board_size", "5")
    black.page.select_option("#overlap", "go")
    black.page.click("input[type=submit]")
    black.status().to_have_text("Waiting for opponent to join",
                                timeout=LOAD_TIMEOUT)

    white.page.goto(f"{site}/gengo/")
    white.page.get_by_role("link", name=name).click(timeout=LOAD_TIMEOUT)

    black.status().to_have_text("Click on the board to move",
                                timeout=LOAD_TIMEOUT)
    white.status().to_have_text("Waiting for opponent to play")

    black.click_point(1, 1)
    white.status().to_have_text("Click on the board to move", timeout=TIMEOUT)
    expect(white.stones()).to_have_count(1)

    white.click_point(3, 3)
    black.status().to_have_text("Click on the board to move", timeout=TIMEOUT)
    expect(black.stones()).to_have_count(2)

    # Clicking on a stone does nothing: no move is sent.
    black.page.locator("#stones circle").first.click(force=True)
    black.status().to_have_text("Click on the board to move")

    # Undo: black takes back white's move, and white is to play again.
    black.page.click("#undo")
    white.status().to_have_text("Click on the board to move", timeout=TIMEOUT)
    expect(white.stones()).to_have_count(1)
    white.click_point(3, 2)
    black.status().to_have_text("Click on the board to move", timeout=TIMEOUT)

    # An invalid move: on the stone's own square.
    black.click_point(3, 2)
    black.status().to_have_text("Click on the board to move", timeout=TIMEOUT)
    assert any("Invalid move" in d for d in black.dialogs)
    assert not white.dialogs

    black.page.click("#pass")
    white.status().to_have_text("Click on the board to move", timeout=TIMEOUT)
    white.page.click("#pass")
    black.status().to_have_text("Click on the board to move", timeout=TIMEOUT)
    black.page.click("#pass")

    for p in (black, white):
        p.status().to_have_text("Game complete", timeout=TIMEOUT)
        expect(p.page.locator("#black-stone-score")).to_have_text("1")
        expect(p.page.locator("#white-stone-score")).to_have_text("1")
        expect(p.page.locator("#pass")).to_be_disabled()
    black.page.wait_for_timeout(500)
    black.status().to_have_text("Game complete")

    for p in (black, white):
        assert p.errors == []
        # Every stdlib module must come from brython_stdlib.js, not the server
        assert not [u for u in p.requests if "/static/brython/Lib/" in u]


def test_list_shows_an_error_when_the_game_server_is_down(browser, monkeypatch):
    monkeypatch.setenv("GENGO_WS_URL", "ws://127.0.0.1:9")   # nothing there
    server, url = serve_app()
    try:
        player = Player(browser)
        player.page.goto(f"{url}/gengo/")
        expect(player.page.locator("#games")).to_contain_text(
            "Couldn’t reach the game server", timeout=LOAD_TIMEOUT)
    finally:
        server.shutdown()


def test_game_page_shows_when_the_connection_drops(site, browser,
                                                  game_server_process):
    player = Player(browser)
    player.page.goto(
        f"{site}/gengo/game?game_name=lonely&board_size=5&action=new"
        "&overlap=go&handicap=")
    player.status().to_have_text("Waiting for opponent to join",
                                 timeout=LOAD_TIMEOUT)
    game_server_process.stop()
    player.status().to_contain_text("Lost the connection", timeout=TIMEOUT)
    expect(player.page.locator("#status")).to_have_class("error")


def test_joining_a_missing_game_shows_the_error(site, browser):
    player = Player(browser)
    player.page.goto(
        f"{site}/gengo/game?game_name=nobody&board_size=5&action=join")
    player.status().to_contain_text("There is no game called 'nobody'",
                                    timeout=LOAD_TIMEOUT)
    # the close that follows must not replace it
    player.page.wait_for_timeout(500)
    player.status().to_contain_text("There is no game called 'nobody'")
    expect(player.page.locator("#status")).to_have_class("error")
    expect(player.page.locator("#pass")).to_be_disabled()
    player.page.get_by_role("link", name="Back to the game list").click()
    expect(player.page).to_have_url(f"{site}/gengo/")
    assert player.errors == []


def test_taken_name_shows_the_error(site, browser):
    first, second = Player(browser), Player(browser)
    url = (f"{site}/gengo/game?game_name=dup&board_size=5&action=new"
           "&overlap=go&handicap=")
    first.page.goto(url)
    first.status().to_have_text("Waiting for opponent to join",
                                timeout=LOAD_TIMEOUT)
    second.page.goto(url)
    second.status().to_contain_text("already a game called 'dup'",
                                    timeout=LOAD_TIMEOUT)
    first.status().to_have_text("Waiting for opponent to join")


def test_closing_the_tab_of_a_waiting_game_unlists_it(site, browser):
    creator, other = Player(browser), Player(browser)
    creator.page.goto(
        f"{site}/gengo/game?game_name=gone&board_size=5&action=new"
        "&overlap=go&handicap=")
    creator.status().to_have_text("Waiting for opponent to join",
                                  timeout=LOAD_TIMEOUT)
    other.page.goto(f"{site}/gengo/")
    expect(other.page.get_by_role("link", name="gone")).to_be_visible(
        timeout=LOAD_TIMEOUT)

    creator.page.close()
    other.page.wait_for_timeout(500)
    other.page.reload()
    expect(other.page.locator("#games")).to_have_text(
        "(no active games)", timeout=LOAD_TIMEOUT)


def test_opponent_closing_their_tab_is_shown(site, browser):
    black, white = Player(browser), Player(browser)
    black.page.goto(
        f"{site}/gengo/game?game_name=bye&board_size=5&action=new"
        "&overlap=go&handicap=&play_black=on")
    black.status().to_have_text("Waiting for opponent to join",
                                timeout=LOAD_TIMEOUT)
    white.page.goto(f"{site}/gengo/game?game_name=bye&board_size=5&action=join")
    black.status().to_have_text("Click on the board to move",
                                timeout=LOAD_TIMEOUT)

    white.page.close()
    black.status().to_contain_text("opponent left", timeout=TIMEOUT)
    expect(black.page.locator("#status")).to_have_class("error")
    expect(black.page.locator("#pass")).to_be_disabled()
    assert black.errors == []
