"""
Lab 04 - Minesweeper reconstruction
Student: Riccardo Dell'Anna Misurale

Reverse-engineered from game_obfuscated.pyc by:
  1. Running it and observing prompts and board output
  2. Disassembling the bytecode to list code objects, names,
     string and numeric constants
  3. Reconstructing the behavior as readable Python

The visible evidence that drove the reconstruction:
  - Prompts:
      "Board height (2 - 10) : "
      "Board width  (2 - 10) : "
      "How many mines (less then <H*W>) : "
      "How many over would you like to dig? : "
      "How many down would you like to dig? : "
  - Error messages:
      "You must enter an integer (2 - 10) : "
      "please enter an integer between 0 and <max>"
      "That cell already exposed! Try again"
      "Uh Oh, you hit a mine, You Lost..."
      "Congratulations! You won."
  - Glyphs used in the display:
      'v'  (literal 'v')  marks unrevealed cells in the raw grid
      chr(0x2666)  (a diamond) rendered instead when a cell is
                   still hidden from the user
      ' '  empty revealed cell (zero neighboring mines)
      '1'..'8'     revealed cell showing the neighbor count
      chr(0x1F4A3) (bomb emoji) for a mine after a loss
  - Display layout (3x3 example):
        0    1    2
      - - - - - - - -
    0 | v  | v  | v  |
      - - - - - - - -
    1 | v  | v  | v  |
      - - - - - - - -
    2 | v  | v  | v  |
      - - - - - - - -

================================================================
STI DESCRIPTION
================================================================

STATE
  - height, width      : board dimensions (ints, 2..10)
  - num_mines          : number of mines placed
  - mines   : set of (row, col) tuples listing mine locations
  - revealed: 2d list[list[str]] - the user-visible board
              each cell is either 'v' (hidden) or the revealed
              content (' ', '1'..'8', or the bomb char)

TRANSITIONS
  - place_mines()       randomly picks `num_mines` unique cells
  - dig(row, col)       the only user action:
      * if it is a mine -> lose
      * else -> set the cell to count_neighbors(row, col);
        if that count is 0, flood-fill reveal the 8 neighbors
        recursively (same behavior as classic Minesweeper)

INVARIANTS
  I1. mines and revealed stay consistent: a cell never contains
      a revealed value if it is a mine (the only way a user sees
      a mine is by losing, which ends the game).
  I2. flood fill only expands through 0-count cells, so the user
      never auto-reveals a numbered cell that they did not dig.
  I3. the game ends as soon as `hidden_non_mine_cells == 0` (win)
      or the user digs a mine (loss); no further input is read.
  I4. user inputs are clamped: height/width in [2..10], mines in
      [1..H*W-1], dig coordinates in [0..W-1] and [0..H-1].
================================================================
"""

from __future__ import annotations

import os
import platform
import random

HIDDEN = "v"
MINE = "\U0001f4a3"      # bomb emoji
FLAG_GLYPH = "\u2666"    # diamond, shown for hidden cells


# ------------------------------------------------------------------
# Screen helpers
# ------------------------------------------------------------------
def clear_screen() -> None:
    """Clear the terminal. On Windows use `cls`, otherwise `clear`."""
    try:
        cmd = "cls" if platform.system() == "Windows" else "clear"
        os.system(cmd)
    except Exception:
        pass


# ------------------------------------------------------------------
# Board construction and queries
# ------------------------------------------------------------------
def make_revealed(height: int, width: int) -> list[list[str]]:
    """Return an HxW board where every cell starts hidden."""
    return [[HIDDEN for _ in range(width)] for _ in range(height)]


def in_bounds(row: int, col: int, height: int, width: int) -> bool:
    """Return True iff (row, col) is a legal cell index."""
    return 0 <= row < height and 0 <= col < width


def is_mine(row: int, col: int, mines: set[tuple[int, int]]) -> bool:
    """Return True iff (row, col) is one of the mine positions."""
    return (row, col) in mines


def place_mines(
    height: int, width: int, num_mines: int
) -> set[tuple[int, int]]:
    """Return a set of `num_mines` unique (row, col) mine positions.
    Uses rejection sampling with randrange, matching the approach
    visible in the disassembled _10 code object."""
    mines: set[tuple[int, int]] = set()
    while len(mines) < num_mines:
        r = random.randrange(height)
        c = random.randrange(width)
        mines.add((r, c))
    return mines


def count_neighbors(
    row: int, col: int, height: int, width: int, mines: set[tuple[int, int]]
) -> int:
    """Count how many of the 8 neighbors of (row, col) are mines."""
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = row + dr, col + dc
            if in_bounds(nr, nc, height, width) and is_mine(nr, nc, mines):
                count += 1
    return count


# ------------------------------------------------------------------
# Display
# ------------------------------------------------------------------
def display_board(
    revealed: list[list[str]],
    height: int,
    width: int,
    reveal_everything: bool = False,
    mines: set[tuple[int, int]] | None = None,
) -> None:
    """Print the board.

    Hidden cells show the diamond glyph, revealed cells show their
    content. If `reveal_everything` is True (used on loss), mine
    cells are forced to show the bomb emoji.
    """
    # column header
    header = "      " + "    ".join(str(c) for c in range(width))
    sep = "    " + ("- " * (1 + 2 * width)).rstrip()
    print()
    print(header)
    print(sep)

    for r in range(height):
        row_cells = []
        for c in range(width):
            cell = revealed[r][c]
            if reveal_everything and mines is not None and (r, c) in mines:
                glyph = MINE
            elif cell == HIDDEN:
                glyph = FLAG_GLYPH
            else:
                glyph = cell
            row_cells.append(f" {glyph} ")
        print(f"  {r} | " + " | ".join(row_cells) + " |")
        print(sep)
    print()


# ------------------------------------------------------------------
# Digging (flood fill)
# ------------------------------------------------------------------
def dig(
    row: int,
    col: int,
    revealed: list[list[str]],
    mines: set[tuple[int, int]],
    height: int,
    width: int,
) -> bool:
    """Attempt to reveal (row, col). Returns True if the player hit
    a mine (game over), False otherwise.

    If the digged cell has 0 neighboring mines, flood-fill reveal
    its 8 neighbors recursively (classic Minesweeper behavior).
    """
    if not in_bounds(row, col, height, width):
        return False
    if revealed[row][col] != HIDDEN:
        # already revealed - the caller should tell the user
        return False
    if is_mine(row, col, mines):
        revealed[row][col] = MINE
        return True

    n = count_neighbors(row, col, height, width, mines)
    revealed[row][col] = " " if n == 0 else str(n)

    if n == 0:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if in_bounds(nr, nc, height, width) and revealed[nr][nc] == HIDDEN:
                    dig(nr, nc, revealed, mines, height, width)

    return False


def has_won(
    revealed: list[list[str]],
    height: int,
    width: int,
    num_mines: int,
) -> bool:
    """Win when every non-mine cell has been revealed."""
    hidden = sum(
        1 for r in range(height) for c in range(width)
        if revealed[r][c] == HIDDEN
    )
    return hidden == num_mines


# ------------------------------------------------------------------
# Input helpers
# ------------------------------------------------------------------
def _read_int_in_range(prompt: str, lo: int, hi: int, retry_prompt: str | None = None) -> int:
    """Prompt repeatedly until the user types an integer in [lo, hi]."""
    if retry_prompt is None:
        retry_prompt = prompt
    text = prompt
    while True:
        raw = input(text)
        try:
            value = int(raw)
        except ValueError:
            text = retry_prompt
            continue
        if lo <= value <= hi:
            return value
        text = retry_prompt


def get_board_settings() -> tuple[int, int, int]:
    """Ask the user for board height, width, and mine count.
    Mirrors the exact prompts from the obfuscated game."""
    height = _read_int_in_range(
        "\nBoard height (2 - 10) : ",
        2, 10,
        retry_prompt="You must enter an integer (2 - 10) : ",
    )
    width = _read_int_in_range(
        "Board width (2 - 10) : ",
        2, 10,
        retry_prompt="You must enter an integer (2 - 10) : ",
    )
    max_mines = height * width - 1
    mines = _read_int_in_range(
        f"How many mines (less then {max_mines + 1}) : ",
        1, max_mines,
        retry_prompt="Invalid number of mines, please re-enter : ",
    )
    return height, width, mines


# ------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------
def main() -> None:
    clear_screen()
    height, width, num_mines = get_board_settings()
    mines = place_mines(height, width, num_mines)
    revealed = make_revealed(height, width)

    while True:
        display_board(revealed, height, width)
        col = _read_int_in_range(
            "\nHow many over would you like to dig? : ",
            0, width - 1,
            retry_prompt=f"please enter an integer between 0 and {width - 1} : ",
        )
        row = _read_int_in_range(
            "How many down would you like to dig? : ",
            0, height - 1,
            retry_prompt=f"please enter an integer between 0 and {height - 1} : ",
        )

        if revealed[row][col] != HIDDEN:
            print("That cell already exposed! Try again")
            continue

        hit_mine = dig(row, col, revealed, mines, height, width)
        if hit_mine:
            display_board(
                revealed, height, width,
                reveal_everything=True, mines=mines,
            )
            print("Uh Oh, you hit a mine, You Lost...")
            return

        if has_won(revealed, height, width, num_mines):
            display_board(revealed, height, width)
            print("Congratulations! You won.")
            return


if __name__ == "__main__":
    main()
