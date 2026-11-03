# Backlog archive — gengo

Prefix: GENGO · Archive of: BACKLOG.md · Schema: v1

## [GENGO-1] Upgrade Brython

- **Status:** done
- **Priority:** unknown
- **Size:** session
- **Depends on:** GENGO-6
- **Tags:** ui, stability
- **Related:** GENGO-2, GENGO-7

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

**Browser smoke test (moved here from GENGO-6, 2026-10-31):** add an automated
browser test, for example Playwright, that loads `/gengo/`, sees the game list,
creates a game in one page, joins it from a second, and plays a few moves. It is
the only test that runs the client code itself. Write it against the new Brython
(or the JavaScript rewrite), not 3.6: headless Chrome was too slow with 3.6's
IndexedDB cache to be usable. GENGO-6's protocol tests cover the server side of
the same exchange.

### Acceptance criteria
- [x] An automated browser test creates, joins and plays a game against a local server, and runs in under a minute
- [x] `/gengo/` lists games and `/gengo/game` plays a full game in current Chrome, Firefox and Safari
- [x] No requests to `/gengo/static/brython/Lib/...` appear in the nginx log during normal loads
- [x] If "Loading…" recurs, the page shows an error rather than hanging silently

### Notes
- 2026-10-31: Upgraded to Brython 3.14.3 (npm tarball, sha512 checked; 3.15.0
  was three weeks old). The scripts needed almost nothing: `brython(1)` became
  `brython({debug: 1})`, and `browser.websocket`, `browser.html`, `svg` and `<=`
  all still work, so a JavaScript rewrite is not needed. Script URLs carry
  `?v=3.14.3` so a cached 3.6 `brython.js` is not mixed with the new stdlib.
  Headless Chromium now loads `/gengo/` and gets the list in about 2 s, against
  80+ s with 3.6.
- 2026-10-31: Errors are now shown: the list or the game status says when the
  websocket closes early, and a plain-JavaScript timer replaces "Loading…" or
  "Connecting…" with an error after 10 s if Brython never starts. Also fixed:
  clicks on a grid line or a stone sent an empty move (which crashed the game
  before GENGO-6) because they landed on the line or stone rather than the
  square; join links now URL-encode the game name. Removed the unused
  `join.html` and `new.html` templates.
- 2026-10-31: `gengo/test/test_browser.py`, run with `pytest --browser-tests`:
  a full game (create, join, moves, a click on a stone, undo, an invalid move,
  three passes), the list's error with no game server, and the game page's
  error when the server goes away; it also asserts no `/static/brython/Lib/`
  requests and no script errors. About 20 s for Chromium and Firefox together.
  Playwright's WebKit hangs opening any page on macOS 14, so it is off by
  default (`GENGO_BROWSERS`), and Safari needs a check by hand.
- 2026-11-01: Jack played a game in Safari; it works.
- 2026-11-01: Deployed (bc0b103, then 1a60dcd). The nginx log since the
  Brython deploy has no `/gengo/static/brython/Lib/` requests; six loads of
  the live `/gengo/` in Chromium and Firefox got the list in 1.1-1.8 s with
  no script errors. Done.

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

- **Status:** done
- **Priority:** P3
- **Size:** multi
- **Depends on:** none
- **Tags:** test
- **Related:** GENGO-8
- **Commits:** 9125fee

Found by project-init (2026-10-27). `pytest` passes, but there are only two
tests, both in `gengo/test/test_gengo.py`. The game server
(`gengo/server/`) and the Flask routes have none. That matters for GENGO-1 and
GENGO-3, which change the client and the server.

**Scope (agreed 2026-10-31):** three layers, all under pytest. A browser test of
the Brython client is not part of this item; it belongs to GENGO-1.

1. **Websocket protocol.** Start the real game server on a free port and drive
   two `websockets` clients through it. This pins the contract the client must
   keep through GENGO-1: `"list games"`; `"new game"` + name + settings JSON;
   `"join game"` + name; moves as `"x,y"` strings, `"pass"`, `"undo"`; and the
   JSON board replies (`board`, `stones`, `pairs`, `is_my_turn`, `show_scores`,
   `done`, `warning`). The same harness is what GENGO-2 and GENGO-3 need for
   disconnect and restart tests. The module-level `games` and `options` dicts
   must be reset between tests.
2. **Flask routes.** With Flask's test client: `/gengo/` renders, `/gengo/new`
   and `/gengo/join` redirect, and `/gengo/game` renders the `div#rules`
   attributes that `board.py` reads, in the `"True"`/`"False"`/`"-"` forms the
   server compares against.
3. **Game rules** in `src/gengo.py`: ko, suicide (allowed and not),
   `play_in_own_overlap`, handicap, the three-pass end, and `create_replay`.

**Undo is meant to work this way:** only the player to move can send `"undo"`,
and it takes back the opponent's last move. A player cannot undo their own move
unless the opponent agrees, so the opponent's undo is that agreement. Tests
should assert this.

**Bugs the tests find:** fix small ones as part of this item. For a larger one,
open a new backlog item, mark the test `xfail` with that item's ID in the
reason, and note it here. Already visible:
- An unknown `overlap` setting leaves `overlap_lists` unset, so `run_game`
  raises `UnboundLocalError`.
- `/gengo/game` without `board_size` raises a 500 (`int(None)`).
- Joining a game that does not exist does nothing and the client hangs (the
  abandoned-game case is GENGO-2).

### Acceptance criteria
- [x] Protocol tests play a full game between two clients against the real server, including a pass, an undo, an invalid move (warning sent only to the mover) and the three-pass end
- [x] Protocol tests cover "list games" before and after a game is created and joined
- [x] Route tests cover `/gengo/`, the two redirects, and `/gengo/game` for both `action=new` and `action=join`
- [x] Rule tests cover ko, suicide, `play_in_own_overlap`, handicap, the three-pass end and undo via `create_replay`
- [x] Every bug found is either fixed or has its own backlog item and an `xfail` test naming it
- [x] `pytest` runs all of it from the repo root in a few seconds, with no network beyond localhost

### Notes
- 2026-10-31: Done. 45 tests pass and 3 are `xfail`, in about 5 s
  (`test_server.py`, `test_routes.py`, plus rule tests added to
  `test_gengo.py`). Server tests run the real server on a free localhost port
  in a background thread (`conftest.py`) and use the `websockets` sync client.
  The "full game" criterion is met across several tests rather than one long
  game. Fixed here: the three bugs listed above (unknown `overlap` now closes
  the connection with code 1008 and drops the game; a bad `board_size` is a
  400); malformed or off-board moves, which crashed the game task, or for a
  negative coordinate wrapped round the board, now get a warning; quotes on the
  `div#rules` attributes, which broke on a game name with a space and let a
  crafted name inject attributes; and after the third pass the server no
  longer prompts the next player, which had replaced "Game complete" with
  "Click on the board to move". The join/new/started-game hangs are GENGO-8,
  with an `xfail` test each.
- 2026-10-31: Board size capped at 51 (Jack's choice), in both `routes.py` (400)
  and the game server (closes with 1008), so a crafted request cannot make the
  server build a huge board.

## [GENGO-7] Local web play works only on port 5000, which macOS blocks

- **Status:** done
- **Priority:** unknown
- **Size:** quick
- **Depends on:** none
- **Tags:** ui, bug
- **Related:** GENGO-4, GENGO-1

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
- [x] A local game can be played with Flask on a port other than 5000
- [x] The deployed site still connects through `/gengo/ws`

### Notes
- 2026-10-31: Done as part of GENGO-1, whose browser tests needed it. The app
  passes `GENGO_WS_URL` to the pages as `data-ws-url` on `<body>`; empty (the
  default, as deployed) means `/gengo/ws` on the page's host. README updated.
  The local steps were run as written with Flask on 5050. The deployed-site
  criterion stays open until the next deploy.
- 2026-11-01: Deployed; the live pages connect through `/gengo/ws`.

## [GENGO-8] Bad "new game" and "join game" requests hang instead of getting an error

- **Status:** done
- **Priority:** unknown
- **Size:** session
- **Depends on:** none
- **Tags:** server, ui, bug
- **Related:** GENGO-2, GENGO-6

The websocket protocol has no error reply, so the server silently ignores a
request it cannot serve, and the page waits forever on "Waiting for opponent":

- "join game" for a name not in `games` does nothing.
- "new game" with a name already in `games` does nothing.
- "join game" for a game that has already started puts the connection on the
  game's queue, which nobody reads again.

Found by GENGO-6 (2026-10-31). Each case has an `xfail` test in
`gengo/test/test_server.py` that expects a JSON message with an `error` key;
the reply format is a suggestion, not settled. Fixing it needs both the server
and `board.py` (show the error, link back to `/gengo/`), so it fits with
GENGO-1 or with GENGO-2, whose abandoned-game case is the same hang.

### Acceptance criteria
- [x] Each of the three cases gets an error reply, and the page shows it
- [x] The three `xfail` tests pass with the marks removed

### Notes
- 2026-11-01: Done. The server answers `{"error": message}` and closes the
  connection for all three cases, plus bad settings (still close code 1008)
  and an unknown action. `board.py` shows the message in the status with a
  link back to `/gengo/`, and the close that follows does not replace it.
  Two further fixes in the same code: a joiner claims the second seat at once
  (status `joined`), so a second joiner is refused even before `run_game`
  picks the first up; and the name of a finished game can be used again,
  since games are never removed (GENGO-2). The `xfail` marks are gone; new
  server tests cover the race, name reuse and unknown actions, and two
  browser tests cover the page.
- 2026-11-01: Deployed in 1a60dcd; a live "join game" for a missing name
  gets the error reply over `wss://bennetto.com/gengo/ws`.

## [GENGO-9] Pin the Python packages

- **Status:** done
- **Priority:** unknown
- **Size:** quick
- **Depends on:** none
- **Tags:** server, stability
- **Related:** INFRA-1, INFRA-5, INFRA-9
- **Commits:** 3a5e6ff

`requirements.txt` names numpy, psycopg2-binary, websockets and Flask with no
versions, and the `gengo-web` image adds gunicorn the same way. Every build
that re-runs `pip install` can get different versions, so a new release can
reach the site on an unrelated deploy, or break it. Locally, websockets went
from 16 to 17 between two installs during GENGO-6.

Pinning does not stop a rebuild from restarting a container: a re-run `pip
install` writes new files, so the image changes even when the versions do
not. That is what happened to `gengo-web` on 2026-11-01 after the build cache
was trimmed (INFRA-1); keeping the cache (INFRA-5) is what prevents it.

**What to do:** pin every package, including the ones Flask and the rest pull
in, to the versions the deployed images run now, so pinning changes nothing in
production. Keep the unpinned top-level list somewhere so upgrading stays a
deliberate, simple step, and say how in the README. gunicorn is installed by
`docker/gengo-web.Dockerfile` in bennetto-infra, so pinning it is a change there.

### Acceptance criteria
- [x] Every package installed in both gengo images is pinned to an exact version
- [x] The pinned versions match what production ran before the change
- [x] Two builds with the build cache cleared in between give the same packages
- [x] The README says how to upgrade the pins

### Notes
- 2026-11-01: `requirements.txt` now holds the exact `pip freeze` of the
  running `gengo-ws` container (Python 3.11.18; `gengo-web` has the same plus
  gunicorn 26.2.0), and `requirements.in` the four direct packages unpinned.
  `update_requirements.sh` re-pins inside `python:3.11-slim`; not yet run,
  since Docker was not running locally. Two clean `--no-cache-dir` installs
  of the pins gave identical package sets (local Python 3.12, standing in for
  a Docker build with the cache cleared), and all 65 tests pass on them,
  browser tests included. gunicorn pinned in bennetto-infra's
  `docker/gengo-web.Dockerfile`, uncommitted. Deploying this should change no
  version on the server.
- 2026-11-01: Deployed (gengo 3a5e6ff, infra 19717c7 for gunicorn, pointer
  8d33bd6). Only `gengo-web` and `gengo-ws` were recreated, and `pip freeze`
  in each is unchanged from before. `update_requirements.sh` is still
  untried; run it the next time Docker is up locally.
- 2026-11-02: Ran `update_requirements.sh`. It works, and resolved exactly
  the pinned versions (only the header comment changed, which was discarded).
