#!python
+# not quite ready for 3.7
+#from __future__ import annotations
import psycopg2
import re
from typing import Set, Tuple, Sequence, List, Optional
import ast
import numpy as np
import logging
import argparse


class InvalidMove(Exception):
    pass


class Rules:
    '''A group of options to control the play of the game
    overlap and neighbor are lists of tuples of positive numbers
    should assert some things about these, eg, overlap includes (0, 0)
    Future options will be allowed around suicide.
    '''
    def __init__(self,
                 overlap: List[Tuple[int, int]],
                 neighbor: List[Tuple[int, int]],
                 size: int = 11,
                 no_capture_back_ko: bool = True,
                 allow_suicide: bool = True,
                 handicap: int = 1) -> None:
        """
        size: board size
        no_capture_back_ko: should single-stone capture-backs be illegal (a ko-rule variant)
        allow_suicide: should suicide be illegal?
        handicap: number of moves the black plays at the beginning of the game
        """
        self.size = size
        self.overlap = overlap
        self.neighbor = neighbor
        self.no_capture_back_ko = no_capture_back_ko
        self.allow_suicide = allow_suicide
        self.handicap = handicap


class Game:
    '''A game played between two people'''
    def __init__(self,
                 players: Tuple['Player', 'Player'],
                 rules: Rules,
                 name: str = None) -> None:
        self.players = players
        self.players[0].index = 0
        self.players[1].index = 1
        self.moves = []  # type: List[Optional[Tuple[int, int]]]
        self.board = GridBoard(rules)
        self.rules = rules
        self.next_player = 0
        self.id = None
        self.name = name
        self.is_done = False  # type: bool
        self.last_move_single_capture = None  # type: Optional[Stone]
        self.extra_moves = self.rules.handicap - 1

    def __str__(self) -> str:
        return str(self.board)

    def move(self, location: Optional[Tuple[int, int]]) -> None:
        self.moves.append(location)
        logging.info(f"Move at {self.moves}")
        if location is None:
            # check if it's the third pass
            if (len(self.moves) > 2 and
               self.moves[-2] is None and
               self.moves[-3] is None):
                self.is_done = True
        else:
            self.board[location].play(self.players[self.next_player], self)
        if self.extra_moves <= 0:
            self.next_player = 1 - self.next_player
        else:
            self.extra_moves -= 1

    # database methods. Should separate off as ORM.
    @staticmethod
    def load(conn, id):
        cur = conn.cursor()
        cur.execute('''select id, name, player1, player2 from game''')
        row = cur.fetchone()

    def save(self, conn):
        '''
        Add to database if new object and id is missing
        Otherwise: save recent moves
        '''
        cur = conn.cursor()

        if self.id is None:
            cur.execute("""insert into game (player1, player2)
                           values (%s, %s) returning id""",
                        (self.players[0].id,
                         self.players[1].id))
            self.id = cur.fetchone()[0]
        sequence = 0
        for move in self.moves:
            cur.execute("""insert into move (game, row, col, sequence)
                        values (%s, %s, %s, %s)""",
                        (self.id,
                         move[0],
                         move[1],
                         sequence))
            sequence += 1
        conn.commit()

    def create_replay(self, moves_to_drop=1):
        replay = Game(self.players, self.rules, self.name)
        for move in self.moves[:len(self.moves)-moves_to_drop]:
            replay.move(move)
        return replay


class Board:
    '''A fairly static object,
    created once for each size/shape of board and ruleset.'''
    def __init__(self):
        pass


class GridBoard (Board):
    '''A subclass of board that's on a square grid,
    with identical overlap and neighbor matrices for each space.
    Most boards are one of these.'''

    def __init__(self,
                 rules: Rules) -> None:
        self.size = rules.size
        self.grid = [[Space() for i0 in range(rules.size)]
                     for i1 in range(rules.size)]
        for i0 in range(rules.size):
            for i1 in range(rules.size):
                space = self[i0, i1]
                space.coord = (i0, i1)
                for dir in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                    for x in rules.overlap:
                        j0 = i0 + x[0] * dir[0]
                        j1 = i1 + x[1] * dir[1]
                        if 0 <= j0 < rules.size and 0 <= j1 < rules.size:
                            self[i0, i1].overlap.add(self[j0, j1])
                    for x in rules.neighbor:
                        j0 = i0 + x[0] * dir[0]
                        j1 = i1 + x[1] * dir[1]
                        if 0 <= j0 < rules.size and 0 <= j1 < rules.size:
                            self[i0, i1].neighbor.add(self[j0, j1])

    def __str__(self) -> str:
        '''Return string version of board'''
        result = "  "
        for j in range(self.size):
            result += '{0:3d}'.format(j)
        result += '\n'

        for i in range(self.size):
            result += '{0:3d} '.format(i)
            for j in range(self.size):
                space = self[i, j]
                if space.is_empty():
                    result += '.  '
                elif space.stone is not None:
                    result += '{}{:<2d}'.format(space.stone.owner.symbol,
                                                space.stone.group.count)
                else:
                    result += '*  '
            result += '\n'
        result += '\n'
        return result

    def __iter__(self):
        """Iterate over all the spaces in a board."""
        for i0 in range(self.size):
            for i1 in range(self.size):
                yield self[i0, i1]

    def stone_scores(self) -> Tuple[int, ...]:
        scores = [0, 0]
        for space in self:
            if space.stone is not None:
                scores[space.stone.owner.index] += 1
        return tuple(scores)

    def get_adjacent(self, coord: Tuple[int, int]):
        """return four adjacent locations to a tuple (fewer if on edge)"""
        i, j = coord
        result = []
        if i != 0:
            result.append((i-1, j))
        if i != self.size-1:
            result.append((i+1, j))
        if j != 0:
            result.append((i, j-1))
        if j != self.size-1:
            result.append((i, j+1))
        return result

    def area_scores(self) -> Tuple[int, int]:
        # calculate ownership of each space.
        # first, label spaces that are part of an overlap based n the owner.
        # label 2 if overlapped by both, -1 if by neither
        ownership = -np.ones((self.size, self.size))
        for space in self:
            if space.stone is not None:
                for overlap in space.overlap:
                    if ownership[overlap.coord] == -1:
                        ownership[overlap.coord] = space.stone.owner.index
                    elif ownership[overlap.coord] != space.stone.owner.index:
                        # it's overlapped by both players
                        ownership[overlap.coord] = 2
        for i in range(self.size):
            for j in range(self.size):
                if ownership[i, j] == -1:
                    # it's unassigned. Do a breadth-first search
                    # of unassigned adjacent points.
                    # to start, it's surrounded by nothing
                    surrounded_by = -1
                    visited = set()  # type: Set[Tuple[int, int]]
                    queue = [(i, j)]
                    while len(queue):
                        current = queue.pop(0)
                        if current not in visited:
                            if ownership[current] == -1:
                                visited.add(current)
                                queue.extend(self.get_adjacent(current))
                            elif surrounded_by == -1:
                                surrounded_by = ownership[current]
                            elif surrounded_by != ownership[current]:
                                # it's surrounded by both colors.
                                # no need to search more
                                surrounded_by = 2
                                break
                    # if board empty, set to 2
                    # so we don't have to calculate at each point
                    if surrounded_by == -1:
                        surrounded_by = 2
                    for coord in visited:
                        ownership[coord] = surrounded_by

        result0 = int((ownership == 0).sum())
        result1 = int((ownership == 1).sum())
        return (result0, result1)

    def find_neighbor_stones(self) -> List[List[Tuple[int, int]]]:
        neighbor_pairs = [[], []]  # type: List[List[Tuple[int, int]]]
        for a in self:
            if a.stone is not None:
                for b in a.neighbor:
                    if (b.stone is not None and
                       a.stone.owner == b.stone.owner and
                       a.coord > b.coord):
                        neighbor_pairs[a.stone.owner.index].append((a.coord,
                                                                    b.coord))
        return neighbor_pairs

    def colors(self) -> Tuple[List[List[str]],
                              List[List[Tuple[int, int]]],
                              Tuple[int, int],
                              List[List[Tuple[int, int]]]]:
        '''Return list of lists of colors to paint on the server.
        This will be replaced by...something else'''
        empty_color = 'sandybrown'  # type:str
        overlap_color = 'grey'  # type: str
        board = []  # type: List[List[str]]

        for i in range(self.size):
            row = []
            for j in range(self.size):
                space = self[i, j]
                if space.is_empty():
                    row.append("empty")
                else:
                    row.append("overlap")
            board.append(row)
        stones = [[], []]  # type: List[List[Tuple[int, int]]]
        for space in self:
            if space.stone is not None:
                stones[space.stone.owner.index].append(space.coord)
        scores = self.stone_scores()
        pairs = self.find_neighbor_stones()
        return (board, stones, scores, pairs)

    def __getitem__(self,
                    coords: Tuple[int, int]) -> "Space":
        '''Return the Space object at the specified coordinates'''
        return self.grid[coords[0]][coords[1]]

    def __setitem__(self,
                    coords: Tuple[int, int],
                    value: "Space") -> None:
        '''Set the Space object at the specified coordinates'''
        self.grid[coords[0]][coords[1]] = value

    def load(self, id_):
        pass


class Player:
    def __init__(self, name, symbol, color, id):
        self.id = id
        self.name = name
        self.symbol = symbol  # should be single character, for printing
        self.color = color
        self.index = None  # the index of a player in a game; first play is 0


class Space:
    def __init__(self):
        self.overlapcount = 0  # number of stones with which it overlaps
        self.stone = None
        self.overlap = set()
        self.neighbor = set()
        # there's also a coord, I think,
        # a tuple, but that's not part of the base class
        self.liberty_of = set()  # groups of which this is a liberty
        self.coord = None  # type: Optional[Tuple[Int, Int]]

    def is_empty(self) -> bool:
        '''does it not overlap with a stone?'''
        return self.overlapcount == 0

    def play(self, player: Player, game: Game) -> None:
        if not self.is_empty():
            raise InvalidMove("Moved inside overlap")

        possible_ko = False

        # create stone which will create group and find liberties
        self.stone = Stone(player, self)
        # add to existing groups
        merge_groups = set()
        for group in self.liberty_of:
            if group.owner == player and group != self.stone.group:
                merge_groups.add(group)
        for group in merge_groups:
            self.stone.group.merge(group)
        # keep track of all groups affected by the play
        affected_groups = set()
        # make this space and all overlaps not empty
        for space in self.overlap:
            space.overlapcount += 1
            # find neighboring opponent's groups
            for group in space.liberty_of:
                group.liberties.remove(space)
                logging.info("removed liberty {}; remaining: {} from group {}".format(
                      space.coord,
                      len(group.liberties),
                      group.count))
                affected_groups.add(group)
            space.liberty_of.clear()
        # add this stone's group to the affected group
        # (if it's a single suicide it won't be included)
        affected_groups.add(self.stone.group)

        # first check opponent's groups for death...
        moribund_groups = set()
        for group in affected_groups:
            if group.owner != player:
                if len(group.liberties) == 0:
                    moribund_groups.add(group)
        # check if it's a single-stone capture for ko
        if game.rules.no_capture_back_ko:
            if (len(moribund_groups) == 1 and
               len(list(moribund_groups)[0].stones) == 1):
                    # check if we captured the last move
                    # (and that made a single capture)
                    if (game.last_move_single_capture ==
                       list(list(moribund_groups)[0].stones)[0]):
                        # then this is a ko (unless there's suicide)
                        possible_ko = True
                    game.last_move_single_capture = self.stone
            else:
                game.last_move_single_capture = None

        # they all die at the same time
        # (it's possible one might open liberties for another,
        # but that would lead to indeterminate situations)
        for group in moribund_groups:
            group.die()
        # ...and now handle suicides
        # (we're making these legal for now because it's easier)
        moribund_groups = set()
        for group in affected_groups:
            if group.owner == player:
                if len(group.liberties) == 0:
                    moribund_groups.add(group)
        if not game.rules.allow_suicide and moribund_groups:
            raise InvalidMove("Suicides are not allowed.")
        # if there were suicides, it won't lead to a ko
        if game.rules.no_capture_back_ko:
            if len(moribund_groups):
                game.last_move_single_capture = None
                possible_ko = False
        if possible_ko:
            raise InvalidMove("Ko (captured singleton capture)")

        for group in moribund_groups:
            group.die()


class Stone:
    def __init__(self, owner: Player, location: Space):
        self.owner = owner
        self.location = location  # the space it's at
        self.group = Group(self)

    def die(self) -> None:
        '''
        kill a stone in a group, adding liberties to other groups as needed
        '''
        logging.info("The stone died.")
        self.location.stone = None
        for space in self.location.overlap:
            space.overlapcount -= 1
            # add as liberty to other groups
            if space.is_empty():
                logging.info("Freed a space to be a liberty...")
                for neighbor in space.neighbor:
                    if (neighbor.stone is not None and
                       neighbor.stone.group != self.group):
                        space.liberty_of.add(neighbor.stone.group)
                        neighbor.stone.group.liberties.add(space)
                        logging.info("  ...bring group {} to {}".format(
                            neighbor.stone.group.count,
                            len(neighbor.stone.group.liberties)))


class Group:
    groupcount = 0

    def __init__(self, stone: Stone) -> None:
        self.count = Group.groupcount
        Group.groupcount += 1
        self.stones = [stone]
        self.owner = stone.owner
        self.liberties = set()  # type: Set[Space]
        for space in stone.location.neighbor:
            if space.is_empty():
                self.liberties.add(space)
                space.liberty_of.add(self)
        logging.info("New group liberties: ", len(self.liberties))

    def die(self) -> None:
        logging.info("The group died.")
        for stone in self.stones:
            stone.die()
        self.stones.clear()
        self.liberties.clear()
        del self

    # combing with another group
    def merge(self, other: "Group") -> None:
        logging.info(f"Merging {self.count} with group {other.count}")
        assert(self != other)
        for stone in other.stones:
            logging.info(f"moving stone at {stone.location.coord} between groups")
            self.stones.append(stone)
            stone.group = self
        other.stones.clear()
        for space in other.liberties:
            logging.info(f"moving liberty at {space.coord} between groups")
            self.liberties.add(space)
            space.liberty_of.remove(other)
            space.liberty_of.add(self)
        other.liberties.clear()
        del other
        logging.info(f"Liberties in merged group: {len(self.liberties)}")



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Play Gengo, a generalized version of go')

    parser.add_argument('--no-suicide', dest='allow_suicide',
                        action='store_false', help="Don't allow suicide/friendly fire")
    parser.add_argument('--board-size', dest="board_size", default=19,
                        type=int, help="Size of the board")
    parser.add_argument('--handicap', dest="handicap", default=1,
                        type=int, help="Number of free handicap stones for the black player")
    args = parser.parse_args()
    print(args)

    rules = Rules([(0, 0), (1, 0), (0, 1), (1, 1)],
                  [(2, 0), (0, 2), (2, 1), (1, 2)],
                  size=vars(args)['board_size'],
                  allow_suicide=vars(args)['allow_suicide'],
                  handicap=vars(args)['handicap'])

    p1 = Player("X", "X", "black", 1)
    p2 = Player("O", "O", "white", 2)

    game = Game((p1, p2), rules)

    while (True):
        print(game)
        print(f"{game.players[game.next_player].name}'s turn. Enter coodinates:  ", end="")
        move_input = input()
        if re.match(r"^\s*\d+\s*,\s*\d+\s*$", move_input):
            move = ast.literal_eval(move_input)
            try:
                game.move(move)
            except InvalidMove as e:
                print(e)
                game = game.create_replay()

        elif re.match(r"\s*$", move_input):
            move = None
            game.move(move)
        elif re.match("^[Uu]", move_input):
            print("Undoing last move")
            game = game.create_replay()
        else:
            continue

        if game.is_done:
            break
    print(game)
    logging.info(f"The game is complete")
    print(f"The final score is {game.board.stone_scores()}")
    """
    conn = psycopg2.connect("dbname='gengo'")
    conn.set_session(autocommit=True)
    game.save(conn)
    """
