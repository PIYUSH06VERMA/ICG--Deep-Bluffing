from functools import total_ordering

RANK_ORDER = "23456789TJQKA"
RANK_TO_VALUE = {r: i + 2 for i, r in enumerate(RANK_ORDER)}  
VALUE_TO_RANK = {v: r for r, v in RANK_TO_VALUE.items()}

SUITS = set("shdc")  


@total_ordering
class Card:
    __slots__ = ("rank_char", "suit", "value")

    def __init__(self, code: str):
        if len(code) != 2 or code[0] not in RANK_TO_VALUE or code[1] not in SUITS:
            raise ValueError(f"Invalid card code: {code!r}")
        self.rank_char = code[0]
        self.suit = code[1]
        self.value = RANK_TO_VALUE[self.rank_char]  

    # ---- dunder methods -------------------------------------------------
    def __repr__(self):
        return f"{self.rank_char}{self.suit}"

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

    @staticmethod
    def parse_list(codes):
        """Convenience: turn ['Ah', 'Kd'] into [Card('Ah'), Card('Kd')]."""
        return [Card.get(c) for c in codes]

    @staticmethod
    def get(code: str):
        cached = _CARD_CACHE.get(code)
        if cached is None:
            cached = Card(code)
            _CARD_CACHE[code] = cached
        return cached


_CARD_CACHE = {}
