from constants import INITIAL_STACK

class Player:
    """
    Represents a poker player.
    """

    def __init__(self, name, bot=None):
        self.name = name
        self.bot = bot
        self.stack = INITIAL_STACK

        self.hole_cards = []
        self.current_bet = 0
        self.folded = False

        self.is_dealer = False
        self.is_small_blind = False
        self.is_big_blind = False

    def reset_for_new_hand(self):
        self.hole_cards.clear()
        self.current_bet = 0
        self.folded = False
        self.is_dealer = False
        self.is_small_blind = False
        self.is_big_blind = False

    def receive_card(self, card):
        if len(self.hole_cards) >= 2:
            raise ValueError("Player already has two hole cards.")
        self.hole_cards.append(card)

    def receive_cards(self, cards):
        for card in cards:
            self.receive_card(card)

    def clear_hand(self):
        self.hole_cards.clear()

    def bet(self, amount):
        if amount < 0:
            raise ValueError("Bet amount cannot be negative.")
        if amount > self.stack:
            raise ValueError("Player does not have enough chips.")
        self.stack -= amount
        self.current_bet += amount

    def place_bet(self, amount):
        actual_amount = min(amount, self.stack)
        self.bet(actual_amount)
        return actual_amount

    def amount_to_call(self, highest_bet):
        return max(0, highest_bet - self.current_bet)

    def reset_bet(self):
        self.current_bet = 0

    def reset_betting_round(self):
        self.reset_bet()

    def win_chips(self, amount):
        if amount < 0:
            raise ValueError("Cannot win negative chips.")
        self.stack += amount

    def fold(self):
        self.folded = True

    def __repr__(self):
        return (
            f"Player("
            f"name={self.name}, "
            f"stack={self.stack}, "
            f"cards={self.hole_cards}, "
            f"bet={self.current_bet}, "
            f"folded={self.folded})"
        )
