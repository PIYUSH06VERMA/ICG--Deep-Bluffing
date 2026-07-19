"""
engine/player.py

Represents a poker player.
"""

from __future__ import annotations

from engine.hand import Hand


class Player:
    """
    Represents one poker player.
    """

    def __init__(self, name: str, chips: int):

        self.name = name
        self.chips = chips

        self.hand = Hand()

        self.current_bet = 0

        self.folded = False

        self.all_in = False

    # ---------------------------------------------------------
    # Chip Management
    # ---------------------------------------------------------

    def bet(self, amount: int):
        """
        Place a bet.

        Returns actual amount deducted.
        """

        if amount < 0:
            raise ValueError("Bet cannot be negative.")

        actual = min(amount, self.chips)

        self.chips -= actual

        self.current_bet += actual

        if self.chips == 0:
            self.all_in = True

        return actual

    def win(self, amount: int):

        self.chips += amount

    # ---------------------------------------------------------
    # Player Actions
    # ---------------------------------------------------------

    def fold(self):

        self.folded = True

    # ---------------------------------------------------------
    # Reset Between Hands
    # ---------------------------------------------------------

    def reset_for_new_hand(self):

        self.hand.clear()

        self.current_bet = 0

        self.folded = False

        self.all_in = False

    # ---------------------------------------------------------
    # Queries
    # ---------------------------------------------------------

    @property
    def active(self):
        return not self.folded

    # ---------------------------------------------------------
    # String Methods
    # ---------------------------------------------------------

    def __repr__(self):

        return (
            f"Player("
            f"{self.name}, "
            f"chips={self.chips}, "
            f"bet={self.current_bet})"
        )

    def __str__(self):

        return (
            f"{self.name}"
            f" | Chips: {self.chips}"
            f" | Bet: {self.current_bet}"
        )

    def reset_bet(self):
        """
        Reset the player's contribution for a new betting street.
        """
        self.current_bet = 0

if __name__ == "__main__":

    p = Player("Hero", 100)

    print(p)

    p.bet(15)

    print(p)

    p.hand.add_card(
        __import__("engine.card").card.Card.from_string("Ah")
    )

    p.hand.add_card(
        __import__("engine.card").card.Card.from_string("Kd")
    )

    print(p.hand)

    p.fold()

    print(p.folded)

    p.reset_for_new_hand()

    print(p.hand)