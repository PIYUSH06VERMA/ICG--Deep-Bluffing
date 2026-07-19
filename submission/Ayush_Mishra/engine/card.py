"""
engine/card.py

Represents a single playing card.

Internal Representation
-----------------------
Rank : int
    2-14

Suit : int
    0 Hearts
    1 Diamonds
    2 Clubs
    3 Spades

Example
-------
Card.from_string("Ah")

Author:
Deep Bluffing Team
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import total_ordering


@total_ordering
@dataclass(frozen=True, slots=True)
class Card:
    """
    Immutable playing card.
    """

    rank: int
    suit: int

    # --------------------------
    # Constants
    # --------------------------
    from utils.constants import (
        HEARTS,
        DIAMONDS,
        CLUBS,
        SPADES,
        SUIT_TO_CHAR,
        CHAR_TO_SUIT,
        VALUE_TO_RANK,
        RANK_TO_VALUE,
    )

    # --------------------------
    # Validation
    # --------------------------

    def __post_init__(self):

        if not (2 <= self.rank <= 14):
            raise ValueError(f"Invalid rank {self.rank}")

        if not (0 <= self.suit <= 3):
            raise ValueError(f"Invalid suit {self.suit}")

    # --------------------------
    # Constructors
    # --------------------------

    @classmethod
    def from_string(cls, card: str) -> "Card":
        """
        Example
        -------
        Card.from_string("Ah")
        """

        card = card.strip()

        if len(card) != 2:
            raise ValueError(f"Invalid card: {card}")

        rank_char = card[0].upper()
        suit_char = card[1].lower()

        if rank_char not in cls.RANK_TO_VALUE:
            raise ValueError(rank_char)

        if suit_char not in cls.CHAR_TO_SUIT:
            raise ValueError(suit_char)

        return cls(
            cls.RANK_TO_VALUE[rank_char],
            cls.CHAR_TO_SUIT[suit_char],
        )

    @classmethod
    def from_id(cls, idx: int) -> "Card":
        """
        Card IDs

        0  -> 2h
        1  -> 2d
        ...
        51 -> As
        """

        if not (0 <= idx < 52):
            raise ValueError(idx)

        rank = idx // 4 + 2
        suit = idx % 4

        return cls(rank, suit)

    # --------------------------
    # Properties
    # --------------------------

    @property
    def id(self) -> int:
        """
        Unique integer in [0,51]
        """

        return (self.rank - 2) * 4 + self.suit

    @property
    def rank_char(self) -> str:
        return self.VALUE_TO_RANK[self.rank]

    @property
    def suit_char(self) -> str:
        return self.SUIT_TO_CHAR[self.suit]

    @property
    def color(self) -> str:
        return "Red" if self.suit in (0, 1) else "Black"

    # --------------------------
    # Comparison
    # --------------------------

    def __lt__(self, other):

        if not isinstance(other, Card):
            return NotImplemented

        return self.rank < other.rank

    # --------------------------
    # String Representation
    # --------------------------

    def __str__(self):

        return f"{self.rank_char}{self.suit_char}"

    def __repr__(self):

        return f"Card('{self}')"

    # --------------------------
    # Utility
    # --------------------------

    def to_tuple(self):

        return self.rank, self.suit

    def to_dict(self):

        return {
            "rank": self.rank,
            "suit": self.suit,
        }


if __name__ == "__main__":

    a = Card.from_string("Ah")
    b = Card.from_string("Kd")
    c = Card.from_string("7s")

    print(a)
    print(a.id)
    print(a.rank)
    print(a.suit)
    print(a.color)

    print(a > b)
    print(c < b)

    print(sorted([a, b, c]))

    print(Card.from_id(51))