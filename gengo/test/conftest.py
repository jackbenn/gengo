import asyncio
import threading

import pytest
import websockets

from ..server import server as game_server


@pytest.fixture
def ws_url():
    """Run the real game server on a free localhost port in a background
    thread, and return its websocket URL.

    The server keeps its games in module-level dicts, so they are reset before
    each test. On teardown every task left on the server's loop (games and
    connection handlers that would otherwise run forever) is cancelled.
    """
    game_server.games.clear()
    game_server.options.clear()
    game_server.options['database'] = False

    loop = asyncio.new_event_loop()
    started = threading.Event()
    state = {}

    async def start():
        state['server'] = await websockets.serve(
            game_server.get_connection, "127.0.0.1", 0)
        started.set()

    def run():
        asyncio.set_event_loop(loop)
        loop.create_task(start())
        loop.run_forever()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    assert started.wait(5), "game server did not start"
    port = state['server'].sockets[0].getsockname()[1]

    yield f"ws://127.0.0.1:{port}"

    async def stop():
        state['server'].close(close_connections=True)
        me = asyncio.current_task()
        tasks = [t for t in asyncio.all_tasks() if t is not me]
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    asyncio.run_coroutine_threadsafe(stop(), loop).result(5)
    loop.call_soon_threadsafe(loop.stop)
    thread.join(5)
    loop.close()
    game_server.games.clear()
