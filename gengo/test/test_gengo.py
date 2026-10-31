import unittest
from ..src.gengo import Rules, GridBoard, Game, Space, Group, Stone, Player


class TestGengo(unittest.TestCase):

    def test_plays(self):
        p1 = Player("X", "X", "black", 1)
        p2 = Player("O", "O", "white", 2)

        rules = Rules([(0, 0), (1, 0), (0, 1), (1, 1)],
                      [(2, 0), (0, 2), (2, 1), (1, 2)],
                      11)
        game = Game([p1, p2], rules)
        game.move((2, 2))
        game.move((3, 4))

        self.assertFalse(game.board[2, 2].is_empty())
        self.assertFalse(game.board[3, 4].is_empty())
        self.assertFalse(game.board[1, 1].is_empty())
        self.assertTrue(game.board[0, 0].is_empty())

    def test_captures(self):
        p1 = Player("X", "X", "black", 1)
        p2 = Player("O", "O", "white", 2)
        rules = Rules([(0, 0), (1, 0), (0, 1), (1, 1)],
                      [(2, 0), (0, 2), (2, 1), (1, 2)],
                      11)
        game = Game([p1, p2], rules)
        game.move((2, 1))
        game.move((0, 1))
        self.assertFalse(game.board[0, 1].is_empty())
        game.move((0, 3))
        self.assertTrue(game.board[0, 1].is_empty())


# --- pytest-style rule tests -----------------------------------------------
import pytest
from ..src.gengo import InvalidMove

GO = ([(0, 0)], [(1, 0)])                    # plain go
STANDARD = ([(0, 0), (1, 0), (1, 1)], [(2, 0), (2, 1)])


def new_game(overlaps=GO, size=5, **options):
    # Rules extends the neighbour list in place, so give it fresh lists
    rules = Rules(list(overlaps[0]), list(overlaps[1]), size, **options)
    return Game([Player("X", "X", "black", 1), Player("O", "O", "white", 2)],
                rules)


def play(game, *moves):
    for move in moves:
        game.move(move)
    return game


def stones(game):
    black, white = game.board.get_stones_positions()
    return set(black), set(white)


def ko_position():
    """White has just played (1,1); black can capture it at (1,2), leaving a
    single black stone that white could at once capture back."""
    return play(new_game(),
                (0, 1), (0, 2), (1, 0), (2, 2), (2, 1), (1, 3),
                (4, 4), (1, 1))


def test_ko_forbids_an_immediate_capture_back():
    game = play(ko_position(), (1, 2))
    assert (1, 1) not in stones(game)[1]
    with pytest.raises(InvalidMove, match="Ko"):
        game.move((1, 1))
    game = game.create_replay()
    assert (1, 2) in stones(game)[0]
    assert game.next_player == 1


def test_ko_capture_back_is_allowed_after_a_move_elsewhere():
    game = play(ko_position(), (1, 2), (4, 0), (3, 4), (1, 1))
    assert (1, 2) not in stones(game)[0]
    assert (1, 1) in stones(game)[1]


@pytest.mark.parametrize("allow", [True, False])
def test_suicide(allow):
    game = play(new_game(allow_suicide=allow), (0, 1), (4, 4), (1, 0))
    if allow:
        game.move((0, 0))
        assert stones(game) == ({(0, 1), (1, 0)}, {(4, 4)})
        assert game.board[0, 0].is_empty()
    else:
        with pytest.raises(InvalidMove, match="Suicide"):
            game.move((0, 0))


def test_cannot_play_in_own_overlap_by_default():
    game = play(new_game(STANDARD, size=11), (2, 2), (8, 8))
    with pytest.raises(InvalidMove, match="overlap"):
        game.move((3, 3))


def test_play_in_own_overlap():
    game = play(new_game(STANDARD, size=11, play_in_own_overlap=True),
                (2, 2), (8, 8), (3, 3))
    assert stones(game)[0] == {(2, 2), (3, 3)}
    game = play(game, (6, 6))
    with pytest.raises(InvalidMove, match="opponent's overlap"):
        game.move((7, 7))
    game = game.create_replay()
    with pytest.raises(InvalidMove, match="existing stone"):
        game.move((2, 2))


def test_handicap_gives_black_extra_moves_first():
    game = new_game(handicap=3)
    for _ in range(3):
        assert game.next_player == 0
        game.move(None)
    assert game.next_player == 1
    game.move(None)
    assert game.next_player == 0


def test_three_passes_in_a_row_end_the_game():
    game = play(new_game(), None, None, (0, 0), None, None)
    assert not game.is_done
    game.move(None)
    assert game.is_done


def test_replay_drops_the_last_move_and_restores_captures():
    """This is undo: the player to move takes back the opponent's move."""
    game = play(new_game(), (0, 1), (0, 0), (1, 0))
    assert stones(game) == ({(0, 1), (1, 0)}, set())
    game = game.create_replay()
    assert stones(game) == ({(0, 1)}, {(0, 0)})
    assert game.next_player == 0


def test_scores():
    game = play(new_game(), (0, 1), (4, 4), (1, 0), (3, 4), (1, 1))
    assert game.board.stone_scores() == (3, 2)
    # Black owns its stones and the corner they enclose; the open middle
    # touches both colours and belongs to no one.
    assert game.board.area_scores() == (4, 2)
