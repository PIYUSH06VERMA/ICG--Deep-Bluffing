"""
evaluator.py
------------
Pure-Python 7-card hand evaluator (2 hole cards + 5 community cards).

No external poker libraries are used (per the assignment's constraints).
Only `itertools` and `collections.Counter` from the standard library are
used, exactly as suggested in the project's Research Board.

The public entry point is `best_hand_rank(cards)`, which takes a list of
7 `Card` objects and returns a tuple:

    (category, tiebreak_1, tiebreak_2, ...)

Tuples compare lexicographically, so `best_hand_rank(a) > best_hand_rank(b)`
is a correct and total ordering of poker hand strength -- higher is better.

Category values (higher = stronger):
    8  Straight Flush (includes Royal Flush, A-high straight flush)
    7  Four of a Kind
    6  Full House
    5  Flush
    4  Straight
    3  Three of a Kind
    2  Two Pair
    1  One Pair
    0  High Card
"""

from itertools import combinations
from collections import Counter

STRAIGHT_FLUSH, FOUR_KIND, FULL_HOUSE, FLUSH, STRAIGHT, \
    THREE_KIND, TWO_PAIR, ONE_PAIR, HIGH_CARD = range(8, -1, -1)


def _straight_high(sorted_unique_ranks_desc):
    """
    Given a list of unique ranks sorted descending, return the high card
    of the best straight found, or None if no straight exists.
    Handles the wheel straight (A-5-4-3-2) where Ace plays low.
    """
    ranks = sorted_unique_ranks_desc
    # Handle wheel: A,5,4,3,2 -> treat Ace (14) as 1 as well.
    candidates = set(ranks)
    if 14 in candidates:
        candidates.add(1)

    candidates = sorted(candidates, reverse=True)
    consecutive = 1
    best_high = None
    for i in range(1, len(candidates)):
        if candidates[i] == candidates[i - 1] - 1:
            consecutive += 1
            if consecutive >= 5:
                # The high card of this straight is 5 positions back.
                high = candidates[i - 4]
                best_high = high if best_high is None else max(best_high, high)
        else:
            consecutive = 1
    return best_high


def _evaluate_5(cards):
    """Evaluate exactly 5 Card objects and return a comparable rank tuple."""
    ranks = sorted((c.rank for c in cards), reverse=True)
    suits = [c.suit for c in cards]
    rank_counts = Counter(ranks)
    # Group ranks by how many times they appear, e.g. {2: [7], 1: [13, 9, 4]}
    by_count = {}
    for rank, count in rank_counts.items():
        by_count.setdefault(count, []).append(rank)
    for count in by_count:
        by_count[count].sort(reverse=True)

    is_flush = len(set(suits)) == 1
    unique_ranks_desc = sorted(set(ranks), reverse=True)
    straight_high = _straight_high(unique_ranks_desc)

    if is_flush and straight_high is not None:
        return (STRAIGHT_FLUSH, straight_high)

    if 4 in by_count:
        quad = by_count[4][0]
        kicker = max(r for r in ranks if r != quad)
        return (FOUR_KIND, quad, kicker)

    if 3 in by_count and 2 in by_count:
        trips = by_count[3][0]
        pair = by_count[2][0]
        return (FULL_HOUSE, trips, pair)

    if 3 in by_count and len(by_count[3]) >= 2:
        # Two triples in 5 cards is impossible, kept for safety only.
        trips = by_count[3][0]
        pair = by_count[3][1]
        return (FULL_HOUSE, trips, pair)

    if is_flush:
        return (FLUSH, *ranks)

    if straight_high is not None:
        return (STRAIGHT, straight_high)

    if 3 in by_count:
        trips = by_count[3][0]
        kickers = sorted((r for r in ranks if r != trips), reverse=True)
        return (THREE_KIND, trips, *kickers)

    if 2 in by_count and len(by_count[2]) >= 2:
        pairs = sorted(by_count[2], reverse=True)[:2]
        kicker = max(r for r in ranks if r not in pairs)
        return (TWO_PAIR, pairs[0], pairs[1], kicker)

    if 2 in by_count:
        pair = by_count[2][0]
        kickers = sorted((r for r in ranks if r != pair), reverse=True)
        return (ONE_PAIR, pair, *kickers)

    return (HIGH_CARD, *ranks)


def best_hand_rank_bruteforce(cards):
    """
    Reference/verification implementation: tries every 5-card subset of the
    given 6 or 7 cards via itertools.combinations (as suggested in the
    project's Research Board) and returns the strongest resulting hand.
    This is correct but O(C(7,5)) = 21x slower than `best_hand_rank`, so it
    is kept around purely to unit-test the optimized evaluator below
    (see test_evaluator.py) rather than for use inside the hot betting loop.
    """
    if len(cards) < 5:
        raise ValueError("Need at least 5 cards to evaluate a poker hand")
    if len(cards) == 5:
        return _evaluate_5(cards)
    best = None
    for combo in combinations(cards, 5):
        r = _evaluate_5(combo)
        if best is None or r > best:
            best = r
    return best


def best_hand_rank(cards):
    """
    cards: list of 5, 6, or 7 Card objects (hole + community).
    Returns the best achievable 5-card rank tuple.

    This is an O(n) direct-counting evaluator (n = len(cards) <= 7), used
    instead of the O(C(n,5)) brute-force combinations approach because the
    Monte Carlo rollouts in agent.py call this function tens of thousands
    of times per hand and must run fast enough for a 10,000-hand
    tournament. Correctness is verified against `best_hand_rank_bruteforce`
    in test_evaluator.py across thousands of random hands.
    """
    if len(cards) < 5:
        raise ValueError("Need at least 5 cards to evaluate a poker hand")
    if len(cards) == 5:
        return _evaluate_5(cards)

    ranks = [c.rank for c in cards]
    suits = [c.suit for c in cards]
    suit_counts = Counter(suits)
    rank_counts = Counter(ranks)

    by_count = {}
    for rank, count in rank_counts.items():
        by_count.setdefault(count, []).append(rank)
    for count in by_count:
        by_count[count].sort(reverse=True)

    # --- Straight flush / Flush -------------------------------------------------
    flush_suit = None
    for s, cnt in suit_counts.items():
        if cnt >= 5:
            flush_suit = s
            break

    if flush_suit is not None:
        flush_ranks = sorted({c.rank for c in cards if c.suit == flush_suit}, reverse=True)
        sf_high = _straight_high(flush_ranks)
        if sf_high is not None:
            return (STRAIGHT_FLUSH, sf_high)

    # --- Four of a Kind -----------------------------------------------------
    if 4 in by_count:
        quad = by_count[4][0]
        kicker = max(r for r in ranks if r != quad)
        return (FOUR_KIND, quad, kicker)

    trips_list = sorted(by_count.get(3, []), reverse=True)
    pairs_list = sorted(by_count.get(2, []), reverse=True)

    # --- Full House -----------------------------------------------------------
    if trips_list:
        if len(trips_list) >= 2:
            return (FULL_HOUSE, trips_list[0], trips_list[1])
        if pairs_list:
            return (FULL_HOUSE, trips_list[0], pairs_list[0])

    # --- Flush (non-straight) --------------------------------------------------
    if flush_suit is not None:
        flush_ranks = sorted((c.rank for c in cards if c.suit == flush_suit), reverse=True)[:5]
        return (FLUSH, *flush_ranks)

    # --- Straight ---------------------------------------------------------------
    unique_ranks_desc = sorted(set(ranks), reverse=True)
    straight_high = _straight_high(unique_ranks_desc)
    if straight_high is not None:
        return (STRAIGHT, straight_high)

    # --- Three of a Kind ----------------------------------------------------
    if trips_list:
        trips = trips_list[0]
        kickers = sorted((r for r in ranks if r != trips), reverse=True)[:2]
        return (THREE_KIND, trips, *kickers)

    # --- Two Pair / One Pair --------------------------------------------------
    if len(pairs_list) >= 2:
        top_two = pairs_list[:2]
        kicker = max(r for r in ranks if r not in top_two)
        return (TWO_PAIR, top_two[0], top_two[1], kicker)

    if len(pairs_list) == 1:
        pair = pairs_list[0]
        kickers = sorted((r for r in ranks if r != pair), reverse=True)[:3]
        return (ONE_PAIR, pair, *kickers)

    # --- High Card ------------------------------------------------------------
    return (HIGH_CARD, *unique_ranks_desc[:5])


CATEGORY_NAMES = {
    STRAIGHT_FLUSH: "Straight Flush",
    FOUR_KIND: "Four of a Kind",
    FULL_HOUSE: "Full House",
    FLUSH: "Flush",
    STRAIGHT: "Straight",
    THREE_KIND: "Three of a Kind",
    TWO_PAIR: "Two Pair",
    ONE_PAIR: "One Pair",
    HIGH_CARD: "High Card",
}


def describe(rank_tuple):
    """Human readable description of a rank tuple, useful for debugging/logs."""
    return CATEGORY_NAMES[rank_tuple[0]]


def compare_hands(cards_a, cards_b):
    """
    Returns 1 if hand A wins, -1 if hand B wins, 0 if it's a tie (split pot).
    """
    ra, rb = best_hand_rank(cards_a), best_hand_rank(cards_b)
    if ra > rb:
        return 1
    if rb > ra:
        return -1
    return 0
