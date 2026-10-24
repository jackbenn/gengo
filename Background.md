# Background

I've always been interested in variants of go. Most variations, differences between counting methods and ko rules, have only a minor effect on strategy. Most others don't work well. While other abstract games, chess or backgammon or mancala in many ways, are easy to tweak in ways that might even improve them, go resists change.

Changing the grid works poorly. I've played on hexagonal and triagular gridsL they just aren't interesting. But I wondered about more extreme variations, including a continuous board, where a stone could be placed anywhere on the board, not just points of a grid.

## Continuous go

A [few versions](https://jpneto.github.io/world_abstract_games/boards.htm) of this have been proposed, largely differening on the definition of what it means for two stones to be neighbors. The most obvious (that stones touch if and only if the overlap areas touch) may be problematic, as it becomes vanishingly rare (unless carefully planned) for a move to connect three other stones.

The earliest I found are Open Go, played on a circular board with stones about 1/20 of its diameter, in which a stone can be played anywhere it doesn't overlap another stone and leaves room for another stone to touch it, and Pekka Karjalainen's Free Placement Go, which is similar but played on a square board. A more recent proposal, [Continuous Go](https://www.reddit.com/r/baduk/comments/1jyfjzc/), uses disks on a square board and handles ko by prohibiting any position whose graph of connected stones repeats an earlier one, even if the stones have shifted slightly. It also scores the final board as-is, without removing dead stones, because judging life and death would be so difficult.

One detailed set of such rules by Henry Segerman is [topological go](https://www.segerman.org/topologo/), which defines go on any topological space together with a set of allowed stone placements. Stones are connected if the closure of their union is connected, so no grid is needed. Ordinary go and [go on a general graph](https://www.segerman.org/topologo/gengraphgo.html) are both special cases. He also points out that a group's liberties can't really be counted, only whether it has any, as the number of stones that fit next to a group depends on how they're placed.

The larger problem with continuous go is playing it: it's impractical with a physical board based on the difficulty in determinining whether stones actually touched. It would only work with a program that guided the player, showing them the full results on a play before it happened. [Voronoi Go](https://voronoigo.com) is one such program: stones can be played anywhere on the board, and territory is computed from the Voronoi diagram of the stones. It has an online bot and a [Rust implementation of the rules](https://docs.rs/voronoi-go).

## Gengo


Looking for a comprimise between regular go and continuous variants, I came up with a generalized version of go several years ago, one that wasn't continuous but operated on a board with finer grain than the actual stones. It could be played on a regular board, but a standard go board made for a small game, and it took practice to to keep track of connected stones.

Like continuous go, there are differences in the rules for when stones are neighbors, but in gengo this is a parameter to the rules. The specific rules include the idea of an *overlap region* and a *neighbor region* around each stone. Other stones can't be played within a stone's overlap region. Stones played within each other's neighbor region are considered adjacent. The default regions look like this:

```
  n n n
n o o o n
n o x o n
n o o o n
  n n n
```

where x is the stone itself (which is in the overlap region), o shows the overlap region, and n shows the neighbor region.

This is choosen to have similar behavior to standard go (e.g., a single stone in the open can be captured by four other stones) but other choices might make better games. Regular go can be seen as a special case of gengo with an overlap region of

```
  n
n x n
  n
```

Well, mostly. The ordinary ko rule is impractical in gengo with fine meshes (and even more so in continuous go) as players can play at similar positions that are effective equivalent. Inside I took a different approach: a player cannot make a play capturing a single stone, if that stone was played the previous turn, and on that previous turn the player captured a single stone. For regular go this is equivalent to the (non-super-)ko rule.

The best scoring rule was unclear. The clean choice is [stone scoring](https://senseis.xmp.net/?StoneScoring) but this makes for a dull endgam, as each player gradually fills their territory. As an alternative I've something similar to [area scoring](https://senseis.xmp.net/?ChineseScoring) that counts spaces in rather than stones. [Territory scoring](https://senseis.xmp.net/?TerritoryScoring) wouldn't work, as territory is counted in spaces and captures in stones.

Suicide is more complicated, as it is possible for a stone to capture other stone belonging to the same player but not itself (friendly fire). I allow all of these by default, and suicide and friendly-fire capture happens simutaneously.

Another available rule variation allows players to play within the overlap of one's own stones (but not one's opponent's stones). This avoids some awkward situations where a player's stones are not connected but a connecting stone can't be played between then. Playing this together with scone scoring is not recommended as the game would devolve into filling every possible space.
