"""
evaluator.py
------------
From-scratch poker hand evaluator (no external poker libraries).

Public API:
    best_hand_rank(cards)      -> tuple, comparable, higher = stronger
    compare_hands(a_cards, b_cards) -> 1 if a wins, -1 if b wins, 0 if tie
    hand_category_name(rank_tuple) -> human readable name

Design notes
------------
A naive implementation evaluates all C(7,5)=21 five-card subsets and takes
the max. That is correct (a reference version of exactly that approach,
`evaluator_slow_reference.py`, was used during development to cross-check
this one -- see `test_evaluator.py`), but it is ~21x more work than
necessary, and it became the dominant cost of the Monte-Carlo rollouts
used by the bot's equity engine (equity.py), since a single decision can
run hundreds of rollout iterations, each requiring two 7-card evaluations.

Instead, this module evaluates the best 5-card hand out of up to 7 cards
directly, in a small constant number of passes:
    1. Count values (collections.Counter) and suits.
    2. Straight-flush check: if a suit has >=5 cards, look for 5
       consecutive ranks within that suit (including the wheel, A-2-3-4-5).
    3. Quads -> Full House -> Flush -> Straight -> Trips -> Two Pair ->
       One Pair -> High Card, tested in strict descending hand-strength
       order so the first category that matches is the correct one.

Every branch returns a tuple (category, tiebreak_1, tiebreak_2, ...).
Python's native tuple comparison then implements kicker rules for free:
higher category always wins; within a category, tiebreakers are compared
left-to-right exactly as poker kicker rules require.
"""

from collections import Counter

from card import Card, parse_cards

# Category indices: bigger = stronger hand.
HIGH_CARD, ONE_PAIR, TWO_PAIR, TRIPS, STRAIGHT, FLUSH, FULL_HOUSE, QUADS, STRAIGHT_FLUSH = range(9)

HAND_NAMES = {
    HIGH_CARD: "High Card",
    ONE_PAIR: "One Pair",
    TWO_PAIR: "Two Pair",
    TRIPS: "Three of a Kind",
    STRAIGHT: "Straight",
    FLUSH: "Flush",
    FULL_HOUSE: "Full House",
    QUADS: "Four of a Kind",
    STRAIGHT_FLUSH: "Straight Flush",
}


def _straight_high(unique_vals_desc):
    """unique_vals_desc: distinct card values, sorted descending.
    Returns the high card of the best 5-consecutive run, else None.
    Handles the wheel (A-2-3-4-5, where the Ace plays low)."""
    s = set(unique_vals_desc)
    for high in unique_vals_desc:
        if high >= 6 and all((high - i) in s for i in range(5)):
            return high
        if high == 5 and all(v in s for v in (5, 4, 3, 2)) and 14 in s:
            return 5  # wheel: A-2-3-4-5
    return None


def best_hand_rank(cards):
    """cards: iterable of Card objects or raw code strings, length 5..7.
    Returns the best achievable 5-card rank tuple as (category, *tiebreaks).
    """
    cards = parse_cards(cards)
    if len(cards) < 5:
        raise ValueError("Need at least 5 cards to evaluate a poker hand.")

    pairs = sorted(((c.value, c.suit) for c in cards), reverse=True)
    values = [v for v, _ in pairs]
    value_counts = Counter(values)
    suit_counts = Counter(s for _, s in pairs)

    # ---- Straight flush -------------------------------------------------
    flush_suit = next((s for s, cnt in suit_counts.items() if cnt >= 5), None)
    if flush_suit is not None:
        flush_vals_desc = sorted({v for v, s in pairs if s == flush_suit}, reverse=True)
        sf_high = _straight_high(flush_vals_desc)
        if sf_high is not None:
            return (STRAIGHT_FLUSH, sf_high)

    by_count = sorted(value_counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)

    # ---- Four of a Kind ---------------------------------------------------
    if by_count[0][1] == 4:
        quad_val = by_count[0][0]
        kicker = max(v for v in values if v != quad_val)
        return (QUADS, quad_val, kicker)

    # ---- Full House (trips + a pair, or trips + a second trips) --------
    if by_count[0][1] == 3:
        trips_val = by_count[0][0]
        pair_candidates = [v for v, c in by_count[1:] if c >= 2]
        if pair_candidates:
            pair_val = max(pair_candidates)
            return (FULL_HOUSE, trips_val, pair_val)

    # ---- Flush --------------------------------------------------------
    if flush_suit is not None:
        flush_vals_desc = sorted({v for v, s in pairs if s == flush_suit}, reverse=True)[:5]
        return (FLUSH, *flush_vals_desc)

    # ---- Straight -------------------------------------------------------
    unique_vals_desc = sorted(value_counts.keys(), reverse=True)
    straight_hi = _straight_high(unique_vals_desc)
    if straight_hi is not None:
        return (STRAIGHT, straight_hi)

    # ---- Trips (no full house available) --------------------------------
    if by_count[0][1] == 3:
        trips_val = by_count[0][0]
        kickers = sorted((v for v in values if v != trips_val), reverse=True)[:2]
        return (TRIPS, trips_val, *kickers)

    # ---- Two Pair / One Pair --------------------------------------------
    pair_vals = sorted((v for v, c in by_count if c == 2), reverse=True)
    if len(pair_vals) >= 2:
        top2 = pair_vals[:2]
        kicker = max(v for v in values if v not in top2)
        return (TWO_PAIR, top2[0], top2[1], kicker)
    if len(pair_vals) == 1:
        pair_val = pair_vals[0]
        kickers = sorted((v for v in values if v != pair_val), reverse=True)[:3]
        return (ONE_PAIR, pair_val, *kickers)

    # ---- High Card --------------------------------------------------------
    return (HIGH_CARD, *values[:5])


def compare_hands(cards_a, cards_b):
    ra, rb = best_hand_rank(cards_a), best_hand_rank(cards_b)
    if ra > rb:
        return 1
    if rb > ra:
        return -1
    return 0


def hand_category_name(rank_tuple):
    return HAND_NAMES[rank_tuple[0]]
