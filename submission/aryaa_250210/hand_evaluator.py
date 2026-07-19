"""
hand_evaluator.py
------------------
The core "engine math" file. Given any 5 cards, it scores the hand.
Given any 7 cards (2 hole + 5 community), it finds the BEST possible 5-card hand.

Scoring approach:
Every hand is converted into a tuple like (category, tiebreak1, tiebreak2, ...).
Python compares tuples element-by-element automatically, so:
    (6, 10, 5) > (6, 10, 3)   -> full house of tens beats full house of tens
    (6, 10, 5) > (5, 14, 13)  -> full house always beats a flush
This means we NEVER have to hand-write comparison logic between hand types.
We just build the tuple correctly and Python's > and == do the rest.

Category numbers (higher = stronger):
8 = Straight Flush (Royal Flush is just the highest straight flush, Ace-high)
7 = Four of a Kind
6 = Full House
5 = Flush
4 = Straight
3 = Three of a Kind
2 = Two Pair
1 = One Pair
0 = High Card
"""

from itertools import combinations
from collections import Counter


def evaluate_5(cards):
    """
    cards: list of exactly 5 Card objects.
    Returns a comparable tuple representing the hand's strength.
    """
    values = sorted((c.value for c in cards), reverse=True)
    suits = [c.suit for c in cards]
    is_flush = len(set(suits)) == 1

    unique_values = sorted(set(values), reverse=True)
    is_straight = False
    straight_high = None

    if len(unique_values) == 5:
        if unique_values[0] - unique_values[4] == 4:
            is_straight = True
            straight_high = unique_values[0]
        # Special case: wheel straight A-2-3-4-5 (Ace plays LOW here)
        elif unique_values == [14, 5, 4, 3, 2]:
            is_straight = True
            straight_high = 5

    counts = Counter(values)
    # Sort by (how many of this rank, then rank value) - both descending
    count_items = sorted(counts.items(), key=lambda item: (-item[1], -item[0]))
    count_pattern = [c for _, c in count_items]
    ordered_values = [v for v, _ in count_items]

    if is_straight and is_flush:
        return (8, straight_high)
    if count_pattern == [4, 1]:
        return (7, ordered_values[0], ordered_values[1])
    if count_pattern == [3, 2]:
        return (6, ordered_values[0], ordered_values[1])
    if is_flush:
        return (5, *values)
    if is_straight:
        return (4, straight_high)
    if count_pattern == [3, 1, 1]:
        return (3, ordered_values[0], *ordered_values[1:])
    if count_pattern == [2, 2, 1]:
        return (2, ordered_values[0], ordered_values[1], ordered_values[2])
    if count_pattern == [2, 1, 1, 1]:
        return (1, ordered_values[0], *ordered_values[1:])
    return (0, *values)


def best_hand(seven_cards):
    """
    seven_cards: list of 7 Card objects (2 hole + up to 5 community).
    If fewer than 7 are given (e.g. mid-hand), it still works with whatever
    5+ cards are available.
    Returns the best scoring tuple among all possible 5-card combinations.
    """
    best_score = None
    for combo in combinations(seven_cards, 5):
        score = evaluate_5(list(combo))
        if best_score is None or score > best_score:
            best_score = score
    return best_score


HAND_NAMES = {
    8: "Straight Flush",
    7: "Four of a Kind",
    6: "Full House",
    5: "Flush",
    4: "Straight",
    3: "Three of a Kind",
    2: "Two Pair",
    1: "One Pair",
    0: "High Card",
}


def describe(score_tuple):
    """Human readable label, e.g. (6, 10, 5) -> 'Full House'"""
    return HAND_NAMES[score_tuple[0]]
