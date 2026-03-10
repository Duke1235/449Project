"""
test_solitaire.py
=================
xUnit test suite for Peg Solitaire (CS449 Sprint 2).

Tests are organised by User Story / Acceptance Criterion so that the
Sprint 2 submission table can reference class + method names directly.

Test classes
------------
TestBoardShapes          – US1: board size & type (AC 1.1, 1.2, 2.1, 2.2)
TestNewGame              – US2: starting a new game (AC 3.1, 3.2)
TestMakeMove             – US3: making a move (AC 4.1, 4.2)
TestEndOfGame            – US4: game-over detection (AC 5.1, 5.2)
TestHexGrid              – geometry helpers used by hex board
TestAdditional           – extra tests not tied to a single AC

Run with:
    python -m pytest test_solitaire.py -v
or:
    python test_solitaire.py
"""

import unittest
import math
from game_logic import Board, HexGrid, SolitaireGame


# ──────────────────────────────────────────────────────────────────────────────
# US 1  –  Choose board size and type
# AC 1.1  select valid board size  |  AC 1.2  change board size
# AC 2.1  select English board     |  AC 2.2  select Hexagon / Diamond
# ──────────────────────────────────────────────────────────────────────────────

class TestBoardShapes(unittest.TestCase):
    """Tests for board construction (User Story 1 — choose board size & type)."""

    # ── AC 1.1  valid board sizes ─────────────────────────────────────────────

    def test_ac1_1_english_size7_cell_count(self):
        """English size-7 board must have exactly 33 valid cells."""
        cells = Board.english(7)
        self.assertEqual(len(cells), 33)

    def test_ac1_1_english_size5_cell_count(self):
        """English size-5 board: third=1, so col/row band 1..3 → 21 valid cells."""
        cells = Board.english(5)
        # Recompute expected count from the formula
        third = 5 // 3  # = 1
        expected = len({(r, c) for r in range(5) for c in range(5)
                        if (third <= c < 5 - third) or (third <= r < 5 - third)})
        self.assertEqual(len(cells), expected)

    def test_ac1_1_diamond_size7_cell_count(self):
        """Diamond size-7 board has 25 cells (manhattan diamond)."""
        cells = Board.diamond(7)
        self.assertEqual(len(cells), 25)

    def test_ac1_1_hexagon_size9_row_lengths(self):
        """Hexagonal size-9 board row lengths must be 5,6,7,8,9,8,7,6,5."""
        cells = Board.hexagon(9)
        expected = [5, 6, 7, 8, 9, 8, 7, 6, 5]
        actual = [
            len([c for (r2, c) in cells if r2 == r])
            for r in range(9)
        ]
        self.assertEqual(actual, expected)

    def test_ac1_1_hexagon_size5_row_lengths(self):
        """Hexagonal size-5 board row lengths must be 3,4,5,4,3."""
        cells = Board.hexagon(5)
        expected = [3, 4, 5, 4, 3]
        actual = [
            len([c for (r2, c) in cells if r2 == r])
            for r in range(5)
        ]
        self.assertEqual(actual, expected)

    # ── AC 1.2  change board size (game re-initialises correctly) ─────────────

    def test_ac1_2_resize_english_7_to_9(self):
        """Changing size from 7 to 9 changes the cell count."""
        g7 = SolitaireGame("English", 7)
        g9 = SolitaireGame("English", 9)
        self.assertGreater(g9.cell_count(), g7.cell_count())

    def test_ac1_2_hexagon_different_sizes_differ(self):
        """Hexagon size 7 and size 9 must have different cell counts."""
        g7 = SolitaireGame("Hexagon", 7)
        g9 = SolitaireGame("Hexagon", 9)
        self.assertNotEqual(g7.cell_count(), g9.cell_count())

    # ── AC 2.1  English board type ────────────────────────────────────────────

    def test_ac2_1_english_board_is_cross_shaped(self):
        """English board must be cross-shaped: corners (0,0) not in valid cells."""
        cells = Board.english(7)
        self.assertNotIn((0, 0), cells)
        self.assertNotIn((0, 6), cells)
        self.assertNotIn((6, 0), cells)
        self.assertNotIn((6, 6), cells)

    def test_ac2_1_english_centre_in_cells(self):
        """Centre cell must be part of English board."""
        cells = Board.english(7)
        self.assertIn((3, 3), cells)

    # ── AC 2.2  Hexagon / Diamond board types ─────────────────────────────────

    def test_ac2_2_hexagon_board_type_stored(self):
        """SolitaireGame must store the board_type as 'Hexagon'."""
        g = SolitaireGame("Hexagon", 9)
        self.assertEqual(g.board_type, "Hexagon")

    def test_ac2_2_diamond_board_type_stored(self):
        """SolitaireGame must store the board_type as 'Diamond'."""
        g = SolitaireGame("Diamond", 7)
        self.assertEqual(g.board_type, "Diamond")

    def test_ac2_2_diamond_corners_absent(self):
        """Diamond board must not include the four grid corners."""
        cells = Board.diamond(7)
        self.assertNotIn((0, 0), cells)
        self.assertNotIn((6, 6), cells)

    def test_ac2_2_invalid_board_type_raises(self):
        """Constructing with unknown board_type must raise ValueError."""
        with self.assertRaises(ValueError):
            SolitaireGame("Triangle", 7)


# ──────────────────────────────────────────────────────────────────────────────
# US 2  –  Start a new game
# AC 3.1  new game with settings  |  AC 3.2  reset existing game
# ──────────────────────────────────────────────────────────────────────────────

class TestNewGame(unittest.TestCase):
    """Tests for game initialisation (User Story 2 — start a new game)."""

    # ── AC 3.1  game created with selected settings ───────────────────────────

    def test_ac3_1_english_game_pegs_minus_one(self):
        """New English game has (cell_count - 1) pegs (centre removed)."""
        g = SolitaireGame("English", 7)
        self.assertEqual(g.peg_count(), g.cell_count() - 1)

    def test_ac3_1_hexagon_game_pegs_minus_one(self):
        """New Hexagon game has (cell_count - 1) pegs."""
        g = SolitaireGame("Hexagon", 9)
        self.assertEqual(g.peg_count(), g.cell_count() - 1)

    def test_ac3_1_diamond_game_pegs_minus_one(self):
        """New Diamond game has (cell_count - 1) pegs."""
        g = SolitaireGame("Diamond", 7)
        self.assertEqual(g.peg_count(), g.cell_count() - 1)

    def test_ac3_1_english_centre_empty_at_start(self):
        """Centre cell must be empty at game start for English board."""
        g = SolitaireGame("English", 7)
        self.assertNotIn((3, 3), g.pegs)

    def test_ac3_1_hexagon_centre_empty_at_start(self):
        """Centre cell must be empty at game start for Hexagon board."""
        g = SolitaireGame("Hexagon", 9)
        self.assertNotIn((4, 4), g.pegs)

    def test_ac3_1_initial_moves_available(self):
        """A new game must have at least one valid move."""
        for bt in SolitaireGame.BOARD_TYPES:
            with self.subTest(board_type=bt):
                g = SolitaireGame(bt, 9 if bt == "Hexagon" else 7)
                self.assertGreater(len(g.get_valid_moves()), 0)

    # ── AC 3.2  reset clears previous state ───────────────────────────────────

    def test_ac3_2_reset_restores_peg_count(self):
        """After making moves, reset() must restore the original peg count."""
        g = SolitaireGame("English", 7)
        original_count = g.peg_count()
        moves = g.get_valid_moves()
        g.make_move(moves[0][0], moves[0][2])
        g.make_move(moves[1][0], moves[1][2])
        g.reset()
        self.assertEqual(g.peg_count(), original_count)

    def test_ac3_2_reset_empties_centre(self):
        """After reset(), centre cell must be empty again."""
        g = SolitaireGame("English", 7)
        # Make a move to fill centre
        g.pegs.add((3, 3))   # manually add peg to centre for test setup
        g.reset()
        self.assertNotIn((3, 3), g.pegs)

    def test_ac3_2_reset_with_new_type(self):
        """Changing board_type then calling reset() applies the new shape."""
        g = SolitaireGame("English", 7)
        english_count = g.cell_count()
        g.board_type = "Diamond"
        g.reset()
        self.assertNotEqual(g.cell_count(), english_count)


# ──────────────────────────────────────────────────────────────────────────────
# US 3  –  Making a move
# AC 4.1  valid move accepted  |  AC 4.2  invalid move rejected
# ──────────────────────────────────────────────────────────────────────────────

class TestMakeMove(unittest.TestCase):
    """Tests for move execution (User Story 3 — making a move)."""

    def setUp(self):
        self.game_eng = SolitaireGame("English", 7)
        self.game_hex = SolitaireGame("Hexagon", 9)

    # ── AC 4.1  valid move ────────────────────────────────────────────────────

    def test_ac4_1_valid_move_returns_true(self):
        """make_move() must return True for a valid move."""
        g = self.game_eng
        fr, _, to = g.get_valid_moves()[0]
        self.assertTrue(g.make_move(fr, to))

    def test_ac4_1_valid_move_reduces_peg_count(self):
        """After a valid move the peg count decreases by 1."""
        g = self.game_eng
        before = g.peg_count()
        fr, _, to = g.get_valid_moves()[0]
        g.make_move(fr, to)
        self.assertEqual(g.peg_count(), before - 1)

    def test_ac4_1_from_cell_empty_after_move(self):
        """The source cell must be empty after a valid move."""
        g = self.game_eng
        fr, _, to = g.get_valid_moves()[0]
        g.make_move(fr, to)
        self.assertNotIn(fr, g.pegs)

    def test_ac4_1_jumped_cell_empty_after_move(self):
        """The jumped-over cell must be empty after a valid move."""
        g = self.game_eng
        fr, mid, to = g.get_valid_moves()[0]
        g.make_move(fr, to)
        self.assertNotIn(mid, g.pegs)

    def test_ac4_1_destination_filled_after_move(self):
        """The destination cell must contain a peg after a valid move."""
        g = self.game_eng
        fr, _, to = g.get_valid_moves()[0]
        g.make_move(fr, to)
        self.assertIn(to, g.pegs)

    def test_ac4_1_hex_valid_move(self):
        """Valid move works correctly on a Hexagon board."""
        g = self.game_hex
        fr, mid, to = g.get_valid_moves()[0]
        result = g.make_move(fr, to)
        self.assertTrue(result)
        self.assertNotIn(fr, g.pegs)
        self.assertNotIn(mid, g.pegs)
        self.assertIn(to, g.pegs)

    # ── AC 4.2  invalid move rejected ─────────────────────────────────────────

    def test_ac4_2_move_to_occupied_cell_rejected(self):
        """Moving to a cell that already has a peg must return False."""
        g = self.game_eng
        # Pick any peg; try to move it to another peg's position
        pegs = list(g.pegs)
        self.assertFalse(g.make_move(pegs[0], pegs[1]))

    def test_ac4_2_move_off_board_rejected(self):
        """Moving to a cell not on the board must return False."""
        g = self.game_eng
        fr = list(g.pegs)[0]
        self.assertFalse(g.make_move(fr, (-1, -1)))

    def test_ac4_2_move_without_jumped_peg_rejected(self):
        """A jump over an empty cell must be rejected."""
        g2 = SolitaireGame("English", 7)
        fr, mid, to = g2.get_valid_moves()[0]
        g2.pegs.discard(mid)   # remove the peg to be jumped over
        self.assertFalse(g2.make_move(fr, to))

    def test_ac4_2_move_does_not_change_state_on_failure(self):
        """A failed move must leave peg positions unchanged."""
        g = self.game_eng
        before = frozenset(g.pegs)
        g.make_move((0, 0), (0, 6))   # clearly invalid
        self.assertEqual(frozenset(g.pegs), before)

    def test_ac4_2_is_valid_move_helper(self):
        """is_valid_move() must agree with make_move() results."""
        g = self.game_eng
        fr, _, to = g.get_valid_moves()[0]
        self.assertTrue(g.is_valid_move(fr, to))
        self.assertFalse(g.is_valid_move(fr, fr))   # same cell → invalid


# ──────────────────────────────────────────────────────────────────────────────
# US 4  –  Game over detection
# AC 5.1  detect no moves  |  AC 5.2  detect win (1 peg)
# ──────────────────────────────────────────────────────────────────────────────

class TestEndOfGame(unittest.TestCase):
    """Tests for win/loss detection (User Story 4 — checking end of game)."""

    # ── AC 5.1  no valid moves = game over ────────────────────────────────────

    def test_ac5_1_fresh_game_not_over(self):
        """A freshly started game must NOT be game-over."""
        g = SolitaireGame("English", 7)
        self.assertFalse(g.is_game_over())

    def test_ac5_1_single_isolated_peg_is_game_over(self):
        """One peg with no neighbours → game over (also a win)."""
        g = SolitaireGame("English", 7)
        g.pegs = {(3, 3)}
        self.assertTrue(g.is_game_over())

    def test_ac5_1_two_non_adjacent_pegs_game_over(self):
        """Two pegs that cannot jump each other → game over."""
        g = SolitaireGame("English", 7)
        g.pegs = {(0, 3), (6, 3)}   # far apart, no path
        self.assertTrue(g.is_game_over())

    def test_ac5_1_two_adjacent_pegs_not_game_over(self):
        """Two pegs with an empty landing cell → NOT game over."""
        g = SolitaireGame("English", 7)
        # pegs at (3,1) and (3,2); empty (3,3) → valid jump
        g.pegs = {(3, 1), (3, 2)}
        self.assertFalse(g.is_game_over())

    # ── AC 5.2  exactly one peg = win ─────────────────────────────────────────

    def test_ac5_2_one_peg_is_win(self):
        """Exactly one peg remaining must be detected as a win."""
        g = SolitaireGame("English", 7)
        g.pegs = {(3, 3)}
        self.assertTrue(g.is_win())

    def test_ac5_2_two_pegs_not_win(self):
        """Two or more pegs remaining must NOT be a win."""
        g = SolitaireGame("English", 7)
        g.pegs = {(3, 3), (3, 4)}
        self.assertFalse(g.is_win())

    def test_ac5_2_fresh_game_not_win(self):
        """A fresh game with many pegs must NOT be a win."""
        g = SolitaireGame("English", 7)
        self.assertFalse(g.is_win())

    def test_ac5_2_win_implies_game_over(self):
        """A win state (1 peg) must also satisfy is_game_over()."""
        g = SolitaireGame("English", 7)
        g.pegs = {(3, 3)}
        self.assertTrue(g.is_win())
        self.assertTrue(g.is_game_over())


# ──────────────────────────────────────────────────────────────────────────────
# Hex geometry tests
# ──────────────────────────────────────────────────────────────────────────────

class TestHexGrid(unittest.TestCase):
    """Tests for HexGrid geometry helpers."""

    def setUp(self):
        self.centers, self.cw, self.ch = HexGrid.cell_centers(9)
        self.adj, self.step = HexGrid.build_adjacency(self.centers)

    def test_centre_has_six_neighbours(self):
        """Centre cell of a hex board must have exactly 6 neighbours."""
        centre = (4, 4)
        self.assertEqual(len(self.adj[centre]), 6)

    def test_horizontal_step_matches_formula(self):
        """Horizontal spacing must equal sqrt(3) * HEX_R."""
        expected = math.sqrt(3) * HexGrid.HEX_R
        self.assertAlmostEqual(self.step, expected, places=1)

    def test_all_cells_have_centers(self):
        """Every cell in hexagon(9) must have a pixel centre."""
        cells = Board.hexagon(9)
        for cell in cells:
            self.assertIn(cell, self.centers)

    def test_corner_cells_have_fewer_neighbours(self):
        """Corner cells of the hex board must have fewer than 6 neighbours."""
        corner = (0, 0)
        self.assertLess(len(self.adj[corner]), 6)

    def test_jumps_from_centre_are_six(self):
        """Centre cell should have 6 possible jump directions."""
        centre = (4, 4)
        jumps = HexGrid.get_jumps(centre, self.adj, self.centers, self.step)
        self.assertEqual(len(jumps), 6)


# ──────────────────────────────────────────────────────────────────────────────
# Additional tests (not tied to a specific AC)
# ──────────────────────────────────────────────────────────────────────────────

class TestAdditional(unittest.TestCase):
    """Extra tests covering edge cases and robustness."""

    def test_peg_count_matches_len_pegs(self):
        """peg_count() must equal len(game.pegs)."""
        g = SolitaireGame("English", 7)
        self.assertEqual(g.peg_count(), len(g.pegs))

    def test_cell_count_matches_valid_cells(self):
        """cell_count() must equal len(game.valid_cells)."""
        g = SolitaireGame("Hexagon", 9)
        self.assertEqual(g.cell_count(), len(g.valid_cells))

    def test_multiple_moves_reduce_peg_count(self):
        """Each successive valid move must reduce peg count by 1."""
        g = SolitaireGame("English", 7)
        for _ in range(5):
            moves = g.get_valid_moves()
            if not moves:
                break
            before = g.peg_count()
            fr, _, to = moves[0]
            g.make_move(fr, to)
            self.assertEqual(g.peg_count(), before - 1)

    def test_repr_contains_board_type(self):
        """__repr__ must mention the board type."""
        g = SolitaireGame("Diamond", 7)
        self.assertIn("Diamond", repr(g))

    def test_hexagon_size7_total_cells(self):
        """Hexagon size-7 board should have 37 cells (7+6+5+... centred)."""
        cells = Board.hexagon(7)
        expected = sum(7 - abs(r - 3) for r in range(7))
        self.assertEqual(len(cells), expected)

    def test_english_all_cells_in_row_or_col_band(self):
        """Every English cell must lie in the middle row-band or col-band."""
        size = 7
        third = size // 3
        cells = Board.english(size)
        for (r, c) in cells:
            in_col = third <= c < size - third
            in_row = third <= r < size - third
            self.assertTrue(in_col or in_row,
                            f"Cell ({r},{c}) outside both bands")

    def test_diamond_symmetric(self):
        """Diamond board must be symmetric about both axes."""
        cells = Board.diamond(7)
        mid = 3
        for (r, c) in cells:
            self.assertIn((mid*2-r, c), cells, f"Not symmetric vertically: ({r},{c})")
            self.assertIn((r, mid*2-c), cells, f"Not symmetric horizontally: ({r},{c})")

    def test_no_move_from_empty_cell(self):
        """get_valid_moves() must never list a move from an empty cell."""
        g = SolitaireGame("English", 7)
        for (fr, mid, to) in g.get_valid_moves():
            self.assertIn(fr, g.pegs, f"from_cell {fr} is not a peg!")

    def test_board_row_lengths_helper(self):
        """Board.row_lengths() must agree with actual Board.hexagon() cells."""
        size = 9
        expected = Board.row_lengths(size)
        cells = Board.hexagon(size)
        actual = [len([c for (r2,c) in cells if r2==r]) for r in range(size)]
        self.assertEqual(actual, expected)


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
