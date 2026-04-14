"""
test_solitaire.py
=================
xUnit test suite for Peg Solitaire — Sprint 3.

Tests are organised by User Story / Acceptance Criterion so that the
Sprint 3 submission tables can reference class + method names directly.

Test classes
------------
TestBoardShapes      – US1: board size & type         (AC 1.1–1.4)
TestGameModeChoice   – US2: choose game mode           (AC 2.1–2.2)
TestNewGame          – US3: start a new game           (AC 3.1–3.2)
TestManualMove       – US4: make a move (manual)       (AC 4.1–4.2)
TestManualGameOver   – US5: manual game is over        (AC 5.1–5.2)
TestAutoMove         – US6: make a move (automated)    (AC 6.1–6.2)
TestAutoGameOver     – US7: automated game is over     (AC 7.1–7.2)
TestRandomize        – US8: randomize board state      (AC 8.1–8.2)
TestHexGrid          – Geometry helpers (hex board)
TestAdditional       – Extra tests not tied to a single AC

Run with:
    python -m unittest test_solitaire -v
"""

import unittest
import math
import random
import os
import json
import tempfile
from game_logic import Board, HexGrid, SolitaireGame, ManualGame, AutomatedGame, GameRecorder


# ──────────────────────────────────────────────────────────────────────────────
# US 1  –  Choose a board size and type
# AC 1.1 valid board size  | AC 1.2 change board size
# AC 1.3 English board     | AC 1.4 Hexagon / Diamond boards
# ──────────────────────────────────────────────────────────────────────────────

class TestBoardShapes(unittest.TestCase):
    """US1 — board shape construction tests."""

    # AC 1.1 ──────────────────────────────────────────────────────────────────

    def test_ac1_1_english_size7_cell_count(self):
        """English size-7 board must have exactly 33 valid cells."""
        self.assertEqual(len(Board.english(7)), 33)

    def test_ac1_1_english_size5_cell_count(self):
        """English size-5 board cell count matches the formula."""
        third = 5 // 3
        expected = len({(r, c) for r in range(5) for c in range(5)
                        if (third <= c < 5 - third) or (third <= r < 5 - third)})
        self.assertEqual(len(Board.english(5)), expected)

    def test_ac1_1_diamond_size7_cell_count(self):
        """Diamond size-7 board has 25 cells."""
        self.assertEqual(len(Board.diamond(7)), 25)

    def test_ac1_1_hexagon_size9_row_lengths(self):
        """Hexagonal size-9 board row lengths must be 5,6,7,8,9,8,7,6,5."""
        cells = Board.hexagon(9)
        actual = [len([c for (r2, c) in cells if r2 == r]) for r in range(9)]
        self.assertEqual(actual, [5, 6, 7, 8, 9, 8, 7, 6, 5])

    def test_ac1_1_hexagon_size5_row_lengths(self):
        """Hexagonal size-5 board row lengths must be 3,4,5,4,3."""
        cells = Board.hexagon(5)
        actual = [len([c for (r2, c) in cells if r2 == r]) for r in range(5)]
        self.assertEqual(actual, [3, 4, 5, 4, 3])

    # AC 1.2 ──────────────────────────────────────────────────────────────────

    def test_ac1_2_resize_english_7_to_9(self):
        """Changing size 7→9 increases cell count for English board."""
        self.assertGreater(
            ManualGame("English", 9).cell_count(),
            ManualGame("English", 7).cell_count()
        )

    def test_ac1_2_hexagon_different_sizes_differ(self):
        """Hexagon size 7 and size 9 must have different cell counts."""
        self.assertNotEqual(
            ManualGame("Hexagon", 7).cell_count(),
            ManualGame("Hexagon", 9).cell_count()
        )

    # AC 1.3 ──────────────────────────────────────────────────────────────────

    def test_ac1_3_english_board_is_cross_shaped(self):
        """English board corners must NOT be in valid cells."""
        cells = Board.english(7)
        for corner in [(0, 0), (0, 6), (6, 0), (6, 6)]:
            self.assertNotIn(corner, cells)

    def test_ac1_3_english_centre_in_cells(self):
        """Centre cell must be part of the English board."""
        self.assertIn((3, 3), Board.english(7))

    # AC 1.4 ──────────────────────────────────────────────────────────────────

    def test_ac1_4_hexagon_board_type_stored(self):
        g = ManualGame("Hexagon", 9)
        self.assertEqual(g.board_type, "Hexagon")

    def test_ac1_4_diamond_board_type_stored(self):
        g = ManualGame("Diamond", 7)
        self.assertEqual(g.board_type, "Diamond")

    def test_ac1_4_diamond_corners_absent(self):
        cells = Board.diamond(7)
        self.assertNotIn((0, 0), cells)
        self.assertNotIn((6, 6), cells)

    def test_ac1_4_invalid_board_type_raises(self):
        with self.assertRaises(ValueError):
            ManualGame("Triangle", 7)


# ──────────────────────────────────────────────────────────────────────────────
# US 2  –  Choose the game mode
# AC 2.1 create ManualGame  | AC 2.2 create AutomatedGame
# ──────────────────────────────────────────────────────────────────────────────

class TestGameModeChoice(unittest.TestCase):
    """US2 — selecting Manual or Automated game mode."""

    # AC 2.1 ──────────────────────────────────────────────────────────────────

    def test_ac2_1_manual_game_is_manual_game_instance(self):
        """Choosing Manual mode must produce a ManualGame instance."""
        g = ManualGame("English", 7)
        self.assertIsInstance(g, ManualGame)

    def test_ac2_1_manual_game_is_also_solitaire_game(self):
        """ManualGame must be a subclass of SolitaireGame."""
        g = ManualGame("English", 7)
        self.assertIsInstance(g, SolitaireGame)

    def test_ac2_1_manual_game_has_move_history(self):
        """ManualGame must expose a move_history list."""
        g = ManualGame("English", 7)
        self.assertIsInstance(g.move_history, list)

    # AC 2.2 ──────────────────────────────────────────────────────────────────

    def test_ac2_2_automated_game_is_automated_game_instance(self):
        """Choosing Automated mode must produce an AutomatedGame instance."""
        g = AutomatedGame("English", 7)
        self.assertIsInstance(g, AutomatedGame)

    def test_ac2_2_automated_game_is_also_solitaire_game(self):
        """AutomatedGame must be a subclass of SolitaireGame."""
        g = AutomatedGame("English", 7)
        self.assertIsInstance(g, SolitaireGame)

    def test_ac2_2_automated_game_has_last_move_attr(self):
        """AutomatedGame must expose last_move attribute."""
        g = AutomatedGame("English", 7)
        self.assertTrue(hasattr(g, "last_move"))


# ──────────────────────────────────────────────────────────────────────────────
# US 3  –  Start a new game
# AC 3.1 pegs initialised  | AC 3.2 reset clears state
# ──────────────────────────────────────────────────────────────────────────────

class TestNewGame(unittest.TestCase):
    """US3 — game initialisation."""

    # AC 3.1 ──────────────────────────────────────────────────────────────────

    def test_ac3_1_english_game_pegs_minus_one(self):
        g = ManualGame("English", 7)
        self.assertEqual(g.peg_count(), g.cell_count() - 1)

    def test_ac3_1_hexagon_game_pegs_minus_one(self):
        g = ManualGame("Hexagon", 9)
        self.assertEqual(g.peg_count(), g.cell_count() - 1)

    def test_ac3_1_diamond_game_pegs_minus_one(self):
        g = ManualGame("Diamond", 7)
        self.assertEqual(g.peg_count(), g.cell_count() - 1)

    def test_ac3_1_english_centre_empty_at_start(self):
        g = ManualGame("English", 7)
        self.assertNotIn((3, 3), g.pegs)

    def test_ac3_1_hexagon_centre_empty_at_start(self):
        g = ManualGame("Hexagon", 9)
        self.assertNotIn((4, 4), g.pegs)

    def test_ac3_1_initial_moves_available_all_types(self):
        """A new game of every board type must have at least one valid move."""
        for bt in SolitaireGame.BOARD_TYPES:
            with self.subTest(board_type=bt):
                g = ManualGame(bt, 9 if bt == "Hexagon" else 7)
                self.assertGreater(len(g.get_valid_moves()), 0)

    # AC 3.2 ──────────────────────────────────────────────────────────────────

    def test_ac3_2_reset_restores_peg_count(self):
        """After moves, reset() must restore the original peg count."""
        g = ManualGame("English", 7)
        original = g.peg_count()
        moves = g.get_valid_moves()
        g.make_move(moves[0][0], moves[0][2])
        g.reset()
        self.assertEqual(g.peg_count(), original)

    def test_ac3_2_reset_clears_move_history(self):
        """After reset(), ManualGame.move_history must be empty."""
        g = ManualGame("English", 7)
        moves = g.get_valid_moves()
        g.make_move(moves[0][0], moves[0][2])
        self.assertEqual(len(g.move_history), 1)
        g.reset()
        self.assertEqual(len(g.move_history), 0)

    def test_ac3_2_reset_empties_centre(self):
        """After reset(), centre cell must be empty."""
        g = ManualGame("English", 7)
        g.pegs.add((3, 3))
        g.reset()
        self.assertNotIn((3, 3), g.pegs)


# ──────────────────────────────────────────────────────────────────────────────
# US 4  –  Make a move in a manual game
# AC 4.1 valid move accepted  | AC 4.2 invalid move rejected
# ──────────────────────────────────────────────────────────────────────────────

class TestManualMove(unittest.TestCase):
    """US4 — making a move in a ManualGame."""

    def setUp(self):
        self.game_eng = ManualGame("English", 7)
        self.game_hex = ManualGame("Hexagon", 9)

    # AC 4.1 ──────────────────────────────────────────────────────────────────

    def test_ac4_1_valid_move_returns_true(self):
        fr, _, to = self.game_eng.get_valid_moves()[0]
        self.assertTrue(self.game_eng.make_move(fr, to))

    def test_ac4_1_move_reduces_peg_count_by_one(self):
        before = self.game_eng.peg_count()
        fr, _, to = self.game_eng.get_valid_moves()[0]
        self.game_eng.make_move(fr, to)
        self.assertEqual(self.game_eng.peg_count(), before - 1)

    def test_ac4_1_move_recorded_in_history(self):
        """A successful move must be appended to move_history."""
        fr, _, to = self.game_eng.get_valid_moves()[0]
        self.game_eng.make_move(fr, to)
        self.assertEqual(len(self.game_eng.move_history), 1)
        self.assertEqual(self.game_eng.move_history[0], (fr, to))

    def test_ac4_1_hex_valid_move_returns_true(self):
        moves = self.game_hex.get_valid_moves()
        if moves:
            fr, _, to = moves[0]
            self.assertTrue(self.game_hex.make_move(fr, to))

    def test_ac4_1_from_cell_becomes_empty(self):
        fr, _, to = self.game_eng.get_valid_moves()[0]
        self.game_eng.make_move(fr, to)
        self.assertNotIn(fr, self.game_eng.pegs)

    def test_ac4_1_to_cell_gains_peg(self):
        fr, _, to = self.game_eng.get_valid_moves()[0]
        self.game_eng.make_move(fr, to)
        self.assertIn(to, self.game_eng.pegs)

    def test_ac4_1_jumped_peg_removed(self):
        fr, mid, to = self.game_eng.get_valid_moves()[0]
        self.game_eng.make_move(fr, to)
        self.assertNotIn(mid, self.game_eng.pegs)

    # AC 4.2 ──────────────────────────────────────────────────────────────────

    def test_ac4_2_move_to_occupied_cell_rejected(self):
        moves = self.game_eng.get_valid_moves()
        fr, _, _ = moves[0]
        # Try to move to a cell that already has a peg
        occupied = next(iter(self.game_eng.pegs - {fr}))
        self.assertFalse(self.game_eng.make_move(fr, occupied))

    def test_ac4_2_jump_over_empty_cell_rejected(self):
        fr, mid, to = self.game_eng.get_valid_moves()[0]
        self.game_eng.pegs.discard(mid)
        self.assertFalse(self.game_eng.make_move(fr, to))

    def test_ac4_2_failed_move_does_not_change_state(self):
        before = frozenset(self.game_eng.pegs)
        self.game_eng.make_move((0, 0), (0, 6))
        self.assertEqual(frozenset(self.game_eng.pegs), before)

    def test_ac4_2_failed_move_not_in_history(self):
        """A failed move must NOT be recorded in move_history."""
        self.game_eng.make_move((0, 0), (0, 6))
        self.assertEqual(len(self.game_eng.move_history), 0)

    def test_ac4_2_is_valid_move_helper(self):
        fr, _, to = self.game_eng.get_valid_moves()[0]
        self.assertTrue(self.game_eng.is_valid_move(fr, to))
        self.assertFalse(self.game_eng.is_valid_move(fr, fr))


# ──────────────────────────────────────────────────────────────────────────────
# US 5  –  A manual game is over
# AC 5.1 no moves = game over  | AC 5.2 one peg = win
# ──────────────────────────────────────────────────────────────────────────────

class TestManualGameOver(unittest.TestCase):
    """US5 — end-of-game detection for ManualGame."""

    # AC 5.1 ──────────────────────────────────────────────────────────────────

    def test_ac5_1_fresh_game_not_over(self):
        g = ManualGame("English", 7)
        self.assertFalse(g.is_game_over())

    def test_ac5_1_single_isolated_peg_is_game_over(self):
        g = ManualGame("English", 7)
        g.pegs = {(3, 3)}
        self.assertTrue(g.is_game_over())

    def test_ac5_1_two_non_adjacent_pegs_game_over(self):
        g = ManualGame("English", 7)
        g.pegs = {(0, 3), (6, 3)}
        self.assertTrue(g.is_game_over())

    def test_ac5_1_two_adjacent_pegs_with_empty_landing_not_game_over(self):
        g = ManualGame("English", 7)
        g.pegs = {(3, 1), (3, 2)}
        self.assertFalse(g.is_game_over())

    # AC 5.2 ──────────────────────────────────────────────────────────────────

    def test_ac5_2_one_peg_is_win(self):
        g = ManualGame("English", 7)
        g.pegs = {(3, 3)}
        self.assertTrue(g.is_win())

    def test_ac5_2_two_pegs_not_win(self):
        g = ManualGame("English", 7)
        g.pegs = {(3, 3), (3, 4)}
        self.assertFalse(g.is_win())

    def test_ac5_2_fresh_game_not_win(self):
        g = ManualGame("English", 7)
        self.assertFalse(g.is_win())

    def test_ac5_2_win_implies_game_over(self):
        g = ManualGame("English", 7)
        g.pegs = {(3, 3)}
        self.assertTrue(g.is_win())
        self.assertTrue(g.is_game_over())


# ──────────────────────────────────────────────────────────────────────────────
# US 6  –  Make a move in an automated game
# AC 6.1 auto_step makes a move  | AC 6.2 auto_step when no moves returns False
# ──────────────────────────────────────────────────────────────────────────────

class TestAutoMove(unittest.TestCase):
    """US6 — making a move in an AutomatedGame."""

    def setUp(self):
        self.game = AutomatedGame("English", 7)

    # AC 6.1 ──────────────────────────────────────────────────────────────────

    def test_ac6_1_auto_step_returns_true_when_moves_available(self):
        self.assertTrue(self.game.auto_step())

    def test_ac6_1_auto_step_reduces_peg_count(self):
        before = self.game.peg_count()
        self.game.auto_step()
        self.assertEqual(self.game.peg_count(), before - 1)

    def test_ac6_1_auto_step_sets_last_move(self):
        self.game.auto_step()
        self.assertIsNotNone(self.game.last_move)
        self.assertIsInstance(self.game.last_move, tuple)
        self.assertEqual(len(self.game.last_move), 2)

    def test_ac6_1_auto_step_hex_board(self):
        g = AutomatedGame("Hexagon", 9)
        self.assertTrue(g.auto_step())

    def test_ac6_1_auto_step_diamond_board(self):
        g = AutomatedGame("Diamond", 7)
        self.assertTrue(g.auto_step())

    def test_ac6_1_solve_returns_non_empty_move_list(self):
        """solve() must return at least one move for a fresh game."""
        moves = self.game.solve()
        self.assertGreater(len(moves), 0)

    def test_ac6_1_solve_reduces_peg_count(self):
        """After solve(), the board should have fewer pegs than at start."""
        initial = self.game.peg_count()
        self.game.solve()
        self.assertLess(self.game.peg_count(), initial)

    # AC 6.2 ──────────────────────────────────────────────────────────────────

    def test_ac6_2_auto_step_returns_false_when_no_moves(self):
        """auto_step() on a stuck position must return False."""
        self.game.pegs = {(0, 3), (6, 3)}  # two non-adjacent pegs, no moves
        self.assertFalse(self.game.auto_step())

    def test_ac6_2_auto_step_no_state_change_when_no_moves(self):
        self.game.pegs = {(0, 3), (6, 3)}
        before = frozenset(self.game.pegs)
        self.game.auto_step()
        self.assertEqual(frozenset(self.game.pegs), before)


# ──────────────────────────────────────────────────────────────────────────────
# US 7  –  An automated game is over
# AC 7.1 auto solve then game over  | AC 7.2 is_win after solve
# ──────────────────────────────────────────────────────────────────────────────

class TestAutoGameOver(unittest.TestCase):
    """US7 — end-of-game detection for AutomatedGame."""

    # AC 7.1 ──────────────────────────────────────────────────────────────────

    def test_ac7_1_game_over_after_solve(self):
        """After solve(), is_game_over() must be True."""
        g = AutomatedGame("English", 7)
        g.solve()
        self.assertTrue(g.is_game_over())

    def test_ac7_1_fresh_automated_game_not_over(self):
        g = AutomatedGame("English", 7)
        self.assertFalse(g.is_game_over())

    def test_ac7_1_game_over_detected_during_step_loop(self):
        """Step-by-step auto_step() eventually leads to game over."""
        g = AutomatedGame("Diamond", 7)
        steps = 0
        while not g.is_game_over():
            g.auto_step()
            steps += 1
            if steps > 500:
                self.fail("Step loop did not terminate in 500 steps")
        self.assertTrue(g.is_game_over())

    # AC 7.2 ──────────────────────────────────────────────────────────────────

    def test_ac7_2_win_check_after_solve(self):
        """After solve(), is_win() should reflect final peg count."""
        g = AutomatedGame("English", 7)
        g.solve()
        # Win is possible but not guaranteed; at minimum peg count is checked
        self.assertEqual(g.is_win(), g.peg_count() == 1)

    def test_ac7_2_automated_game_one_peg_is_win(self):
        g = AutomatedGame("English", 7)
        g.pegs = {(3, 3)}
        self.assertTrue(g.is_win())


# ──────────────────────────────────────────────────────────────────────────────
# US 8  –  Randomize the state of the board during a manual game
# AC 8.1 randomize changes board  | AC 8.2 board remains valid after randomize
# ──────────────────────────────────────────────────────────────────────────────

class TestRandomize(unittest.TestCase):
    """US8 — randomize_board() on a ManualGame."""

    def setUp(self):
        random.seed(42)
        self.game = ManualGame("English", 7)

    # AC 8.1 ──────────────────────────────────────────────────────────────────

    def test_ac8_1_randomize_returns_positive_move_count(self):
        n = self.game.randomize_board(num_moves=5)
        self.assertGreater(n, 0)

    def test_ac8_1_randomize_changes_board_state(self):
        before = frozenset(self.game.pegs)
        self.game.randomize_board(num_moves=5)
        after = frozenset(self.game.pegs)
        self.assertNotEqual(before, after)

    def test_ac8_1_randomize_does_not_pollute_history(self):
        """randomize_board() must NOT add entries to move_history."""
        self.game.randomize_board(num_moves=5)
        self.assertEqual(len(self.game.move_history), 0)

    def test_ac8_1_randomize_hex_board(self):
        g = ManualGame("Hexagon", 9)
        n = g.randomize_board(num_moves=5)
        self.assertGreater(n, 0)

    # AC 8.2 ──────────────────────────────────────────────────────────────────

    def test_ac8_2_pegs_remain_subset_of_valid_cells(self):
        """After randomize, all pegs must still be on valid cells."""
        self.game.randomize_board(num_moves=10)
        self.assertTrue(self.game.pegs.issubset(self.game.valid_cells))

    def test_ac8_2_peg_count_decreases(self):
        """Randomization removes pegs; count must decrease."""
        before = self.game.peg_count()
        self.game.randomize_board(num_moves=5)
        self.assertLess(self.game.peg_count(), before)

    def test_ac8_2_game_still_has_valid_cells_after_randomize(self):
        """valid_cells must be unchanged after randomize."""
        before_cells = frozenset(self.game.valid_cells)
        self.game.randomize_board(num_moves=10)
        self.assertEqual(frozenset(self.game.valid_cells), before_cells)

    def test_ac8_2_automated_game_has_no_randomize(self):
        """AutomatedGame must NOT have a randomize_board method."""
        g = AutomatedGame("English", 7)
        self.assertFalse(hasattr(g, "randomize_board"))


# ──────────────────────────────────────────────────────────────────────────────
# Hex geometry tests
# ──────────────────────────────────────────────────────────────────────────────

class TestHexGrid(unittest.TestCase):
    """Tests for HexGrid geometry helpers."""

    def setUp(self):
        self.centers, self.cw, self.ch = HexGrid.cell_centers(9)
        self.adj, self.step = HexGrid.build_adjacency(self.centers)

    def test_centre_has_six_neighbours(self):
        self.assertEqual(len(self.adj[(4, 4)]), 6)

    def test_horizontal_step_matches_formula(self):
        expected = math.sqrt(3) * HexGrid.HEX_R
        self.assertAlmostEqual(self.step, expected, places=1)

    def test_all_cells_have_centers(self):
        for cell in Board.hexagon(9):
            self.assertIn(cell, self.centers)

    def test_corner_cells_have_fewer_neighbours(self):
        self.assertLess(len(self.adj[(0, 0)]), 6)

    def test_jumps_from_centre_are_six(self):
        jumps = HexGrid.get_jumps((4, 4), self.adj, self.centers, self.step)
        self.assertEqual(len(jumps), 6)


# ──────────────────────────────────────────────────────────────────────────────
# Additional tests (not tied to a specific AC)
# ──────────────────────────────────────────────────────────────────────────────

class TestAdditional(unittest.TestCase):
    """Extra tests covering hierarchy, edge cases, and robustness."""

    def test_class_hierarchy_manual_is_subclass(self):
        """ManualGame must be a proper subclass of SolitaireGame."""
        self.assertTrue(issubclass(ManualGame, SolitaireGame))

    def test_class_hierarchy_automated_is_subclass(self):
        """AutomatedGame must be a proper subclass of SolitaireGame."""
        self.assertTrue(issubclass(AutomatedGame, SolitaireGame))

    def test_peg_count_matches_len_pegs(self):
        g = ManualGame("English", 7)
        self.assertEqual(g.peg_count(), len(g.pegs))

    def test_cell_count_matches_valid_cells(self):
        g = ManualGame("Hexagon", 9)
        self.assertEqual(g.cell_count(), len(g.valid_cells))

    def test_multiple_moves_reduce_peg_count(self):
        g = ManualGame("English", 7)
        for _ in range(5):
            moves = g.get_valid_moves()
            if not moves:
                break
            before = g.peg_count()
            fr, _, to = moves[0]
            g.make_move(fr, to)
            self.assertEqual(g.peg_count(), before - 1)

    def test_repr_contains_class_name(self):
        self.assertIn("ManualGame", repr(ManualGame("English", 7)))
        self.assertIn("AutomatedGame", repr(AutomatedGame("English", 7)))

    def test_hexagon_size7_total_cells(self):
        cells = Board.hexagon(7)
        expected = sum(7 - abs(r - 3) for r in range(7))
        self.assertEqual(len(cells), expected)

    def test_english_all_cells_in_row_or_col_band(self):
        size, third = 7, 2
        for (r, c) in Board.english(size):
            self.assertTrue(
                (third <= c < size - third) or (third <= r < size - third),
                f"Cell ({r},{c}) outside both bands"
            )

    def test_diamond_symmetric(self):
        cells = Board.diamond(7)
        mid = 3
        for (r, c) in cells:
            self.assertIn((mid * 2 - r, c), cells)
            self.assertIn((r, mid * 2 - c), cells)

    def test_no_move_from_empty_cell(self):
        g = ManualGame("English", 7)
        for (fr, _, _) in g.get_valid_moves():
            self.assertIn(fr, g.pegs)

    def test_board_row_lengths_helper(self):
        size = 9
        expected = Board.row_lengths(size)
        cells = Board.hexagon(size)
        actual = [len([c for (r2, c) in cells if r2 == r]) for r in range(size)]
        self.assertEqual(actual, expected)

    def test_solve_returns_list_of_tuples(self):
        g = AutomatedGame("English", 7)
        moves = g.solve()
        self.assertIsInstance(moves, list)
        for m in moves:
            self.assertIsInstance(m, tuple)
            self.assertEqual(len(m), 2)

    def test_manual_game_history_grows_with_moves(self):
        g = ManualGame("English", 7)
        for i in range(3):
            moves = g.get_valid_moves()
            if not moves:
                break
            fr, _, to = moves[0]
            g.make_move(fr, to)
            self.assertEqual(len(g.move_history), i + 1)


# ──────────────────────────────────────────────────────────────────────────────
# US 20  –  Record a game to a file
# AC 20.1  recording captures every move
# AC 20.2  recording captures randomize snapshots
# AC 20.3  recording saves a valid JSON file
# AC 20.4  automated game recording captures moves via auto_step
# ──────────────────────────────────────────────────────────────────────────────

class TestRecordGame(unittest.TestCase):
    """US20 — record a solitaire game into a file."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.game = ManualGame("English", 7)
        self.recorder = GameRecorder("English", 7, "Manual")
        self.game.recorder = self.recorder

    # AC 20.1 ─────────────────────────────────────────────────────────────────

    def test_ac20_1_recorder_starts_inactive(self):
        """A freshly constructed recorder must not be active."""
        rec = GameRecorder("English", 7, "Manual")
        self.assertFalse(rec.is_active)

    def test_ac20_1_recorder_active_after_start(self):
        """Calling start() must activate the recorder."""
        self.recorder.start()
        self.assertTrue(self.recorder.is_active)

    def test_ac20_1_move_captured_when_active(self):
        """Every valid move made while recording must appear in events."""
        self.recorder.start()
        fr, _, to = self.game.get_valid_moves()[0]
        self.game.make_move(fr, to)
        move_events = [e for e in self.recorder.events if e["type"] == "move"]
        self.assertEqual(len(move_events), 1)
        self.assertEqual(move_events[0]["from"], list(fr))
        self.assertEqual(move_events[0]["to"],   list(to))

    def test_ac20_1_multiple_moves_all_captured(self):
        """All moves made during a recording must be stored in order."""
        self.recorder.start()
        made = []
        for _ in range(4):
            moves = self.game.get_valid_moves()
            if not moves:
                break
            fr, _, to = moves[0]
            self.game.make_move(fr, to)
            made.append((fr, to))
        move_events = [e for e in self.recorder.events if e["type"] == "move"]
        self.assertEqual(len(move_events), len(made))

    def test_ac20_1_move_not_captured_when_inactive(self):
        """Moves made before start() must NOT be captured."""
        fr, _, to = self.game.get_valid_moves()[0]
        self.game.make_move(fr, to)          # recorder not started
        self.assertEqual(len(self.recorder.events), 0)

    def test_ac20_1_failed_move_not_captured(self):
        """A rejected move must not produce a recording event."""
        self.recorder.start()
        self.game.make_move((0, 0), (0, 6))  # always invalid
        self.assertEqual(len(self.recorder.events), 0)

    # AC 20.2 ─────────────────────────────────────────────────────────────────

    def test_ac20_2_randomize_captured_as_snapshot(self):
        """randomize_board() while recording must produce a 'randomize' event."""
        self.recorder.start()
        self.game.randomize_board(num_moves=5)
        rand_events = [e for e in self.recorder.events if e["type"] == "randomize"]
        self.assertEqual(len(rand_events), 1)

    def test_ac20_2_randomize_snapshot_contains_pegs(self):
        """The 'randomize' event must store the full peg list."""
        self.recorder.start()
        self.game.randomize_board(num_moves=5)
        snap = next(e for e in self.recorder.events if e["type"] == "randomize")
        self.assertIn("pegs", snap)
        self.assertIsInstance(snap["pegs"], list)
        self.assertGreater(len(snap["pegs"]), 0)

    def test_ac20_2_randomize_snapshot_matches_board(self):
        """The snapshot must exactly match the board's peg set after randomize."""
        self.recorder.start()
        self.game.randomize_board(num_moves=5)
        snap = next(e for e in self.recorder.events if e["type"] == "randomize")
        recorded_pegs = {tuple(p) for p in snap["pegs"]}
        self.assertEqual(recorded_pegs, self.game.pegs)

    def test_ac20_2_randomize_not_captured_when_inactive(self):
        """randomize_board() before start() must not produce events."""
        self.game.randomize_board(num_moves=5)
        self.assertEqual(len(self.recorder.events), 0)

    # AC 20.3 ─────────────────────────────────────────────────────────────────

    def test_ac20_3_save_creates_file(self):
        """save() must create a file at the given path."""
        self.recorder.start()
        fr, _, to = self.game.get_valid_moves()[0]
        self.game.make_move(fr, to)
        path = os.path.join(self.tmpdir, "test_game.json")
        self.recorder.save(path)
        self.assertTrue(os.path.isfile(path))

    def test_ac20_3_saved_file_is_valid_json(self):
        """The saved file must be parseable JSON."""
        self.recorder.start()
        fr, _, to = self.game.get_valid_moves()[0]
        self.game.make_move(fr, to)
        path = os.path.join(self.tmpdir, "test_game.json")
        self.recorder.save(path)
        with open(path) as fh:
            data = json.load(fh)
        self.assertIn("metadata", data)
        self.assertIn("events",   data)

    def test_ac20_3_metadata_fields_present(self):
        """The JSON metadata block must contain board_type, size, mode."""
        self.recorder.start()
        path = os.path.join(self.tmpdir, "meta_test.json")
        self.recorder.save(path)
        with open(path) as fh:
            data = json.load(fh)
        meta = data["metadata"]
        self.assertEqual(meta["board_type"], "English")
        self.assertEqual(meta["size"],       7)
        self.assertEqual(meta["mode"],       "Manual")

    def test_ac20_3_save_returns_filepath(self):
        """save() must return the path it wrote to."""
        self.recorder.start()
        path = os.path.join(self.tmpdir, "ret_path.json")
        returned = self.recorder.save(path)
        self.assertEqual(returned, path)

    def test_ac20_3_stop_deactivates_recorder(self):
        """stop() must set is_active to False."""
        self.recorder.start()
        self.recorder.stop()
        self.assertFalse(self.recorder.is_active)

    # AC 20.4 ─────────────────────────────────────────────────────────────────

    def test_ac20_4_automated_game_moves_recorded(self):
        """auto_step() while recording must produce move events."""
        ag = AutomatedGame("English", 7)
        rec = GameRecorder("English", 7, "Automated")
        ag.recorder = rec
        rec.start()
        for _ in range(5):
            if not ag.auto_step():
                break
        move_events = [e for e in rec.events if e["type"] == "move"]
        self.assertGreater(len(move_events), 0)

    def test_ac20_4_automated_full_game_recorded(self):
        """Recording a full automated game must capture all its moves."""
        ag = AutomatedGame("English", 7)
        rec = GameRecorder("English", 7, "Automated")
        ag.recorder = rec
        rec.start()
        while ag.auto_step():
            pass
        move_events = [e for e in rec.events if e["type"] == "move"]
        self.assertGreater(len(move_events), 0)
        path = os.path.join(self.tmpdir, "auto_full.json")
        rec.save(path)
        with open(path) as fh:
            data = json.load(fh)
        self.assertEqual(data["metadata"]["mode"], "Automated")


# ──────────────────────────────────────────────────────────────────────────────
# US 21  –  Replay a game from a file
# AC 21.1  replay rebuilds board state move-by-move
# AC 21.2  replay handles randomize snapshots correctly
# AC 21.3  replay of an automated game reproduces move count
# AC 21.4  load() raises on a bad file
# ──────────────────────────────────────────────────────────────────────────────

class TestReplayGame(unittest.TestCase):
    """US21 — replay a recorded solitaire game from a file."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def _record_manual_game(self, num_moves=5, board_type="English", size=7):
        """Helper: play and record num_moves of a ManualGame, return filepath."""
        game = ManualGame(board_type, size)
        rec  = GameRecorder(board_type, size, "Manual")
        game.recorder = rec
        rec.start()
        for _ in range(num_moves):
            moves = game.get_valid_moves()
            if not moves:
                break
            fr, _, to = moves[0]
            game.make_move(fr, to)
        rec.stop()
        path = os.path.join(self.tmpdir, "manual.json")
        rec.save(path)
        return path, game   # also return final game state for comparison

    def _record_automated_game(self, board_type="English", size=7):
        """Helper: run and record a full AutomatedGame, return filepath."""
        game = AutomatedGame(board_type, size)
        rec  = GameRecorder(board_type, size, "Automated")
        game.recorder = rec
        rec.start()
        while game.auto_step():
            pass
        rec.stop()
        path = os.path.join(self.tmpdir, "auto.json")
        rec.save(path)
        return path, game

    # AC 21.1 ─────────────────────────────────────────────────────────────────

    def test_ac21_1_load_returns_dict_with_metadata_and_events(self):
        """GameRecorder.load() must return a dict with metadata and events keys."""
        path, _ = self._record_manual_game()
        data = GameRecorder.load(path)
        self.assertIn("metadata", data)
        self.assertIn("events",   data)

    def test_ac21_1_build_replay_game_returns_game_and_events(self):
        """build_replay_game() must return a SolitaireGame and an events list."""
        path, _ = self._record_manual_game()
        data = GameRecorder.load(path)
        game, events = GameRecorder.build_replay_game(data)
        self.assertIsInstance(game, SolitaireGame)
        self.assertIsInstance(events, list)

    def test_ac21_1_replay_produces_correct_final_peg_count(self):
        """Replaying all move events must yield the same peg count as the original game."""
        path, original = self._record_manual_game(num_moves=5)
        data = GameRecorder.load(path)
        replay_game, events = GameRecorder.build_replay_game(data)
        for event in events:
            if event["type"] == "move":
                fr = tuple(event["from"])
                to = tuple(event["to"])
                SolitaireGame.make_move(replay_game, fr, to)
        self.assertEqual(replay_game.peg_count(), original.peg_count())

    def test_ac21_1_replay_produces_correct_peg_positions(self):
        """After replaying all moves the peg set must match the original game."""
        path, original = self._record_manual_game(num_moves=5)
        data = GameRecorder.load(path)
        replay_game, events = GameRecorder.build_replay_game(data)
        for event in events:
            if event["type"] == "move":
                fr = tuple(event["from"])
                to = tuple(event["to"])
                SolitaireGame.make_move(replay_game, fr, to)
        self.assertEqual(replay_game.pegs, original.pegs)

    def test_ac21_1_replay_game_board_type_matches(self):
        """Replayed game must use the same board type as the recorded one."""
        path, _ = self._record_manual_game(board_type="Diamond", size=7)
        data = GameRecorder.load(path)
        game, _ = GameRecorder.build_replay_game(data)
        self.assertEqual(game.board_type, "Diamond")

    def test_ac21_1_replay_game_size_matches(self):
        """Replayed game must use the same board size as the recorded one."""
        path, _ = self._record_manual_game(board_type="English", size=7)
        data = GameRecorder.load(path)
        game, _ = GameRecorder.build_replay_game(data)
        self.assertEqual(game.size, 7)

    def test_ac21_1_replay_move_count_matches_events(self):
        """Number of move events in the file must equal moves applied during recording."""
        num_moves = 4
        path, _ = self._record_manual_game(num_moves=num_moves)
        data = GameRecorder.load(path)
        move_events = [e for e in data["events"] if e["type"] == "move"]
        self.assertEqual(len(move_events), num_moves)

    # AC 21.2 ─────────────────────────────────────────────────────────────────

    def test_ac21_2_randomize_event_in_recording(self):
        """A game that calls randomize_board must produce a randomize event in the file."""
        game = ManualGame("English", 7)
        rec  = GameRecorder("English", 7, "Manual")
        game.recorder = rec
        rec.start()
        # make a move, then randomize
        fr, _, to = game.get_valid_moves()[0]
        game.make_move(fr, to)
        game.randomize_board(num_moves=5)
        rec.stop()
        path = os.path.join(self.tmpdir, "rand_game.json")
        rec.save(path)
        data = GameRecorder.load(path)
        rand_events = [e for e in data["events"] if e["type"] == "randomize"]
        self.assertEqual(len(rand_events), 1)

    def test_ac21_2_replay_randomize_restores_peg_set(self):
        """Applying a randomize event must restore pegs to the recorded snapshot."""
        game = ManualGame("English", 7)
        rec  = GameRecorder("English", 7, "Manual")
        game.recorder = rec
        rec.start()
        game.randomize_board(num_moves=6)
        pegs_after_rand = frozenset(game.pegs)
        rec.stop()
        path = os.path.join(self.tmpdir, "rand_replay.json")
        rec.save(path)

        data = GameRecorder.load(path)
        replay_game, events = GameRecorder.build_replay_game(data)
        for event in events:
            if event["type"] == "randomize":
                replay_game.pegs = {tuple(p) for p in event["pegs"]}

        self.assertEqual(frozenset(replay_game.pegs), pegs_after_rand)

    def test_ac21_2_mixed_move_and_randomize_replay(self):
        """Move events before and after a randomize event must replay correctly."""
        game = ManualGame("English", 7)
        rec  = GameRecorder("English", 7, "Manual")
        game.recorder = rec
        rec.start()
        # move before randomize
        fr, _, to = game.get_valid_moves()[0]
        game.make_move(fr, to)
        # randomize
        game.randomize_board(num_moves=4)
        # move after randomize
        moves = game.get_valid_moves()
        if moves:
            fr2, _, to2 = moves[0]
            game.make_move(fr2, to2)
        final_pegs = frozenset(game.pegs)
        rec.stop()
        path = os.path.join(self.tmpdir, "mixed.json")
        rec.save(path)

        data  = GameRecorder.load(path)
        rgame, events = GameRecorder.build_replay_game(data)
        for event in events:
            if event["type"] == "move":
                SolitaireGame.make_move(rgame, tuple(event["from"]), tuple(event["to"]))
            elif event["type"] == "randomize":
                rgame.pegs = {tuple(p) for p in event["pegs"]}

        self.assertEqual(frozenset(rgame.pegs), final_pegs)

    # AC 21.3 ─────────────────────────────────────────────────────────────────

    def test_ac21_3_automated_replay_game_is_automated_game(self):
        """Replaying an automated recording must produce an AutomatedGame."""
        path, _ = self._record_automated_game()
        data = GameRecorder.load(path)
        game, _ = GameRecorder.build_replay_game(data)
        self.assertIsInstance(game, AutomatedGame)

    def test_ac21_3_automated_replay_peg_count_matches(self):
        """Replaying a full automated game must reach the same peg count."""
        path, original = self._record_automated_game()
        data = GameRecorder.load(path)
        replay_game, events = GameRecorder.build_replay_game(data)
        for event in events:
            if event["type"] == "move":
                SolitaireGame.make_move(replay_game, tuple(event["from"]), tuple(event["to"]))
        self.assertEqual(replay_game.peg_count(), original.peg_count())

    def test_ac21_3_automated_replay_peg_positions_match(self):
        """Replaying a full automated game must yield the identical peg set."""
        path, original = self._record_automated_game()
        data = GameRecorder.load(path)
        replay_game, events = GameRecorder.build_replay_game(data)
        for event in events:
            if event["type"] == "move":
                SolitaireGame.make_move(replay_game, tuple(event["from"]), tuple(event["to"]))
        self.assertEqual(replay_game.pegs, original.pegs)

    def test_ac21_3_hex_automated_replay_peg_positions_match(self):
        """Full replay of a Hexagon automated game must reproduce final board."""
        game = AutomatedGame("Hexagon", 9)
        rec  = GameRecorder("Hexagon", 9, "Automated")
        game.recorder = rec
        rec.start()
        while game.auto_step():
            pass
        rec.stop()
        path = os.path.join(self.tmpdir, "hex_auto.json")
        rec.save(path)

        data = GameRecorder.load(path)
        replay_game, events = GameRecorder.build_replay_game(data)
        for event in events:
            if event["type"] == "move":
                SolitaireGame.make_move(replay_game, tuple(event["from"]), tuple(event["to"]))
        self.assertEqual(replay_game.pegs, game.pegs)

    # AC 21.4 ─────────────────────────────────────────────────────────────────

    def test_ac21_4_load_raises_on_missing_file(self):
        """load() must raise an exception when the file does not exist."""
        with self.assertRaises(Exception):
            GameRecorder.load("/nonexistent/path/game.json")

    def test_ac21_4_load_raises_on_invalid_json(self):
        """load() must raise an exception when the file contains invalid JSON."""
        bad_path = os.path.join(self.tmpdir, "bad.json")
        with open(bad_path, "w") as fh:
            fh.write("this is not json {{{{")
        with self.assertRaises(Exception):
            GameRecorder.load(bad_path)

    def test_ac21_4_events_list_is_ordered(self):
        """Events in the loaded file must be in the order they were recorded."""
        game = ManualGame("English", 7)
        rec  = GameRecorder("English", 7, "Manual")
        game.recorder = rec
        rec.start()
        recorded_moves = []
        for _ in range(3):
            moves = game.get_valid_moves()
            if not moves:
                break
            fr, _, to = moves[0]
            game.make_move(fr, to)
            recorded_moves.append((list(fr), list(to)))
        rec.stop()
        path = os.path.join(self.tmpdir, "order_test.json")
        rec.save(path)

        data = GameRecorder.load(path)
        move_events = [e for e in data["events"] if e["type"] == "move"]
        for i, (exp_fr, exp_to) in enumerate(recorded_moves):
            self.assertEqual(move_events[i]["from"], exp_fr)
            self.assertEqual(move_events[i]["to"],   exp_to)


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)