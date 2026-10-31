# Backlog — gengo

Prefix: GENGO · Next ID: 8 · Schema: v1

## [GENGO-1] Upgrade Brython

- **Status:** idea
- **Priority:** unknown
- **Size:** session
- **Depends on:** none
- **Tags:** ui, stability
- **Related:** GENGO-2

The client runs Brython 3.6.2 (`gengo/app/static/brython/`, last touched in
2018) in current Chrome (153+). It is the main suspect for an intermittent
failure where the "Join a Game" list on `/gengo/` stays on "Loading…".

**What was seen (2026-10-28 UTC):** nginx logs for one browser show four loads
of `/gengo/` in two minutes. Three opened `/gengo/ws` within 1–2 s and got the
game list. The fourth, at 00:38:51, requested
`/gengo/static/brython/Lib/browser/svg.py?v=…` and got a 404, then never opened
a websocket. Brython should take `browser.svg` from the bundled
`brython_stdlib.js` (it is in there), so it missed that VFS and fell back to
fetching the module from the server. The import failed, `list_games.py` stopped
before creating the websocket, and the page stayed on "Loading…". The server was
healthy throughout: containers up, no restarts, and a direct `wss://` test got
the list at once.

**Not reproduced.** Jack reloaded many times, with hard reloads and emptying the
cache, and could not get it to fail again. Headless Chrome was no use: even with
a warm profile, Brython's "using indexedDB for stdlib modules cache" path took
80+ s compiling a few stdlib modules, while a real browser connects in 1–2 s.
The suspicion is Brython 3.6's IndexedDB module cache misbehaving in a modern
browser, but that is not confirmed.

**What to do:** move to a current Brython release. Expect API changes: the
`brython(1)` call in `onload` (now an options object), `browser.websocket`,
`browser.html` and `svg` usage in `list_games.py` and `board.py`, and the
`brython_stdlib.js` bundle. If the upgrade is large, consider whether these two
small scripts should just be JavaScript.

### Acceptance criteria
- [ ] `/gengo/` lists games and `/gengo/game` plays a full game in current Chrome, Firefox and Safari
- [ ] No requests to `/gengo/static/brython/Lib/...` appear in the nginx log during normal loads
- [ ] If "Loading…" recurs, the page shows an error rather than hanging silently

## [GENGO-2] Games whose creator has left stay listed and hang anyone who joins

- **Status:** idea
- **Priority:** unknown
- **Size:** session
- **Depends on:** none
- **Tags:** server, bug

The game server (`gengo/server/server.py`) keeps games in the module-level
`games` dict and never removes one. A game is listed by "list games" while its
`status` is `'created'`, which stays true after the creator's websocket closes.

Seen 2026-10-28: the creator of `dsfadfdasf` disconnected on Oct 26 at 18:43
(nginx logged the `/gengo/ws` close), but the game was still listed a day later.
Joining it puts the joiner's websocket on the queue, and `run_game` then tries to
play against a closed connection, so the joiner waits forever.

**What to do:** when the creator's connection closes before a second player
joins, drop the game from `games` (and cancel its `run_game` task). Also handle a
player disconnecting mid-game, so the other player is told rather than left
waiting. `get_connection` currently keeps each connection alive with an
`asyncio.sleep(60)` loop and does not notice the close.

### Acceptance criteria
- [ ] A game disappears from the list within a few seconds of its creator closing the tab
- [ ] Joining a game whose creator has gone shows an error instead of hanging
- [ ] If one player disconnects mid-game, the other is told

## [GENGO-3] Keep games across a game-server restart

- **Status:** idea
- **Priority:** unknown
- **Size:** multi
- **Depends on:** none
- **Tags:** server, ui, stability
- **Related:** INFRA-2, INFRA-3

All game state lives in memory in `gengo-ws`, so any restart of that container
(a deploy, a crash, a host reboot) ends every game in progress. INFRA-2 and
INFRA-3 reduce how often a deploy restarts it; this makes a restart harmless.

**What to do:** save each game's settings and move list to a volume as it is
played, and replay them when the server starts (`Game.create_replay` already
rebuilds a game from its moves). The browser clients also need to reconnect
after their websocket drops and re-identify themselves as a player of their game,
which needs some notion of a player token. The unused `--database` option
(postgres via `psycopg2`) is an older take on saving finished games; it could be
removed or folded into this.

### Notes
- 2026-10-31: What `--database` does now (found by repo-docs): only when that
  flag is passed, and only when a game ends, `Game.save` writes the game and its
  moves to a local Postgres database `gengo` (`sql/create_tables.sql`).
  `Game.load` is a stub (a SELECT whose result is discarded) and nothing calls
  it, so no game is ever read back. Production passes no `--database` and has
  no Postgres. Added in 2019 as "untested". For a restart it would need saving
  per move and loading on start; the schema (game, move with a sequence) could
  serve as the store, or a file on a volume could replace it.

## [GENGO-4] Add `## Getting started` to the README

- **Status:** done
- **Priority:** unknown
- **Size:** quick
- **Depends on:** none
- **Tags:** docs, baseline
- **Related:** GENGO-5, META-6

Found by project-init (2026-10-27). The README explains the game and how to run
it, but has no `## Getting started` section (setup, run, test, what is not in
the repo), so `PROJECTS.yaml` flags it `has_cold_start: false`. Run META-6's
`repo-docs` skill to write it. The site deploy (Docker, nginx at `/gengo/`,
the websocket at `/gengo/ws`) lives in `bennetto-infra`, and the section should
say so.

### Notes
- 2026-10-31: Done by repo-docs: `## Usage` became `## Getting started`, with Setup and Not in this repo added (the latter says the deploy lives in bennetto-infra); verified on Python 3.8 and 3.10.

## [GENGO-5] README gives the wrong path for the command-line game

- **Status:** done
- **Priority:** unknown
- **Size:** quick
- **Depends on:** none
- **Tags:** docs, bug
- **Related:** GENGO-4

Found by project-init (2026-10-27). The README says to run `python gengo.py`
"from this directory", but the file is at `gengo/src/gengo.py`. Check what
actually works (module run, import paths) and fix the instructions. The web
instructions mention ports 5000 and 8765, which describe local development,
not the deployed site; check those too.

### Notes
- 2026-10-31: Fixed by repo-docs: `python gengo/src/gengo.py`; the start page is `/gengo/` (`/gengo/new` and `/gengo/join` only redirect there). The ports 5000 and 8765 describe local development and are kept as such; on macOS 5000 needs AirPlay Receiver off (GENGO-7).

## [GENGO-6] Tests cover very little

- **Status:** idea
- **Priority:** unknown
- **Size:** multi
- **Depends on:** none
- **Tags:** test

Found by project-init (2026-10-27). `pytest` passes, but there are only two
tests, both in `gengo/test/test_gengo.py`. The game server
(`gengo/server/`) and the Flask routes have none. That matters for GENGO-1 and
GENGO-3, which change the client and the server.

## [GENGO-7] Local web play works only on port 5000, which macOS blocks

- **Status:** idea
- **Priority:** unknown
- **Size:** quick
- **Depends on:** none
- **Tags:** ui, bug
- **Related:** GENGO-4

`websocket_url()` in `gengo/app/static/js/board.py` and `list_games.py` goes
straight to the game server (`ws://host:8765`) only when the page's port is
5000, and otherwise to `/gengo/ws`, which only nginx serves. On macOS port 5000
is held by AirPlay Receiver, so `flask run` fails there, and `flask run --port
5050` serves the pages but the board cannot reach the game server. Found by
repo-docs (2026-10-31).

Likely fix: decide from the absence of a proxy rather than the port number, for
example a template variable or config value giving the websocket URL, so any
local port works.

### Acceptance criteria
- [ ] A local game can be played with Flask on a port other than 5000
- [ ] The deployed site still connects through `/gengo/ws`
