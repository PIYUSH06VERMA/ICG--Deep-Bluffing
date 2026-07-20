from itertools import combinations
from collections import Counter

from card import Card

STRAIGHT_FLUSH, QUADS, FULL_HOUSE, FLUSH, STRAIGHT, TRIPS, TWO_PAIR, ONE_PAIR, HIGH_CARD = range(8, -1, -1)

HAND_NAMES = {
    STRAIGHT_FLUSH: "Straight Flush",
    QUADS: "Four of a Kind",
    FULL_HOUSE: "Full House",
    FLUSH: "Flush",
    STRAIGHT: "Straight",
    TRIPS: "Three of a Kind",
    TWO_PAIR: "Two Pair",
    ONE_PAIR: "One Pair",
    HIGH_CARD: "High Card",
}


def _straight_high(distinct_values_desc):
    values = list(distinct_values_desc)
    if 14 in values:
        values = values + [1]  
    run = 1
    best_high = None
    for i in range(1, len(values)):
        if values[i] == values[i - 1] - 1:
            run += 1
            if run >= 5:
                best_high = values[i - 4]
        elif values[i] == values[i - 1]:
            continue 
        else:
            run = 1
    return best_high


def evaluate_5(cards)
    assert len(cards) == 5
    counts = [0] * 15  
    values = [0, 0, 0, 0, 0]
    first_suit = cards[0].suit
    is_flush = True
    for i, c in enumerate(cards):
        values[i] = c.value
        counts[c.value] += 1
        if c.suit != first_suit:
            is_flush = False
    values.sort(reverse=True)

    groups = [(counts[v], v) for v in range(14, 1, -1) if counts[v]]
    groups.sort(reverse=True)
    distinct_desc = [v for _, v in sorted(groups, key=lambda g: g[1], reverse=True)]

    straight_high = _straight_high(distinct_desc) if len(distinct_desc) == 5 else None

    if is_flush and straight_high:
        return (STRAIGHT_FLUSH, straight_high)

    top_count, top_val = groups[0]

    if top_count == 4:
        kicker = max(v for v in values if v != top_val)
        return (QUADS, top_val, kicker)

    if top_count == 3 and groups[1][0] == 2:
        return (FULL_HOUSE, top_val, groups[1][1])

    if is_flush:
        return (FLUSH, *values)

    if straight_high:
        return (STRAIGHT, straight_high)

    if top_count == 3:
        kickers = sorted((v for v in values if v != top_val), reverse=True)
        return (TRIPS, top_val, *kickers)

    if top_count == 2 and groups[1][0] == 2:
        pair_hi, pair_lo = top_val, groups[1][1]
        kicker = max(v for v in values if v != pair_hi and v != pair_lo)
        return (TWO_PAIR, pair_hi, pair_lo, kicker)

    if top_count == 2:
        kickers = sorted((v for v in values if v != top_val), reverse=True)
        return (ONE_PAIR, top_val, *kickers)

    return (HIGH_CARD, *values)


def best_hand(seven_cards):
    cards = list(seven_cards)
    if len(cards) < 5:
        raise ValueError("Need at least 5 cards to evaluate a poker hand")

    best_score, best_combo = None, None
    for combo in combinations(cards, 5):
        score = evaluate_5(combo)
        if best_score is None or score > best_score:
            best_score, best_combo = score, combo
    return best_score, best_combo


def compare_hands(cards_a, cards_b):
    score_a, _ = best_hand(cards_a)
    score_b, _ = best_hand(cards_b)
    if score_a > score_b:
        return 1
    if score_b > score_a:
        return -1
    return 0


def hand_name(score_tuple):
    return HAND_NAMES[score_tuple[0]]


if __name__ == "__main__":
    royal = Card.parse_list(["Ah", "Kh", "Qh", "Jh", "Th"])
    wheel = Card.parse_list(["Ah", "2d", "3c", "4s", "5h"])
    quads = Card.parse_list(["9h", "9d", "9c", "9s", "2h"])
    print(hand_name(evaluate_5(royal)), evaluate_5(royal))
    print(hand_name(evaluate_5(wheel)), evaluate_5(wheel))
    print(hand_name(evaluate_5(quads)), evaluate_5(quads))
