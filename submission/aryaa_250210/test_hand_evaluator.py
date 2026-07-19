"""
test_hand_evaluator.py
------------------------
Sanity checks. Run this file directly: `python test_hand_evaluator.py`
If it prints "ALL TESTS PASSED", the core hand-ranking math is trustworthy.
"""

from card import cards_from_strings
from hand_evaluator import evaluate_5, best_hand, describe


def check(name, cards_str, expected_category):
    cards = cards_from_strings(cards_str)
    score = evaluate_5(cards)
    actual = describe(score)
    status = "OK" if score[0] == expected_category else "FAIL"
    print(f"[{status}] {name}: {cards_str} -> {actual} {score}")
    assert score[0] == expected_category, f"{name} failed! got {actual}"


def main():
    check("Royal Flush", ['Ah', 'Kh', 'Qh', 'Jh', 'Th'], 8)
    check("Straight Flush", ['9c', '8c', '7c', '6c', '5c'], 8)
    check("Four of a Kind", ['Ah', 'Ad', 'Ac', 'As', '2h'], 7)
    check("Full House", ['Kh', 'Kd', 'Kc', '2s', '2h'], 6)
    check("Flush", ['Ah', 'Jh', '8h', '5h', '2h'], 5)
    check("Straight", ['9h', '8d', '7c', '6s', '5h'], 4)
    check("Wheel Straight (A-2-3-4-5)", ['Ah', '2d', '3c', '4s', '5h'], 4)
    check("Three of a Kind", ['7h', '7d', '7c', 'Ks', '2h'], 3)
    check("Two Pair", ['Jh', 'Jd', '4c', '4s', '2h'], 2)
    check("One Pair", ['Th', 'Td', '9c', '5s', '2h'], 1)
    check("High Card", ['Ah', 'Jd', '8c', '5s', '2h'], 0)

    # Kicker test: Pair of Aces with King kicker beats Pair of Aces with Queen kicker
    hand1 = cards_from_strings(['Ah', 'Ad', 'Kc', '5s', '2h'])
    hand2 = cards_from_strings(['As', 'Ac', 'Qc', '5d', '2c'])
    score1, score2 = evaluate_5(hand1), evaluate_5(hand2)
    assert score1 > score2, "Kicker comparison failed!"
    print(f"[OK] Kicker test: AA+K kicker beats AA+Q kicker")

    # 7-card best_hand test: best 5-card hand out of 7 cards
    seven = cards_from_strings(['Ah', 'Kh', 'Qh', 'Jh', 'Th', '2c', '3d'])
    score = best_hand(seven)
    assert score[0] == 8, "best_hand failed to find the royal flush among 7 cards!"
    print(f"[OK] best_hand correctly found Royal Flush from 7 cards")

    # Split pot test: identical 5-card hands should tie exactly
    tie1 = evaluate_5(cards_from_strings(['Ah', 'Ad', 'Kc', '5s', '2h']))
    tie2 = evaluate_5(cards_from_strings(['As', 'Ac', 'Kd', '5c', '2d']))
    assert tie1 == tie2, "Identical hands should tie!"
    print(f"[OK] Split pot / tie detection works")

    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    main()
