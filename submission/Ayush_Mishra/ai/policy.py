"""
ai/policy.py

Decision-making policy for the poker bot.
"""

import random


class PokerPolicy:
    """
    Converts estimated hand strength into a poker action.
    """

    def choose_action(
        self,
        strength,
        legal_actions,
        amount_to_call,
    ):
        """
        Parameters
        ----------
        strength : float
            Estimated probability of winning.

        legal_actions : list[str]

        amount_to_call : int
        """

        # --------------------------------------------------
        # Monster hands
        # --------------------------------------------------

        if strength >= 0.85:

            if "raise" in legal_actions:
                return "raise"

            if "call" in legal_actions:
                return "call"

            return "check"

        # --------------------------------------------------
        # Strong hands
        # --------------------------------------------------

        if strength >= 0.65:

            if (
                "raise" in legal_actions
                and random.random() < 0.35
            ):
                return "raise"

            if "call" in legal_actions:
                return "call"

            return "check"

        # --------------------------------------------------
        # Medium hands
        # --------------------------------------------------

        if strength >= 0.45:

            if amount_to_call == 0:
                return "check"

            return "call"

        # --------------------------------------------------
        # Weak hands
        # --------------------------------------------------

        if amount_to_call == 0:
            return "check"

        return "fold"