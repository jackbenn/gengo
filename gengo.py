#!python

# iterating over sets when removing items?????

# General logic:
#    Application starts up, reads in Board from database
#        maybe it generate overlap information, maybe it reads it in
#    Application reads Game information
#         (including Players, Users, Stones, and Groups)
#    If a result of user choosing an action,
#        Applcation performs that action
#    Application generates web page


# Rule Questions:
# Should suicide be legal? (currently: yes)
# Should it be legal to kill one's own groups
#        (not connected to the stone played)
#        (currently: yes)
#    If so, should the group with the stone played die before,
#        after, or at the same time as others of that player?
#        (currently: same time)
#    The current option seems the most logical and easiest to code.
# Should it be legal to play inside the overlap of one's own stones?
#    Pro:
#        it avoids the weird inability to connect stones
#    Con:
#        it doesn't solve the friendly-fire problem
#        it makes stone-counting ineffective
#        it feels a little weird


class Game:
    '''A game played between two people'''
    def __init__(self, players, board):
        self.players = players
        self.moves = []
        self.board = board
        self.next_player = 0
    
    def __str__(self):
        return str(self.board)

    def move(self, location):
        self.board[location].play(self.players[self.next_player])
        self.moves.append(location)
        self.next_player = 1 - self.next_player



class Board:
    '''A fairly static object,
    created once for each size/shape of board and ruleset.'''
    def __init__(self):
        pass


class GridBoard (Board):
    '''A subclass of board that's on a square grid,
    with identical overlap and neighbor matrices for each space.
    Most boards are one of these.'''

    def __init__(self, size, overlap, neighbor):
        # overlap and touches are lists of tuples of positive numbers
        # should assert some things about these, eg, overlap includes (0, 0)
        self.size = size
        self.grid = [[Space() for i0 in range(size)] for i1 in range(size)]
        for i0 in range(size):
            for i1 in range(size):
                space = self[i0, i1]
                space.coord = (i0, i1)
                for dir in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                    for x in overlap:
                        j0 = i0 + x[0] * dir[0]
                        j1 = i1 + x[1] * dir[1]
                        if 0 <= j0 < size and 0 <= j1 < size:
                            self[i0, i1].overlap.add(self[j0, j1])
                    for x in neighbor:
                        j0 = i0 + x[0] * dir[0]
                        j1 = i1 + x[1] * dir[1]
                        if 0 <= j0 < size and 0 <= j1 < size:
                            self[i0, i1].neighbor.add(self[j0, j1])

    def __str__(self):
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

    def __getitem__(self, coords):
        '''Return the Space object at the specified coordinates'''
        return self.grid[coords[0]][coords[1]]

    def __setitem__(self, coords, value):
        '''Set the Space object at the specified coordinates'''
        self.grid[coords[0]][coords[1]] = value

    def load(self, id_):
        pass


class Player:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol  # should be single character, for printing


class Space:
    def __init__(self):
        self.overlapcount = 0  # number of stones with which it overlaps
        self.stone = None
        self.overlap = set()
        self.neighbor = set()
        # there's also a coord, I think,
        # a tuple, but that's not part of the base class
        self.liberty_of = set()  # groups of which this is a liberty

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

    def __init__(self, stone):
        self.count = Group.groupcount
        Group.groupcount += 1
        self.stones = [stone]
        self.owner = stone.owner
        self.liberties = set()
        for space in stone.location.neighbor:
            if space.is_empty():
                self.liberties.add(space)
                space.liberty_of.add(self)
        print("New group liberties: ", len(self.liberties))

    def die(self):
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
    gb = GridBoard(11, [(0, 0), (1, 0), (0, 1), (1, 1)],
                       [(2, 0), (0, 2), (2, 1), (1, 2)])
    #gb = GridBoard(11, [(0, 0)],
    #                   [(1, 0), (0, 1)])
    print(gb)

    p1 = Player("X", "X")
    p2 = Player("O", "O")
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
        next = eval(input())
        if type(next).__name__ != "tuple":
            break
        game.move(next)
        print(game)
