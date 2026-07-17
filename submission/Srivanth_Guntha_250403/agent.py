

import random

from card import parse_cards
from equity import estimate_equity


class BasePokerBot:
    def __init__(self, name):
        self.name = name

    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        """
        Calculates the optimal move for Limit Texas Hold'em.

        Parameters:
        - hole_cards (list): Your two private cards, e.g., ['Ah', 'Kd']
        - community_cards (list): Shared public cards, e.g., ['7s', '7c', '2d'] (Empty pre-flop)
        - pot_size (int): Total chips currently in the middle pot
        - stack_size (int): Your remaining chips in your stack
        - amount_to_call (int): Chips required to put in to stay in the hand
        - legal_actions (list): Available valid moves, e.g., ['FOLD', 'CALL', 'RAISE']

        Returns:
        - A string exactly matching ONE of the elements in legal_actions.
        """
        raise NotImplementedError("Your bot logic goes here!")


class CustomPokerBot(BasePokerBot):
   

    # Raise-for-value thresholds by street (equity must exceed this)
    RAISE_THRESHOLD = {
        "PREFLOP": 0.62,
        "FLOP": 0.63,
        "TURN": 0.66,
        "RIVER": 0.68,
    }
    # Safety margin subtracted from the pot-odds break-even point before
    # folding -- avoids folding hands that are only marginally -EV due to
    # equity-estimate noise (Monte-Carlo variance).
    FOLD_MARGIN = 0.04

    # Semi-bluff/raise probability band: equities in [BLUFF_LO, BLUFF_HI)
    # are "medium strength" hands that raise a small fraction of the time
    # for balance instead of always just calling.
    BLUFF_LO = 0.42
    BLUFF_HI = 0.58
    BLUFF_FREQ = 0.15

    MC_ITERS = {"PREFLOP": 80, "FLOP": 100, "TURN": 90, "RIVER": 150}

    def _street(self, community_cards):
        n = len(community_cards)
        if n == 0:
            return "PREFLOP"
        if n == 3:
            return "FLOP"
        if n == 4:
            return "TURN"
        return "RIVER"

    def _bluff_rng(self, hole_cards, community_cards, pot_size, amount_to_call):
        seed = hash((tuple(sorted(hole_cards)), tuple(community_cards), pot_size, amount_to_call, self.name))
        return random.Random(seed)

    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        street = self._street(community_cards)
        hole = parse_cards(hole_cards)
        board = parse_cards(community_cards)

        n_iter = self.MC_ITERS[street]
        equity = estimate_equity(hole, board, n_iter=n_iter)

        can_raise = "RAISE" in legal_actions
        can_fold = "FOLD" in legal_actions

        # --- Facing no bet (check available via CALL) -----------------
        if amount_to_call == 0:
            if can_raise and equity >= self.RAISE_THRESHOLD[street]:
                return "RAISE"
            if can_raise and self.BLUFF_LO <= equity < self.BLUFF_HI:
                rng = self._bluff_rng(hole_cards, community_cards, pot_size, amount_to_call)
                if rng.random() < self.BLUFF_FREQ:
                    return "RAISE"
            return "CALL"  # functions as CHECK

        # --- Facing a bet ----------------------------------------------
        pot_odds = amount_to_call / (pot_size + amount_to_call)

        # Clear value raise
        if can_raise and equity >= self.RAISE_THRESHOLD[street]:
            return "RAISE"

        # Occasional balanced semi-bluff raise with medium equity
        if can_raise and self.BLUFF_LO <= equity < self.BLUFF_HI:
            rng = self._bluff_rng(hole_cards, community_cards, pot_size, amount_to_call)
            if rng.random() < self.BLUFF_FREQ:
                return "RAISE"

        
        if equity + self.FOLD_MARGIN >= pot_odds:
            return "CALL"

        if can_fold:
            return "FOLD"
        return "CALL"
