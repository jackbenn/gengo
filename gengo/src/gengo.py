#!python

# iterating over sets when removing items?????
"""
General logic:
    Application starts up, reads in Board from database
        maybe it generate overlap information, maybe it reads it in
    Application reads Game information
        (including Players, Users, Stones, and Groups)
    If a result of user choosing an action,
         Application performs that action
    Application generates web page
"""

import psycopg2
import re
from typing import Set, Tuple, Sequence, List, Optional
import ast


class Rules:
    '''A group of options to control the play of the game
    overlap and neighbor are lists of tuples of positive numbers
    should assert some things about these, eg, overlap includes (0, 0)
    '''
    def __init__(self,
                 overlap: List[Tuple[int, int]],
                 neighbor: List[Tuple[int, int]],
                 size: int=11) -> None:
        self.size = size
        self.overlap = overlap
        self.neighbor = neighbor


class Game:
    '''A game played between two people'''
    def __init__(self,
                 players: Tuple['Player', 'Player'],
                 board: 'GridBoard',
                 name: str=None) -> None:
        self.players = players
        self.moves = []  # type: List[Tuple[int, int]]
        self.board = board
        self.next_player = 0
        self.id = None
        self.name = name
        self.is_done = False

    def __str__(self) -> str:
        return str(self.board)

    def move(self, location: Optional[Tuple[int, int]]) -> None:
        if location is None:
            if (len(self.moves) > 1 and
                  self.moves[-1] is None and
                  self.moves[-2] is None):
                self.is_done = True
        else:
            self.board[location].play(self.players[self.next_player])
        self.moves.append(location)
        self.next_player = 1 - self.next_player

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
        self.rules = rules
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
        for j in range(self.rules.size):
            result += '{0:3d}'.format(j)
        result += '\n'

        for i in range(self.rules.size):
            result += '{0:3d} '.format(i)
            for j in range(self.rules.size):
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

    def colors(self) -> str:
        '''Return list of lists of colors to paint on the server.
        This will be replaced by...something else'''
        empty_color = 'sandybrown'  # type:str
        overlap_color = 'grey'  # type: str
        result = []

        for i in range(self.rules.size):
            row = []
            for j in range(self.rules.size):
                space = self[i, j]
                if space.is_empty():
                    row.append(empty_color)
                elif space.stone is not None:
                    row.append(space.stone.owner.color)
                else:
                    row.append(overlap_color)
            result.append(row)
        return str(result)

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

    def is_empty(self):
        '''does it not overlap with a stone?'''
        return self.overlapcount == 0

    def play(self, player):
        assert(self.is_empty())
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
                print("removed liberty {}; remaining: {} from group {}".format(
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
        for group in moribund_groups:
            group.die()


class Stone:
    def __init__(self, owner, location):
        self.owner = owner
        self.location = location  # the space it's at
        self.group = Group(self)

    def die(self):
        '''
        kill a stone in a group, adding liberties to other groups as needed
        '''
        print("The stone died.")
        self.location.stone = None
        for space in self.location.overlap:
            space.overlapcount -= 1
            # add as liberty to other groups
            if space.is_empty():
                print("Freed a space to be a liberty...")
                for neighbor in space.neighbor:
                    if (neighbor.stone is not None and
                       neighbor.stone.group != self.group):
                        space.liberty_of.add(neighbor.stone.group)
                        neighbor.stone.group.liberties.add(space)
                        print("  ...bring group {} to {}".format(
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
        print("New group liberties: ", len(self.liberties))

    def die(self) -> None:
        print("The group died.")
        for stone in self.stones:
            stone.die()
        self.stones.clear()
        self.liberties.clear()
        del self

    # combing with another group
    def merge(self, other):
        print("Merging ", self.count, " with group ", other.count)
        assert(self != other)
        for stone in other.stones:
            print("moving stone at ", stone.location.coord)
            self.stones.append(stone)
            stone.group = self
        other.stones.clear()
        for space in other.liberties:
            print("moving liberty at ", space.coord)
            self.liberties.add(space)
            space.liberty_of.remove(other)
            space.liberty_of.add(self)
        other.liberties.clear()
        del other
        print("Liberties in merged group: ", len(self.liberties))


if __name__ == '__main__':
    rules = Rules([(0, 0), (1, 0), (0, 1), (1, 1)],
                  [(2, 0), (0, 2), (2, 1), (1, 2)],
                  11)
    gb = GridBoard(rules)
    # gb = GridBoard(11, [(0, 0)],
    #                   [(1, 0), (0, 1)])
    print(gb)

    p1 = Player("X", "X", "black", 1)
    p2 = Player("O", "O", "white", 2)
    '''
    gb[2, 2].play(p1)
    print(gb)

    gb[3, 4].play(p2)
    print(gb)

    gb[0, 2].play(p2)
    print(gb)
    print("liberties: ", len(gb[0, 2].stone.group.liberties))

    gb[1, 0].play(p2)
    print(gb)
    print("liberties: ", len(gb[0, 2].stone.group.liberties))

    gb[4, 0].play(p2)
    print(gb)
    print("liberties: ", len(gb[0, 2].stone.group.liberties))

    gb[5, 2].play(p2)
    print(gb)
    print("liberties: ", len(gb[0, 2].stone.group.liberties))

    b[0, 4].play(p2)
    print(gb)

    print("liberties: ", len(gb[0, 2].stone.group.liberties))

    gb[1, 6].play(p1)
    print(gb)

    print("liberties: ", len(gb[0, 2].stone.group.liberties))

    gb[3, 6].play(p1)
    print(gb)

    print("liberties: ", len(gb[0, 2].stone.group.liberties))

    gb[3, 2].play(p1)
    print(gb)
    '''

    game = Game((p1, p2), gb)

    while (True):
        move = input()
        if re.match("^\s*\d+\s*,\s*\d+\s*$", move):
            move = ast.literal_eval(move)
        elif re.match("\s*", move):
            move = None
        else:
            continue
        game.move(move)
        print(game)

        if game.is_done:
            break
    print("Game is complete")
    #conn = psycopg2.connect("dbname='gengo'")
    # conn.set_session(autocommit=True)
    #game.save(conn)
