# Background

Gengo was inspired when I was thinking of the idea of playing go on a continuous board. In such a game "stones" of non-zero area could be placed anywhere within a square (or other shaped) region, other than overlapping other stones.

A [few versions](http://www.di.fc.ul.pt/~jpn/gv/boards.htm#continuous) of this have been proposed, largely differening on the definition of what it means for two stones to be neighbors. The most obvious (that stones touch if and only if the overlap areas touch) may be problematic, as it becomes vanishingly rare (unless carefully planned) for a move to connect three other stones. One detailed set of such rules by Henry Segerman is [topological go](http://www.segerman.org/topologo/).

The larger problem with continuous go is playing it: it's impractical with a physical board based on the difficulty in determinining whether stones actually touched. It would only be practical with a program that guided the player, showing them the full results on a play before it happened.

Looking for something similar, a few years ago I came up with a generalized version of go, one that wasn't continuous but operated on a board with finer grain than the actual stones. It could be played on a regular board, but a standard go board made for a small game, and it took practice to to keep track of connected stones.

Like continuous go, there are differences in the rules for when stones are neighbors, but in gengo this is a parameter to the rules. The specific rules include the idea of an "overlap region" and a "neighbor region" around each stone. Other stones can't be played within a stone's overlap region. A stones played within each other's neighbor region are considered adjacent. The default regions look like this:

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

Well, mostly. The ordinary ko rule is impractical in gengo with fine meshes (and even more so in continuous go) as players can play at similar positions that are effective equivalent. Inside use a more complicated rule that a player cannot make a play capturing a single stone, if that stone was playe the previous turn, and on the previous turn the player captured a single stone. For regular go this is equivalent to the (non-super-)ko rule.

The best scoring rule is unclear. The obvious choice is [stone scoring](https://senseis.xmp.net/?StoneScoring) but this doesn't make for a fun endgame. I've implemented something similar to area scoring that counts spaces rather than stones.

Suicide is a bit more complicated, as it is possible for a stone to capture other stone belonging to the same player but not itself (friendly fire). I allow all of these by default, and suicide and friendly-fire capture happens simutaneously.

One possible rule variation is to allow players to play within the overlap of one's own stones (but not one's opponent's stones). This has the advantage of avoiding some awkward situations where a players stones are not connected but a connecting stone can't be played between then. But maybe that's just part of the game.
