"""
agent.py
--------
CRITICAL entry point for the tournament arena.

Strategy archetype chosen: Monte-Carlo Expected-Value (EV) heuristics.

High-level idea
================
At every decision point we don't know the opponent's hole cards (the
"Imperfect Information" of the assignment). We approximate our winning
probability ("equity") against a *uniformly random* opponent hand by
running Monte Carlo rollouts (see equity_calculator.py): sample an
opponent hand + the remaining community cards many times, score both
hands with our from-scratch hand_evaluator.py, and average
win/tie/loss into a single equity number in [0, 1].

Given that equity estimate, the decision reduces to comparing it
against the pot odds required to profitably call, per the classic
Expected Value inequality:

    EV(call) = equity * (pot_size + amount_to_call)
               - (1 - equity) * amount_to_call

    Calling is +EV whenever:
        equity > amount_to_call / (pot_size + amount_to_call)   [pot odds]

We layer three decision bands on top of that baseline pot-odds rule:
  1. equity >= RAISE_THRESHOLD              -> RAISE  (value / build the pot)
  2. pot_odds + SAFETY_MARGIN < equity       -> CALL   (profitable but not
                                                          strong enough to raise)
  3. otherwise                               -> FOLD   (unless a cheap/free
                                                          semi-bluff raise or
                                                          free check applies)

A small semi-bluff frequency is mixed in on drawing hands so the bot
is not purely "bet only the nuts, fold everything else" (which would
be trivially exploitable) -- see BLUFF_* constants below.
"""

import random
from card import Card
from equity_calculator import estimate_equity

# ---- Tunable strategy constants -------------------------------------------------
RAISE_THRESHOLD = 0.66          # equity needed to raise for value
SAFETY_MARGIN = 0.03            # extra equity above pot-odds required to call
                                 # (guards against Monte-Carlo sampling noise)
BLUFF_EQUITY_LOW = 0.35         # drawing hands with equity in this band...
BLUFF_EQUITY_HIGH = 0.55        # ...are semi-bluff-raised at BLUFF_FREQ
BLUFF_FREQ = 0.15

# Simulation budget per street (deeper streets get more sims: fewer
# remaining unknown cards means each rollout is cheaper AND the pot is
# usually bigger, so accuracy matters more).
SIMS_BY_STREET = {0: 150, 3: 200, 4: 250, 5: 300}


class BasePokerBot:
    def __init__(self, name):
        self.name = name

    def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                    amount_to_call, legal_actions):
        """
        Calculates the optimal move for Limit Texas Hold'em.

        Parameters:
        - hole_cards (list): Your two private cards, e.g. ['Ah', 'Kd']
        - community_cards (list): Shared public cards, e.g. ['7s', 'Td', '2c']
        - pot_size (int): Total chips currently in the middle pot
        - stack_size (int): Your remaining chips in your stack
        - amount_to_call (int): Chips required to put in to stay in
        - legal_actions (list): Available valid moves, e.g. ['FOLD', 'CALL']

        Returns:
        - A string exactly matching ONE of the elements in legal_actions
        """
        raise NotImplementedError("Your bot logic goes here!")


class CustomPokerBot(BasePokerBot):
    def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                    amount_to_call, legal_actions):

        # --- Defensive fallback: if something upstream is malformed, never
        # crash the arena -- always return a legal action. ---
        if not legal_actions:
            return "FOLD"

        try:
            hero_cards = Card.from_list(hole_cards)
            board_cards = Card.from_list(community_cards)
        except Exception:
            # Unparseable card strings -> safest legal fallback.
            return self._safe_default(legal_actions, amount_to_call)

        num_sims = SIMS_BY_STREET.get(len(board_cards), 300)
        equity = estimate_equity(hero_cards, board_cards, num_simulations=num_sims)

        # Pot odds: the break-even equity required to profitably call.
        if amount_to_call > 0:
            pot_odds = amount_to_call / (pot_size + amount_to_call)
        else:
            pot_odds = 0.0  # free to see the next card (check)

        can_raise = "RAISE" in legal_actions
        can_call = "CALL" in legal_actions
        can_fold = "FOLD" in legal_actions

        # 1) Strong value hands -> raise/build the pot.
        if equity >= RAISE_THRESHOLD and can_raise:
            return "RAISE"

        # 2) Semi-bluff: occasionally raise drawing hands to deny pure
        #    "bet strong / check-fold weak" predictability.
        if (can_raise and BLUFF_EQUITY_LOW <= equity < BLUFF_EQUITY_HIGH
                and random.random() < BLUFF_FREQ):
            return "RAISE"

        # 3) Profitable call: equity clears pot odds with a safety margin.
        if equity > pot_odds + SAFETY_MARGIN and can_call:
            return "CALL"

        # 4) Free action (nothing to call) -> just check via CALL.
        if amount_to_call == 0 and can_call:
            return "CALL"

        # 5) Not profitable -> fold if possible, else take whatever's legal.
        if can_fold:
            return "FOLD"
        return self._safe_default(legal_actions, amount_to_call)

    @staticmethod
    def _safe_default(legal_actions, amount_to_call):
        """Last-resort legal move if the primary logic can't decide."""
        if amount_to_call == 0 and "CALL" in legal_actions:
            return "CALL"
        if "FOLD" in legal_actions:
            return "FOLD"
        return legal_actions[0]