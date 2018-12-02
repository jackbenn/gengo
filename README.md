# Gengo

Python application to run a generalized version of go, in which a stone extends across multiple spaces.

## Rules

Gengo is similar to go, but stones have an a overlap region in which other stones cannot be played, and a neighbor region (beyond the immediate adjacent stones) in which stones are considered to be neighbors. For ordinary go, the overlap is only the space on which the stone is played, and the neighbors are the four points above and below that point.

Gengo can be played with any set of regions, but the default regions look like this:
```
  n n n
n o o o n
n o x o n
n o o o n
  n n n
```
where x is the stone itself, o show the overlap region, and any stones played at n are neighbors.


## Usage

To run the python program, from this directory do

```
python gengo.py
```
Enter a move as a tuple of a row and a column, e.g.
```
2,3
```

To run web app, from the web directory, do:

```
export FLASK_APP=routes.py
export FLASK_ENV=development
flask run
```

Note the web app is really just experimental so far.
