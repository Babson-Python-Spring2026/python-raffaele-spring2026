"""Convert portfolio_splits CSV to a structured JSON with new_shares / old_shares."""

import csv, json, math
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "data" / "source" / "portfolio_splits_true_splits_only_20260331b.csv"
DST = Path(__file__).resolve().parents[2] / "data" / "source" / "portfolio_splits.json"


def ratio_to_fraction(ratio: float) -> tuple[int, int]:
    """Turn a float ratio into (new_shares, old_shares) as coprime integers.

    Examples
    --------
    10.0  -> (10, 1)   # 10-for-1
    1.5   -> (3, 2)    # 3-for-2
    0.1   -> (1, 10)   # 1-for-10 reverse split
    """
    frac = ratio.as_integer_ratio()          # exact for any float
    gcd  = math.gcd(frac[0], frac[1])
    return frac[0] // gcd, frac[1] // gcd


def convert(src: Path = SRC, dst: Path = DST) -> dict:
    splits = []
    with open(src, newline="") as f:
        for row in csv.DictReader(f):
            new, old = ratio_to_fraction(float(row["Split Ratio"]))
            splits.append({
                "date":       row["Date"],
                "ticker":     row["Ticker"],
                "new_shares": new,
                "old_shares": old,
            })

    payload = {"splits": splits}

    with open(dst, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {len(splits)} split(s) to {dst}")
    return payload


if __name__ == "__main__":
    convert()
