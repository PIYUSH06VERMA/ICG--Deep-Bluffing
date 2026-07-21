"""
engine/betting.py

Betting engine for Heads-Up Limit Texas Hold'em.
"""

from __future__ import annotations

from engine.player import Player


class BettingRound:
    """
    Manages one betting street.
    """

    def __init__(self, bet_size: int, raise_cap: int = 4):

        self.bet_size = bet_size
        self.raise_cap = raise_cap

        self.current_bet = 0
        self.raise_count = 0

        self.pot = 0

    # -------------------------------------------------
    # Utility
    # -------------------------------------------------

    def amount_to_call(self, player: Player) -> int:
        """
        Chips required for player to call.
        """
        return max(0, self.current_bet - player.current_bet)

    def can_raise(self) -> bool:
        """
        Whether another raise is allowed.
        """
        return self.raise_count < self.raise_cap

    # -------------------------------------------------
    # Actions
    # -------------------------------------------------

    def post_blind(self, player: Player, amount: int):

        posted = player.bet(amount)

        self.current_bet = max(self.current_bet, player.current_bet)

        self.pot += posted

        return posted

    def call(self, player: Player):

        amount = self.amount_to_call(player)

        paid = player.bet(amount)

        self.pot += paid

        return paid

    def check(self, player: Player):

        if self.amount_to_call(player) != 0:
            raise ValueError("Player cannot check.")

    def raise_bet(self, player: Player):

        if not self.can_raise():
            raise ValueError("Raise cap reached.")

        total = self.amount_to_call(player) + self.bet_size

        paid = player.bet(total)

        self.current_bet += self.bet_size

        self.raise_count += 1

        self.pot += paid

        return paid

    def fold(self, player: Player):

        player.fold()

    # -------------------------------------------------
    # Reset
    # -------------------------------------------------

    def next_street(self, bet_size: int):

        self.bet_size = bet_size

        self.current_bet = 0
        self.raise_count = 0

    # -------------------------------------------------
    # Representation
    # -------------------------------------------------

    def __repr__(self):

        return (
            f"Pot={self.pot}, "
            f"CurrentBet={self.current_bet}, "
            f"Raises={self.raise_count}"
        )
