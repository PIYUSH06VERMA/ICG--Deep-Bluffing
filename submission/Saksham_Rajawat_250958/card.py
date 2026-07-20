"""
card.py
-------
Core primitives for representing playing cards and a standard 52-card deck.

Design notes
============
* Cards are represented externally as 2-character strings, e.g. "Ah", "Td".
  The first character is the RANK ('2'-'9', 'T', 'J', 'Q', 'K', 'A') and the
  second character is the SUIT ('h', 'd', 'c', 's').
* Internally, a `Card` object stores an integer rank value (2-14, Ace high)
  so that comparisons, sorting, and hand evaluation are trivial arithmetic
  operations instead of string comparisons.
* Dunder methods (`__eq__`, `__lt__`, `__gt__`, `__repr__`, `__hash__`) are
  implemented so that lists of `Card` objects can be sorted directly with
  `sorted(cards)` and compared with the standard `<`, `>`, `==` operators,
  exactly as suggested in the project's Research Board.
"""

from functools import total_ordering

RANK_CHAR_TO_VALUE = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
    '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14,
}
VALUE_TO_RANK_CHAR = {v: k for k, v in RANK_CHAR_TO_VALUE.items()}
VALID_SUITS = {'h', 'd', 'c', 's'}


@total_ordering
class Card:
    """A single playing card, e.g. Card('A', 'h') or Card.from_str('Ah')."""

    __slots__ = ("rank", "suit")

    def __init__(self, rank, suit):
        """
        rank: either the integer value (2-14) or the rank character.
        suit: single lowercase character in {'h','d','c','s'}.
        """
        if isinstance(rank, str):
            if rank not in RANK_CHAR_TO_VALUE:
                raise ValueError(f"Invalid rank character: {rank!r}")
            self.rank = RANK_CHAR_TO_VALUE[rank]
        elif isinstance(rank, int):
            if rank not in VALUE_TO_RANK_CHAR:
                raise ValueError(f"Invalid rank value: {rank!r}")
            self.rank = rank
        else:
            raise TypeError("rank must be str or int")

        suit = suit.lower()
        if suit not in VALID_SUITS:
            raise ValueError(f"Invalid suit: {suit!r}")
        self.suit = suit

    @classmethod
    def from_str(cls, card_str):
        """Build a Card from a 2-character string like 'Ah', 'Td', '2c'."""
        if len(card_str) != 2:
            raise ValueError(f"Card string must be 2 chars, got {card_str!r}")
        return cls(card_str[0].upper(), card_str[1].lower())

    def __repr__(self):
        return f"{VALUE_TO_RANK_CHAR[self.rank]}{self.suit}"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    def __lt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank < other.rank

    def __hash__(self):
        return hash((self.rank, self.suit))


def parse_cards(card_strs):
    """Convert a list of card strings (e.g. ['Ah', 'Kd']) into Card objects."""
    return [Card.from_str(c) for c in card_strs]


class Deck:
    """A standard 52-card deck with shuffle/draw semantics."""

    def __init__(self, rng=None):
        import random
        self._rng = rng if rng is not None else random.Random()
        self.cards = [Card(r, s) for r in RANK_CHAR_TO_VALUE for s in VALID_SUITS]
        self._rng.shuffle(self.cards)
        self._pos = 0

    def draw(self, n=1):
        """Draw n cards from the top of the deck."""
        if self._pos + n > len(self.cards):
            raise RuntimeError("Not enough cards left in the deck")
        drawn = self.cards[self._pos:self._pos + n]
        self._pos += n
        return drawn

    def remaining(self):
        return self.cards[self._pos:]

    def __len__(self):
        return len(self.cards) - self._pos
