"""
Lab 3 - Portfolio Transaction Functions

Implements the four functions the class discussion (04-08 W) listed:

  1. create_transaction(...)           -> append one validated event
  2. get_cash_balance(as_of_date)      -> reconstruct cash at a date
  3. build_portfolio(as_of_date)       -> reconstruct positions + cash
  4. list_transactions_for_ticker(ticker)

Design notes (STI):
  - STATE is the transactions ledger (JSON file). Portfolio and cash
    balance are *derived* from it, not stored.
  - TRANSITIONS are `create_transaction` calls; every other function
    only reads state.
  - INVARIANTS the ledger must respect:
      I1. dates must appear in the market-date list
      I2. tickers must appear in the ticker universe (or be $$$$)
      I3. input prices for buy/sell must be within +-15% of the
          source-of-truth price for that ticker on that date
      I4. after any transaction, resulting cash must be >= 0
      I5. after any transaction, resulting shares for every non-cash
          ticker must be >= 0

Uppercase TYPE values as used by the class file organization discussion:
  BUY, SELL, CNTRB, WDRW, DIV, SPLT

The existing transactions.json in this repo uses lowercase types
(`buy`, `sell`, `contribution`), so both the lowercase and the
uppercase aliases are accepted on read. New records are always
written with the canonical uppercase form.
"""

from __future__ import annotations

import json
from datetime import date as _date
from pathlib import Path

# ------------------------------------------------------------------
# File locations
# ------------------------------------------------------------------
# This file sits at labs/lab_03/scripts/functions/create_transactions.py
# so we go up 3 levels to reach labs/lab_03/
LAB_DIR = Path(__file__).resolve().parents[2]
DATA_SYSTEM = LAB_DIR / "data" / "system"

TRANSACTIONS_FILE = DATA_SYSTEM / "transactions" / "transactions.json"
MKT_DATES_FILE    = DATA_SYSTEM / "mkt_dates.json"
TICKER_UNIV_FILE  = DATA_SYSTEM / "ticker_universe.json"
PRICES_DATES_FILE = DATA_SYSTEM / "prices_dates.json"

CASH_TICKER = "$$$$"

# Canonical uppercase types
TYPE_BUY    = "BUY"
TYPE_SELL   = "SELL"
TYPE_CNTRB  = "CNTRB"
TYPE_WDRW   = "WDRW"
TYPE_DIV    = "DIV"
TYPE_SPLT   = "SPLT"
VALID_TYPES = {TYPE_BUY, TYPE_SELL, TYPE_CNTRB, TYPE_WDRW, TYPE_DIV, TYPE_SPLT}

# Map old lowercase values to the canonical uppercase ones
_LEGACY_TYPE_MAP = {
    "buy":          TYPE_BUY,
    "sell":         TYPE_SELL,
    "contribution": TYPE_CNTRB,
    "withdrawal":   TYPE_WDRW,
    "dividend":     TYPE_DIV,
    "split":        TYPE_SPLT,
}


def _normalize_type(t: str) -> str:
    if t in VALID_TYPES:
        return t
    lowered = t.lower()
    if lowered in _LEGACY_TYPE_MAP:
        return _LEGACY_TYPE_MAP[lowered]
    if lowered.upper() in VALID_TYPES:
        return lowered.upper()
    raise ValueError(f"unknown transaction type: {t!r}")


# ------------------------------------------------------------------
# File loaders (cached on demand, re-read on each call to keep the
# functions side-effect-light for testing)
# ------------------------------------------------------------------
def _load_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_transactions() -> list[dict]:
    return _load_json(TRANSACTIONS_FILE, [])


def save_transactions(transactions: list[dict]) -> None:
    TRANSACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRANSACTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=4)


def load_mkt_dates() -> list[str]:
    return _load_json(MKT_DATES_FILE, [])


def load_ticker_universe() -> list[str]:
    return _load_json(TICKER_UNIV_FILE, [])


def load_prices_dates() -> dict:
    return _load_json(PRICES_DATES_FILE, {})


# ------------------------------------------------------------------
# Validation helpers (the source of truth for invariants I1..I3)
# ------------------------------------------------------------------
def _validate_date(d: str, mkt_dates: list[str]) -> None:
    if d not in mkt_dates:
        raise ValueError(f"date {d!r} is not a valid market date")


def _validate_ticker(t: str, universe: list[str]) -> None:
    if t not in universe:
        raise ValueError(f"ticker {t!r} is not in the universe")


def _validate_price(
    ticker: str,
    on_date: str,
    price: float,
    prices_dates: dict,
    tolerance: float = 0.15,
) -> None:
    """+- tolerance (default 15%) vs source-of-truth price."""
    rows = prices_dates.get(on_date, [])
    match = next((r for r in rows if r["ticker"] == ticker), None)
    if match is None:
        raise ValueError(
            f"no price record for {ticker} on {on_date} in prices_dates.json"
        )
    truth = match["raw_price"]
    low  = truth * (1 - tolerance)
    high = truth * (1 + tolerance)
    if not (low <= price <= high):
        raise ValueError(
            f"price {price} for {ticker} on {on_date} outside +-{tolerance*100:.0f}% "
            f"of source-of-truth {truth}"
        )


def _next_record_number(transactions: list[dict]) -> int:
    existing = [t.get("record_number", 0) for t in transactions]
    return (max(existing) + 1) if existing else 1


# ------------------------------------------------------------------
# Core state reconstruction
# ------------------------------------------------------------------
def _parse_iso(d: str) -> _date:
    y, m, day = d.split("-")
    return _date(int(y), int(m), int(day))


def _transactions_up_to(
    transactions: list[dict], as_of_date: str
) -> list[dict]:
    """Return transactions whose date is <= as_of_date, in chronological
    order by (date, record_number)."""
    cutoff = _parse_iso(as_of_date)
    filtered = [t for t in transactions if _parse_iso(t["date"]) <= cutoff]
    filtered.sort(
        key=lambda t: (_parse_iso(t["date"]), t.get("record_number", 0))
    )
    return filtered


def _apply_to_holdings(
    holdings: dict[str, float], txn: dict
) -> None:
    """Mutate a {ticker -> shares} dict to reflect one transaction.
    Cash is tracked under CASH_TICKER (``$$$$``)."""
    ttype = _normalize_type(txn["type"])
    ticker = txn.get("ticker", CASH_TICKER)
    shares = float(txn.get("shares", 0) or 0)
    price  = float(txn.get("price", 0) or 0)

    if ttype == TYPE_BUY:
        # shares in, cash out
        holdings[ticker] = holdings.get(ticker, 0.0) + shares
        holdings[CASH_TICKER] = holdings.get(CASH_TICKER, 0.0) - shares * price
    elif ttype == TYPE_SELL:
        holdings[ticker] = holdings.get(ticker, 0.0) - shares
        holdings[CASH_TICKER] = holdings.get(CASH_TICKER, 0.0) + shares * price
    elif ttype == TYPE_CNTRB:
        # contribution: cash in. shares field is the dollar amount.
        holdings[CASH_TICKER] = holdings.get(CASH_TICKER, 0.0) + shares * price
    elif ttype == TYPE_WDRW:
        holdings[CASH_TICKER] = holdings.get(CASH_TICKER, 0.0) - shares * price
    elif ttype == TYPE_DIV:
        # dividend: cash in, no share change. shares field = cash amount.
        holdings[CASH_TICKER] = holdings.get(CASH_TICKER, 0.0) + shares * price
    elif ttype == TYPE_SPLT:
        # split: multiply the share count of `ticker` by the ratio
        # stored in `shares` (shares_out / shares_in).
        ratio = shares if shares else 1.0
        holdings[ticker] = holdings.get(ticker, 0.0) * ratio


def get_cash_balance(as_of_date: str, transactions: list[dict] | None = None) -> float:
    """Reconstruct the cash balance as of the end of as_of_date.

    Walks the ledger in chronological order, applying every transaction
    whose date is <= as_of_date. Cash is the $$$$ entry in the running
    holdings dict.
    """
    if transactions is None:
        transactions = load_transactions()
    holdings: dict[str, float] = {CASH_TICKER: 0.0}
    for txn in _transactions_up_to(transactions, as_of_date):
        _apply_to_holdings(holdings, txn)
    return round(holdings.get(CASH_TICKER, 0.0), 2)


def build_portfolio(
    as_of_date: str, transactions: list[dict] | None = None
) -> dict[str, float]:
    """Reconstruct the full portfolio as of as_of_date.

    Returns a dict mapping ticker -> shares (cash shown under $$$$).
    Zero-share positions are dropped except cash, which is always shown.
    """
    if transactions is None:
        transactions = load_transactions()
    holdings: dict[str, float] = {CASH_TICKER: 0.0}
    for txn in _transactions_up_to(transactions, as_of_date):
        _apply_to_holdings(holdings, txn)

    # Drop zero non-cash positions for a clean snapshot.
    return {
        t: round(s, 4)
        for t, s in holdings.items()
        if t == CASH_TICKER or abs(s) > 1e-9
    }


def list_transactions_for_ticker(
    ticker: str, transactions: list[dict] | None = None
) -> list[dict]:
    """Return every transaction record whose ticker matches, sorted
    chronologically (by date, then record_number)."""
    if transactions is None:
        transactions = load_transactions()
    matches = [t for t in transactions if t.get("ticker") == ticker]
    matches.sort(
        key=lambda t: (_parse_iso(t["date"]), t.get("record_number", 0))
    )
    return matches


# ------------------------------------------------------------------
# Create one transaction (the actual write path)
# ------------------------------------------------------------------
def create_transaction(
    date: str,
    type: str,
    ticker: str | None = None,
    shares: float | None = None,
    price: float | None = None,
    *,
    transactions: list[dict] | None = None,
    skip_price_check: bool = False,
    persist: bool = True,
) -> dict:
    """Create and append one validated transaction record.

    Enforces invariants I1..I5. Raises ValueError if any invariant fails.

    Args:
        date: ISO date string (must be in mkt_dates.json)
        type: any of BUY, SELL, CNTRB, WDRW, DIV, SPLT (case-insensitive)
        ticker: required for BUY/SELL/DIV/SPLT; cash trades use $$$$
        shares: numeric amount (shares for BUY/SELL, dollar amount for
                CNTRB/WDRW, cash amount for DIV, ratio for SPLT)
        price: per-share price (1.0 for cash types)
        transactions: optional pre-loaded ledger; if None, loads from disk
        skip_price_check: skip the +-15% price validation (useful for tests)
        persist: when True, write the updated ledger back to disk

    Returns:
        The new transaction record (as a dict).
    """
    ttype = _normalize_type(type)

    mkt_dates = load_mkt_dates()
    universe  = load_ticker_universe()

    # I1: valid date
    _validate_date(date, mkt_dates)

    # I2: valid ticker (cash $$$$ is implicitly valid for cash types)
    if ttype in (TYPE_BUY, TYPE_SELL, TYPE_DIV, TYPE_SPLT):
        if not ticker:
            raise ValueError(f"{ttype} requires a ticker")
        _validate_ticker(ticker, universe)
    else:
        # cash-only types
        ticker = CASH_TICKER
        price = 1.0

    # Fill defaults for cash types and validate numeric fields
    if shares is None:
        raise ValueError("shares is required")
    if ttype in (TYPE_CNTRB, TYPE_WDRW, TYPE_DIV):
        if price is None:
            price = 1.0
    if ttype in (TYPE_BUY, TYPE_SELL) and price is None:
        raise ValueError(f"{ttype} requires a price")
    if ttype == TYPE_SPLT and price is None:
        price = 1.0  # price is irrelevant for splits

    # I3: price sanity for BUY/SELL
    if ttype in (TYPE_BUY, TYPE_SELL) and not skip_price_check:
        prices_dates = load_prices_dates()
        _validate_price(ticker, date, float(price), prices_dates)

    # load the ledger, build the new record
    if transactions is None:
        transactions = load_transactions()
    else:
        transactions = list(transactions)

    record = {
        "date": date,
        "type": ttype,
        "record_number": _next_record_number(transactions),
        "ticker": ticker,
        "shares": float(shares),
        "price": float(price),
    }

    # Simulate applying the transaction to check I4/I5
    preview = list(transactions) + [record]
    simulated = build_portfolio(date, preview)
    cash = simulated.get(CASH_TICKER, 0.0)
    if cash < -1e-9:
        raise ValueError(
            f"transaction would leave cash at {cash:.2f} (< 0)"
        )
    for t, s in simulated.items():
        if t != CASH_TICKER and s < -1e-9:
            raise ValueError(
                f"transaction would leave {t} at {s:.4f} shares (< 0)"
            )

    transactions.append(record)
    if persist:
        save_transactions(transactions)
    return record


# ------------------------------------------------------------------
# Quick self-test driver
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("loading ledger ...")
    tx = load_transactions()
    print(f"  {len(tx)} existing records")

    # 1) list_transactions_for_ticker
    aapl = list_transactions_for_ticker("AAPL", tx)
    print(f"\nAAPL transactions: {len(aapl)}")
    for t in aapl[:3]:
        print(" ", t)
    if len(aapl) > 3:
        print(f"  ... ({len(aapl)-3} more)")

    # 2) get_cash_balance
    as_of = "2025-01-31"
    cash = get_cash_balance(as_of, tx)
    print(f"\ncash balance as of {as_of}: {cash:,.2f}")

    # 3) build_portfolio
    pf = build_portfolio(as_of, tx)
    print(f"\nportfolio as of {as_of}: {len(pf)} positions")
    for t, s in list(pf.items())[:5]:
        print(f"  {t}: {s}")
    if len(pf) > 5:
        print(f"  ... ({len(pf)-5} more)")

    # 4) create_transaction - dry run (do not persist, do not check
    # price because we are generating a synthetic one)
    print("\ncreate_transaction dry run (BUY 10 AAPL on 2025-01-02):")
    try:
        new_rec = create_transaction(
            date="2025-01-02",
            type="BUY",
            ticker="AAPL",
            shares=10,
            price=243.85,
            transactions=tx,
            persist=False,
        )
        print("  OK:", new_rec)
    except ValueError as e:
        print("  ValueError:", e)

    # 5) create_transaction - must reject a bad date
    print("\ncreate_transaction with invalid date (should fail):")
    try:
        create_transaction(
            date="2099-12-31",
            type="BUY",
            ticker="AAPL",
            shares=10,
            price=243.85,
            transactions=tx,
            persist=False,
        )
        print("  UNEXPECTED: did not raise")
    except ValueError as e:
        print("  ValueError (expected):", e)

    # 6) create_transaction - must reject a bad ticker
    print("\ncreate_transaction with invalid ticker (should fail):")
    try:
        create_transaction(
            date="2025-01-02",
            type="BUY",
            ticker="ZZZZ",
            shares=10,
            price=100.0,
            transactions=tx,
            persist=False,
        )
        print("  UNEXPECTED: did not raise")
    except ValueError as e:
        print("  ValueError (expected):", e)

    # 7) create_transaction - must reject a price outside +-15%
    print("\ncreate_transaction with out-of-band price (should fail):")
    try:
        create_transaction(
            date="2025-01-02",
            type="BUY",
            ticker="AAPL",
            shares=10,
            price=50.0,  # far below source of truth
            transactions=tx,
            persist=False,
        )
        print("  UNEXPECTED: did not raise")
    except ValueError as e:
        print("  ValueError (expected):", e)

    # 8) create_transaction - must reject a buy that would overdraft cash
    print("\ncreate_transaction that would overdraft cash (should fail):")
    try:
        create_transaction(
            date="2025-01-02",
            type="BUY",
            ticker="AAPL",
            shares=1_000_000,
            price=243.85,
            transactions=tx,
            persist=False,
        )
        print("  UNEXPECTED: did not raise")
    except ValueError as e:
        print("  ValueError (expected):", e)

    # 9) create_transaction - must reject a sell that would go short
    print("\ncreate_transaction that would sell more than we own (should fail):")
    try:
        create_transaction(
            date="2025-01-31",
            type="SELL",
            ticker="AAPL",
            shares=10_000_000,
            price=236.0,
            transactions=tx,
            persist=False,
        )
        print("  UNEXPECTED: did not raise")
    except ValueError as e:
        print("  ValueError (expected):", e)

    print("\nself-test finished.")
