"""
Project Deep-Bluffing submission entry point.

Implements CustomPokerBot: a Monte Carlo equity estimator feeding
a rule-based decision layer (pot odds, hand-strength tiers, and
occasional bluffing).

Strategy summary (see report.pdf for full justification):
  1. Estimate hand equity via Monte Carlo simulation
     (monte_carlo.estimate_win_probability), using
     win + 0.5 * tie as the equity figure.
  2. Classify that equity into a hand-strength tier
     (poker_bot.PokerBot.classify_hand_strength).
  3. Choose FOLD / CALL / RAISE using pot-odds-aware heuristics
     per tier, with a small bluff frequency on weak hands early
     in the hand (poker_bot.PokerBot.choose_action).
"""

from card import Card
from constants import PRE_FLOP, FLOP, TURN, RIVER
from monte_carlo import estimate_win_probability
from poker_bot import PokerBot


class BasePokerBot:
    def __init__(self, name):
        self.name = name

    def get_action(self, hole_cards, community_cards, pot_size,
                    stack_size, amount_to_call, legal_actions):
        """
        Calculates the optimal move for Limit Texas Hold'em.

        Parameters:
        - hole_cards (list): Your two private cards, e.g., ['Ah', 'Kd']
        - community_cards (list): Shared public cards, e.g., ['7s', '7c', '2d']
          (Empty pre-flop)
        - pot_size (int): Total chips currently in the middle pot
        - stack_size (int): Your remaining chips in your stack
        - amount_to_call (int): Chips required to put in to stay in the hand
        - legal_actions (list): Available valid moves, e.g., ['FOLD', 'CALL', 'RAISE']

        Returns:
        - A string exactly matching ONE of the elements in legal_actions.
        """
        raise NotImplementedError("Your bot logic goes here!")


# Number of card-strings mapped to which betting street, based on
# how many community cards are visible.
_STREET_BY_BOARD_LENGTH = {
    0: PRE_FLOP,
    3: FLOP,
    4: TURN,
    5: RIVER,
}

# Simulation counts tuned for the 10,000-hand tournament's time
# budget. Since choose_action only needs the RIGHT THRESHOLD TIER
# (thresholds are spaced 0.20 apart) rather than a precise equity
# figure, even 100-200 simulations keep average error well under
# the gap between tiers. Measured: 100 sims ~= 0.04 avg equity
# error, ~25ms/call; 1000 sims only narrows that to ~0.02 while
# costing ~10x more time, which is not worth the trade at this
# tournament's scale (10,000 hands x up to ~8 decisions/hand).
_NUM_SIMULATIONS_BY_STREET = {
    PRE_FLOP: 100,
    FLOP: 150,
    TURN: 150,
    RIVER: 200,
}


class CustomPokerBot(BasePokerBot):
    """
    Monte Carlo equity estimation + rule-based decision layer.
    """

    def __init__(self, name):
        super().__init__(name)
        self.strategy = PokerBot()

    def get_action(self, hole_cards, community_cards, pot_size,
                    stack_size, amount_to_call, legal_actions):

        hole = [Card.from_string(c) for c in hole_cards]
        board = [Card.from_string(c) for c in community_cards]

        street = _STREET_BY_BOARD_LENGTH.get(len(board))
        if street is None:
            # Defensive fallback: an unexpected board length should
            # never happen given the engine's street progression,
            # but if it did, don't crash the arena over it.
            street = RIVER

        num_simulations = _NUM_SIMULATIONS_BY_STREET[street]

        equity_result = estimate_win_probability(
            hole_cards=hole,
            community_cards=board,
            num_simulations=num_simulations,
        )

        action = self.strategy.choose_action(
            win_probability=equity_result["equity"],
            pot_size=pot_size,
            amount_to_call=amount_to_call,
            legal_actions=legal_actions,
            street=street,
        )

        # Final safety net: never return something illegal, no
        # matter what upstream logic decided.
        if action not in legal_actions:
            action = "CALL" if "CALL" in legal_actions else legal_actions[0]

        return action
