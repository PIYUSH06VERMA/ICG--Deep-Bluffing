"""
evaluator.py
------------
Standard-deck poker hand evaluation, built only from itertools + collections
(no external poker libraries, per the assignment constraints).

Public API
----------
best_hand_rank(cards: list[Card]) -> tuple
    `cards` may contain 5, 6, or 7 Card objects (hole + community).
    Returns a tuple that can be compared with > / < / == : a *strictly*
    larger tuple means a strictly stronger poker hand. Equal tuples mean
    an exact tie (including kickers) -> split pot.

compare_hands(cards_a, cards_b) -> int
    Convenience wrapper: +1 if a wins, -1 if b wins, 0 if a tie.

The rank tuple format is:
    (category, tiebreak_1, tiebreak_2, ...)
where `category` is an int 0-8 (8 = straight flush ... 0 = high card),
chosen so that plain tuple comparison in Python does the right thing.
"""

from itertools import combinations
from collections import Counter

# Category codes (higher = better)
STRAIGHT_FLUSH = 8
FOUR_OF_A_KIND = 7
FULL_HOUSE = 6
FLUSH = 5
STRAIGHT = 4
THREE_OF_A_KIND = 3
TWO_PAIR = 2
ONE_PAIR = 1
HIGH_CARD = 0

CATEGORY_NAMES = {
    8: "Straight Flush", 7: "Four of a Kind", 6: "Full House", 5: "Flush",
    4: "Straight", 3: "Three of a Kind", 2: "Two Pair", 1: "One Pair", 0: "High Card",
}


def _straight_high(sorted_unique_values_desc):
    """Given distinct card values sorted descending, return the high card of
    the best straight found, or None. Handles the wheel (A-2-3-4-5 -> high=5)."""
    vals = sorted_unique_values_desc
    # Ace can also count as 1 for the wheel straight.
    if 14 in vals:
        vals = vals + [1]
    for i in range(len(vals) - 4):
        window = vals[i:i + 5]
        if window[0] - window[4] == 4 and len(set(window)) == 5:
            return window[0]
    return None


def rank_5card_hand(cards):
    """Rank exactly 5 Card objects. Returns a comparable tuple."""
    values = sorted((c.value for c in cards), reverse=True)
    suits = [c.suit for c in cards]
    value_counts = Counter(values)
    # groups sorted by (count, value) descending -> handles kicker ordering
    groups = sorted(value_counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    group_values = [v for v, _ in groups]

    is_flush = len(set(suits)) == 1
    straight_high = _straight_high(sorted(set(values), reverse=True))
    is_straight = straight_high is not None

    if is_straight and is_flush:
        return (STRAIGHT_FLUSH, straight_high)
    if groups[0][1] == 4:
        kicker = max(v for v in values if v != group_values[0])
        return (FOUR_OF_A_KIND, group_values[0], kicker)
    if groups[0][1] == 3 and groups[1][1] == 2:
        return (FULL_HOUSE, group_values[0], group_values[1])
    if is_flush:
        return (FLUSH, *values)
    if is_straight:
        return (STRAIGHT, straight_high)
    if groups[0][1] == 3:
        kickers = sorted((v for v in values if v != group_values[0]), reverse=True)
        return (THREE_OF_A_KIND, group_values[0], *kickers)
    if groups[0][1] == 2 and groups[1][1] == 2:
        pair_hi, pair_lo = sorted([group_values[0], group_values[1]], reverse=True)
        kicker = max(v for v in values if v != pair_hi and v != pair_lo)
        return (TWO_PAIR, pair_hi, pair_lo, kicker)
    if groups[0][1] == 2:
        kickers = sorted((v for v in values if v != group_values[0]), reverse=True)
        return (ONE_PAIR, group_values[0], *kickers)
    return (HIGH_CARD, *values)


def best_hand_rank(cards):
    """Best 5-card rank achievable from 5, 6, or 7 cards."""
    if len(cards) < 5:
        raise ValueError("Need at least 5 cards to rank a poker hand")
    if len(cards) == 5:
        return rank_5card_hand(cards)
    return max(rank_5card_hand(list(combo)) for combo in combinations(cards, 5))


def compare_hands(cards_a, cards_b):
    ra, rb = best_hand_rank(cards_a), best_hand_rank(cards_b)
    if ra > rb:
        return 1
    if rb > ra:
        return -1
    return 0


def describe(rank_tuple):
    """Human-readable label for a rank tuple, e.g. 'Full House'."""
    return CATEGORY_NAMES[rank_tuple[0]]


# -----------------------------------------------------------------------
# Fast single-pass evaluator for exactly 7 (value, suit) tuples.
#
# `best_hand_rank` above is the simple, obviously-correct reference
# implementation (enumerate all C(7,5)=21 five-card hands and take the
# max). It is used by the engine for the one showdown per hand.
#
# `fast_rank7` below computes the same rank tuple in a single O(7) pass
# without enumerating combinations, so it is used inside the Monte-Carlo
# equity rollouts in agent.py, which call the evaluator thousands of times
# per hand. Its output is verified identical to `best_hand_rank` by an
# exhaustive randomised test in test_engine.py.
# -----------------------------------------------------------------------
def fast_rank7(value_suit_pairs):
    """value_suit_pairs: iterable of 7 (value:int 2-14, suit:str) tuples."""
    values = [v for v, s in value_suit_pairs]
    suit_counts = Counter(s for v, s in value_suit_pairs)

    flush_suit = None
    for s, cnt in suit_counts.items():
        if cnt >= 5:
            flush_suit = s
            break

    if flush_suit is not None:
        flush_values_desc = sorted({v for v, s in value_suit_pairs if s == flush_suit}, reverse=True)
        sf_high = _straight_high(flush_values_desc)
        if sf_high is not None:
            return (STRAIGHT_FLUSH, sf_high)

    value_counts = Counter(values)
    # (count, value) sorted by count desc, then value desc
    groups = sorted(((cnt, val) for val, cnt in value_counts.items()), reverse=True)

    if groups[0][0] == 4:
        four_val = groups[0][1]
        kicker = max(v for v in values if v != four_val)
        return (FOUR_OF_A_KIND, four_val, kicker)

    if groups[0][0] == 3:
        pair_val = next((val for cnt, val in groups[1:] if cnt >= 2), None)
        if pair_val is not None:
            return (FULL_HOUSE, groups[0][1], pair_val)

    if flush_suit is not None:
        flush_values = sorted((v for v, s in value_suit_pairs if s == flush_suit), reverse=True)[:5]
        return (FLUSH, *flush_values)

    straight_high = _straight_high(sorted(set(values), reverse=True))
    if straight_high is not None:
        return (STRAIGHT, straight_high)

    if groups[0][0] == 3:
        trips_val = groups[0][1]
        kickers = sorted((v for v in values if v != trips_val), reverse=True)[:2]
        return (THREE_OF_A_KIND, trips_val, *kickers)

    if groups[0][0] == 2:
        pairs = sorted((val for cnt, val in groups if cnt == 2), reverse=True)
        if len(pairs) >= 2:
            hi, lo = pairs[0], pairs[1]
            kicker = max(v for v in values if v != hi and v != lo)
            return (TWO_PAIR, hi, lo, kicker)
        hi = pairs[0]
        kickers = sorted((v for v in values if v != hi), reverse=True)[:3]
        return (ONE_PAIR, hi, *kickers)

    return (HIGH_CARD, *sorted(values, reverse=True)[:5])
