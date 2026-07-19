"""
engine/game.py

Heads-Up Limit Texas Hold'em game engine.
"""

from __future__ import annotations

from engine.human_player import HumanPlayer
from engine.deck import Deck
from engine.player import Player
from engine.betting import BettingRound

from engine.evaluator import Evaluator
class PokerGame:

    SMALL_BLIND = 1
    BIG_BLIND = 2

    SMALL_BET = 2
    BIG_BET = 4

    def __init__(self, starting_chips: int = 100, players=None):

        if players is None:
            self.players = [
                Player("Player 1", starting_chips),
                Player("Player 2", starting_chips),
            ]
        else:
            self.players = players

        self.deck = Deck()

        self.evaluator = Evaluator()

        self.board = []

        self.dealer = 0

        self.betting = BettingRound(self.SMALL_BET)

        self.street = "PRE_FLOP"

    # -------------------------------------------------

    @property
    def small_blind(self):
        return self.players[self.dealer]

    @property
    def big_blind(self):
        return self.players[1 - self.dealer]

    # -------------------------------------------------

    def rotate_dealer(self):

        self.dealer = 1 - self.dealer

    # -------------------------------------------------

    def reset_hand(self):

        self.deck.reset()
        self.deck.shuffle()

        self.board.clear()

        self.street = "PRE_FLOP"

        self.betting = BettingRound(self.SMALL_BET)

        for player in self.players:
            player.reset_for_new_hand()

    def post_blinds(self):
        """
        Post the small blind and big blind.
        """

        self.betting.post_blind(
            self.small_blind,
            self.SMALL_BLIND
        )

        self.betting.post_blind(
            self.big_blind,
            self.BIG_BLIND
        )

    def deal_hole_cards(self):
        """
        Deal two hole cards to each player.
        Cards are dealt alternately, starting with the small blind (dealer).
        """

        for _ in range(2):
            self.small_blind.hand.add_card(
                self.deck.deal()
            )

            self.big_blind.hand.add_card(
                self.deck.deal()
            )

    # -------------------------------------------------
    # Community Cards
    # -------------------------------------------------

    def deal_flop(self):
        """
        Burn one card and deal the flop.
        """

        self.deck.burn()

        self.board.extend(self.deck.deal(3))

        self.street = "FLOP"

    def deal_turn(self):
        """
        Burn one card and deal the turn.
        """

        self.deck.burn()

        self.board.append(self.deck.deal())

        self.street = "TURN"

    def deal_river(self):
        """
        Burn one card and deal the river.
        """

        self.deck.burn()

        self.board.append(self.deck.deal())

        self.street = "RIVER"

    def legal_actions(self, player):
        """
        Returns the legal actions available to the player.
        """

        actions = []

        to_call = self.betting.amount_to_call(player)

        if to_call == 0:
            actions.append("check")
        else:
            actions.append("fold")
            actions.append("call")

        if self.betting.can_raise():
            actions.append("raise")

        return actions

    def apply_action(self, player, action):
        """
        Apply a betting action for a player.
        """

        action = action.lower()

        if action == "fold":
            self.betting.fold(player)

        elif action == "call":
            self.betting.call(player)

        elif action == "check":
            self.betting.check(player)

        elif action == "raise":
            self.betting.raise_bet(player)

        else:
            raise ValueError(f"Unknown action: {action}")

    def betting_round(self, bots):
        """
        Play one complete betting round.

        Returns
        -------
        bool
            True if betting completed normally.
            False if someone folded and the hand ended.
        """

        # Pre-flop: Small Blind acts first
        # Post-flop: Big Blind acts first
        current = self.dealer if self.street == "PRE_FLOP" else 1 - self.dealer

        # Tracks whether each player has acted since the last raise
        acted = [False, False]

        while True:

            player = self.players[current]

            # Skip all-in players
            if player.all_in:
                acted[current] = True
                current = 1 - current
                continue

            legal = self.legal_actions(player)

            # -----------------------------
            # Human or AI action
            # -----------------------------
            if isinstance(bots[current], HumanPlayer):

                print("\n" + "=" * 45)
                print("YOUR TURN")
                print("=" * 45)

                print("\nYour Cards:")
                print(*player.hand.get_cards())

                print("\nCommunity Cards:")
                if self.board:
                    print(*self.board)
                else:
                    print("(None)")

                print(f"\nPot: {self.betting.pot}")
                print(f"Your Chips: {player.chips}")
                print(f"Amount to Call: {self.betting.amount_to_call(player)}")
                print("\nLegal Actions:")
                print(", ".join(legal))

                action = bots[current].choose_action(legal)

            else:

                action = bots[current].get_action(
                    hole_cards=player.hand.get_cards(),
                    community_cards=self.board,
                    pot_size=self.betting.pot,
                    stack_size=player.chips,
                    amount_to_call=self.betting.amount_to_call(player),
                    legal_actions=legal,
                )

                print(f"\nAI chooses: {action.upper()}")

            action = action.strip().lower()

            self.apply_action(player, action)

            # Folding immediately ends the hand
            if player.folded:
                return False

            # A raise starts a new betting cycle
            if action == "raise":
                acted = [False, False]
                acted[current] = True
            else:
                acted[current] = True

            # Betting round ends only when:
            # 1. Both players have acted since the last raise.
            # 2. Both players have equal bets.
            if (
                    acted[0]
                    and acted[1]
                    and self.players[0].current_bet == self.players[1].current_bet
            ):
                return True

            # Switch player
            current = 1 - current

    def showdown(self):
        """
        Compare both hands and determine the winner.

        Returns
        -------
        Player | None
            Winning player, or None if tied.
        """

        player1 = self.players[0]
        player2 = self.players[1]

        cards1 = player1.hand.get_cards() + self.board
        cards2 = player2.hand.get_cards() + self.board

        result = self.evaluator.compare(cards1, cards2)

        if result > 0:
            return player1

        elif result < 0:
            return player2

        return None

    def award_pot(self, winner):
        """
        Award the pot to the winner.

        Parameters
        ----------
        winner : Player | None
            None indicates a tie.
        """

        pot = self.betting.pot

        if winner is None:
            split = pot // 2

            self.players[0].win(split)
            self.players[1].win(pot - split)

        else:
            winner.win(pot)

        self.betting.pot = 0

    def play_hand(self, bots):
        """
        Play one complete hand of Heads-Up Limit Texas Hold'em.

        Parameters
        ----------
        bots : list
            Two bot objects implementing get_action().
        """

        # -----------------------------
        # Start a new hand
        # -----------------------------
        self.reset_hand()

        self.post_blinds()

        self.deal_hole_cards()

        # -----------------------------
        # Pre-Flop
        # -----------------------------

        if not self.betting_round(bots):
            winner = next(player for player in self.players if not player.folded)
            self.award_pot(winner)
            self.rotate_dealer()
            return winner

        # -----------------------------
        # Flop
        # -----------------------------
        for player in self.players:
            player.reset_bet()

        self.deal_flop()

        self.betting.next_street(self.SMALL_BET)

        if not self.betting_round(bots):
            winner = next(player for player in self.players if not player.folded)
            self.award_pot(winner)
            self.rotate_dealer()
            return winner

        # -----------------------------
        # Turn
        # -----------------------------
        for player in self.players:
            player.reset_bet()

        self.deal_turn()

        self.betting.next_street(self.BIG_BET)

        if not self.betting_round(bots):
            winner = next(player for player in self.players if not player.folded)
            self.award_pot(winner)
            self.rotate_dealer()
            return winner

        # -----------------------------
        # River
        # -----------------------------
        for player in self.players:
            player.reset_bet()

        self.deal_river()

        self.betting.next_street(self.BIG_BET)

        if not self.betting_round(bots):
            winner = next(player for player in self.players if not player.folded)
            self.award_pot(winner)
            self.rotate_dealer()
            return winner

        # -----------------------------
        # Showdown
        # -----------------------------
        winner = self.showdown()

        print("\n" + "=" * 50)
        print("SHOWDOWN")
        print("=" * 50)

        for player in self.players:
            print(f"\n{player.name}:")
            print("Hole Cards:", *player.hand.get_cards())

        print("\nBoard:")
        print(*self.board)

        if winner is None:
            print("\nResult: Split Pot")
        else:
            print(f"\nWinner: {winner.name}")

        self.award_pot(winner)

        self.rotate_dealer()

        return winner




if __name__ == "__main__":

    game = PokerGame()

    game.reset_hand()

    game.post_blinds()

    game.deal_hole_cards()

    print("Hole Cards")

    for p in game.players:
        print(p.name, p.hand)

    print()

    game.deal_flop()

    print("Flop")

    print(game.board)

    print()

    game.deal_turn()

    print("Turn")

    print(game.board)

    print()

    game.deal_river()

    print("River")

    print(game.board)