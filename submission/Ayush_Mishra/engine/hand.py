"""
engine/hand.py

Represents a player's hand in Texas Hold'em.
"""

from __future__ import annotations

from itertools import combinations
from typing import Iterable

from engine.card import Card


class Hand:
    """
    Represents a player's hole cards.
    """

    def __init__(self, cards: Iterable[Card] | None = None):

        self.cards = list(cards) if cards else []

    # -------------------------------------------------
    # Hole Cards
    # -------------------------------------------------

    def add_card(self, card: Card) -> None:

        if len(self.cards) >= 2:
            raise ValueError("A player cannot have more than two hole cards.")

        self.cards.append(card)

    def clear(self) -> None:

        self.cards.clear()

    # -------------------------------------------------
    # Access
    # -------------------------------------------------

    def get_cards(self) -> list[Card]:

        return self.cards.copy()

    # -------------------------------------------------
    # Hand Generation
    # -------------------------------------------------

    def all_cards(self, board: Iterable[Card]) -> list[Card]:
        """
        Returns the complete 7-card hand.
        """

        board = list(board)

        if len(board) > 5:
            raise ValueError("Board cannot contain more than five cards.")

        return self.cards + board

    def five_card_combinations(
        self,
        board: Iterable[Card],
    ):
        """
        Generate every possible 5-card hand.

        Returns
        -------
        generator of tuple[Card]
        """

        cards = self.all_cards(board)

        if len(cards) < 5:
            raise ValueError("Need at least five total cards.")

        return combinations(cards, 5)

    # -------------------------------------------------
    # Magic Methods
    # -------------------------------------------------

    def __len__(self):

        return len(self.cards)

    def __iter__(self):

        return iter(self.cards)

    def __getitem__(self, index):

        return self.cards[index]

    def __repr__(self):

        return f"Hand({self.cards})"

    def __str__(self):

        return " ".join(str(card) for card in self.cards)


if __name__ == "__main__":

    hole = Hand()

    hole.add_card(Card.from_string("Ah"))
    hole.add_card(Card.from_string("Kd"))

    board = [
        Card.from_string("Qs"),
        Card.from_string("Jh"),
        Card.from_string("Tc"),
        Card.from_string("2d"),
        Card.from_string("7c"),
    ]

    print("Hole Cards:")
    print(hole)

    print("\nBoard:")
    print(board)

    print("\nTotal Cards:")
    print(hole.all_cards(board))

    print("\nFive Card Combinations:")

    count = 0
    for combo in hole.five_card_combinations(board):
        print(combo)
        count += 1

    print("\nTotal:", count)