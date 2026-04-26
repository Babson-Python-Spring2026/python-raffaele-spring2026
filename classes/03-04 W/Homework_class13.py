"""
Homework: Reading Code with State / Transitions / Invariants (Tic-Tac-Toe)

This program brute-forces tic-tac-toe WITHOUT recursion.

What it actually counts:
- It explores all possible games where X starts and players alternate.
- The search STOPS as soon as someone wins (a terminal state).
- It also records full boards that end in a tie.
- It tracks UNIQUE *terminal* boards "up to symmetry" (rotations + reflections),
  meaning rotated/flipped versions are treated as the same terminal board.

================================================================
STUDENT ANSWERS
================================================================

1) STATE
-------------------------------------------------
The state of this program is everything that mutates while the
nested loops execute. Concretely, the state is:

  - `board`: the 9-cell list that currently holds 'X', 'O', or ' '
    in the squares reached along the current search path.
  - `unique_seen`: the growing list of terminal boards already
    recorded, each stored in canonical form (lex-min of its 8
    symmetry variants).
  - Integer counters that summarise what has been discovered so far:
       full_boards, x_wins_on_full_board, draws_on_full_board,
       x_wins, o_wins, ties
  - The loop indices (x1, o1, x2, ... , x5) which together describe
    "which square each player is currently trying on each ply".

The counters and `unique_seen` are the *accumulated* state; `board`
is the *working* state used to decide what to do next.

2) TRANSITIONS
-------------------------------------------------
Transitions are the places where state changes. In this file they
live in three categories:

  (a) Working-state transitions on `board`:
        - Every `board[xi] = 'X'` and `board[oi] = 'O'` inside the
          nested for-loops PLACES a mark (state change forward).
        - Every `board[xi] = ' '` / `board[oi] = ' '` at the bottom
          of each nested loop UNDOES that mark (state change back).
        Together these drive the depth-first exploration.

  (b) Accumulated-state transitions inside functions:
        - `record_unique_board()` mutates the globals
          `unique_seen`, `x_wins`, `o_wins`, `ties`.
        - `record_full_board()` mutates `full_boards`,
          `x_wins_on_full_board`, `draws_on_full_board` and also
          calls `record_unique_board()`.

  (c) Search-control transitions:
        - `should_continue()` does not itself mutate `board`, but
          it decides whether the next nested loop will run. When
          it returns False, the current branch is pruned and the
          corresponding undo at the bottom of the loop runs.

3) FOUR INVARIANTS (and what enforces each)
-------------------------------------------------
  I1. At any moment during the search, `board` contains exactly
      `move_number` non-blank cells. Enforced by pairing every
      assignment with a matching undo at the end of each loop body.

  I2. X and O alternate. Enforced structurally: odd-indexed loops
      write 'X', even-indexed loops write 'O', and no loop skips
      a turn.

  I3. We never keep exploring a branch after somebody has won.
      Enforced by `should_continue()` calling `has_winner()` and
      returning False on any winning board, which pruning the
      deeper loops.

  I4. `unique_seen` never contains two boards that are equivalent
      under rotation/reflection. Enforced by `record_unique_board()`
      computing `standard_form()` first and checking
      `rep not in unique_seen` before appending.

  (Bonus I5.) Every terminal board ends up recorded exactly once in
      `unique_seen`, because every branch either hits a winner
      (recorded via `should_continue` -> `record_unique_board`)
      or reaches 9 plies (recorded via `record_full_board`).

6) NON-OBVIOUS PART: why standard_form() produces uniqueness
-------------------------------------------------
A tic-tac-toe position has 8 symmetric variants: the identity, three
rotations (90, 180, 270 degrees), and four reflections (the original
flipped vertically and then rotated three more times). Two boards
that look different as flat lists can actually be the same game
situation once you allow the board to be rotated or mirrored.
`standard_form()` builds all 8 of those variants for a given board
and then returns `min(variants)`. Because `min` is deterministic and
every variant of a given equivalence class produces *the same set*
of 8 variants (just in a different order), every member of the
class collapses to exactly the same minimum. That shared minimum
is what we store in `unique_seen`. The `rep not in unique_seen`
check in `record_unique_board` then guarantees that each symmetry
class is counted at most once, which is why `len(unique_seen)` is
138 and not the much larger raw count of terminal boards.

7) WHAT THE PRINTED NUMBERS MEAN
-------------------------------------------------
    print 1:  127872
      = `full_boards`
      = the number of 9-ply game paths the search reaches where no
        one has won along the way AND the board becomes completely
        full. It is NOT the number of distinct drawn positions;
        identical full boards reached by different move orders are
        counted multiple times here.

    print 2:  138 81792 46080 91 44 3
      These are, in order:
        138   = len(unique_seen)
                total distinct terminal boards up to symmetry
                (wins for X + wins for O + ties, de-duplicated).
        81792 = x_wins_on_full_board
                number of 9-ply paths where X wins on the final
                (9th) move, so the board is full and X has three
                in a row. Counted with move-order multiplicity.
        46080 = draws_on_full_board
                number of 9-ply paths that end with a full board
                and no winner, again counted with multiplicity.
                Note 81792 + 46080 = 127872 = full_boards.
        91    = x_wins
                distinct terminal boards (up to symmetry) in which
                X has won. Includes wins that happened before move
                9 as well as wins on move 9.
        44    = o_wins
                distinct terminal boards (up to symmetry) in which
                O has won.
        3     = ties
                distinct full boards (up to symmetry) that end in
                a tie. And 91 + 44 + 3 = 138 = len(unique_seen).
================================================================
"""

# ----------------------------
# Global running totals (STATE)
# ----------------------------

unique_seen = []             # Canonical forms of every distinct terminal board we've already recorded.
                             # We store the "standard form" (lex-min of the 8 symmetry variants)
                             # so that boards which are rotations/reflections of one another
                             # collapse to the same key and are counted only once.
board = [' '] * 9            # The working tic-tac-toe board, flattened to 9 cells.
                             # The nested loops mutate this in place while descending the
                             # search tree, then UNDO each move on the way back up so we can
                             # reuse the same list for sibling branches (DFS with backtracking).

full_boards = 0              # Raw count of 9-ply search paths where every square got filled.
                             # Counts with multiplicity: the same final position reached by
                             # different move orders is counted once per order.
x_wins_on_full_board = 0     # Among those full-board paths, how many end with X having three in a row.
draws_on_full_board = 0      # Among those full-board paths, how many end with no winner (true ties).

x_wins = 0                   # Distinct terminal boards (up to symmetry) where X has won.
o_wins = 0                   # Distinct terminal boards (up to symmetry) where O has won.
ties = 0                     # Distinct full boards (up to symmetry) that end in a tie.


# ----------------------------
# Board representation helpers
# ----------------------------

def to_grid(flat_board: list[str]) -> list[list[str]]:
    """Convert the 9-cell flat board into a 3x3 grid (a list of 3 rows,
    each a list of 3 cells). This is a pure helper; it does not mutate
    the flat board. The grid form is what the rotation and flip helpers
    operate on."""
    grid = []
    for row in range(3):
        row_vals = []
        for col in range(3):
            row_vals.append(flat_board[row * 3 + col])
        grid.append(row_vals)
    return grid


def rotate_clockwise(grid: list[list[str]]) -> list[list[str]]:
    """Return a NEW 3x3 grid that is the 90-degree clockwise rotation of
    the input grid. The rule is: the element at (r, c) moves to (c, 2-r)
    in the output. Used by standard_form() to enumerate the four
    rotational variants of a board."""
    rotated = [[' '] * 3 for _ in range(3)]
    for r in range(3):
        for c in range(3):
            rotated[c][2 - r] = grid[r][c]
    return rotated


def flip_vertical(grid: list[list[str]]) -> list[list[str]]:
    """Return a NEW 3x3 grid that is the input grid mirrored top-to-bottom
    (row 0 swaps with row 2). Combined with rotate_clockwise this gives us
    the remaining four reflection-based variants of a board."""
    return [grid[2], grid[1], grid[0]]


def standard_form(flat_board: list[str]) -> list[list[str]]:
    """Compute the canonical representative of a board's symmetry class.
    It builds all 8 variants (4 rotations of the board plus 4 rotations
    of its vertical flip) and returns min(variants). Because every member
    of a symmetry class generates the same 8 variants, every member maps
    to the same minimum. This is the key used to decide whether a
    terminal board is 'new'."""
    grid = to_grid(flat_board)
    flipped = flip_vertical(grid)

    variants = []
    for _ in range(4):
        variants.append(grid)
        variants.append(flipped)
        grid = rotate_clockwise(grid)
        flipped = rotate_clockwise(flipped)

    return min(variants)


def record_unique_board(flat_board: list[str]) -> None:
    """Record a terminal board in the de-duplicated catalog.
    Computes the canonical form, adds it to unique_seen only if an
    equivalent board has not already been recorded, and bumps exactly
    one of the three per-outcome counters (x_wins, o_wins, ties)."""
    global x_wins, o_wins, ties

    rep = standard_form(flat_board)

    # Gate: only count a board once per symmetry class. Because `rep` is
    # the canonical form, any rotation or reflection of a board we have
    # already recorded will produce the same rep and be filtered here.
    if rep not in unique_seen:
        unique_seen.append(rep)

        # First sighting of this symmetry class -> classify the outcome
        # (X win / O win / tie) and bump the matching counter. Each of
        # the three counters therefore holds "how many distinct terminal
        # positions of that type exist, up to symmetry".
        winner = who_won(flat_board)
        if winner == 'X':
            x_wins += 1
        elif winner == 'O':
            o_wins += 1
        else:
            ties += 1


# ----------------------------
# Game logic
# ----------------------------

def has_winner(flat_board: list[str]) -> bool:
    """Return True iff some player currently has three in a row.
    Implements the classic 'row/col/diagonal sum' trick: X contributes
    +10, O contributes -10, empty contributes 0, so a line total with
    absolute value 30 means all three cells belong to the same player."""
    winning_lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # cols
        [0, 4, 8], [6, 4, 2],             # diagonals
    ]

    for line in winning_lines:
        score = 0
        for idx in line:
            if flat_board[idx] == 'X':
                score += 10
            elif flat_board[idx] == 'O':
                score -= 10
        if abs(score) == 30:
            return True

    return False


def who_won(flat_board: list[str]) -> str:
    """Return 'X', 'O', or 'TIE' based on the current board.
    Same sum trick as has_winner(): a line total of +30 means X has
    three in a row, -30 means O, anything else means no winner on
    that line. If no line wins, the function falls through and returns
    'TIE' (meaning 'nobody has won'; the caller decides whether the
    board is actually full)."""
    winning_lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # cols
        [0, 4, 8], [6, 4, 2],             # diagonals
    ]

    for line in winning_lines:
        score = 0
        for idx in line:
            if flat_board[idx] == 'X':
                score += 10
            elif flat_board[idx] == 'O':
                score -= 10

        if score == 30:
            return 'X'
        elif score == -30:
            return 'O'

    return 'TIE'


def should_continue(flat_board: list[str], move_number: int) -> bool:
    """Decide whether the search should keep placing deeper moves.
    If the current board already contains a winner, this is a terminal
    state: we record it via record_unique_board() and return False so
    the caller prunes the rest of that branch. Otherwise return True
    and the next nested loop will try every empty cell."""
    # Pruning rule: a winning position is terminal. We record it here
    # (so winning-before-move-9 boards are still captured) and signal
    # the caller to skip the deeper loops for this branch.
    if has_winner(flat_board):
        record_unique_board(flat_board)
        return False
    return True


def record_full_board(flat_board: list[str]) -> None:
    """Called once for every 9-move path that did not short-circuit on
    a prior winner. Bumps the raw full-board counters (which count paths
    with move-order multiplicity) and also forwards to record_unique_board
    so the position is added to the de-duplicated catalog."""
    global full_boards, x_wins_on_full_board, draws_on_full_board

    # Terminal state: 9 plies placed. We still want to de-duplicate the
    # final position, so forward it to record_unique_board() first.
    record_unique_board(flat_board)
    full_boards += 1

    # On a completely full board the only possibilities are "X wins on
    # move 9" (X made the ninth move) or "draw". O can never win here
    # because a win by O would have been caught at move 8 by should_continue.
    if has_winner(flat_board):
        x_wins_on_full_board += 1
    else:
        draws_on_full_board += 1


# ----------------------------
# Brute force search (9 nested loops)
# ----------------------------

# TRANSITIONS IN THE LOOP BODY:
#   Each `board[xi] = 'X'` / `board[oi] = 'O'` below is a forward
#   transition (a move is placed on the working board). Each
#   `board[xi] = ' '` / `board[oi] = ' '` at the bottom of a loop is
#   the matching reverse transition (the undo needed for DFS
#   backtracking).
#
# OTHER PLACES TRANSITIONS HAPPEN:
#   - inside record_unique_board()  (mutates unique_seen, x_wins,
#     o_wins, ties)
#   - inside record_full_board()    (mutates full_boards,
#     x_wins_on_full_board, draws_on_full_board)
#   - should_continue() does not mutate board directly, but it
#     controls whether the next forward transition is attempted.

# Move 1: X
for x1 in range(9):
    board[x1] = 'X'
    if should_continue(board, 1):

        # Move 2: O
        for o1 in range(9):
            if board[o1] == ' ':
                board[o1] = 'O'
                if should_continue(board, 2):

                    # Move 3: X
                    for x2 in range(9):
                        if board[x2] == ' ':
                            board[x2] = 'X'
                            if should_continue(board, 3):

                                # Move 4: O
                                for o2 in range(9):
                                    if board[o2] == ' ':
                                        board[o2] = 'O'
                                        if should_continue(board, 4):

                                            # Move 5: X
                                            for x3 in range(9):
                                                if board[x3] == ' ':
                                                    board[x3] = 'X'
                                                    if should_continue(board, 5):

                                                        # Move 6: O
                                                        for o3 in range(9):
                                                            if board[o3] == ' ':
                                                                board[o3] = 'O'
                                                                if should_continue(board, 6):

                                                                    # Move 7: X
                                                                    for x4 in range(9):
                                                                        if board[x4] == ' ':
                                                                            board[x4] = 'X'
                                                                            if should_continue(board, 7):

                                                                                # Move 8: O
                                                                                for o4 in range(9):
                                                                                    if board[o4] == ' ':
                                                                                        board[o4] = 'O'
                                                                                        if should_continue(board, 8):

                                                                                            # Move 9: X
                                                                                            for x5 in range(9):
                                                                                                if board[x5] == ' ':
                                                                                                    board[x5] = 'X'

                                                                                                    # Full board reached (terminal)
                                                                                                    record_full_board(board)

                                                                                                    # undo move 9
                                                                                                    board[x5] = ' '

                                                                                        # undo move 8
                                                                                        board[o4] = ' '

                                                                            # undo move 7
                                                                            board[x4] = ' '

                                                                # undo move 6
                                                                board[o3] = ' '

                                                    # undo move 5
                                                    board[x3] = ' '

                                        # undo move 4
                                        board[o2] = ' '

                            # undo move 3
                            board[x2] = ' '

                # undo move 2
                board[o1] = ' '

    # undo move 1
    board[x1] = ' '


print(full_boards)
print(len(unique_seen), x_wins_on_full_board, draws_on_full_board, x_wins, o_wins, ties)
