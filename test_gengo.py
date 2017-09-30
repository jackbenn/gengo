import unittest
from gengo import GridBoard, Space, Group, Stone, Player

class TestGengo(unittest.TestCase):

    def test_plays(self):
        p1 = Player("X", "X")
        p2 = Player("O", "O")
        gb = GridBoard(11, [(0, 0), (1, 0), (0, 1), (1, 1)],
                           [(2, 0), (0, 2), (2, 1), (1, 2)])
        gb[2, 2].play(p1)
        gb[3, 4].play(p2)
        self.assertFalse(gb[2, 2].is_empty())
        self.assertFalse(gb[3, 4].is_empty())
        self.assertFalse(gb[1, 1].is_empty())
        self.assertTrue(gb[0, 0].is_empty())

    def test_captures(self):
        p1 = Player("X", "X")
        p2 = Player("O", "O")
        gb = GridBoard(11, [(0, 0), (1, 0), (0, 1), (1, 1)],
                           [(2, 0), (0, 2), (2, 1), (1, 2)])
        gb[2, 1].play(p1)
        gb[0, 1].play(p2)
        self.assertFalse(gb[0, 1].is_empty())
        gb[0, 3].play(p1)
        self.assertTrue(gb[0, 1].is_empty())

