# Backlog — gengo

Prefix: GENGO · Next ID: 10 · Schema: v1

## [GENGO-2] Games whose creator has left stay listed and hang anyone who joins

- **Status:** done
- **Priority:** P2
- **Size:** session
- **Depends on:** none
- **Tags:** server, bug
- **Commits:** d5d6fa7

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
- [x] A game disappears from the list within a few seconds of its creator closing the tab
- [x] Joining a game whose creator has gone shows an error instead of hanging
- [x] If one player disconnects mid-game, the other is told

### Notes
- 2026-11-02: `run_game` now waits for a joiner and for each move while
  watching the other connection, and drops the game from `games` however it
  ends (finished, creator gone, player gone mid-game); finished games used to
  stay in the dict for ever. The player still connected gets "Your opponent
  left, so the game is over." through the existing error display (GENGO-8).
  `keep_open`'s sleep loop is replaced by `wait_closed()`. A closed tab is
  noticed at once; a connection that just dies (laptop lid, lost network)
  only when websockets' keepalive ping times out, 20 s + 20 s by default.
  Tests: five protocol tests and two browser tests.
- 2026-11-03: Deployed (pointer 93774fa). Only `gengo-web` and `gengo-ws`
  were recreated. Checked live over `wss://bennetto.com/gengo/ws`: a waiting
  game left the list within a second of its creator closing, joining it then
  got "There is no game called …", and closing one player mid-game sent the
  other "Your opponent left, so the game is over."

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
