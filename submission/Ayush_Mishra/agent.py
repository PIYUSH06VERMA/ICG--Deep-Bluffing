"""
agent.py

Poker agent for Heads-Up Limit Texas Hold'em.
"""

from ai.montecarlo import MonteCarloSimulator
from ai.policy import PokerPolicy


class PokerAgent:
    """
    Poker-playing agent using Monte Carlo simulation
    and a decision policy.
    """

    def __init__(self, simulations=10000):

        self.simulator = MonteCarloSimulator(
            simulations=simulations
        )

        self.policy = PokerPolicy()

    def get_action(
        self,
        hole_cards,
        community_cards,
        pot_size,
        stack_size,
        amount_to_call,
        legal_actions,
    ):
        """
        Decide the next action.
        """

        strength = self.simulator.estimate_strength(
            hole_cards,
            community_cards,
        )

        action = self.policy.choose_action(
            strength,
            legal_actions,
            amount_to_call,
        )

        return action

if __name__ == "__main__":

    from engine.card import Card

    agent = PokerAgent(simulations=1000)

    hole = [
        Card.from_string("Ah"),
        Card.from_string("Ad"),
    ]

    board = []

    action = agent.get_action(
        hole_cards=hole,
        community_cards=board,
        pot_size=3,
        stack_size=100,
        amount_to_call=1,
        legal_actions=["fold", "call", "raise"],
    )

    print("Chosen Action:", action)