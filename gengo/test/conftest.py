import asyncio
import threading

import pytest
import websockets

from ..server import server as game_server


class GameServer:
    """The real game server, on a free localhost port in a background thread.

    The server keeps its games in module-level dicts, so they are reset when
    it starts. stop() closes every connection and cancels every task left on
    the server's loop (games and connection handlers that would otherwise run
    forever); it is safe to call more than once.
    """

    def __init__(self):
        game_server.games.clear()
        game_server.options.clear()
        game_server.options['database'] = False

        self.loop = asyncio.new_event_loop()
        started = threading.Event()

        async def start():
            self.server = await websockets.serve(
                game_server.get_connection, "127.0.0.1", 0)
            started.set()

        def run():
            asyncio.set_event_loop(self.loop)
            self.loop.create_task(start())
            self.loop.run_forever()

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        assert started.wait(5), "game server did not start"
        port = self.server.sockets[0].getsockname()[1]
        self.url = f"ws://127.0.0.1:{port}"

    def stop(self):
        if self.loop.is_closed():
            return

        async def shutdown():
            self.server.close(close_connections=True)
            me = asyncio.current_task()
            tasks = [t for t in asyncio.all_tasks() if t is not me]
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

        asyncio.run_coroutine_threadsafe(shutdown(), self.loop).result(5)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(5)
        self.loop.close()
        game_server.games.clear()


@pytest.fixture
def game_server_process():
    server = GameServer()
    yield server
    server.stop()


@pytest.fixture
def ws_url(game_server_process):
    """The websocket URL of a game server running for this test."""
    return game_server_process.url
