"""
game_logic.py
=============
Pure game-logic layer for Peg Solitaire.
No GUI / tkinter imports here — fully unit-testable in isolation.

Classes
-------
Board       – builds valid-cell sets for English, Hexagon, Diamond boards
HexGrid     – computes pixel centres and adjacency for the hexagonal board
SolitaireGame – owns game state, move validation, win/loss detection
"""

import math


# ──────────────────────────────────────────────────────────────────────────────
# Board shape factories
# ──────────────────────────────────────────────────────────────────────────────

class Board:
    """Static factory methods that return a frozenset of valid (row, col) cells."""

    @staticmethod
    def english(size: int = 7) -> set:
        """Cross-shaped English board. size must be odd."""
        cells = set()
        third = size // 3
        for r in range(size):
            for c in range(size):
                if (third <= c < size - third) or (third <= r < size - third):
                    cells.add((r, c))
        return cells

    @staticmethod
    def diamond(size: int = 7) -> set:
        """Diamond (rotated square) board."""
        cells = set()
        mid = size // 2
        for r in range(size):
            for c in range(size):
                if abs(r - mid) + abs(c - mid) <= mid:
                    cells.add((r, c))
        return cells

    @staticmethod
    def hexagon(size: int = 9) -> set:
        """
        Hexagonal board.
        Row lengths for size=9: 5,6,7,8,9,8,7,6,5
        General formula: row r has (size - |r - mid|) cells.
        """
        cells = set()
        mid = size // 2
        for r in range(size):
            row_len = size - abs(r - mid)
            for c in range(row_len):
                cells.add((r, c))
        return cells

    @staticmethod
    def row_lengths(size: int) -> list:
        """Return list of row lengths for a hexagonal board of given size."""
        mid = size // 2
        return [size - abs(r - mid) for r in range(size)]


# ──────────────────────────────────────────────────────────────────────────────
# Hexagonal grid geometry
# ──────────────────────────────────────────────────────────────────────────────

class HexGrid:
    """
    Computes pixel centres for a pointy-top hexagonal grid and
    builds adjacency lists used for move detection.
    """

    HEX_R = 21  # circumradius in pixels

    @classmethod
    def cell_centers(cls, size: int, pad_x: int = 44, pad_y: int = 44) -> tuple:
        """
        Returns (centers_dict, canvas_width, canvas_height).
        centers_dict maps (row, col) -> (cx, cy).
        Uses pointy-top layout: h_space = sqrt(3)*R, v_space = 1.5*R.
        """
        R = cls.HEX_R
        h_space = math.sqrt(3) * R
        v_space = 1.5 * R
        mid = size // 2
        widest = size
        total_width = (widest - 1) * h_space + pad_x * 2

        centers = {}
        for r in range(size):
            row_len = size - abs(r - mid)
            missing = widest - row_len
            x_start = pad_x + (missing / 2.0) * h_space
            y = pad_y + r * v_space
            for c in range(row_len):
                centers[(r, c)] = (x_start + c * h_space, y)

        canvas_w = total_width
        canvas_h = pad_y * 2 + (size - 1) * v_space
        return centers, canvas_w, canvas_h

    @classmethod
    def build_adjacency(cls, centers: dict) -> tuple:
        """
        Build neighbour lists by proximity.
        Returns (adjacency_dict, step_distance).
        Two cells are neighbours when their distance ≈ step (smallest pairwise dist).
        """
        cells = list(centers.keys())
        if len(cells) < 2:
            return {c: [] for c in cells}, 1.0

        # Sample to find step distance
        sample = cells[:min(30, len(cells))]
        dists = []
        for i, a in enumerate(sample):
            ax, ay = centers[a]
            for b in sample[i + 1:]:
                bx, by = centers[b]
                dists.append(math.hypot(bx - ax, by - ay))
        dists.sort()
        step = dists[0]

        adjacency = {c: [] for c in cells}
        for a in cells:
            ax, ay = centers[a]
            for b in cells:
                if a == b:
                    continue
                bx, by = centers[b]
                if abs(math.hypot(bx - ax, by - ay) - step) < step * 0.25:
                    adjacency[a].append(b)

        return adjacency, step

    @classmethod
    def get_jumps(cls, cell: tuple, adjacency: dict,
                  centers: dict, step: float) -> list:
        """
        Return all (mid_cell, to_cell) jump pairs reachable from cell.
        A jump reflects cell through mid to land on to.
        """
        cx, cy = centers[cell]
        jumps = []
        for mid in adjacency.get(cell, []):
            mx, my = centers[mid]
            tx, ty = 2 * mx - cx, 2 * my - cy
            best, best_d = None, float('inf')
            for c2, (px, py) in centers.items():
                d = math.hypot(px - tx, py - ty)
                if d < best_d:
                    best_d, best = d, c2
            if best is not None and best_d < step * 0.35 and best != cell:
                jumps.append((mid, best))
        return jumps


# ──────────────────────────────────────────────────────────────────────────────
# Game state
# ──────────────────────────────────────────────────────────────────────────────

class SolitaireGame:
    """
    Owns all mutable game state.

    Attributes
    ----------
    board_type  : "English" | "Hexagon" | "Diamond"
    size        : int  (board size parameter)
    valid_cells : set of (r, c) that are part of the board
    pegs        : set of (r, c) that currently hold a peg
    """

    BOARD_TYPES = ("English", "Hexagon", "Diamond")

    def __init__(self, board_type: str = "Hexagon", size: int = 9):
        if board_type not in self.BOARD_TYPES:
            raise ValueError(f"board_type must be one of {self.BOARD_TYPES}")
        self.board_type = board_type
        self.size = size
        # hex-specific geometry (populated in reset())
        self._centers: dict = {}
        self._adjacency: dict = {}
        self._step: float = 1.0
        self.valid_cells: set = set()
        self.pegs: set = set()
        self.reset()

    # ── setup ──────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Rebuild board and place all pegs except the centre."""
        size = self.size

        if self.board_type == "English":
            self.valid_cells = Board.english(size)
            center = (size // 2, size // 2)
        elif self.board_type == "Diamond":
            self.valid_cells = Board.diamond(size)
            center = (size // 2, size // 2)
        else:  # Hexagon
            self.valid_cells = Board.hexagon(size)
            mid = size // 2
            row_len = size  # widest row
            center = (mid, row_len // 2)
            self._centers, _, _ = HexGrid.cell_centers(size)
            self._adjacency, self._step = HexGrid.build_adjacency(self._centers)

        self.pegs = set(self.valid_cells)
        self.pegs.discard(center)

    # ── move queries ────────────────────────────────────────────────────────

    def get_valid_moves(self) -> list:
        """Return list of (from_cell, mid_cell, to_cell) for all legal moves."""
        moves = []
        for cell in list(self.pegs):
            r, c = cell
            if self.board_type == "Hexagon":
                for mid, to in HexGrid.get_jumps(
                        cell, self._adjacency, self._centers, self._step):
                    if (mid in self.pegs
                            and to in self.valid_cells
                            and to not in self.pegs):
                        moves.append((cell, mid, to))
            else:
                for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                    mid = (r + dr // 2, c + dc // 2)
                    to = (r + dr, c + dc)
                    if (mid in self.valid_cells
                            and to in self.valid_cells
                            and mid in self.pegs
                            and to not in self.pegs):
                        moves.append((cell, mid, to))
        return moves

    def is_valid_move(self, from_cell: tuple, to_cell: tuple) -> bool:
        """Return True if moving from_cell to to_cell is a legal jump."""
        return any(
            fr == from_cell and to == to_cell
            for fr, _, to in self.get_valid_moves()
        )

    def make_move(self, from_cell: tuple, to_cell: tuple) -> bool:
        """
        Attempt to move the peg at from_cell to to_cell.
        Returns True and mutates state on success; returns False otherwise.
        """
        if self.board_type == "Hexagon":
            for mid, to in HexGrid.get_jumps(
                    from_cell, self._adjacency, self._centers, self._step):
                if (to == to_cell
                        and mid in self.pegs
                        and to in self.valid_cells
                        and to not in self.pegs):
                    self.pegs.discard(from_cell)
                    self.pegs.discard(mid)
                    self.pegs.add(to)
                    return True
            return False
        else:
            fr, fc = from_cell
            tr, tc = to_cell
            mid = ((fr + tr) // 2, (fc + tc) // 2)
            if (from_cell in self.pegs
                    and to_cell in self.valid_cells
                    and to_cell not in self.pegs
                    and mid in self.pegs
                    and abs(fr - tr) + abs(fc - tc) == 2
                    and (fr == tr or fc == tc)):
                self.pegs.discard(from_cell)
                self.pegs.discard(mid)
                self.pegs.add(to_cell)
                return True
            return False

    # ── end-of-game detection ───────────────────────────────────────────────

    def is_game_over(self) -> bool:
        """True when no legal moves remain (loss or win)."""
        return len(self.get_valid_moves()) == 0

    def is_win(self) -> bool:
        """True when exactly one peg remains."""
        return len(self.pegs) == 1

    # ── helpers ─────────────────────────────────────────────────────────────

    def peg_count(self) -> int:
        return len(self.pegs)

    def cell_count(self) -> int:
        return len(self.valid_cells)

    def __repr__(self) -> str:
        return (f"SolitaireGame(type={self.board_type!r}, size={self.size}, "
                f"pegs={self.peg_count()})")
