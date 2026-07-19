"""
card.py
--------
Defines the Card object used throughout the poker engine.

A card string looks like 'Ah', 'Td', '9c' etc.
- First char  = rank (2-9, T, J, Q, K, A)
- Second char = suit (h, d, c, s)  -> hearts, diamonds, clubs, spades
"""

RANKS = "23456789TJQKA"
SUITS = "hdcs"

# Map rank character -> numeric value (2 through 14, Ace high)
RANK_VALUES = {rank: index + 2 for index, rank in enumerate(RANKS)}


class Card:
    def __init__(self, card_str):
        card_str = card_str.strip()
        self.rank_char = card_str[0].upper()
        self.suit = card_str[1].lower()

        if self.rank_char not in RANK_VALUES:
            raise ValueError(f"Invalid rank in card: {card_str}")
        if self.suit not in SUITS:
            raise ValueError(f"Invalid suit in card: {card_str}")

        self.value = RANK_VALUES[self.rank_char]

    # ---- dunder methods so cards sort/compare naturally ----
    def __repr__(self):
        # This keeps the exact same string format the arena uses, e.g. 'Ah'
        return f"{self.rank_char}{self.suit}"

    def __eq__(self, other):
        return self.value == other.value and self.suit == other.suit

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value

    def __hash__(self):
        return hash((self.value, self.suit))


def cards_from_strings(card_strings):
    """Helper: ['Ah', 'Kd'] -> [Card('Ah'), Card('Kd')]"""
    return [Card(c) for c in card_strings]
