# Gengo

Python application to run a generalized version of go, in which a stone extends across multiple spaces.

## Rules

Gengo is a generalized version of go that allows stones to be placed on a finer-grained grid. Stones have an a overlap region in which other stones cannot be played, and a neighbor region (beyond the immediate adjacent stones) in which stones are considered to be neighbors. For the full rules look [here](Rules.md).

## Usage

To run the python program, from this directory do

```
python gengo.py
```
Enter a move as a tuple of a row and a column, e.g.
```
2,3
```
To run server, from this directory do
```
python start_server.py
```

To run web app, from the `gengo/app` directory, do

```
export FLASK_APP=routes.py
export FLASK_ENV=development
flask run
```

Note that this is still in pre-alpha and is mostly useful for understanding the game.