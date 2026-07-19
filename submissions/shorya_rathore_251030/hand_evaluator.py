"""
Hand evaluator for HULHE poker engine.

Depends on cards.py (Card class).

Public API:
    evaluate_hand(cards)          -> best 5-card score tuple from any number (5,6,7) of Card objects
    compare_hands(score_a, score_b) -> 1 if a wins, -1 if b wins, 0 if tie
    HAND_NAMES                    -> dict mapping category int -> human-readable name

Score representation:
    A hand's strength is represented as a tuple:
        (category, tiebreak_1, tiebreak_2, ...)
    where `category` is 0-9 (9 = royal/straight flush ... 0 = high card... see HAND_CATEGORIES)
    and the tiebreak values are rank values (2-14) in the order that decides ties,
    e.g. for two pair: (pair1_rank, pair2_rank, kicker_rank).

    Tuples compare correctly with normal Python tuple comparison (>, <, ==),
    which naturally handles kickers because tuples compare element by element.
"""

from itertools import combinations
from collections import Counter

from cards import Card  # your Card class from cards.py

# ---- Hand category constants (higher = stronger) ----------------------
HIGH_CARD = 0
ONE_PAIR = 1
TWO_PAIR = 2
THREE_OF_A_KIND = 3
STRAIGHT = 4
FLUSH = 5
FULL_HOUSE = 6
FOUR_OF_A_KIND = 7
STRAIGHT_FLUSH = 8
ROYAL_FLUSH = 9  # special case of straight flush (ace-high), scored same as SF

HAND_NAMES = {
    HIGH_CARD: "High Card",
    ONE_PAIR: "One Pair",
    TWO_PAIR: "Two Pair",
    THREE_OF_A_KIND: "Three of a Kind",
    STRAIGHT: "Straight",
    FLUSH: "Flush",
    FULL_HOUSE: "Full House",
    FOUR_OF_A_KIND: "Four of a Kind",
    STRAIGHT_FLUSH: "Straight Flush",
    ROYAL_FLUSH: "Royal Flush",
}


def _rank_counts_desc(values):
    """
    Given a list of rank values (ints), return list of (rank, count) sorted by:
    count desc, then rank desc. E.g. for a full house AAA88 -> [(14,3), (8,2)]
    """
    counter = Counter(values)
    return sorted(counter.items(), key=lambda item: (-item[1], -item[0]))


def _straight_high(values):
    """
    Given a set of unique rank values present in the 5-card hand, return the
    high card of the straight if one exists, else None.
    Handles the wheel straight (A-2-3-4-5) where Ace counts as 1 (high=5).
    """
    unique_vals = sorted(set(values), reverse=True)

    # Special-case: wheel (A,2,3,4,5) -- Ace plays low
    if {14, 2, 3, 4, 5}.issubset(unique_vals):
        # check the rest normally too, but ensure wheel is considered
        pass

    # Check standard 5-consecutive run within unique_vals
    for i in range(len(unique_vals) - 4):
        window = unique_vals[i:i + 5]
        if window[0] - window[4] == 4:
            return window[0]  # high card of the straight

    # Check wheel explicitly (A-2-3-4-5), straight high = 5
    if {14, 2, 3, 4, 5}.issubset(set(unique_vals)):
        return 5

    return None


def score_five_card_hand(cards):
    """
    Score EXACTLY 5 Card objects. Returns a tuple (category, tiebreakers...).
    """
    if len(cards) != 5:
        raise ValueError("score_five_card_hand requires exactly 5 cards")

    values = [c.value for c in cards]
    suits = [c.suit for c in cards]

    is_flush = len(set(suits)) == 1
    straight_high = _straight_high(values)

    rank_counts = _rank_counts_desc(values)   # e.g. [(14,3),(8,2)] for full house
    counts_pattern = [count for _, count in rank_counts]

    # --- Straight flush / Royal flush ---
    if is_flush and straight_high is not None:
        category = ROYAL_FLUSH if straight_high == 14 else STRAIGHT_FLUSH
        return (STRAIGHT_FLUSH, straight_high)  # royal is just the top straight flush

    # --- Four of a kind ---
    if counts_pattern[0] == 4:
        quad_rank = rank_counts[0][0]
        kicker = rank_counts[1][0]
        return (FOUR_OF_A_KIND, quad_rank, kicker)

    # --- Full house ---
    if counts_pattern[0] == 3 and counts_pattern[1] == 2:
        trip_rank = rank_counts[0][0]
        pair_rank = rank_counts[1][0]
        return (FULL_HOUSE, trip_rank, pair_rank)

    # --- Flush ---
    if is_flush:
        kickers = sorted(values, reverse=True)
        return (FLUSH, *kickers)

    # --- Straight ---
    if straight_high is not None:
        return (STRAIGHT, straight_high)

    # --- Three of a kind ---
    if counts_pattern[0] == 3:
        trip_rank = rank_counts[0][0]
        kickers = sorted([r for r, c in rank_counts if c == 1], reverse=True)
        return (THREE_OF_A_KIND, trip_rank, *kickers)

    # --- Two pair ---
    if counts_pattern[0] == 2 and counts_pattern[1] == 2:
        pair_ranks = sorted([r for r, c in rank_counts if c == 2], reverse=True)
        kicker = [r for r, c in rank_counts if c == 1][0]
        return (TWO_PAIR, pair_ranks[0], pair_ranks[1], kicker)

    # --- One pair ---
    if counts_pattern[0] == 2:
        pair_rank = rank_counts[0][0]
        kickers = sorted([r for r, c in rank_counts if c == 1], reverse=True)
        return (ONE_PAIR, pair_rank, *kickers)

    # --- High card ---
    kickers = sorted(values, reverse=True)
    return (HIGH_CARD, *kickers)


def evaluate_hand(cards):
    """
    Given ANY number of Card objects >= 5 (typically 7: 2 hole + 5 community),
    return the BEST possible 5-card score tuple.
    """
    if len(cards) < 5:
        raise ValueError("Need at least 5 cards to evaluate a hand")

    best_score = None
    for combo in combinations(cards, 5):
        score = score_five_card_hand(list(combo))
        if best_score is None or score > best_score:
            best_score = score

    return best_score


def compare_hands(score_a, score_b):
    """
    Compare two score tuples (from evaluate_hand).
    Returns:
         1 if score_a wins
        -1 if score_b wins
         0 if tie (split pot)
    """
    if score_a > score_b:
        return 1
    elif score_a < score_b:
        return -1
    return 0


def hand_category_name(score):
    """Human-readable name for a score tuple, e.g. 'Full House'."""
    return HAND_NAMES[score[0]]


if __name__ == "__main__":
    # ---- sanity tests against known hands ----

    def make(cards_strs):
        return Card.parse_list(cards_strs)

    tests = []

    # Royal flush vs straight flush
    royal = evaluate_hand(make(['Ah', 'Kh', 'Qh', 'Jh', 'Th', '2d', '3c']))
    sflush = evaluate_hand(make(['9h', '8h', '7h', '6h', '5h', '2d', '3c']))
    print("Royal flush score:", royal, hand_category_name(royal))
    print("Straight flush score:", sflush, hand_category_name(sflush))
    assert compare_hands(royal, sflush) == 1

    # Quads vs full house
    quads = evaluate_hand(make(['7h', '7d', '7s', '7c', '2d', '2h', '3c']))
    boat = evaluate_hand(make(['Kh', 'Kd', 'Ks', 'Qd', 'Qh', '2d', '3c']))
    print("Quads:", quads, hand_category_name(quads))
    print("Full house:", boat, hand_category_name(boat))
    assert compare_hands(quads, boat) == 1

    # Wheel straight (A-2-3-4-5)
    wheel = evaluate_hand(make(['Ah', '2d', '3s', '4c', '5h', 'Kd', 'Qc']))
    print("Wheel straight:", wheel, hand_category_name(wheel))
    assert wheel[0] == STRAIGHT and wheel[1] == 5

    # Two pair kicker tie-break
    tp1 = evaluate_hand(make(['Ah', 'Ad', 'Kh', 'Kd', '2c', '3d', '4h']))  # AA KK 4 kicker
    tp2 = evaluate_hand(make(['Ah', 'Ad', 'Kh', 'Kd', '2c', '3d', '9h']))  # AA KK 9 kicker
    print("Two pair (4 kicker):", tp1)
    print("Two pair (9 kicker):", tp2)
    assert compare_hands(tp1, tp2) == -1  # tp2 wins on kicker

    # Exact tie -> split pot
    h1 = evaluate_hand(make(['Ah', 'Kd', '7c', '7d', '2s', '3h', '4c']))
    h2 = evaluate_hand(make(['As', 'Kc', '7h', '7s', '2d', '3c', '4d']))
    print("Tie test:", h1, h2)
    assert compare_hands(h1, h2) == 0

    # Flush vs straight
    flush = evaluate_hand(make(['2h', '5h', '9h', 'Jh', 'Kh', '3d', '4c']))
    straight = evaluate_hand(make(['5d', '6c', '7h', '8s', '9d', '2c', '3h']))
    assert compare_hands(flush, straight) == 1

    print("\nAll evaluator sanity tests passed!")
