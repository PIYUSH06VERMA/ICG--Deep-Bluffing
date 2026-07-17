"""
card.py
-------
Core OOP primitives for the Deep-Bluffing poker engine.

Implements a Card object with full dunder-method support (__eq__, __lt__,
__gt__, __repr__, __hash__) so that lists of Card objects can be sorted,
compared, and de-duplicated using native Python semantics, and a Deck
object built on top of it.

Card string format (as specified by the assignment):
    rank : one of '2','3','4','5','6','7','8','9','T','J','Q','K','A'
    suit : one of 'h','d','c','s'   (lower-case)
Example: 'Ah' = Ace of hearts, 'Td' = Ten of diamonds.
"""

import random
from functools import total_ordering

RANK_ORDER = "23456789TJQKA"
RANK_VALUE = {r: i + 2 for i, r in enumerate(RANK_ORDER)}   # '2'->2 ... 'A'->14
VALUE_RANK = {v: r for r, v in RANK_VALUE.items()}
SUITS = "hdcs"


@total_ordering
class Card:
    __slots__ = ("rank", "suit", "value")

    def __init__(self, code: str):
        if len(code) != 2:
            raise ValueError(f"Invalid card code: {code!r}")
        rank, suit = code[0].upper(), code[1].lower()
        if rank not in RANK_VALUE:
            raise ValueError(f"Invalid rank in card code: {code!r}")
        if suit not in SUITS:
            raise ValueError(f"Invalid suit in card code: {code!r}")
        self.rank = rank
        self.suit = suit
        self.value = RANK_VALUE[rank]

    # ---- dunder methods -------------------------------------------------
    def __repr__(self):
        return f"{self.rank}{self.suit}"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.value == other.value and self.suit == other.suit

    def __lt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.value < other.value

    def __hash__(self):
        return hash((self.value, self.suit))


class Deck:
    """A standard 52-card deck with shuffle / draw semantics."""

    def __init__(self, exclude=None):
        exclude = set(str(c) for c in (exclude or []))
        self.cards = [
            Card(r + s) for r in RANK_ORDER for s in SUITS
            if (r + s) not in exclude
        ]

    def shuffle(self, rng: random.Random = None):
        (rng or random).shuffle(self.cards)
        return self

    def draw(self, n=1):
        drawn = self.cards[:n]
        self.cards = self.cards[n:]
        return drawn

    def remaining(self):
        return list(self.cards)

    def __len__(self):
        return len(self.cards)


def parse_cards(codes):
    """Convert a list of raw string codes (e.g. ['Ah','Kd']) into Card objects."""
    return [Card(c) if not isinstance(c, Card) else c for c in codes]
