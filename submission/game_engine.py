from deck import Deck
from hand_evaluator import evaluate_seven_cards, compare_hands
from constants import (
    SMALL_BLIND, BIG_BLIND, SMALL_BET, BIG_BET, MAX_RAISES,
    PRE_FLOP, FLOP, TURN, RIVER,
    FOLD, CALL, RAISE
)


class GameEngine:
    """
    Heads-up Limit Texas Hold'em engine.

    Plays exactly one isolated hand per play_hand() call: blinds,
    dealing, betting rounds (correct HU turn order, fixed bet sizes
    per street, 4-bet cap), showdown, and pot distribution
    (including split pots). Alternates the dealer button
    automatically at the end of each hand.
    """

    MAX_BETS_PER_STREET = 1 + MAX_RAISES  # 4 total: 1 initial bet + 3 raises

    def __init__(self, player1, player2):
        self.players = [player1, player2]
        self.dealer_index = 0

        self.deck = None
        self.community_cards = []
        self.pot = 0

        self.street = None
        self.current_bet = 0
        self.raises_this_round = 0
        self.last_aggressor = None

        self.hand_over = False
        self.winner = None

    # -------------------------------------------------
    # Hand Setup
    # -------------------------------------------------

    def reset_hand(self):
        self.deck = Deck()
        self.deck.shuffle()

        self.community_cards = []
        self.pot = 0

        self.current_bet = 0
        self.raises_this_round = 0
        self.last_aggressor = None

        self.hand_over = False
        self.winner = None

        for player in self.players:
            player.reset_for_new_hand()

    def assign_positions(self):
        dealer = self.players[self.dealer_index]
        non_dealer = self.players[1 - self.dealer_index]

        dealer.is_dealer = True
        dealer.is_small_blind = True
        non_dealer.is_big_blind = True

    def post_blinds(self):
        sb = self.players[self.dealer_index]
        bb = self.players[1 - self.dealer_index]

        self.pot += sb.place_bet(SMALL_BLIND)
        self.pot += bb.place_bet(BIG_BLIND)

        self.current_bet = BIG_BLIND

    def deal_hole_cards(self):
        for player in self.players:
            player.receive_cards(self.deck.deal_hole_cards())

    def deal_flop(self):
        self.community_cards.extend(self.deck.deal_flop())

    def deal_turn(self):
        self.community_cards.append(self.deck.deal_turn())

    def deal_river(self):
        self.community_cards.append(self.deck.deal_river())

    # -------------------------------------------------
    # Betting Utilities
    # -------------------------------------------------

    def get_opponent(self, player):
        return self.players[1] if player is self.players[0] else self.players[0]

    def current_raise_amount(self):
        """
        Pre-Flop & Flop -> Small Bet (2)
        Turn & River    -> Big Bet (4)
        """
        return SMALL_BET if self.street in (PRE_FLOP, FLOP) else BIG_BET

    def raises_allowed(self):
        """
        True if the street hasn't hit the 4-total-bets cap yet
        (1 initial bet + up to 3 raises).
        """
        return self.raises_this_round < MAX_RAISES

    def get_legal_actions(self, player):
        amount_to_call = player.amount_to_call(self.current_bet)

        if amount_to_call == 0:
            actions = [CALL]  # acts as CHECK
            if self.raises_allowed() and player.stack > 0:
                actions.append(RAISE)
            return actions

        actions = [FOLD, CALL]
        if self.raises_allowed() and player.stack > amount_to_call:
            actions.append(RAISE)
        return actions

    def _sanitize_action(self, action, legal_actions):
        """Defends against a bot returning something illegal."""
        if isinstance(action, str) and action.upper() in legal_actions:
            return action.upper()
        if CALL in legal_actions:
            return CALL
        return FOLD

    # -------------------------------------------------
    # Action Execution
    # -------------------------------------------------

    def apply_action(self, player, action):
        if action not in self.get_legal_actions(player):
            raise ValueError(f"Illegal action: {action}")

        amount_to_call = player.amount_to_call(self.current_bet)
        opponent = self.get_opponent(player)

        if action == FOLD:
            player.fold()
            self.hand_over = True
            self.winner = opponent
            return

        if action == CALL:
            if amount_to_call > 0:
                chips = player.place_bet(amount_to_call)
                self.pot += chips
            return

        if action == RAISE:
            raise_increment = self.current_raise_amount()
            total_amount = amount_to_call + raise_increment

            chips = player.place_bet(total_amount)
            self.pot += chips

            self.current_bet += raise_increment
            self.raises_this_round += 1
            self.last_aggressor = player
            return

    # -------------------------------------------------
    # Betting Round
    # -------------------------------------------------

    def betting_round(self):
        """
        Runs one full street of betting to completion.
        Requires self.street to already be set by the caller.
        """
        if self.street == PRE_FLOP:
            current_player = self.players[self.dealer_index]
        else:
            current_player = self.players[1 - self.dealer_index]

        first_player = current_player
        self.last_aggressor = None

        while not self.hand_over:
            legal_actions = self.get_legal_actions(current_player)

            action = current_player.bot.get_action(
                hole_cards=[str(c) for c in current_player.hole_cards],
                community_cards=[str(c) for c in self.community_cards],
                pot_size=self.pot,
                stack_size=current_player.stack,
                amount_to_call=current_player.amount_to_call(self.current_bet),
                legal_actions=legal_actions
            )
            action = self._sanitize_action(action, legal_actions)

            self.apply_action(current_player, action)

            if self.hand_over:
                return

            next_player = self.get_opponent(current_player)

            if self.last_aggressor is None:
                # No raise this street yet: end once both have acted.
                if next_player is first_player:
                    break
            else:
                # A raise happened: end when action returns to the
                # last aggressor (i.e. everyone has responded to it).
                if next_player is self.last_aggressor:
                    break

            current_player = next_player

        # Prepare for the next street.
        for player in self.players:
            player.reset_betting_round()
        self.current_bet = 0
        self.raises_this_round = 0
        self.last_aggressor = None

    # -------------------------------------------------
    # Showdown
    # -------------------------------------------------

    def get_best_hand(self, player):
        seven_cards = player.hole_cards + self.community_cards
        return evaluate_seven_cards(seven_cards)

    def award_pot(self, player):
        player.win_chips(self.pot)
        self.pot = 0

    def split_pot(self):
        """
        Splits the pot evenly; any leftover chip (odd pot) goes to
        the non-dealer, rotating the bias with the button rather
        than fixing it to one player across the match.
        """
        half = self.pot // 2
        remainder = self.pot - 2 * half

        self.players[0].win_chips(half)
        self.players[1].win_chips(half)

        if remainder:
            self.players[1 - self.dealer_index].win_chips(remainder)

        self.pot = 0

    def showdown(self):
        hand1 = self.get_best_hand(self.players[0])
        hand2 = self.get_best_hand(self.players[1])

        result = compare_hands(hand1, hand2)

        if result > 0:
            self.winner = self.players[0]
            self.award_pot(self.players[0])
        elif result < 0:
            self.winner = self.players[1]
            self.award_pot(self.players[1])
        else:
            self.winner = None
            self.split_pot()

        self.hand_over = True

    # -------------------------------------------------
    # Play One Complete Hand
    # -------------------------------------------------

    def play_hand(self):
        """
        Plays one complete hand of Heads-Up Limit Hold'em.

        Returns
        -------
        Player or None
            The winning player, or None on a split pot.
        """
        self.reset_hand()
        self.assign_positions()
        self.post_blinds()
        self.deal_hole_cards()

        # Pre-Flop
        self.street = PRE_FLOP
        self.betting_round()

        # Flop
        if not self.hand_over:
            self.street = FLOP
            self.deal_flop()
            self.betting_round()

        # Turn
        if not self.hand_over:
            self.street = TURN
            self.deal_turn()
            self.betting_round()

        # River
        if not self.hand_over:
            self.street = RIVER
            self.deal_river()
            self.betting_round()

        # Showdown
        if not self.hand_over:
            self.showdown()
        else:
            self.award_pot(self.winner)

        self.dealer_index = 1 - self.dealer_index

        return self.winner
