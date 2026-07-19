from constants import RANKS, SUITS, RANK_VALUES


class Card:
    """
    Represents a single playing card.

    Examples:
        Card('A', 'h')  -> Ace of Hearts
        Card('T', 's')  -> Ten of Spades
    """

    def __init__(self, rank, suit):
        if rank not in RANKS:
            raise ValueError(f"Invalid rank: {rank}")

        if suit not in SUITS:
            raise ValueError(f"Invalid suit: {suit}")

        self.rank = rank
        self.suit = suit
        self.value = RANK_VALUES[rank]

    @classmethod
    def from_string(cls, card_str):
        if len(card_str) != 2:
            raise ValueError(f"Invalid card string: {card_str}")

        rank = card_str[0]
        suit = card_str[1]

        return cls(rank, suit)

    def __str__(self):
        return f"{self.rank}{self.suit}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    def __lt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.value < other.value

    def __gt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.value > other.value

    def __hash__(self):
        return hash((self.rank, self.suit))
