"""
Course:      CMPS 5113 - Advanced Programming Language Concepts
Assignment:  Program 3 - Open-Ended OOP GUI Program (Laser & Mirror Logic)
Author:      Harika Vemulapalli
Date:        November 2026
Description: A grid-based logic and deduction game built with Python tkinter.
             Players fire laser probes around a 5x5 board to deduce hidden
             reflectors/blockers and route the beam into the target sensor.
"""

import random
import tkinter as tk
from tkinter import messagebox


class GridBoard:
    """Represents a 5x5 grid with hidden puzzle elements and player placements."""

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
        """Creates a solvable 5x5 mirror-deduction layout with a target exit."""
        self.solution = [["." for _ in range(self.SIZE)] for _ in range(self.SIZE)]
        self.player_grid = [["." for _ in range(self.SIZE)] for _ in range(self.SIZE)]

        # Place 3 hidden mirrors ('/' or '\') and 1 blocker ('#')
        positions = [(r, c) for r in range(self.SIZE) for c in range(self.SIZE) if not (r == 4 and c == 2)]
        chosen = random.sample(positions, 4)

        self.solution[chosen[0][0]][chosen[0][1]] = "/"
        self.solution[chosen[1][0]][chosen[1][1]] = "\\"
        self.solution[chosen[2][0]][chosen[2][1]] = random.choice(["/", "\\"])
        self.solution[chosen[3][0]][chosen[3][1]] = "#"

        # Pick a target edge cell different from bottom-center entry (4, 2)
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

    def trace_beam(self, use_player_grid: bool, start_r: int, start_c: int, start_dir: int) -> tuple[str, list[tuple[int, int]]]:
        """
        Traces a beam starting just outside (start_r, start_c) moving in start_dir.
        Returns (outcome_label, path_cells).
        """
        grid = self.player_grid if use_player_grid else self.solution
        r, c, direction = start_r, start_c, start_dir
        path: list[tuple[int, int]] = []
        visited_states: set[tuple[int, int, int]] = set()

        while 0 <= r < self.SIZE and 0 <= c < self.SIZE:
            state = (r, c, direction)
            if state in visited_states:
                return "LOOPED", path
            visited_states.add(state)
            path.append((r, c))

            cell = grid[r][c]
            if cell == "#":
                return "ABSORBED (Blocker)", path
            if cell in ("/", "\\"):
                direction = self._reflect(direction, cell)

            r += self.DR[direction]
            c += self.DC[direction]

        # Exited the board at (r, c) after stepping out of bounds
        exit_r = max(0, min(self.SIZE - 1, r - self.DR[direction]))
        exit_c = max(0, min(self.SIZE - 1, c - self.DC[direction]))
        target_r, target_c, _ = self.target_exit
        if (exit_r, exit_c) == (target_r, target_c):
            return f"HIT TARGET ({exit_r + 1}, {exit_c + 1})", path
        return f"EXITED AT ({exit_r + 1}, {exit_c + 1})", path


class LaserPuzzleGame:
    """Manages puzzle state, probe count, win/loss tally, and selected cell."""

    def __init__(self) -> None:
        self.board = GridBoard()
        self.selected_cell: tuple[int, int] = (2, 2)
        self.probes_fired: int = 0
        self.wins: int = 0
        self.losses: int = 0
        self.last_path: list[tuple[int, int]] = []
        self.status: str = (
            "Select a cell and place '/' or '\\' mirrors, or fire a Probe from an edge to deduce hidden mirrors."
        )

    def new_puzzle(self) -> None:
        self.board.generate_puzzle()
        self.selected_cell = (2, 2)
        self.probes_fired = 0
        self.last_path = []
        self.status = "New 5x5 puzzle generated! Deduce mirror positions and route the beam to the TARGET cell."

    def cycle_player_mirror(self) -> None:
        """Cycles the selected cell through '.' -> '/' -> '\\' -> '.'."""
        r, c = self.selected_cell
        order = [".", "/", "\\"]
        current = self.board.player_grid[r][c]
        next_val = order[(order.index(current) + 1) % len(order)]
        self.board.player_grid[r][c] = next_val
        label = "Empty" if next_val == "." else f"Mirror '{next_val}'"
        self.status = f"Cell ({r + 1}, {c + 1}) set to {label}."

    def fire_probe(self, entry_side: str = "BOTTOM", lane: int = 2) -> None:
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

        outcome, path = self.board.trace_beam(False, sr, sc, sdir)
        self.last_path = path
        self.status = f"Probe #{self.probes_fired} ({entry_side} lane {lane + 1}) -> {outcome}."

    def check_solution(self) -> None:
        """Checks whether the player's placed mirrors route the beam from (4, 2) up to the TARGET."""
        outcome, path = self.board.trace_beam(True, GridBoard.SIZE - 1, 2, 0)
        self.last_path = path
        target_r, target_c, _ = self.board.target_exit

        # Verify that the player's mirrors actually deflect the beam into the target
        hit_target = outcome.startswith("HIT TARGET")
        placed_any = any(
            self.board.player_grid[r][c] in ("/", "\\")
            for r in range(GridBoard.SIZE)
            for c in range(GridBoard.SIZE)
        )

        if hit_target and placed_any:
            self.wins += 1
            self.status = (
                f"SOLVED! Your mirrors routed the beam to TARGET ({target_r + 1}, {target_c + 1}) "
                f"using {self.probes_fired} probe(s)!"
            )
        else:
            self.losses += 1
            self.status = (
                f"Not quite ({outcome}). Target is ({target_r + 1}, {target_c + 1}). "
                "Adjust your mirrors or fire more probes to deduce the path."
            )


class LaserPuzzleGUI:
    """Tkinter GUI for the Laser & Mirror Logic game."""

    def __init__(self, root: tk.Tk, game: LaserPuzzleGame) -> None:
        self.root = root
        self.game = game

        self.root.title("Laser & Mirror Logic — CMPS 5113")
        self.root.geometry("680x620")
        self.root.minsize(600, 560)

        self._build_ui()
        self._refresh_ui()

    def _build_ui(self) -> None:
        top = tk.Frame(self.root, padx=14, pady=10)
        top.pack(fill=tk.X)

        tk.Label(top, text="LASER & MIRROR LOGIC", font=("Helvetica", 19, "bold"), anchor="w").pack(fill=tk.X)
        tk.Label(
            top,
            text=(
                "Logic Goal: Fire probes from edges to deduce hidden mirrors/blockers, then place '/' and '\\' "
                "mirrors to guide the beam from Bottom-Center (Row 5, Col 3) to the TARGET cell."
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

        # 5x5 Grid
        grid_frame = tk.Frame(self.root, padx=14, pady=8)
        grid_frame.pack(expand=True)

        self.cell_buttons: list[list[tk.Button]] = []
        for r in range(GridBoard.SIZE):
            row_btns: list[tk.Button] = []
            for c in range(GridBoard.SIZE):
                btn = tk.Button(
                    grid_frame,
                    text=".",
                    font=("Courier", 16, "bold"),
                    width=5,
                    height=2,
                    command=lambda row=r, col=c: self._on_select_cell(row, col),
                )
                btn.grid(row=r, column=c, padx=4, pady=4)
                row_btns.append(btn)
            self.cell_buttons.append(row_btns)

        self.status_lbl = tk.Label(
            self.root,
            text="",
            font=("Helvetica", 10, "bold"),
            fg="#0F172A",
            wraplength=640,
            justify="center",
            pady=6,
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

    def _on_select_cell(self, r: int, c: int) -> None:
        self.game.selected_cell = (r, c)
        self.game.status = f"Selected cell ({r + 1}, {c + 1}). Click 'Place / Rotate Mirror' to toggle '/' or '\\'."
        self._refresh_ui()

    def _on_cycle_mirror(self) -> None:
        self.game.cycle_player_mirror()
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
            "1. Choose an edge (TOP, BOTTOM, LEFT, RIGHT) and row/column (1-5), then click 'Fire Probe' "
            "to see where a beam exits or gets blocked.\n"
            "2. Use probe results to deduce where hidden mirrors ('/' or '\\') or blockers ('#') sit.\n"
            "3. Click any grid cell and press 'Place / Rotate Mirror' to place '/' or '\\'.\n"
            "4. Click 'Check Solution' to test routing the beam from Bottom-Center into the TARGET cell."
        )
        messagebox.showinfo("Help — Laser & Mirror Logic", msg)

    def _show_credits(self) -> None:
        msg = (
            "CMPS 5113 — Program 3 (Open-Ended OOP GUI)\n\n"
            "Game: Laser & Mirror Logic\n"
            "Author: Harika Vemulapalli"
        )
        messagebox.showinfo("Credits", msg)

    def _refresh_ui(self) -> None:
        self.stats_lbl.config(
            text=f"Probes Fired: {self.game.probes_fired}   |   Wins: {self.game.wins}   |   Losses: {self.game.losses}"
        )
        self.status_lbl.config(text=self.game.status)

        tr, tc, _ = self.game.board.target_exit
        sr, sc = self.game.selected_cell
        path_set = set(self.game.last_path)

        for r in range(GridBoard.SIZE):
            for c in range(GridBoard.SIZE):
                val = self.game.board.player_grid[r][c]
                display_txt = val
                bg = "#F8FAFC"

                if (r, c) == (tr, tc) and val == ".":
                    display_txt = "TGT"
                    bg = "#FEF3C7"
                elif (r, c) in path_set and val == ".":
                    display_txt = "*"
                    bg = "#E0F2FE"

                if (r, c) == (sr, sc):
                    bg = "#DBEAFE"

                self.cell_buttons[r][c].config(text=display_txt, bg=bg)


def main() -> None:
    root = tk.Tk()
    game = LaserPuzzleGame()
    LaserPuzzleGUI(root, game)
    root.mainloop()


if __name__ == "__main__":
    main()