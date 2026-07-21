"""
card.py
-------
A minimal, self-contained representation of a playing card.

Cards are given to us (and must be returned) as two-character strings,
e.g. 'Ah', 'Td', '9c', '2s'. This module wraps that string representation
in a small OOP `Card` class so that hand-evaluation code can use natural
Python idioms (sorting, comparisons, set/Counter operations) instead of
parsing strings everywhere.

Rank ordering (low -> high):
    2 3 4 5 6 7 8 9 T J Q K A
Suit is *only* relevant for flush detection - suits have no relative
ordering among themselves.
"""

from functools import total_ordering

RANK_ORDER = "23456789TJQKA"
RANK_TO_VALUE = {r: i + 2 for i, r in enumerate(RANK_ORDER)}   # '2' -> 2 ... 'A' -> 14
VALUE_TO_RANK = {v: r for r, v in RANK_TO_VALUE.items()}
VALID_SUITS = set("hdcs")


@total_ordering
class Card:
    """A single playing card, e.g. Card('A', 'h') or Card.from_str('Ah')."""

    __slots__ = ("rank", "suit", "value")

    def __init__(self, rank: str, suit: str):
        rank = rank.upper()
        suit = suit.lower()
        if rank not in RANK_TO_VALUE:
            raise ValueError(f"Invalid rank: {rank!r}")
        if suit not in VALID_SUITS:
            raise ValueError(f"Invalid suit: {suit!r}")
        self.rank = rank
        self.suit = suit
        self.value = RANK_TO_VALUE[rank]

    @classmethod
    def from_str(cls, s: str) -> "Card":
        if len(s) != 2:
            raise ValueError(f"Malformed card string: {s!r}")
        return cls(s[0], s[1])

    # ---- dunder magic -------------------------------------------------
    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.value == other.value and self.suit == other.suit

    def __lt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.value < other.value

    def __hash__(self):
        return hash((self.rank, self.suit))

    def __repr__(self):
        return f"{self.rank}{self.suit}"

    __str__ = __repr__


def parse_cards(card_strs):
    """['Ah', 'Kd'] -> [Card('A','h'), Card('K','d')]"""
    return [Card.from_str(c) for c in card_strs]


def make_deck():
    """Return a fresh, unshuffled 52-card deck (used by the engine/tests)."""
    return [Card(r, s) for r in RANK_ORDER for s in "hdcs"]
