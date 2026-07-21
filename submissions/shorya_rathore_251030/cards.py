"""
Card class for HULHE poker engine.

Card string format: rank + suit, e.g. 'Ah', 'Td', '9c', '2s'
Ranks: 2 3 4 5 6 7 8 9 T J Q K A   (2 lowest, A highest)
Suits: h d c s
"""

from functools import total_ordering

# Maps rank character -> numeric value (2-14, Ace high)
RANK_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
    '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14,
}
VALUE_TO_RANK = {v: k for k, v in RANK_VALUES.items()}

VALID_SUITS = {'h', 'd', 'c', 's'}


@total_ordering
class Card:
    """
    Represents a single playing card.

    Comparisons (==, <, >, etc.) are based purely on rank value,
    which is what you want for hand-strength/kicker comparisons.
    Use .suit separately when you need to check flushes.
    """

    __slots__ = ('rank', 'suit', 'value')

    def __init__(self, card_str: str):
        card_str = card_str.strip()
        if len(card_str) != 2:
            raise ValueError(f"Invalid card string: {card_str!r}")

        rank_char, suit_char = card_str[0].upper(), card_str[1].lower()

        if rank_char not in RANK_VALUES:
            raise ValueError(f"Invalid rank: {rank_char!r} in {card_str!r}")
        if suit_char not in VALID_SUITS:
            raise ValueError(f"Invalid suit: {suit_char!r} in {card_str!r}")

        self.rank = rank_char          # e.g. 'A'
        self.suit = suit_char          # e.g. 'h'
        self.value = RANK_VALUES[rank_char]  # e.g. 14

    # ---- dunder methods ----------------------------------------------

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        # Two cards are "equal" in poker-strength terms if same rank.
        # (Suit doesn't matter for equality of value; two different
        # physical cards of the same rank still compare equal here.)
        return self.value == other.value

    def __lt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.value < other.value

    def __hash__(self):
        # Hash by the exact card identity (rank+suit), NOT just value,
        # so a set of Cards behaves like a real 52-card deck.
        return hash((self.rank, self.suit))

    def __repr__(self):
        return f"{self.rank}{self.suit}"

    def __str__(self):
        return self.__repr__()

    # ---- convenience ----------------------------------------------

    @classmethod
    def from_str(cls, card_str: str) -> "Card":
        return cls(card_str)

    @staticmethod
    def parse_list(card_strs):
        """Convert a list of strings like ['Ah','Kd'] into a list of Card objects."""
        return [Card(c) for c in card_strs]


def make_deck():
    """Return a fresh, ordered 52-card deck as Card objects."""
    return [Card(r + s) for r in RANK_VALUES for s in VALID_SUITS]


if __name__ == "__main__":
    # quick sanity checks
    a = Card("Ah")
    k = Card("Kd")
    a2 = Card("As")  # same rank, different suit

    print(a, k, a2)
    print("a > k:", a > k)          # True
    print("a == a2:", a == a2)      # True (same rank)
    print("a is a2:", a is a2)      # False (different objects)
    print("hash equal (rank only)?", hash(a) == hash(a2))  # False, different suit

    hand = Card.parse_list(['7s', '7c', '2d', 'Ah', 'Kd'])
    print("sorted hand:", sorted(hand, reverse=True))

    deck = make_deck()
    print("deck size:", len(deck))
    print("deck sample:", deck[:5])
