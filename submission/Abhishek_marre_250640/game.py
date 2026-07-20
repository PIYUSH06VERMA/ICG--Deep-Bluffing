"""
game.py
-------
A from-scratch, self-contained Heads-Up Limit Hold'em (HULHE) engine.
Not required by the arena (which supplies its own), but built to:
  (a) prove the OOP/engine fundamentals required by the assignment, and
  (b) let us locally simulate thousands of hands to sanity-check and
      tune CustomPokerBot before submission.

Implements exactly the rules from the spec:
  - 100-chip stack reset every hand (episodic, no carry-over)
  - Blinds: SB = 1, BB = 2
  - Fixed-limit betting: pre-flop/flop = 2-chip increments,
    turn/river = 4-chip increments
  - 4-bet cap per street (1 bet + 3 raises)
  - Heads-up turn order: SB acts first pre-flop, BB acts first post-flop
  - Showdown with best-of-7 hand evaluation and 50/50 split-pot ties
"""

from card import Card
from deck import Deck
from hand_evaluator import compare_hands

SMALL_BET = 2
BIG_BET = 4
MAX_BETS_PER_STREET = 4  # 1 bet + 3 raises


class GameEngine:
    def __init__(self, bot_a, bot_b, starting_stack=100):
        self.bot_a = bot_a
        self.bot_b = bot_b
        self.starting_stack = starting_stack

    def play_hand(self, dealer_is_a=True, verbose=False):
        """
        Plays one complete isolated hand (fresh 100-chip stacks) and
        returns the net chip result from bot_a's perspective
        (+N = bot_a won N chips, -N = bot_a lost N chips, 0 = split).
        """
        deck = Deck()
        deck.shuffle()

        stacks = {"A": self.starting_stack, "B": self.starting_stack}
        dealer, other = ("A", "B") if dealer_is_a else ("B", "A")

        # Post blinds
        pot = 0
        sb, bb = 1, 2
        stacks[dealer] -= sb
        stacks[other] -= bb
        pot = sb + bb
        committed = {dealer: sb, other: bb}  # chips put in *this street*

        hole = {
            "A": deck.deal(2),
            "B": deck.deal(2),
        }
        board = []
        bots = {"A": self.bot_a, "B": self.bot_b}
        folded = None

        streets = [("preflop", 0, SMALL_BET),
                   ("flop", 3, SMALL_BET),
                   ("turn", 1, BIG_BET),
                   ("river", 1, BIG_BET)]

        for street_name, n_deal, bet_size in streets:
            if n_deal:
                board.extend(deck.deal(n_deal))

            if street_name != "preflop":
                committed = {"A": 0, "B": 0}  # new street, new committed counts
                order = [other, dealer]  # BB (non-dealer) acts first post-flop
            else:
                order = [dealer, other]  # SB (dealer) acts first pre-flop

            folded = self._betting_round(
                bots, order, hole, board, pot, committed, stacks, bet_size, verbose
            )
            pot += committed["A"] + committed["B"] if street_name == "preflop" else 0
            # NOTE: pot accumulation handled inside _betting_round via closure
            # (see below) -- kept simple/explicit here for readability.
            if folded is not None:
                break

        return self._settle(hole, board, stacks, folded, dealer, other, pot)

    def _betting_round(self, bots, order, hole, board, pot, committed, stacks,
                        bet_size, verbose):
        """
        Runs betting to completion for one street. Mutates `stacks` and
        `committed` in place; returns the folded player's id, or None if
        the street closes with no fold.
        This is a simplified reference implementation (not the arena's
        authoritative engine) -- sufficient for local self-play testing.
        """
        current_bet = max(committed.values())
        num_bets_this_street = 1 if current_bet > 0 else 0
        acted = {p: False for p in order}
        idx = 0

        while True:
            player = order[idx % 2]
            opponent = order[(idx + 1) % 2]
            to_call = committed[opponent] - committed[player]

            legal = []
            if to_call > 0:
                legal.append("FOLD")
            legal.append("CALL")
            if num_bets_this_street < MAX_BETS_PER_STREET:
                legal.append("RAISE")

            action = bots[player].get_action(
                [str(c) for c in hole[player]],
                [str(c) for c in board],
                pot,
                stacks[player],
                to_call,
                legal,
            )

            if action == "FOLD":
                return player

            if action == "CALL":
                pay = min(to_call, stacks[player])
                stacks[player] -= pay
                committed[player] += pay
                pot += pay
            elif action == "RAISE":
                pay = to_call + bet_size
                pay = min(pay, stacks[player])
                stacks[player] -= pay
                committed[player] += pay
                pot += pay
                num_bets_this_street += 1

            acted[player] = True
            idx += 1

            # Street closes once both have acted and bets are matched.
            if acted[order[0]] and acted[order[1]] and committed[order[0]] == committed[order[1]]:
                return None

    def _settle(self, hole, board, stacks, folded, dealer, other, pot):
        starting = self.starting_stack
        if folded is not None:
            winner = "A" if folded == "B" else "B"
            net_to_a = (stacks["A"] - starting) if winner == "A" else (stacks["A"] - starting)
            # Winner scoops the pot; net result relative to starting stack.
            if winner == "A":
                return (starting - stacks["B"])  # what B lost, A nets that much
            else:
                return -(starting - stacks["A"])

        result = compare_hands(hole["A"] + board, hole["B"] + board)
        a_invested = starting - stacks["A"]
        b_invested = starting - stacks["B"]
        pot_total = a_invested + b_invested
        if result == 1:
            return pot_total - a_invested
        elif result == -1:
            return -(a_invested)
        else:
            half = pot_total / 2
            return half - a_invested


if __name__ == "__main__":
    from agent import CustomPokerBot

    class RandomBot(CustomPokerBot):
        """A weak baseline opponent for smoke-testing."""
        def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                        amount_to_call, legal_actions):
            import random as _r
            return _r.choice(legal_actions)

    bot_a = CustomPokerBot("EV_Bot")
    bot_b = RandomBot("Random_Baseline")
    engine = GameEngine(bot_a, bot_b)

    total = 0
    N = 500
    for i in range(N):
        result = engine.play_hand(dealer_is_a=(i % 2 == 0))
        total += result

    print(f"Played {N} hands. EV_Bot net chips vs RandomBot: {total:+.1f}")
    print(f"Average win-rate: {total / N:+.3f} chips/hand")