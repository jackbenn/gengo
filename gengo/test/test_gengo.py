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
