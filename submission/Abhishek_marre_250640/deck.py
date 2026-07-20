"""
deck.py
-------
A standard 52-card deck built from Card objects. Used internally by the
agent's Monte-Carlo equity engine to sample opponent hole cards and
un-dealt community cards, and by the standalone game engine (game.py)
for full local simulation / self-play training.
"""

import random
from card import Card, RANKS, SUITS


class Deck:
    def __init__(self, excluded_codes=None):
        """
        excluded_codes: iterable of 2-char card strings (e.g. known hole
        cards / community cards) that must NOT be part of this deck --
        used when Monte-Carlo sampling the remaining unseen cards.
        """
        excluded = set(excluded_codes or [])
        self.cards = [
            Card(r + s) for r in RANKS for s in SUITS
            if (r + s) not in excluded
        ]

    def shuffle(self):
        random.shuffle(self.cards)
        return self

    def deal(self, n=1):
        """Pop n cards off the top of the deck."""
        dealt = self.cards[:n]
        self.cards = self.cards[n:]
        return dealt

    def __len__(self):
        return len(self.cards)

    def __repr__(self):
        return f"Deck({len(self.cards)} cards remaining)"