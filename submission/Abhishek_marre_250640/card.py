"""
card.py
-------
Custom Card representation for the HULHE engine.

A card is built from a 2-character string: rank + suit
  rank: '2'-'9', 'T', 'J', 'Q', 'K', 'A'
  suit: 'h' (hearts), 'd' (diamonds), 'c' (clubs), 's' (spades)

We implement the "Python OOP Magic" dunder methods (__eq__, __lt__, __gt__)
so that lists of Card objects can be sorted / compared directly with
built-ins like sorted(), max(), min() -- no external library required.
"""

from functools import total_ordering

RANKS = "23456789TJQKA"          # index = numeric strength, 2 is weakest
RANK_VALUE = {r: i + 2 for i, r in enumerate(RANKS)}   # '2'->2 ... 'A'->14
SUITS = "hdcs"


@total_ordering
class Card:
    __slots__ = ("rank", "suit", "value")

    def __init__(self, code: str):
        if len(code) != 2 or code[0] not in RANKS or code[1] not in SUITS:
            raise ValueError(f"Invalid card code: {code!r}")
        self.rank = code[0]
        self.suit = code[1]
        self.value = RANK_VALUE[self.rank]      # 2..14, precomputed once

    # ---- OOP magic: makes Card directly sortable/comparable ----
    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        # Two cards are "equal" in poker-strength terms if same rank.
        return self.value == other.value

    def __lt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.value < other.value

    def __hash__(self):
        return hash((self.rank, self.suit))

    def __repr__(self):
        return f"{self.rank}{self.suit}"

    def __str__(self):
        return self.__repr__()

    @classmethod
    def from_list(cls, codes):
        """Helper: build a list of Card objects from a list of strings."""
        return [cls(c) for c in codes]