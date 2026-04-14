"""
game_logic.py
=============
Pure game-logic layer for Peg Solitaire.
No GUI / tkinter imports here — fully unit-testable in isolation.

Class hierarchy (Sprint 3)
--------------------------
SolitaireGame  – abstract base: board setup, move validation, win/loss detection
  ManualGame   – human-driven play; adds randomize_board()
  AutomatedGame – solver-driven play; adds auto_step() and solve()

Supporting classes
------------------
Board    – static factories that return valid-cell sets
HexGrid  – pixel geometry and adjacency for the hexagonal board
"""

import math
import random
import json
import os
from datetime import datetime

# Recordings folder is always placed next to game_logic.py, regardless of
# the working directory the user launches the script from.
_HERE = os.path.dirname(os.path.abspath(__file__))


# ──────────────────────────────────────────────────────────────────────────────
# Board shape factories
# ──────────────────────────────────────────────────────────────────────────────

class Board:
    """Static factory methods that return a set of valid (row, col) cells."""

    @staticmethod
    def english(size: int = 7) -> set:
        """Cross-shaped English board.  size must be odd."""
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
        Row lengths for size=9: 5,6,7,8,9,8,7,6,5.
        General: row r has (size - |r - mid|) cells.
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
    Pixel centres for a pointy-top hexagonal grid and adjacency lists
    used for move detection.
    """

    HEX_R = 21  # circumradius in pixels

    @classmethod
    def cell_centers(cls, size: int, pad_x: int = 44, pad_y: int = 44) -> tuple:
        """
        Returns (centers_dict, canvas_width, canvas_height).
        centers_dict maps (row, col) -> (cx, cy).
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
        """
        cells = list(centers.keys())
        if len(cells) < 2:
            return {c: [] for c in cells}, 1.0

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
# Game Recorder / Replayer
# ──────────────────────────────────────────────────────────────────────────────

class GameRecorder:
    """
    Records a Peg Solitaire game session to a JSON file and replays it.

    File format (JSON)
    ------------------
    {
      "metadata": {
        "board_type": "English",
        "size": 7,
        "mode": "Manual",          # "Manual" or "Automated"
        "recorded_at": "<ISO timestamp>"
      },
      "events": [
        {"type": "move",       "from": [r, c], "to": [r2, c2]},
        {"type": "randomize",  "pegs": [[r, c], ...]},   # snapshot after randomize
        {"type": "autoplay_start"},
        {"type": "autoplay_stop"}
      ]
    }
    """

    RECORDS_DIR = os.path.join(_HERE, "recordings")

    # ── recording ─────────────────────────────────────────────────────────────

    def __init__(self, board_type: str, size: int, mode: str):
        self.board_type = board_type
        self.size = size
        self.mode = mode
        self.events: list = []
        self._active = False

    def start(self) -> None:
        """Begin accumulating events."""
        self.events.clear()
        self._active = True

    def stop(self) -> None:
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def record_move(self, from_cell: tuple, to_cell: tuple) -> None:
        if not self._active:
            return
        self.events.append({
            "type": "move",
            "from": list(from_cell),
            "to":   list(to_cell)
        })

    def record_randomize(self, pegs: set) -> None:
        """Snapshot the full peg set after a randomize so replay is deterministic."""
        if not self._active:
            return
        self.events.append({
            "type": "randomize",
            "pegs": [list(p) for p in sorted(pegs)]
        })

    def record_autoplay_start(self) -> None:
        if self._active:
            self.events.append({"type": "autoplay_start"})

    def record_autoplay_stop(self) -> None:
        if self._active:
            self.events.append({"type": "autoplay_stop"})

    def save(self, filepath: str = None) -> str:
        """
        Write the recorded game to *filepath* (or auto-generate a name).
        Returns the path actually written.
        """
        if filepath is None:
            os.makedirs(self.RECORDS_DIR, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(
                self.RECORDS_DIR,
                f"game_{self.board_type}_{self.size}_{ts}.json"
            )
        payload = {
            "metadata": {
                "board_type":   self.board_type,
                "size":         self.size,
                "mode":         self.mode,
                "recorded_at":  datetime.now().isoformat(timespec="seconds")
            },
            "events": self.events
        }
        with open(filepath, "w") as fh:
            json.dump(payload, fh, indent=2)
        return filepath

    # ── replaying ─────────────────────────────────────────────────────────────

    @staticmethod
    def load(filepath: str) -> dict:
        """Load and return the raw JSON dict from a recording file."""
        with open(filepath, "r") as fh:
            return json.load(fh)

    @staticmethod
    def build_replay_game(recording: dict):
        """
        Construct a fresh game object matching the recording's metadata.
        Returns (game, events_list).
        """
        meta = recording["metadata"]
        board_type = meta["board_type"]
        size       = meta["size"]
        mode       = meta["mode"]

        if mode == "Automated":
            game = AutomatedGame(board_type, size)
        else:
            game = ManualGame(board_type, size)

        return game, recording["events"]


# ──────────────────────────────────────────────────────────────────────────────
# Base game class
# ──────────────────────────────────────────────────────────────────────────────

class SolitaireGame:
    """
    Abstract base class owning all board state.

    Common behaviour (shared by ManualGame and AutomatedGame)
    ---------------------------------------------------------
    * Building the board shape (English / Hexagon / Diamond)
    * Placing pegs at the start (all cells except centre)
    * Validating and executing individual moves
    * Detecting game-over and win conditions

    Subclasses add mode-specific behaviour without duplicating this logic.
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
            row_len = size          # widest row length
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
                    to  = (r + dr, c + dc)
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
        Returns True and mutates state on success; False otherwise.
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
        return (f"{self.__class__.__name__}(type={self.board_type!r}, "
                f"size={self.size}, pegs={self.peg_count()})")


# ──────────────────────────────────────────────────────────────────────────────
# ManualGame  (Sprint 3 subclass)
# ──────────────────────────────────────────────────────────────────────────────

class ManualGame(SolitaireGame):
    """
    Human-controlled game mode.

    Extends SolitaireGame with:
    * randomize_board() – scramble current peg positions into a reachable-
                          looking random state while keeping the game playable.
    * move_history     – ordered list of moves made this session.

    Everything else (board setup, move execution, win detection) is inherited
    unchanged from SolitaireGame, avoiding any code duplication.
    """

    def __init__(self, board_type: str = "Hexagon", size: int = 9):
        super().__init__(board_type, size)
        self.move_history: list = []   # list of (from_cell, to_cell) tuples
        self.recorder = None           # optional GameRecorder

    def reset(self) -> None:
        """Reset board state and clear move history."""
        super().reset()
        if hasattr(self, "move_history"):
            self.move_history.clear()

    def make_move(self, from_cell: tuple, to_cell: tuple) -> bool:
        """Execute a move, record it in move_history, and notify recorder."""
        ok = super().make_move(from_cell, to_cell)
        if ok:
            self.move_history.append((from_cell, to_cell))
            if self.recorder and self.recorder.is_active:
                self.recorder.record_move(from_cell, to_cell)
        return ok

    def randomize_board(self, num_moves: int = 10) -> int:
        """
        Randomize board state by executing up to num_moves random legal moves.

        Returns the number of moves actually executed.
        Does NOT record moves in move_history. Instead sends a full peg-set
        snapshot to the recorder so replay is deterministic.
        """
        executed = 0
        for _ in range(num_moves):
            moves = self.get_valid_moves()
            if not moves:
                break
            fr, _, to = random.choice(moves)
            super().make_move(fr, to)
            executed += 1
        if self.recorder and self.recorder.is_active:
            self.recorder.record_randomize(self.pegs)
        return executed


# ──────────────────────────────────────────────────────────────────────────────
# AutomatedGame  (Sprint 3 subclass)
# ──────────────────────────────────────────────────────────────────────────────

class AutomatedGame(SolitaireGame):
    """
    Solver-driven game mode.

    Extends SolitaireGame with:
    * auto_step()  – execute one move chosen by the heuristic solver.
    * solve()      – play the game to completion and return the move list.
    * last_move    – the most recent (from_cell, to_cell) chosen by the solver.

    The heuristic: prefer moves whose landing cell is closer to the board
    centre, breaking ties randomly.  This produces visually coherent play
    without requiring expensive backtracking.
    """

    def __init__(self, board_type: str = "Hexagon", size: int = 9):
        super().__init__(board_type, size)
        self.last_move = None          # (from_cell, to_cell) or None
        self.recorder = None           # optional GameRecorder

    def reset(self) -> None:
        super().reset()
        if hasattr(self, "last_move"):
            self.last_move = None

    def _heuristic_move(self) -> tuple | None:
        """
        Select the best move according to the centre-proximity heuristic.
        Returns (from_cell, to_cell) or None if no moves exist.
        """
        moves = self.get_valid_moves()
        if not moves:
            return None

        mid = self.size / 2
        if self.board_type == "Hexagon":
            # Use pixel centre distance for hex boards
            cx_mid = (self.size / 2) * math.sqrt(3) * HexGrid.HEX_R
            cy_mid = mid * 1.5 * HexGrid.HEX_R

            def score(move):
                _, _, to = move
                if to in self._centers:
                    tx, ty = self._centers[to]
                    return math.hypot(tx - cx_mid, ty - cy_mid)
                return float('inf')
        else:
            def score(move):
                _, _, to = move
                tr, tc = to
                return math.hypot(tr - mid, tc - mid)

        best_score = min(score(m) for m in moves)
        best_moves = [m for m in moves if abs(score(m) - best_score) < 0.01]
        return random.choice(best_moves)

    def auto_step(self) -> bool:
        """
        Execute one heuristic-chosen move.
        Returns True if a move was made; False if no moves are available.
        """
        move = self._heuristic_move()
        if move is None:
            return False
        fr, _, to = move
        ok = self.make_move(fr, to)
        if ok:
            self.last_move = (fr, to)
            if self.recorder and self.recorder.is_active:
                self.recorder.record_move(fr, to)
        return ok

    def solve(self) -> list:
        """
        Play until no moves remain.
        Returns list of (from_cell, to_cell) tuples representing every move.
        """
        self.reset()
        moves_made = []
        while True:
            move = self._heuristic_move()
            if move is None:
                break
            fr, _, to = move
            if self.make_move(fr, to):
                moves_made.append((fr, to))
                self.last_move = (fr, to)
        return moves_made