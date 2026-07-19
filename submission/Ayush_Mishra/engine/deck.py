"""
engine/deck.py

Deck implementation for Heads-Up Limit Texas Hold'em.

Responsibilities
----------------
- Create a standard 52-card deck
- Shuffle
- Deal cards
- Burn cards
- Remove known cards
- Reset deck
"""

from __future__ import annotations

import random
from typing import Iterable

from engine.card import Card


class Deck:
    """
    Represents a standard shuffled deck of 52 cards.
    """

    def __init__(self, shuffle: bool = True):

        self.reset()

        if shuffle:
            self.shuffle()

    # -------------------------------------------------
    # Core Methods
    # -------------------------------------------------

    def reset(self) -> None:
        """
        Reset to a complete 52-card deck.
        """

        self.cards = [Card.from_id(i) for i in range(52)]

    def shuffle(self) -> None:
        """
        Shuffle the deck.
        """

        random.shuffle(self.cards)

    # -------------------------------------------------
    # Drawing
    # -------------------------------------------------

    def deal(self, n: int = 1):
        """
        Deal n cards from the top.

        Returns
        -------
        Card
            if n == 1

        list[Card]
            otherwise
        """

        if n <= 0:
            raise ValueError("Number of cards must be positive.")

        if n > len(self.cards):
            raise ValueError("Not enough cards remaining.")

        dealt = self.cards[:n]
        self.cards = self.cards[n:]

        if n == 1:
            return dealt[0]

        return dealt

    def burn(self) -> Card:
        """
        Burn one card.

        Texas Hold'em burns one card before
        Flop, Turn and River.
        """

        return self.deal()

    # -------------------------------------------------
    # Removal
    # -------------------------------------------------

    def remove(self, card: Card):
        """
        Remove a known card.

        Used heavily during Monte Carlo simulations.
        """

        self.cards.remove(card)

    def remove_many(self, cards: Iterable[Card]):

        for card in cards:
            self.remove(card)

    # -------------------------------------------------
    # Peek
    # -------------------------------------------------

    def peek(self):

        if not self.cards:
            return None

        return self.cards[0]

    # -------------------------------------------------
    # Magic Methods
    # -------------------------------------------------

    def __len__(self):

        return len(self.cards)

    def __contains__(self, card):

        return card in self.cards

    def __iter__(self):

        return iter(self.cards)

    def __repr__(self):

        return f"Deck({len(self.cards)} cards)"

    # -------------------------------------------------
    # Debug
    # -------------------------------------------------

    def show(self):

        print(" ".join(str(card) for card in self.cards))


if __name__ == "__main__":

    deck = Deck()

    print(deck)

    print()

    print("Top card:", deck.peek())

    print()

    print("Hole Cards")

    print(deck.deal(2))

    print()

    print("Burn")

    print(deck.burn())

    print()

    print("Flop")

    print(deck.deal(3))

    print()

    print("Remaining")

    print(len(deck))