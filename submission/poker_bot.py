import random
from enum import Enum

from constants import PRE_FLOP, FLOP, FOLD, CALL, RAISE


class HandStrength(Enum):
    """
    Categories representing the estimated strength of a hand.
    """
    VERY_WEAK = 0
    WEAK = 1
    MEDIUM = 2
    STRONG = 3
    MONSTER = 4


class PokerBot:
    """
    Rule-based poker strategy using Monte Carlo hand strength
    estimation and poker heuristics.
    """

    THRESHOLDS = [
        (0.25, HandStrength.VERY_WEAK),
        (0.45, HandStrength.WEAK),
        (0.65, HandStrength.MEDIUM),
        (0.85, HandStrength.STRONG),
    ]

    def __init__(self):
        pass

    # -------------------------------------------------
    # Pot Odds
    # -------------------------------------------------

    def calculate_pot_odds(self, pot_size, amount_to_call):
        if amount_to_call <= 0:
            return 0.0
        return amount_to_call / (pot_size + amount_to_call)

    # -------------------------------------------------
    # Hand Strength Classification
    # -------------------------------------------------

    def classify_hand_strength(self, win_probability):
        for threshold, category in self.THRESHOLDS:
            if win_probability < threshold:
                return category
        return HandStrength.MONSTER

    # -------------------------------------------------
    # Legal Action Helpers
    # -------------------------------------------------

    def can_raise(self, legal_actions):
        return RAISE in legal_actions

    def can_call(self, legal_actions):
        return CALL in legal_actions

    def can_fold(self, legal_actions):
        return FOLD in legal_actions

    # -------------------------------------------------
    # Bluffing Logic
    # -------------------------------------------------

    def should_bluff(self, hand_strength, street):
        # Never bluff with good hands.
        if hand_strength not in (HandStrength.VERY_WEAK, HandStrength.WEAK):
            return False

        # Bluff only early in the hand.
        # FIX: previously compared against "PREFLOP"/"FLOP" (no
        # underscore), which never matched constants.PRE_FLOP
        # ("PRE_FLOP"), so bluffing could only ever trigger on FLOP.
        if street not in (PRE_FLOP, FLOP):
            return False

        # 5% bluff frequency.
        return random.random() < 0.05

    # -------------------------------------------------
    # Main Decision Logic
    # -------------------------------------------------

    def choose_action(self, win_probability, pot_size, amount_to_call,
                       legal_actions, street):

        pot_odds = self.calculate_pot_odds(pot_size, amount_to_call)
        hand_strength = self.classify_hand_strength(win_probability)

        # Bluff occasionally
        if self.can_raise(legal_actions) and self.should_bluff(hand_strength, street):
            return RAISE

        if hand_strength == HandStrength.MONSTER:
            if self.can_raise(legal_actions):
                return RAISE
            if self.can_call(legal_actions):
                return CALL

        elif hand_strength == HandStrength.STRONG:
            if self.can_raise(legal_actions):
                return RAISE
            if self.can_call(legal_actions):
                return CALL

        elif hand_strength == HandStrength.MEDIUM:
            if win_probability >= pot_odds:
                if self.can_call(legal_actions):
                    return CALL
                if self.can_raise(legal_actions):
                    return RAISE
            if self.can_fold(legal_actions):
                return FOLD

        elif hand_strength == HandStrength.WEAK:
            if amount_to_call == 0:
                if self.can_call(legal_actions):
                    return CALL
            if win_probability >= pot_odds:
                if self.can_call(legal_actions):
                    return CALL
            if self.can_fold(legal_actions):
                return FOLD

        else:  # VERY_WEAK
            if amount_to_call == 0:
                if self.can_call(legal_actions):
                    return CALL
            if self.can_fold(legal_actions):
                return FOLD

        # Emergency fallback
        if self.can_call(legal_actions):
            return CALL
        if self.can_fold(legal_actions):
            return FOLD
        return legal_actions[0]
