# Gengo

This is a python application/web server that runs a generalized version of go in which a stone extends across multiple spaces. Here's an example a 23x23 board from near the end of the game.

![Sample Game](img/sample_game.png)

## Rules

Gengo is a generalized version of go that allows stones to be placed on a finer-grained grid. Stones have an a overlap region in which other stones cannot be played, and a neighbor region (beyond the immediate adjacent stones) in which stones are considered to be neighbors. For the full rules look [here](Rules.md).

## Getting started

### Setup

Python 3.11, as in the deployed images (3.8 and 3.10 also work).

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Command-line application

To run the python program, from this directory do

```
python gengo/src/gengo.py
```

Several options exists to play for rules; see `python gengo/src/gengo.py -h` for more information.

Enter a move as a tuple of a row and a column, e.g.
```
2,3
```
A move can be undone with `u`; no entry is a pass. Three passes in a row end the game, and `r` resigns.

### Web application

To run gengo on the web, start both a game server and a web server.

To start the game server, from this directory do
```
python start_server.py
```

To start the web server: from the `gengo/app` directory, do

```
export FLASK_APP=routes.py
flask run --host=0.0.0.0
```

(for a development server that reloads on changes, add `--debug`).
This starts a server on port 5000. Point a browser to http://localhost:5000/gengo/ and start a new game, entering its name, the board size and any other options. Point a second browser to the same page and join that game from the list.

On macOS, port 5000 is taken by AirPlay Receiver and `flask run` fails with "Address already in use"; turn it off in System Settings (search for AirPlay Receiver). Another port will serve the pages, but the board then cannot reach the game server (GENGO-7).

To connect to the web server from a client on another machine, ensure the firewall allows access to ports 5000 and 8765 (for websocket connections to the game server).

### Tests

To run tests, do `pytest` from this directory. pytest is not in `requirements.txt`; install it with `pip install pytest`.

### Not in this repo

Nothing is needed to play. The `--database` option (on `start_server.py` and the command-line game) saves finished games to a local Postgres database named `gengo`, created from `sql/create_tables.sql`; it is untested, games are never read back, and the deployed site does not use it (see GENGO-3).

The deployment lives in `bennetto-infra`, of which this repo is a submodule: `docker/gengo-web.Dockerfile` runs the web app under gunicorn and `docker/gengo-ws.Dockerfile` the game server, with nginx serving them at `/gengo/` and the websocket at `/gengo/ws`. Deploy through that repo, not from here.

Note that this is still in beta and is mostly useful for understanding the game.