"""
ai/montecarlo.py

Monte Carlo hand strength estimator for
Heads-Up Limit Texas Hold'em.
"""

import random

from engine.deck import Deck
from engine.evaluator import Evaluator


class MonteCarloSimulator:
    """
    Estimates the probability of winning using Monte Carlo simulation.
    """

    def __init__(self, simulations: int = 1000):
        self.simulations = simulations
        self.evaluator = Evaluator()

    def _remaining_cards(self, known_cards):
        """
        Return all cards that are not already known.
        """
        deck = Deck()
        deck.remove_many(known_cards)
        return deck.cards

    def estimate_strength(self, hole_cards, community_cards):
        """
        Estimate probability of winning.
        """

        wins = 0
        ties = 0

        known_cards = hole_cards + community_cards

        # Compute the remaining deck only once
        remaining_cards = self._remaining_cards(known_cards)

        needed_board = 5 - len(community_cards)
        total_needed = 2 + needed_board

        for _ in range(self.simulations):

            # Randomly choose only the cards we need
            sample = random.sample(remaining_cards, total_needed)

            opponent_cards = sample[:2]
            full_board = community_cards + sample[2:]

            hero_hand = hole_cards + full_board
            opponent_hand = opponent_cards + full_board

            hero_score = self.evaluator.evaluate_best(hero_hand)
            opponent_score = self.evaluator.evaluate_best(opponent_hand)

            if hero_score > opponent_score:
                wins += 1
            elif hero_score == opponent_score:
                ties += 1

        return (wins + 0.5 * ties) / self.simulations


if __name__ == "__main__":

    from engine.card import Card

    simulator = MonteCarloSimulator(simulations=500)

    hole_cards = [
        Card.from_string("Ah"),
        Card.from_string("Ad"),
    ]

    community_cards = []

    strength = simulator.estimate_strength(
        hole_cards,
        community_cards,
    )

    print(f"Estimated Strength: {strength:.3f}")