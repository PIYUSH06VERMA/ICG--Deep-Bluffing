"""
hand_evaluator.py
-----------------
Pure Python, from-scratch poker hand evaluator. No external poker
libraries (treys, etc.) are used per the assignment constraints.

Core idea (quantization of hand strength into a numeric feature space):
Every 5-card hand is mapped to a tuple:

    (category, tiebreaker_1, tiebreaker_2, ...)

where `category` is an int 0-8 (0 = High Card ... 8 = Straight Flush)
and the tiebreaker tuple is ordered so that Python's native tuple
comparison (lexicographic) directly gives the correct poker ranking --
this is the "OOP magic" trick: we never need custom comparison logic,
we just build the right tuple and let >, <, == on tuples do the work.

For a 7-card hand (2 hole + 5 community), we use itertools.combinations
to enumerate all C(7,5) = 21 possible 5-card hands and keep the best one.
"""

import itertools
from collections import Counter

# Category constants (higher = stronger)
HIGH_CARD = 0
ONE_PAIR = 1
TWO_PAIR = 2
THREE_KIND = 3
STRAIGHT = 4
FLUSH = 5
FULL_HOUSE = 6
FOUR_KIND = 7
STRAIGHT_FLUSH = 8

CATEGORY_NAMES = {
    0: "High Card", 1: "One Pair", 2: "Two Pair", 3: "Three of a Kind",
    4: "Straight", 5: "Flush", 6: "Full House", 7: "Four of a Kind",
    8: "Straight Flush",
}


def _straight_high(values_desc_unique):
    """
    Given a sorted-descending list of *unique* card values (2-14),
    return the high card of the best straight found, else None.
    Handles the wheel (A-2-3-4-5, where Ace plays low -> high card 5).
    """
    vals = list(values_desc_unique)
    if 14 in vals:
        vals.append(1)  # allow Ace-low for wheel straight
    for i in range(len(vals) - 4):
        window = vals[i:i + 5]
        if window[0] - window[4] == 4:
            return window[0]
    return None


def evaluate_5(cards):
    """
    Evaluate exactly 5 Card objects.
    Returns a tuple (category, *tiebreakers) suitable for direct
    comparison against another evaluate_5() result.
    """
    values = sorted((c.value for c in cards), reverse=True)
    suits = [c.suit for c in cards]
    value_counts = Counter(values)

    is_flush = len(set(suits)) == 1
    unique_vals_desc = sorted(set(values), reverse=True)
    straight_high = _straight_high(unique_vals_desc)
    is_straight = straight_high is not None

    if is_straight and is_flush:
        return (STRAIGHT_FLUSH, straight_high)

    # Group ranks by frequency: e.g. {4:1, 9:2, ...} -> sort by (count, rank)
    groups = sorted(value_counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    counts = [g[1] for g in groups]
    ranks_by_group = [g[0] for g in groups]

    if counts[0] == 4:
        kicker = ranks_by_group[1]
        return (FOUR_KIND, ranks_by_group[0], kicker)

    if counts[0] == 3 and counts[1] == 2:
        return (FULL_HOUSE, ranks_by_group[0], ranks_by_group[1])

    if is_flush:
        return (FLUSH, *values)

    if is_straight:
        return (STRAIGHT, straight_high)

    if counts[0] == 3:
        kickers = sorted(ranks_by_group[1:], reverse=True)
        return (THREE_KIND, ranks_by_group[0], *kickers)

    if counts[0] == 2 and counts[1] == 2:
        pair_hi, pair_lo = sorted([ranks_by_group[0], ranks_by_group[1]], reverse=True)
        kicker = ranks_by_group[2]
        return (TWO_PAIR, pair_hi, pair_lo, kicker)

    if counts[0] == 2:
        kickers = sorted(ranks_by_group[1:], reverse=True)
        return (ONE_PAIR, ranks_by_group[0], *kickers)

    return (HIGH_CARD, *values)


def evaluate_best_hand_bruteforce(cards):
    """
    Reference / ground-truth implementation: enumerates every C(n,5)
    5-card combination via itertools.combinations and keeps the best.
    Correct but O(21) evaluate_5 calls for a 7-card hand -- kept around
    purely to validate the optimized evaluate_best_hand() below (see
    test_hand_evaluator.py) since brute force is easiest to trust.
    """
    if len(cards) < 5:
        raise ValueError("Need at least 5 cards to evaluate a hand.")
    if len(cards) == 5:
        return evaluate_5(cards)

    best = None
    for combo in itertools.combinations(cards, 5):
        score = evaluate_5(combo)
        if best is None or score > best:
            best = score
    return best


def evaluate_best_hand(cards):
    """
    Optimized best-of-N (5, 6, or 7 card) evaluator. Instead of scoring
    all C(7,5)=21 combinations, it directly derives the best 5-card hand
    from the aggregate rank/suit frequency counts of all N cards -- O(N)
    instead of O(C(n,5) * 5). This matters because the Monte-Carlo
    equity engine calls this thousands of times per decision, and the
    arena runs 10,000+ hands per matchup, so evaluation speed is on the
    critical path.

    Verified equivalent to evaluate_best_hand_bruteforce() by randomized
    cross-validation in test_hand_evaluator.py.
    """
    if len(cards) < 5:
        raise ValueError("Need at least 5 cards to evaluate a hand.")
    if len(cards) == 5:
        return evaluate_5(cards)

    values = [c.value for c in cards]
    suits = [c.suit for c in cards]
    suit_counts = Counter(suits)
    value_counts = Counter(values)

    groups = sorted(value_counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    counts = [g[1] for g in groups]
    ranks_by_group = [g[0] for g in groups]

    # --- Flush / straight-flush check ---
    flush_suit = next((s for s, cnt in suit_counts.items() if cnt >= 5), None)
    flush_hand = None
    if flush_suit is not None:
        flush_values = sorted({c.value for c in cards if c.suit == flush_suit}, reverse=True)
        sf_high = _straight_high(flush_values)
        if sf_high is not None:
            return (STRAIGHT_FLUSH, sf_high)
        flush_hand = tuple(flush_values[:5])

    # --- Four of a kind ---
    if counts[0] == 4:
        quad_rank = ranks_by_group[0]
        kicker = max(v for v in values if v != quad_rank)
        return (FOUR_KIND, quad_rank, kicker)

    # --- Full house (trips + best available pair, incl. a second trip) ---
    if counts[0] == 3 and counts[1] >= 2:
        return (FULL_HOUSE, ranks_by_group[0], ranks_by_group[1])

    # --- Flush ---
    if flush_hand is not None:
        return (FLUSH, *flush_hand)

    # --- Straight ---
    unique_vals_desc = sorted(set(values), reverse=True)
    straight_high = _straight_high(unique_vals_desc)
    if straight_high is not None:
        return (STRAIGHT, straight_high)

    # --- Three of a kind ---
    if counts[0] == 3:
        trip_rank = ranks_by_group[0]
        kickers = sorted((v for v in values if v != trip_rank), reverse=True)[:2]
        return (THREE_KIND, trip_rank, *kickers)

    # --- Two pair (best two pairs among possibly 3 pairs in 7 cards) ---
    if counts[0] == 2 and counts[1] == 2:
        pair_hi, pair_lo = sorted([ranks_by_group[0], ranks_by_group[1]], reverse=True)
        kicker = max(v for v in values if v != pair_hi and v != pair_lo)
        return (TWO_PAIR, pair_hi, pair_lo, kicker)

    # --- One pair ---
    if counts[0] == 2:
        pair_rank = ranks_by_group[0]
        kickers = sorted((v for v in values if v != pair_rank), reverse=True)[:3]
        return (ONE_PAIR, pair_rank, *kickers)

    # --- High card ---
    return (HIGH_CARD, *sorted(values, reverse=True)[:5])


def describe(score_tuple):
    """Human-readable label for a score tuple, e.g. 'Full House'."""
    return CATEGORY_NAMES[score_tuple[0]]


def compare_hands(cards_a, cards_b):
    """
    Returns 1 if hand A wins, -1 if hand B wins, 0 if it's a tie
    (split pot per the 50/50 tie rule).
    """
    score_a = evaluate_best_hand(cards_a)
    score_b = evaluate_best_hand(cards_b)
    if score_a > score_b:
        return 1
    if score_b > score_a:
        return -1
    return 0