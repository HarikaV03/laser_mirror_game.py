"""
Course:      CMPS 5113 - Advanced Programming Language Concepts
Assignment:  Program 3 - Open-Ended OOP GUI Program (Laser & Mirror Logic)
Author:      Harika Vemulapalli
Date:        November 2026
Description: A visual grid-based logic and deduction game built with Python
             tkinter Canvas. Players fire laser probes around a 5x5 optics board
             to deduce hidden mirrors/blockers and route a glowing laser beam
             into the target receiver.
"""

import random
import tkinter as tk
from tkinter import messagebox


class GridBoard:
    """Represents a 5x5 optics grid with hidden puzzle elements and player mirrors."""

    SIZE: int = 5

    # Directions: 0=Up, 1=Right, 2=Down, 3=Left
    DR: list[int] = [-1, 0, 1, 0]
    DC: list[int] = [0, 1, 0, -1]

    def __init__(self) -> None:
        self.solution: list[list[str]] = [["." for _ in range(self.SIZE)] for _ in range(self.SIZE)]
        self.player_grid: list[list[str]] = [["." for _ in range(self.SIZE)] for _ in range(self.SIZE)]
        self.target_exit: tuple[int, int, int] = (0, 2, 0)  # (row, col, exit_dir)
        self.generate_puzzle()

    def generate_puzzle(self) -> None:
        """Creates a solvable 5x5 mirror-deduction layout with a target receiver."""
        self.solution = [["." for _ in range(self.SIZE)] for _ in range(self.SIZE)]
        self.player_grid = [["." for _ in range(self.SIZE)] for _ in range(self.SIZE)]

        # Place 3 hidden mirrors ('/' or '\') and 1 blocker ('#'), avoiding emitter cell (4, 2)
        positions = [
            (r, c)
            for r in range(self.SIZE)
            for c in range(self.SIZE)
            if not (r == self.SIZE - 1 and c == 2)
        ]
        chosen = random.sample(positions, 4)

        self.solution[chosen[0][0]][chosen[0][1]] = "/"
        self.solution[chosen[1][0]][chosen[1][1]] = "\\"
        self.solution[chosen[2][0]][chosen[2][1]] = random.choice(["/", "\\"])
        self.solution[chosen[3][0]][chosen[3][1]] = "#"

        edge_targets = [
            (0, 1, 0),
            (0, 3, 0),
            (1, 4, 1),
            (2, 4, 1),
            (3, 0, 3),
            (1, 0, 3),
        ]
        self.target_exit = random.choice(edge_targets)

    @staticmethod
    def _reflect(direction: int, mirror: str) -> int:
        """Reflects beam direction (0=Up, 1=Right, 2=Down, 3=Left) off '/' or '\\'."""
        if mirror == "/":
            return {0: 1, 1: 0, 2: 3, 3: 2}[direction]
        if mirror == "\\":
            return {0: 3, 1: 2, 2: 1, 3: 0}[direction]
        return direction

    def trace_beam(
        self,
        use_player_grid: bool,
        start_r: int,
        start_c: int,
        start_dir: int,
    ) -> tuple[str, list[tuple[int, int]], tuple[int, int] | None]:
        """
        Traces a beam starting at (start_r, start_c) moving in start_dir.
        Returns (outcome_label, path_cells, blocker_cell_if_hit).
        """
        grid = self.player_grid if use_player_grid else self.solution
        r, c, direction = start_r, start_c, start_dir
        path: list[tuple[int, int]] = []
        visited_states: set[tuple[int, int, int]] = set()

        while 0 <= r < self.SIZE and 0 <= c < self.SIZE:
            state = (r, c, direction)
            if state in visited_states:
                return "LOOPED", path, None
            visited_states.add(state)
            path.append((r, c))

            cell = grid[r][c]
            if cell == "#":
                return "ABSORBED (Blocker)", path, (r, c)
            if cell in ("/", "\\"):
                direction = self._reflect(direction, cell)

            r += self.DR[direction]
            c += self.DC[direction]

        exit_r = max(0, min(self.SIZE - 1, r - self.DR[direction]))
        exit_c = max(0, min(self.SIZE - 1, c - self.DC[direction]))
        target_r, target_c, _ = self.target_exit
        if (exit_r, exit_c) == (target_r, target_c):
            return f"HIT TARGET ({exit_r + 1}, {exit_c + 1})", path, None
        return f"EXITED AT ({exit_r + 1}, {exit_c + 1})", path, None


class LaserPuzzleGame:
    """Manages puzzle state, probe count, win/loss tally, and laser trace data."""

    def __init__(self) -> None:
        self.board = GridBoard()
        self.selected_cell: tuple[int, int] = (2, 2)
        self.probes_fired: int = 0
        self.wins: int = 0
        self.losses: int = 0
        self.last_path: list[tuple[int, int]] = []
        self.blocker_hit: tuple[int, int] | None = None
        self.beam_color: str = "#38BDF8"
        self.status: str = (
            "Click a cell to place/rotate '/' or '\\' mirrors, or fire a Probe from an edge to deduce hidden optics."
        )

    def new_puzzle(self) -> None:
        self.board.generate_puzzle()
        self.selected_cell = (2, 2)
        self.probes_fired = 0
        self.last_path = []
        self.blocker_hit = None
        self.beam_color = "#38BDF8"
        self.status = "New 5x5 optics board ready! Deduce hidden mirrors and route the laser into the glowing TARGET."

    def select_and_cycle_mirror(self, r: int, c: int) -> None:
        """Selects (r, c) and cycles its mirror state: '.' -> '/' -> '\\' -> '.'."""
        self.selected_cell = (r, c)
        order = [".", "/", "\\"]
        current = self.board.player_grid[r][c]
        next_val = order[(order.index(current) + 1) % len(order)]
        self.board.player_grid[r][c] = next_val
        label = "Clear" if next_val == "." else f"Mirror '{next_val}'"
        self.status = f"Cell (Row {r + 1}, Col {c + 1}) -> {label}."

    def fire_probe(self, entry_side: str = "TOP", lane: int = 2) -> None:
        """Fires a test probe into the hidden board from a chosen edge and row/column."""
        self.probes_fired += 1
        lane = max(0, min(GridBoard.SIZE - 1, lane))

        if entry_side == "TOP":
            sr, sc, sdir = 0, lane, 2
        elif entry_side == "BOTTOM":
            sr, sc, sdir = GridBoard.SIZE - 1, lane, 0
        elif entry_side == "LEFT":
            sr, sc, sdir = lane, 0, 1
        else:  # RIGHT
            sr, sc, sdir = lane, GridBoard.SIZE - 1, 3

        outcome, path, blocker = self.board.trace_beam(False, sr, sc, sdir)
        self.last_path = path
        self.blocker_hit = blocker
        self.beam_color = "#F43F5E" if blocker else "#38BDF8"
        self.status = f"Probe #{self.probes_fired} ({entry_side} {lane + 1}) -> {outcome}."

    def check_solution(self) -> None:
        """Traces the player's mirror setup from Bottom-Center emitter (4, 2) upward."""
        outcome, path, blocker = self.board.trace_beam(True, GridBoard.SIZE - 1, 2, 0)
        self.last_path = path
        self.blocker_hit = blocker
        target_r, target_c, _ = self.board.target_exit

        hit_target = outcome.startswith("HIT TARGET")
        placed_any = any(
            self.board.player_grid[r][c] in ("/", "\\")
            for r in range(GridBoard.SIZE)
            for c in range(GridBoard.SIZE)
        )

        if hit_target and placed_any:
            self.wins += 1
            self.beam_color = "#22C55E"
            self.status = (
                f"TARGET LOCKED! Beam routed to ({target_r + 1}, {target_c + 1}) in {self.probes_fired} probe(s)!"
            )
        else:
            self.losses += 1
            self.beam_color = "#F59E0B"
            self.status = (
                f"Missed target ({outcome}). Target is ({target_r + 1}, {target_c + 1}). "
                "Fire more probes or adjust your mirrors."
            )


class LaserPuzzleGUI:
    """Visual Tkinter Canvas GUI for Laser & Mirror Logic."""

    CELL_SIZE: int = 84
    PAD: int = 24

    def __init__(self, root: tk.Tk, game: LaserPuzzleGame) -> None:
        self.root = root
        self.game = game

        self.root.title("Laser & Mirror Logic — CMPS 5113")
        self.root.geometry("680x690")
        self.root.minsize(620, 640)

        self._build_ui()
        self._refresh_ui()

    def _build_ui(self) -> None:
        top = tk.Frame(self.root, padx=14, pady=10)
        top.pack(fill=tk.X)

        tk.Label(top, text="LASER & MIRROR LOGIC", font=("Helvetica", 19, "bold"), anchor="w").pack(fill=tk.X)
        tk.Label(
            top,
            text=(
                "Deduction Goal: Fire probes around the board edges to deduce hidden mirrors/blockers, "
                "then click cells to place '/' or '\\' mirrors and guide the laser into the TARGET."
            ),
            font=("Helvetica", 10),
            fg="#334155",
            anchor="w",
            wraplength=640,
            justify="left",
        ).pack(fill=tk.X, pady=(3, 6))

        self.stats_lbl = tk.Label(top, text="", font=("Helvetica", 10, "bold"), fg="#0F766E", anchor="w")
        self.stats_lbl.pack(fill=tk.X)

        # Probe controls
        probe_bar = tk.Frame(self.root, padx=14, pady=4)
        probe_bar.pack(fill=tk.X)

        tk.Label(probe_bar, text="Probe Edge:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.side_var = tk.StringVar(value="TOP")
        tk.OptionMenu(probe_bar, self.side_var, "TOP", "BOTTOM", "LEFT", "RIGHT").pack(side=tk.LEFT, padx=6)

        tk.Label(probe_bar, text="Row/Col (1-5):", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.lane_var = tk.IntVar(value=2)
        tk.Spinbox(probe_bar, from_=1, to=5, width=4, textvariable=self.lane_var).pack(side=tk.LEFT, padx=6)

        tk.Button(
            probe_bar,
            text="Fire Probe",
            font=("Helvetica", 10, "bold"),
            command=self._on_fire_probe,
        ).pack(side=tk.LEFT, padx=8)

        # Visual Optics Canvas
        canvas_size = self.PAD * 2 + self.CELL_SIZE * GridBoard.SIZE
        self.canvas = tk.Canvas(
            self.root,
            width=canvas_size,
            height=canvas_size,
            bg="#0B1120",
            highlightthickness=2,
            highlightbackground="#1E293B",
        )
        self.canvas.pack(padx=14, pady=8)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        self.status_lbl = tk.Label(
            self.root,
            text="",
            font=("Helvetica", 10, "bold"),
            fg="#0F172A",
            wraplength=640,
            justify="center",
            pady=4,
        )
        self.status_lbl.pack(fill=tk.X, padx=14)

        # Action Buttons (5 working buttons)
        bottom = tk.Frame(self.root, padx=14, pady=12)
        bottom.pack(fill=tk.X)

        tk.Button(
            bottom,
            text="Place / Rotate Mirror",
            font=("Helvetica", 10, "bold"),
            command=self._on_cycle_mirror,
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            bottom,
            text="Check Solution",
            font=("Helvetica", 10, "bold"),
            command=self._on_check,
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            bottom,
            text="New Puzzle",
            font=("Helvetica", 10, "bold"),
            command=self._on_new_puzzle,
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(bottom, text="Credits", font=("Helvetica", 10), command=self._show_credits).pack(side=tk.RIGHT)
        tk.Button(bottom, text="Help", font=("Helvetica", 10), command=self._show_help).pack(
            side=tk.RIGHT, padx=(0, 6)
        )

    def _cell_center(self, r: int, c: int) -> tuple[float, float]:
        x = self.PAD + c * self.CELL_SIZE + self.CELL_SIZE / 2
        y = self.PAD + r * self.CELL_SIZE + self.CELL_SIZE / 2
        return x, y

    def _on_canvas_click(self, event: tk.Event) -> None:
        c = int((event.x - self.PAD) // self.CELL_SIZE)
        r = int((event.y - self.PAD) // self.CELL_SIZE)
        if 0 <= r < GridBoard.SIZE and 0 <= c < GridBoard.SIZE:
            self.game.select_and_cycle_mirror(r, c)
            self._refresh_ui()

    def _on_cycle_mirror(self) -> None:
        r, c = self.game.selected_cell
        self.game.select_and_cycle_mirror(r, c)
        self._refresh_ui()

    def _on_fire_probe(self) -> None:
        lane_idx = int(self.lane_var.get()) - 1
        self.game.fire_probe(self.side_var.get(), lane_idx)
        self._refresh_ui()

    def _on_check(self) -> None:
        self.game.check_solution()
        self._refresh_ui()

    def _on_new_puzzle(self) -> None:
        self.game.new_puzzle()
        self._refresh_ui()

    def _show_help(self) -> None:
        msg = (
            "How to Play Laser & Mirror Logic:\n\n"
            "1. Pick an edge (TOP, BOTTOM, LEFT, RIGHT) and row/col (1-5), then click 'Fire Probe' "
            "to trace how a laser beam behaves.\n"
            "2. Click directly on any grid cell (or use 'Place / Rotate Mirror') to place '/' or '\\' mirrors.\n"
            "3. Click 'Check Solution' to fire from the bottom emitter (Col 3) into the glowing TARGET."
        )
        messagebox.showinfo("Help — Laser & Mirror Logic", msg)

    def _show_credits(self) -> None:
        msg = (
            "CMPS 5113 — Program 3 (Open-Ended OOP GUI)\n\n"
            "Game: Laser & Mirror Logic\n"
            "Author: Harika Vemulapalli"
        )
        messagebox.showinfo("Credits", msg)

    def _draw_mirror(self, r: int, c: int, mirror_type: str) -> None:
        cx, cy = self._cell_center(r, c)
        half = self.CELL_SIZE * 0.34

        if mirror_type == "/":
            x1, y1, x2, y2 = cx - half, cy + half, cx + half, cy - half
            bx1, by1, bx2, by2 = x1 + 3, y1 + 3, x2 + 3, y2 + 3
        else:  # '\'
            x1, y1, x2, y2 = cx - half, cy - half, cx + half, cy + half
            bx1, by1, bx2, by2 = x1 - 3, y1 + 3, x2 - 3, y2 + 3

        # Dark backing + bright reflective glass surface
        self.canvas.create_line(bx1, by1, bx2, by2, fill="#475569", width=6, capstyle=tk.ROUND)
        self.canvas.create_line(x1, y1, x2, y2, fill="#E2E8F0", width=5, capstyle=tk.ROUND)
        self.canvas.create_line(x1, y1, x2, y2, fill="#BAE6FD", width=2, capstyle=tk.ROUND)

    def _draw_laser_beam(self) -> None:
        if not self.game.last_path:
            return

        points: list[float] = []
        for r, c in self.game.last_path:
            cx, cy = self._cell_center(r, c)
            points.extend([cx, cy])

        if len(points) >= 4:
            # Outer glow + inner high-intensity laser core
            self.canvas.create_line(
                points,
                fill=self.game.beam_color,
                width=10,
                smooth=False,
                joinstyle=tk.ROUND,
                capstyle=tk.ROUND,
            )
            self.canvas.create_line(
                points,
                fill="#FFFFFF",
                width=3,
                smooth=False,
                joinstyle=tk.ROUND,
                capstyle=tk.ROUND,
            )

        # Mark start and end of beam
        sx, sy = points[0], points[1]
        ex, ey = points[-2], points[-1]
        self.canvas.create_oval(sx - 6, sy - 6, sx + 6, sy + 6, fill="#FACC15", outline="#FFFFFF", width=2)
        self.canvas.create_oval(ex - 6, ey - 6, ex + 6, ey + 6, fill=self.game.beam_color, outline="#FFFFFF", width=2)

    def _refresh_ui(self) -> None:
        self.stats_lbl.config(
            text=f"Probes Fired: {self.game.probes_fired}   |   Wins: {self.game.wins}   |   Losses: {self.game.losses}"
        )
        self.status_lbl.config(text=self.game.status)
        self.canvas.delete("all")

        tr, tc, _ = self.game.board.target_exit
        sr, sc = self.game.selected_cell
        emitter_r, emitter_c = GridBoard.SIZE - 1, 2

        # Draw grid cells
        for r in range(GridBoard.SIZE):
            for c in range(GridBoard.SIZE):
                x1 = self.PAD + c * self.CELL_SIZE
                y1 = self.PAD + r * self.CELL_SIZE
                x2 = x1 + self.CELL_SIZE
                y2 = y1 + self.CELL_SIZE

                fill = "#111827"
                outline = "#283548"
                width = 1.5

                if (r, c) == (tr, tc):
                    fill = "#1E1B4B"
                    outline = "#FBBF24"
                    width = 2.5
                elif (r, c) == (emitter_r, emitter_c):
                    fill = "#0F2942"
                    outline = "#38BDF8"
                    width = 2

                if (r, c) == (sr, sc):
                    outline = "#22D3EE"
                    width = 3

                self.canvas.create_rectangle(x1 + 2, y1 + 2, x2 - 2, y2 - 2, fill=fill, outline=outline, width=width)

                # Target beacon ring
                if (r, c) == (tr, tc):
                    cx, cy = self._cell_center(r, c)
                    self.canvas.create_oval(cx - 18, cy - 18, cx + 18, cy + 18, outline="#FBBF24", width=3)
                    self.canvas.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, fill="#F59E0B", outline="")

        # Draw glowing laser path on top of dark cells
        self._draw_laser_beam()

        # Draw player mirrors and any revealed blocker on top of beam
        for r in range(GridBoard.SIZE):
            for c in range(GridBoard.SIZE):
                m_val = self.game.board.player_grid[r][c]
                if m_val in ("/", "\\"):
                    self._draw_mirror(r, c, m_val)

                if self.game.blocker_hit == (r, c):
                    x1 = self.PAD + c * self.CELL_SIZE + 16
                    y1 = self.PAD + r * self.CELL_SIZE + 16
                    x2 = self.PAD + (c + 1) * self.CELL_SIZE - 16
                    y2 = self.PAD + (r + 1) * self.CELL_SIZE - 16
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#7F1D1D", outline="#EF4444", width=3)
                    self.canvas.create_line(x1 + 8, y1 + 8, x2 - 8, y2 - 8, fill="#FCA5A5", width=3)
                    self.canvas.create_line(x2 - 8, y1 + 8, x1 + 8, y2 - 8, fill="#FCA5A5", width=3)


def main() -> None:
    root = tk.Tk()
    game = LaserPuzzleGame()
    LaserPuzzleGUI(root, game)
    root.mainloop()


if __name__ == "__main__":
    main()