import random

from card import Card
from constants import RANKS, SUITS


class Deck:
    """
    Represents a standard deck of 52 playing cards.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.cards = [
            Card(rank, suit)
            for rank in RANKS
            for suit in SUITS
        ]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        if not self.cards:
            raise IndexError("Cannot deal from an empty deck.")
        return self.cards.pop()

    def remaining_cards(self):
        return len(self.cards)

    def get_cards(self):
        return self.cards.copy()

    def __len__(self):
        return len(self.cards)

    def __repr__(self):
        return f"Deck({len(self.cards)} cards remaining)"

    def deal_hole_cards(self):
        return [self.deal(), self.deal()]

    def deal_flop(self):
        return [self.deal(), self.deal(), self.deal()]

    def deal_turn(self):
        return self.deal()

    def deal_river(self):
        return self.deal()
