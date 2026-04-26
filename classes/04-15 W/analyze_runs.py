"""
Homework: AI + STI + Python - analyze_runs
Student: Riccardo Dell'Anna Misurale
Due: 2026-04-15

================================================================
PART 1 - STI ANALYSIS
================================================================

STATE (what we must track while scanning the list)
---------------------------------------------------
As we walk through `nums` one element at a time, we need:

  i   - current index
  prev - the previous value we compared against (nums[i-1])
  direction - the current run's direction: 'inc' (strictly
              increasing), 'dec' (strictly decreasing), or 'flat'
              (we just reset, no real direction yet)
  run_len   - length of the run we are currently inside
  run_start - index where the current run started; used only so
              we can slice the actual values out of nums when we
              beat the previous best
  best_inc      - length of the longest increasing run seen so far
  best_inc_start - start index of that longest increasing run
  best_dec      - length of the longest decreasing run seen so far
  best_dec_start - start index of that longest decreasing run
  num_inc       - number of maximal strictly increasing runs found
  num_dec       - number of maximal strictly decreasing runs found
  counted_inc   - True if the current run has already been counted
                  in num_inc (so we don't double count)
  counted_dec   - same for num_dec

Only `best_*` and `num_*` survive to the final return value; the
rest is intermediate state used while scanning.

TRANSITIONS (what happens on each new element)
----------------------------------------------
For each new number `x = nums[i]`, compare to `prev`:

  T1. x > prev
        The current pair is strictly increasing.
        - If the current run is 'inc', extend it: run_len += 1.
        - Otherwise (prev direction was 'dec' or 'flat'), the
          previous run ends here and a NEW increasing run starts
          with length 2: [prev, x]. Reset counted_inc/counted_dec.
        - Mark this as a newly discovered increasing run if it
          has not been counted yet (num_inc += 1, counted_inc = True).
        - If run_len beats best_inc, update best_inc and the start.

  T2. x < prev
        Symmetric to T1 for decreasing.

  T3. x == prev
        Equal adjacent values end any run that was in progress
        (a strictly monotone run cannot include equal neighbors).
        The new "current run" is just the single element x, with
        run_len = 1 and direction 'flat'. No best_* updates.

  Edge cases:
    - Empty list: return zeros everywhere and an empty
      longest_run_values list.
    - Single-element list: the single element is its own run of
      length 1, but it is neither strictly increasing nor strictly
      decreasing, so num_inc = num_dec = 0 and longest_run_values
      is [nums[0]] (any run of length 1 counts as a "longest run"
      only if no longer run exists).

INVARIANTS (must always hold while scanning)
--------------------------------------------
  I1. run_len >= 1 at all times once we have seen at least one
      element. (A run with zero elements is nonsense.)

  I2. best_inc >= 2 only after at least one strictly-increasing
      transition has occurred. Same for best_dec. Until then they
      stay at 0.

  I3. best_inc (resp. best_dec) is never less than any run_len
      observed so far whose direction was 'inc' (resp. 'dec').
      Enforced at every update site: we only overwrite the best
      when run_len > best_inc.

  I4. num_inc counts each maximal strictly-increasing run exactly
      once. Enforced by the `counted_inc` flag: we set it when we
      first enter an increasing run, and clear it any time we leave
      the increasing state (switch to decreasing or hit an equal).

  I5. longest_run_values, when we finally build it, matches the
      recorded longest length. Because we store BOTH the length
      and the start index at the same time in best_inc /
      best_inc_start (and likewise for dec), the slice
      nums[start : start + length] is always in sync.
================================================================
"""


def analyze_runs(nums: list[int]) -> dict:
    """
    Scan `nums` once and return a dictionary describing the
    strictly-monotone runs inside it.

    A "run" is a maximal contiguous slice where each consecutive
    pair is in the same strict direction. Equal adjacent values
    break any run in progress.

    Returns:
        {
          "longest_increasing_run": int,
          "longest_decreasing_run": int,
          "num_increasing_runs": int,
          "num_decreasing_runs": int,
          "longest_run_values": list[int],
        }
    """
    # --- edge case: empty input -------------------------------
    if not nums:
        return {
            "longest_increasing_run": 0,
            "longest_decreasing_run": 0,
            "num_increasing_runs": 0,
            "num_decreasing_runs": 0,
            "longest_run_values": [],
        }

    # --- edge case: single element ----------------------------
    if len(nums) == 1:
        return {
            "longest_increasing_run": 1,
            "longest_decreasing_run": 1,
            "num_increasing_runs": 0,
            "num_decreasing_runs": 0,
            "longest_run_values": [nums[0]],
        }

    # --- initial state ----------------------------------------
    direction = "flat"     # no real direction until we see two different values
    run_len = 1            # the first element is a run of length 1 by itself
    run_start = 0

    # Best runs seen so far. Start at length 1 so that a list of all
    # equal values still reports a meaningful "longest run" of 1
    # (there are no strictly-increasing or strictly-decreasing runs
    # in that case, but at least one element exists).
    best_inc = 0
    best_inc_start = 0
    best_dec = 0
    best_dec_start = 0
    overall_best_len = 1
    overall_best_start = 0

    num_inc = 0
    num_dec = 0
    counted_inc = False
    counted_dec = False

    # --- scan -------------------------------------------------
    for i in range(1, len(nums)):
        prev = nums[i - 1]
        curr = nums[i]

        if curr > prev:
            # increasing transition
            if direction == "inc":
                run_len += 1
            else:
                # starting a brand-new increasing run of length 2
                direction = "inc"
                run_len = 2
                run_start = i - 1
                counted_inc = False
                counted_dec = False

            if not counted_inc:
                num_inc += 1
                counted_inc = True

            if run_len > best_inc:
                best_inc = run_len
                best_inc_start = run_start

        elif curr < prev:
            # decreasing transition
            if direction == "dec":
                run_len += 1
            else:
                direction = "dec"
                run_len = 2
                run_start = i - 1
                counted_inc = False
                counted_dec = False

            if not counted_dec:
                num_dec += 1
                counted_dec = True

            if run_len > best_dec:
                best_dec = run_len
                best_dec_start = run_start

        else:
            # equal: break the current run
            direction = "flat"
            run_len = 1
            run_start = i
            counted_inc = False
            counted_dec = False

        # Track the overall best length so we can build
        # longest_run_values at the end. Either best_inc or best_dec
        # may be the overall leader.
        if best_inc >= best_dec and best_inc > overall_best_len:
            overall_best_len = best_inc
            overall_best_start = best_inc_start
        elif best_dec > best_inc and best_dec > overall_best_len:
            overall_best_len = best_dec
            overall_best_start = best_dec_start

    # --- build longest_run_values -----------------------------
    # Tie-breaking rule (per assignment): "If there is a tie for the
    # longest run, you may return either tied run". We prefer the
    # increasing one on ties because best_inc is checked first above.
    longest_run_values = nums[
        overall_best_start : overall_best_start + overall_best_len
    ]

    return {
        "longest_increasing_run": best_inc,
        "longest_decreasing_run": best_dec,
        "num_increasing_runs": num_inc,
        "num_decreasing_runs": num_dec,
        "longest_run_values": longest_run_values,
    }


# ================================================================
# PART 3 - TESTS
# ================================================================
if __name__ == "__main__":
    cases = [
        ("example from handout", [3, 5, 7, 2, 1, 4]),
        ("all increasing       ", [1, 2, 3, 4]),
        ("all decreasing       ", [5, 4, 3, 2]),
        ("all equal            ", [1, 1, 1]),
        ("single element       ", [4]),
        ("mixed with equals    ", [2, 5, 5, 4, 3, 6]),
        ("empty list           ", []),
        ("zigzag               ", [1, 3, 2, 4, 3, 5]),
    ]
    for label, xs in cases:
        print(f"{label}  nums = {xs}")
        result = analyze_runs(xs)
        for k, v in result.items():
            print(f"    {k:<25} {v}")
        print()
