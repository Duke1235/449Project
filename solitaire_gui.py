"""
solitaire_gui.py
================
Tkinter GUI for Peg Solitaire — Sprint 3.
All game logic is delegated to ManualGame / AutomatedGame (game_logic.py).
This module contains ONLY presentation / interaction code.

Classes
-------
SolitaireApp  – main Tk window; owns the canvas, controls, event loop
"""

import tkinter as tk
from tkinter import messagebox
import math

from game_logic import Board, HexGrid, SolitaireGame, ManualGame, AutomatedGame


# ──────────────────────────────────────────────────────────────────────────────
# Drawing helpers
# ──────────────────────────────────────────────────────────────────────────────

def pointy_hex_polygon(cx: float, cy: float, R: float, gap: float = 1.2) -> list:
    """Return flat list of (x,y,...) for a pointy-top hexagon centred at (cx,cy)."""
    r = R - gap
    pts = []
    for i in range(6):
        angle = math.radians(60 * i + 30)
        pts += [cx + r * math.cos(angle), cy + r * math.sin(angle)]
    return pts


# ──────────────────────────────────────────────────────────────────────────────
# Colour palette
# ──────────────────────────────────────────────────────────────────────────────

C_BG        = "#1a1a2e"
C_BOARD     = "#0f1923"
C_PANEL     = "#16213e"
C_TEXT      = "#ecf0f1"
C_OUTLINE   = "#3d2b2b"
C_PEG_SHELL = "#7b2020"
C_PEG_BODY  = "#c0392b"
C_PEG_IN    = "#e8786a"
C_SEL_SHELL = "#7a5c00"
C_SEL_BODY  = "#c87f00"
C_SEL_IN    = "#ffd080"
C_VALID_SH  = "#1a4a2a"
C_VALID_BD  = "#27ae60"
C_VALID_IN  = "#82e0aa"
C_EMPTY_SH  = "#1a1a2e"
C_HOLE      = "#1f2d3d"
C_AUTO_BODY = "#2980b9"   # blue highlight for auto-played peg

HEX_R   = 21
CELL_SQ = 52

AUTOPLAY_DELAY_MS = 400   # milliseconds between auto-steps


# ──────────────────────────────────────────────────────────────────────────────
# Main application window
# ──────────────────────────────────────────────────────────────────────────────

class SolitaireApp(tk.Tk):
    """
    Top-level window.

    Responsibilities
    ----------------
    * Render the board on a Canvas.
    * Translate user clicks into ManualGame calls.
    * Drive AutomatedGame step-by-step with after() scheduling.
    * Display game status (peg count, messages, win/loss popups).
    """

    def __init__(self):
        super().__init__()
        self.title("Peg Solitaire — CS449")
        self.resizable(False, False)
        self.configure(bg=C_BG)

        # Control variables (bound to Tkinter widgets)
        self.board_type_var = tk.StringVar(value="Hexagon")
        self.game_mode_var  = tk.StringVar(value="Manual")
        self.size_var       = tk.IntVar(value=9)

        # Game state
        self.game: SolitaireGame = None
        self.selected: tuple     = None
        self.valid_targets: list = []
        self._auto_job           = None   # tk after() handle

        # Geometry cache
        self.display_centers: dict = {}

        self._build_ui()
        self._new_game()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        panel = tk.Frame(self, bg=C_PANEL, padx=14, pady=14)
        panel.grid(row=0, column=0, sticky="ns", padx=(12, 0), pady=12)

        # ── Board Type ────────────────────────────────────────────────────────
        tk.Label(panel, text="Board Type", bg=C_PANEL, fg=C_TEXT,
                 font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(0, 6))
        for bt in SolitaireGame.BOARD_TYPES:
            tk.Radiobutton(
                panel, text=bt, variable=self.board_type_var, value=bt,
                bg=C_PANEL, fg=C_TEXT, selectcolor=C_BG,
                activebackground=C_PANEL, activeforeground=C_VALID_BD,
                font=("Helvetica", 11)
            ).pack(anchor="w")

        # ── Game Mode ─────────────────────────────────────────────────────────
        tk.Label(panel, text="Game Mode", bg=C_PANEL, fg=C_TEXT,
                 font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(14, 6))
        for mode in ("Manual", "Automated"):
            tk.Radiobutton(
                panel, text=mode, variable=self.game_mode_var, value=mode,
                bg=C_PANEL, fg=C_TEXT, selectcolor=C_BG,
                activebackground=C_PANEL, activeforeground=C_VALID_BD,
                font=("Helvetica", 11)
            ).pack(anchor="w")

        # ── Board Size ────────────────────────────────────────────────────────
        tk.Label(panel, text="Board Size", bg=C_PANEL, fg=C_TEXT,
                 font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(14, 4))
        sf = tk.Frame(panel, bg=C_PANEL)
        sf.pack(anchor="w")
        tk.Button(sf, text="−", command=self._dec_size, width=2,
                  bg="#2c3e50", fg=C_TEXT, relief="flat",
                  font=("Helvetica", 12, "bold")).pack(side="left")
        tk.Label(sf, textvariable=self.size_var, width=3,
                 bg=C_PANEL, fg=C_VALID_BD,
                 font=("Helvetica", 13, "bold")).pack(side="left")
        tk.Button(sf, text="+", command=self._inc_size, width=2,
                  bg="#2c3e50", fg=C_TEXT, relief="flat",
                  font=("Helvetica", 12, "bold")).pack(side="left")

        # ── Action buttons ────────────────────────────────────────────────────
        tk.Button(
            panel, text="New Game", command=self._new_game,
            bg=C_PEG_BODY, fg="white", relief="flat",
            padx=10, pady=6, font=("Helvetica", 12, "bold"), cursor="hand2"
        ).pack(pady=(20, 4), fill="x")

        self.rand_btn = tk.Button(
            panel, text="Randomize", command=self._randomize,
            bg="#8e44ad", fg="white", relief="flat",
            padx=10, pady=6, font=("Helvetica", 12, "bold"), cursor="hand2"
        )
        self.rand_btn.pack(pady=(4, 4), fill="x")

        self.auto_btn = tk.Button(
            panel, text="▶ Autoplay", command=self._toggle_autoplay,
            bg=C_AUTO_BODY, fg="white", relief="flat",
            padx=10, pady=6, font=("Helvetica", 12, "bold"), cursor="hand2"
        )
        self.auto_btn.pack(pady=(4, 4), fill="x")

        # ── Status ────────────────────────────────────────────────────────────
        self.peg_lbl = tk.Label(panel, text="Pegs: 0", bg=C_PANEL, fg=C_TEXT,
                                font=("Helvetica", 11))
        self.peg_lbl.pack(pady=(14, 0))

        self.status_lbl = tk.Label(
            panel, text="", bg=C_PANEL, fg=C_VALID_BD,
            font=("Helvetica", 10), wraplength=130, justify="center"
        )
        self.status_lbl.pack(pady=(6, 0))

        # ── Canvas ────────────────────────────────────────────────────────────
        self.canvas_frame = tk.Frame(self, bg=C_BG)
        self.canvas_frame.grid(row=0, column=1, padx=12, pady=12)
        self.canvas = tk.Canvas(self.canvas_frame, bg=C_BOARD, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)

    # ── Size controls ─────────────────────────────────────────────────────────

    def _dec_size(self) -> None:
        v = self.size_var.get()
        if v > 5:
            self.size_var.set(v - 2)

    def _inc_size(self) -> None:
        v = self.size_var.get()
        if v < 13:
            self.size_var.set(v + 2)

    # ── Game lifecycle ────────────────────────────────────────────────────────

    def _new_game(self) -> None:
        """Create a fresh game with the chosen settings and redraw."""
        self._stop_autoplay()

        bt   = self.board_type_var.get()
        mode = self.game_mode_var.get()
        size = self.size_var.get()

        # English / Diamond require odd size
        if bt != "Hexagon" and size % 2 == 0:
            size += 1
            self.size_var.set(size)

        if mode == "Manual":
            self.game = ManualGame(bt, size)
            self.rand_btn.config(state="normal")
            self.auto_btn.config(text="▶ Autoplay", state="normal")
            self.canvas.bind("<Button-1>", self._on_click)
        else:  # Automated
            self.game = AutomatedGame(bt, size)
            self.rand_btn.config(state="disabled")
            self.auto_btn.config(text="▶ Start", state="normal")
            self.canvas.unbind("<Button-1>")

        self.selected      = None
        self.valid_targets = []

        self._build_display()
        self._draw()
        self.status_lbl.config(
            text="Select a peg to begin." if mode == "Manual"
            else "Press ▶ Start to autoplay."
        )

    def _build_display(self) -> None:
        """Pre-compute pixel centres for every cell and resize the canvas."""
        game = self.game
        if game.board_type == "Hexagon":
            centers, cw, ch = HexGrid.cell_centers(game.size, pad_x=44, pad_y=44)
            self.display_centers = centers
            self.canvas.config(width=int(cw), height=int(ch + 44))
        else:
            C, pad = CELL_SQ, 30
            self.canvas.config(
                width=game.size * C + pad * 2,
                height=game.size * C + pad * 2
            )
            self.display_centers = {
                (r, c): (pad + c * C + C // 2, pad + r * C + C // 2)
                for (r, c) in game.valid_cells
            }

    # ── Randomize ─────────────────────────────────────────────────────────────

    def _randomize(self) -> None:
        """Randomize board state (manual mode only)."""
        if not isinstance(self.game, ManualGame):
            return
        self._stop_autoplay()
        self.selected      = None
        self.valid_targets = []
        n = self.game.randomize_board(num_moves=12)
        self._draw()
        self.status_lbl.config(text=f"Randomized ({n} moves applied).")
        self._check_end_of_game()

    # ── Autoplay ──────────────────────────────────────────────────────────────

    def _toggle_autoplay(self) -> None:
        """Start or stop the autoplay loop (works for both game modes)."""
        if self._auto_job is not None:
            self._stop_autoplay()
            return

        if isinstance(self.game, AutomatedGame):
            self._auto_btn_running()
            self._auto_step_loop()
        else:
            # Manual mode: temporarily run the heuristic on the ManualGame
            self._auto_btn_running()
            self._auto_step_manual_loop()

    def _auto_btn_running(self) -> None:
        self.auto_btn.config(text="⏹ Stop")

    def _stop_autoplay(self) -> None:
        if self._auto_job is not None:
            self.after_cancel(self._auto_job)
            self._auto_job = None
        self.auto_btn.config(
            text="▶ Autoplay" if isinstance(self.game, ManualGame) else "▶ Start"
        )

    def _auto_step_loop(self) -> None:
        """Step loop for AutomatedGame."""
        if self.game.is_game_over():
            self._stop_autoplay()
            self._check_end_of_game()
            return
        ok = self.game.auto_step()
        self._draw()
        if ok and not self.game.is_game_over():
            self._auto_job = self.after(AUTOPLAY_DELAY_MS, self._auto_step_loop)
        else:
            self._stop_autoplay()
            self._check_end_of_game()

    def _auto_step_manual_loop(self) -> None:
        """Step loop for a ManualGame running in autoplay mode."""
        if self.game.is_game_over():
            self._stop_autoplay()
            self._check_end_of_game()
            return
        moves = self.game.get_valid_moves()
        if not moves:
            self._stop_autoplay()
            self._check_end_of_game()
            return
        import random
        fr, _, to = random.choice(moves)
        self.game.make_move(fr, to)
        self._draw()
        if not self.game.is_game_over():
            self._auto_job = self.after(AUTOPLAY_DELAY_MS, self._auto_step_manual_loop)
        else:
            self._stop_autoplay()
            self._check_end_of_game()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw(self) -> None:
        """Redraw the entire board."""
        self.canvas.delete("all")
        target_set = set(self.valid_targets)
        last_to = None
        if isinstance(self.game, AutomatedGame) and self.game.last_move:
            last_to = self.game.last_move[1]

        for cell, (cx, cy) in self.display_centers.items():
            if cell not in self.game.valid_cells:
                continue
            has_peg   = cell in self.game.pegs
            is_sel    = cell == self.selected
            is_target = cell in target_set
            is_last   = cell == last_to

            if self.game.board_type == "Hexagon":
                self._draw_hex_cell(cx, cy, has_peg, is_sel, is_target, is_last)
            else:
                self._draw_square_cell(cx, cy, has_peg, is_sel, is_target, is_last)

        self.peg_lbl.config(text=f"Pegs: {self.game.peg_count()}")

    def _draw_hex_cell(self, cx, cy, has_peg, is_sel, is_target, is_last=False) -> None:
        R = HEX_R
        outer = pointy_hex_polygon(cx, cy, R, gap=1.2)
        if has_peg:
            if is_last:
                shell, body, dot = "#0a3a5c", C_AUTO_BODY, "#7ec8e3"
            elif is_sel:
                shell, body, dot = C_SEL_SHELL, C_SEL_BODY, C_SEL_IN
            else:
                shell, body, dot = C_PEG_SHELL, C_PEG_BODY, C_PEG_IN
            self.canvas.create_polygon(outer, fill=shell, outline="")
            inner = pointy_hex_polygon(cx, cy, R - 4, gap=0)
            self.canvas.create_polygon(inner, fill=body, outline="")
            dr = R - 11
            self.canvas.create_oval(cx-dr, cy-dr, cx+dr, cy+dr, fill=dot, outline="")
        elif is_target:
            self.canvas.create_polygon(outer, fill=C_VALID_SH, outline="")
            inner = pointy_hex_polygon(cx, cy, R - 4, gap=0)
            self.canvas.create_polygon(inner, fill=C_VALID_BD, outline="")
            dr = R - 11
            self.canvas.create_oval(cx-dr, cy-dr, cx+dr, cy+dr, fill=C_VALID_IN, outline="")
        else:
            self.canvas.create_polygon(outer, fill=C_EMPTY_SH, outline="")
            self.canvas.create_oval(cx-5, cy-5, cx+5, cy+5, fill=C_HOLE, outline="")

    def _draw_square_cell(self, cx, cy, has_peg, is_sel, is_target, is_last=False) -> None:
        R = 16
        if has_peg:
            if is_last:
                col = C_AUTO_BODY
            elif is_sel:
                col = C_SEL_BODY
            else:
                col = C_PEG_BODY
            self.canvas.create_oval(cx-R, cy-R, cx+R, cy+R, fill=col, outline="")
        elif is_target:
            self.canvas.create_oval(cx-R, cy-R, cx+R, cy+R, fill=C_VALID_BD, outline="")
        else:
            self.canvas.create_oval(cx-6, cy-6, cx+6, cy+6, fill=C_HOLE, outline="")

    # ── Click handling ────────────────────────────────────────────────────────

    def _find_cell_at(self, x: int, y: int):
        best, best_d = None, float('inf')
        for cell, (cx, cy) in self.display_centers.items():
            d = math.hypot(x - cx, y - cy)
            if d < best_d:
                best_d, best = d, cell
        return best if best_d <= HEX_R else None

    def _on_click(self, event) -> None:
        if isinstance(self.game, AutomatedGame):
            return
        cell = self._find_cell_at(event.x, event.y)
        if cell is None or cell not in self.game.valid_cells:
            return
        if self.selected is None:
            self._handle_select(cell)
        else:
            self._handle_action(cell)

    def _handle_select(self, cell: tuple) -> None:
        if cell not in self.game.pegs:
            return
        targets = [to for (fr, _, to) in self.game.get_valid_moves() if fr == cell]
        if not targets:
            self.status_lbl.config(text="No valid moves here.")
            return
        self.selected      = cell
        self.valid_targets = targets
        self.status_lbl.config(text="Click a highlighted destination.")
        self._draw()

    def _handle_action(self, cell: tuple) -> None:
        if cell == self.selected:
            self.selected = None
            self.valid_targets = []
            self._draw()
            return
        if cell in self.game.pegs:
            self.selected = None
            self.valid_targets = []
            self._handle_select(cell)
            return
        ok = self.game.make_move(self.selected, cell)
        self.selected = None
        self.valid_targets = []
        self.status_lbl.config(text="" if ok else "Invalid move — try again.")
        self._draw()
        if ok:
            self._check_end_of_game()

    def _check_end_of_game(self) -> None:
        if self.game.is_win():
            messagebox.showinfo(
                "🎉 You Win!",
                f"Incredible! Only 1 peg left!\n"
                f"Board: {self.game.board_type}, Size: {self.game.size}"
            )
            self.status_lbl.config(text="🎉 You Win!")
        elif self.game.is_game_over():
            mode = "Automated" if isinstance(self.game, AutomatedGame) else "Manual"
            messagebox.showinfo(
                "Game Over",
                f"No moves remaining.\n"
                f"Mode: {mode}\n"
                f"Pegs left: {self.game.peg_count()}\n"
                f"Press 'New Game' to try again."
            )
            self.status_lbl.config(text="Game Over!")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = SolitaireApp()
    app.mainloop()