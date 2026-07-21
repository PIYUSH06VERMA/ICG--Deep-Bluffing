"""
engine.py
---------
A from-scratch Heads-Up Limit Texas Hold'em engine.

Implements, per the assignment spec:
  * 2 players, standard 52-card deck, no external poker libraries.
  * Fixed-limit betting: FOLD / CALL / RAISE only, raise size fixed by street.
  * Correct heads-up turn order (SB acts first preflop, BB acts first
    postflop).
  * The 4-bet-per-street cap (1 initial bet + 3 raises).
  * Split pots on exact ties.
  * Each hand is an isolated episode: both stacks reset to 100 chips.

The engine is deliberately decoupled from any particular bot / strategy:
it only requires an object exposing `.get_action(...)` matching the
`BasePokerBot` signature from agent.py.
"""

import random
from dataclasses import dataclass, field

from card import make_deck, Card
from evaluator import best_hand_rank, describe

SMALL_BET = 2
BIG_BET = 4
STARTING_STACK = 100
SB_AMOUNT = 1
BB_AMOUNT = 2
MAX_BETS_PER_STREET = 4  # 1 initial bet + 3 raises

DEALER, NON_DEALER = 0, 1  # seat indices; DEALER posts the SB in heads-up


@dataclass
class HandRecord:
    """Everything a caller might want to inspect after a hand finishes."""
    hole_cards: list
    community_cards: list
    payoffs: list          # chip delta for [dealer, non_dealer], zero-sum
    pot: int
    winner: str            # 'dealer', 'non_dealer', 'split', or 'fold'
    action_log: list = field(default_factory=list)


class HeadsUpLimitHoldem:
    """
    Runs single isolated hands of HULHE between two bots.

    Usage:
        engine = HeadsUpLimitHoldem(seed=42)
        record = engine.play_hand(bot_dealer, bot_non_dealer)
    """

    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    # ------------------------------------------------------------------
    def play_hand(self, dealer_bot, non_dealer_bot):
        deck = make_deck()
        self.rng.shuffle(deck)

        hole = [[deck.pop(), deck.pop()] for _ in range(2)]  # [dealer, non_dealer]
        board = []

        stacks = [STARTING_STACK, STARTING_STACK]
        pot = 0
        contrib_total = [0, 0]  # chips each player has put in the pot this hand

        bots = {DEALER: dealer_bot, NON_DEALER: non_dealer_bot}
        action_log = []

        # ---- forced blinds --------------------------------------------------
        stacks[DEALER] -= SB_AMOUNT
        stacks[NON_DEALER] -= BB_AMOUNT
        contrib_total[DEALER] += SB_AMOUNT
        contrib_total[NON_DEALER] += BB_AMOUNT
        pot += SB_AMOUNT + BB_AMOUNT
        action_log.append(("BLINDS", SB_AMOUNT, BB_AMOUNT))

        streets = [
            ("PREFLOP", 0, SMALL_BET, [DEALER, NON_DEALER], 1),
            ("FLOP", 3, SMALL_BET, [NON_DEALER, DEALER], 0),
            ("TURN", 1, BIG_BET, [NON_DEALER, DEALER], 0),
            ("RIVER", 1, BIG_BET, [NON_DEALER, DEALER], 0),
        ]

        folded_player = None

        for street_name, n_new_cards, increment, order, init_bet_count in streets:
            for _ in range(n_new_cards):
                board.append(deck.pop())

            result = self._betting_round(
                street_name, order, increment, init_bet_count,
                stacks, contrib_total, pot, bots, hole, board, action_log,
            )
            pot = result["pot"]
            if result["folded"] is not None:
                folded_player = result["folded"]
                break

        # ---- resolve the hand -------------------------------------------
        if folded_player is not None:
            winner_seat = DEALER if folded_player == NON_DEALER else NON_DEALER
            payoffs = [0, 0]
            payoffs[winner_seat] = contrib_total[1 - winner_seat]
            payoffs[folded_player] = -contrib_total[folded_player]
            winner_label = "dealer" if winner_seat == DEALER else "non_dealer"
        else:
            cmp = self._compare(hole[DEALER] + board, hole[NON_DEALER] + board)
            if cmp > 0:
                winner_label = "dealer"
                payoffs = [contrib_total[NON_DEALER], -contrib_total[NON_DEALER]]
            elif cmp < 0:
                winner_label = "non_dealer"
                payoffs = [-contrib_total[DEALER], contrib_total[DEALER]]
            else:
                winner_label = "split"
                half = pot / 2.0
                payoffs = [half - contrib_total[DEALER], half - contrib_total[NON_DEALER]]

        return HandRecord(
            hole_cards=hole, community_cards=board, payoffs=payoffs,
            pot=pot, winner=winner_label, action_log=action_log,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _compare(cards_a, cards_b):
        ra, rb = best_hand_rank(cards_a), best_hand_rank(cards_b)
        return (ra > rb) - (ra < rb)

    # ------------------------------------------------------------------
    def _betting_round(self, street_name, order, increment, init_bet_count,
                        stacks, contrib_total, pot, bots, hole, board, action_log):
        """
        Runs one street's worth of betting. `order` = [first_to_act, second].
        Contributions are tracked relative to the start of THIS street so the
        cap rule and amount_to_call are computed correctly per-street.
        """
        street_contrib = {DEALER: 0, NON_DEALER: 0}
        if street_name == "PREFLOP":
            # blinds already posted; reflect them as this street's contributions
            street_contrib[DEALER] = SB_AMOUNT
            street_contrib[NON_DEALER] = BB_AMOUNT
        highest_bet = max(street_contrib.values())
        num_bet_actions = init_bet_count
        num_actions = 0

        while True:
            player = order[num_actions % 2]
            opponent = 1 - player
            amount_to_call = highest_bet - street_contrib[player]
            capped = num_bet_actions >= MAX_BETS_PER_STREET

            legal_actions = []
            if amount_to_call > 0:
                legal_actions.append("FOLD")
            legal_actions.append("CALL")
            can_afford_raise = stacks[player] > amount_to_call  # needs > call amount to add increment
            if not capped and can_afford_raise:
                legal_actions.append("RAISE")

            action = self._safe_get_action(
                bots[player], player, hole, board, pot, stacks, contrib_total,
                amount_to_call, legal_actions,
            )
            action_log.append((street_name, "dealer" if player == DEALER else "non_dealer", action))

            if action == "FOLD":
                return {"pot": pot, "folded": player}

            elif action == "RAISE":
                pay = amount_to_call + increment
                pay = min(pay, stacks[player])  # all-in guard
                stacks[player] -= pay
                street_contrib[player] += pay
                contrib_total[player] += pay
                pot += pay
                highest_bet = max(highest_bet, street_contrib[player])
                num_bet_actions += 1
                num_actions += 1
                continue

            else:  # CALL (covers the "check" case when amount_to_call == 0)
                pay = min(amount_to_call, stacks[player])
                stacks[player] -= pay
                street_contrib[player] += pay
                contrib_total[player] += pay
                pot += pay
                num_actions += 1
                if num_actions == 1:
                    # First action of the street never closes betting: this
                    # preserves the BB's preflop option / first-to-act's
                    # right to see the other player act once, exactly as in
                    # real heads-up limit hold'em.
                    continue
                else:
                    return {"pot": pot, "folded": None}

    # ------------------------------------------------------------------
    @staticmethod
    def _safe_get_action(bot, seat, hole, board, pot, stacks, contrib_total,
                          amount_to_call, legal_actions):
        """Calls the bot; if it misbehaves (bad return / exception), it is
        forced to take the safest legal action so a single buggy bot cannot
        crash the whole tournament arena."""
        hole_strs = [str(c) for c in hole[seat]]
        board_strs = [str(c) for c in board]
        try:
            action = bot.get_action(
                hole_cards=hole_strs,
                community_cards=board_strs,
                pot_size=pot,
                stack_size=stacks[seat],
                amount_to_call=amount_to_call,
                legal_actions=list(legal_actions),
            )
        except Exception:
            action = None
        if action not in legal_actions:
            action = "CALL" if "CALL" in legal_actions else legal_actions[0]
        return action


def run_match(bot_a, bot_b, num_hands=1000, seed=0):
    """
    Plays `num_hands` isolated hands, alternating who is dealer each hand
    (standard heads-up convention), and returns bb/100 for bot_a.
    bb/100 = (net chips won by bot_a / big_blind) / num_hands * 100
    """
    engine = HeadsUpLimitHoldem(seed=seed)
    net_a = 0.0
    for i in range(num_hands):
        if i % 2 == 0:
            record = engine.play_hand(bot_a, bot_b)
            net_a += record.payoffs[DEALER]
        else:
            record = engine.play_hand(bot_b, bot_a)
            net_a += record.payoffs[NON_DEALER]
    bb_per_100 = (net_a / BB_AMOUNT) / num_hands * 100
    return net_a, bb_per_100
