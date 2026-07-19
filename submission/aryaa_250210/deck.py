"""
deck.py
--------
A standard 52-card deck. Used for dealing hole cards and community cards,
and also internally by the bot's Monte Carlo simulator to imagine
possible future cards / opponent hands.
"""

import random
from card import Card, RANKS, SUITS


class Deck:
    def __init__(self):
        self.cards = [Card(r + s) for r in RANKS for s in SUITS]
        random.shuffle(self.cards)

    def deal(self, n):
        """Deal n cards off the top of the deck (removes them from the deck)."""
        dealt, self.cards = self.cards[:n], self.cards[n:]
        return dealt

    def remaining(self):
        return len(self.cards)


def full_deck_minus(known_cards):
    """
    Returns a fresh 52-card deck list with the given known cards removed.
    known_cards: list of Card objects (e.g. your hole cards + community cards)
    Useful for Monte Carlo rollouts where we need to draw from 'unseen' cards.
    """
    known_strs = {str(c) for c in known_cards}
    return [Card(r + s) for r in RANKS for s in SUITS if (r + s) not in known_strs]
