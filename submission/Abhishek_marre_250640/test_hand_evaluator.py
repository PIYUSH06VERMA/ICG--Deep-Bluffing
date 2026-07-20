import random
from card import Card, RANKS, SUITS
from hand_evaluator import (
    evaluate_best_hand, evaluate_best_hand_bruteforce, evaluate_5, describe, compare_hands
)

def C(s):
    return Card.from_list(s.split())

def test(name, cards_str, expected_category):
    cards = C(cards_str)
    score = evaluate_best_hand(cards)
    ok = "OK" if score[0] == expected_category else "FAIL"
    print(f"[{ok}] {name}: {describe(score)} {score}")
    assert score[0] == expected_category, f"{name} expected {expected_category} got {score[0]}"

# Royal flush
test("Royal Flush", "Ah Kh Qh Jh Th 2c 3d", 8)
# Straight flush (non-royal)
test("Straight Flush", "9h 8h 7h 6h 5h 2c 3d", 8)
# Wheel straight flush (A-2-3-4-5 same suit)
test("Wheel Straight Flush", "Ah 2h 3h 4h 5h Kc Qd", 8)
# Four of a kind
test("Four of a Kind", "9h 9d 9c 9s 2h 3d 4c", 7)
# Full house
test("Full House", "9h 9d 9c 4s 4h 2d 3c", 6)
# Flush
test("Flush", "2h 5h 9h Jh Kh 3d 4c", 5)
# Straight
test("Straight", "5h 6d 7c 8s 9h 2d 3c", 4)
# Wheel straight (A-2-3-4-5 mixed suit)
test("Wheel Straight", "Ah 2d 3c 4s 5h Kd Qc", 4)
# Broadway straight
test("Broadway Straight", "Ah Kd Qc Js Th 2d 3c", 4)
# Trips
test("Three of a Kind", "9h 9d 9c 2s 5h 7d 3c", 3)
# Two pair
test("Two Pair", "9h 9d 4c 4s 2h 7d 3c", 2)
# One pair
test("One Pair", "9h 9d 4c 6s 2h 7d 3c", 1)
# High card
test("High Card", "2h 5d 9c Js Kh 7d 3c", 0)

# Kicker comparison: both have pair of Aces, different kickers
handA = C("Ah Ad Kc 5s 2h")
handB = C("Ah Ad Kc 5s 3h")  # slightly higher kicker (3 vs 2) -- but let's make cleanest test
scoreA = evaluate_5(C("Ah Ad Kc 5s 2h"))
scoreB = evaluate_5(C("Ah Ad Kc 5s 3h"))
assert scoreB > scoreA, "Kicker comparison failed"
print("[OK] Kicker comparison: pair of Aces w/ 3 kicker beats pair of Aces w/ 2 kicker")

# Split pot / tie detection
result = compare_hands(C("Ah Kd Qc Js Th 2d 3c"), C("Ac Kh Qd Js Th 4d 5c"))
assert result == 0, f"Expected tie, got {result}"
print("[OK] Split pot: identical best straight (both play the board) ties correctly")

# Cross-validate the optimized O(n) evaluator against brute-force
# ground truth over many random 7-card hands.
full_deck = [r + s for r in RANKS for s in SUITS]
random.seed(42)
mismatches = 0
for trial in range(20000):
    sample = random.sample(full_deck, 7)
    cards = Card.from_list(sample)
    fast = evaluate_best_hand(cards)
    slow = evaluate_best_hand_bruteforce(cards)
    if fast != slow:
        mismatches += 1
        print(f"MISMATCH on {sample}: fast={fast} slow={slow}")

assert mismatches == 0, f"{mismatches} mismatches found between fast and brute-force evaluators!"
print(f"[OK] Cross-validated optimized evaluator against brute force on 20,000 random 7-card hands (0 mismatches)")

print("\nAll hand evaluator tests passed.")