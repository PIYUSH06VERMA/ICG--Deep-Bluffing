"""
equity_calculator.py
--------------------
Estimates hero's win probability ("equity") against a uniformly random
opponent hand, by Monte Carlo rollout: repeatedly sample an opponent
hole-card pair and the remaining un-dealt community cards from the
cards that are not yet visible, then score the resulting 7-card hands
with hand_evaluator.compare_hands.

This is the "Game Theory Context" building block referenced in the
assignment (Monte Carlo Simulations for hand-strength estimation),
and is the sole source of "hidden state" information the agent uses
in place of knowing the opponent's hole cards.
"""

import random
from card import Card, RANKS, SUITS
from hand_evaluator import evaluate_best_hand

FULL_DECK_CODES = [r + s for r in RANKS for s in SUITS]


def estimate_equity(hole_cards, community_cards, num_simulations=400):
    """
    hole_cards: list[Card] (len 2) -- hero's private cards
    community_cards: list[Card] (len 0, 3, 4, or 5)
    num_simulations: number of Monte Carlo rollouts

    Returns: float in [0, 1], hero's estimated equity (win_frac + 0.5*tie_frac)
    """
    known_codes = {str(c) for c in hole_cards} | {str(c) for c in community_cards}
    remaining_codes = [c for c in FULL_DECK_CODES if c not in known_codes]

    n_board_needed = 5 - len(community_cards)

    wins = 0.0
    for _ in range(num_simulations):
        # Sample without replacement: 2 opponent hole cards + remaining board
        sample = random.sample(remaining_codes, 2 + n_board_needed)
        opp_hole = [Card(c) for c in sample[:2]]
        extra_board = [Card(c) for c in sample[2:]]

        full_board = community_cards + extra_board
        hero_score = evaluate_best_hand(hole_cards + full_board)
        opp_score = evaluate_best_hand(opp_hole + full_board)

        if hero_score > opp_score:
            wins += 1.0
        elif hero_score == opp_score:
            wins += 0.5
        # else: loss, +0

    return wins / num_simulations