"""
engine.py
---------
A from-scratch Heads-Up Limit Texas Hold'em (HULHE) engine, built purely
with Object-Oriented Python (no external poker libraries), used to locally
validate agents that implement the BasePokerBot API before they are
submitted to the tournament arena.

Rules implemented (per the assignment spec):
    * 2 players, isolated episodic hands, fresh 100-chip stack each hand.
    * Blinds: SB = 1, BB = 2 (button posts SB).
    * Turn order: pre-flop SB acts first; post-flop BB acts first.
    * Fixed-limit betting: Small Bet = 2 (pre-flop/flop),
                            Big Bet   = 4 (turn/river).
    * Bet cap: max 4 total bets per street (1 bet + 3 raises).
    * Actions: FOLD / CALL (=CHECK when amount_to_call==0) / RAISE.
    * Showdown with best-of-7 evaluation and split pots on exact ties.
"""

import random
from card import Card, Deck
from evaluator import best_hand_rank, hand_category_name


class IllegalActionError(Exception):
    pass


class HandResult:
    def __init__(self, payoff_p0, payoff_p1, log):
        self.payoff_p0 = payoff_p0   # net chip change for player 0 this hand
        self.payoff_p1 = payoff_p1
        self.log = log


class HeadsUpLimitHoldem:
    STARTING_STACK = 100
    SB_AMOUNT = 1
    BB_AMOUNT = 2

    def __init__(self, bot0, bot1, rng=None, verbose=False):
        self.bots = [bot0, bot1]
        self.rng = rng or random.Random()
        self.verbose = verbose

    def _bet_increment(self, street):
        return 2 if street in ("PREFLOP", "FLOP") else 4

    def _log(self, msg, log):
        log.append(msg)
        if self.verbose:
            print(msg)

    def play_hand(self, button=0):
        """button: index (0 or 1) of the player who is Dealer/Small Blind."""
        log = []
        deck = Deck()
        deck.shuffle(self.rng)

        stacks = [self.STARTING_STACK, self.STARTING_STACK]
        other = 1 - button

        hole = {button: deck.draw(2), other: deck.draw(2)}

        # Post blinds
        contrib = {button: self.SB_AMOUNT, other: self.BB_AMOUNT}
        stacks[button] -= self.SB_AMOUNT
        stacks[other] -= self.BB_AMOUNT
        pot = self.SB_AMOUNT + self.BB_AMOUNT
        self._log(f"Blinds posted: P{button}(SB)=1 P{other}(BB)=2", log)

        community = []
        streets = ["PREFLOP", "FLOP", "TURN", "RIVER"]
        folded_player = None

        current_bet = self.BB_AMOUNT  # highest total contributed this street

        for street in streets:
            if street != "PREFLOP":
                current_bet = 0
                contrib = {0: 0, 1: 0}
                if street == "FLOP":
                    community.extend([c.__repr__() for c in deck.draw(3)])
                else:
                    community.extend([c.__repr__() for c in deck.draw(1)])
                self._log(f"-- {street}: board={community} pot={pot}", log)

            # who acts first this street
            if street == "PREFLOP":
                order = [button, other]
                current_bet = self.BB_AMOUNT
                contrib = {button: self.SB_AMOUNT, other: self.BB_AMOUNT}
            else:
                order = [other, button]

            bets_this_street = 1 if street == "PREFLOP" else 0
            MAX_BETS = 4
            acted = {0: False, 1: False}
            idx = 0
            last_raiser = None

            while True:
                p = order[idx % 2]
                to_call = current_bet - contrib[p]

                if acted[p] and to_call == 0 and (last_raiser is None or last_raiser != p):
                    # betting round closes: both have acted and are level
                    break

                legal = []
                if to_call > 0:
                    legal.append("FOLD")
                legal.append("CALL")  # CALL doubles as CHECK when to_call == 0
                if bets_this_street < MAX_BETS and stacks[p] > to_call:
                    legal.append("RAISE")

                hole_strs = [str(c) for c in hole[p]]
                action = self.bots[p].get_action(
                    hole_cards=hole_strs,
                    community_cards=list(community),
                    pot_size=pot,
                    stack_size=stacks[p],
                    amount_to_call=to_call,
                    legal_actions=list(legal),
                )
                if action not in legal:
                    # Invalid action -> treat as forced fold (arena would 0/penalize)
                    self._log(f"P{p} produced illegal action {action!r} (legal={legal}); auto-fold", log)
                    action = "FOLD"

                if action == "FOLD":
                    folded_player = p
                    self._log(f"P{p} FOLDS", log)
                    break
                elif action == "CALL":
                    pay = to_call
                    stacks[p] -= pay
                    contrib[p] += pay
                    pot += pay
                    acted[p] = True
                    self._log(f"P{p} {'CHECKS' if to_call == 0 else f'CALLS {pay}'}", log)
                elif action == "RAISE":
                    inc = self._bet_increment(street)
                    pay = to_call + inc
                    pay = min(pay, stacks[p])  # simplistic cap at stack (no side pots needed at 100/4 scale)
                    stacks[p] -= pay
                    contrib[p] += pay
                    pot += pay
                    current_bet = contrib[p]
                    bets_this_street += 1
                    acted[p] = True
                    last_raiser = p
                    acted[1 - p] = False
                    self._log(f"P{p} RAISES to {current_bet} (pot={pot})", log)

                idx += 1
                if folded_player is not None:
                    break

            if folded_player is not None:
                break

        # Resolve hand
        if folded_player is not None:
            winner = 1 - folded_player
            stacks[winner] += pot
            payoff0 = stacks[0] - self.STARTING_STACK
            payoff1 = stacks[1] - self.STARTING_STACK
            self._log(f"P{folded_player} folded. P{winner} wins pot of {pot}.", log)
        else:
            r0 = best_hand_rank([str(c) for c in hole[0]] + community)
            r1 = best_hand_rank([str(c) for c in hole[1]] + community)
            if r0 > r1:
                stacks[0] += pot
                self._log(f"Showdown: P0 wins with {hand_category_name(r0)}", log)
            elif r1 > r0:
                stacks[1] += pot
                self._log(f"Showdown: P1 wins with {hand_category_name(r1)}", log)
            else:
                stacks[0] += pot / 2
                stacks[1] += pot / 2
                self._log(f"Showdown: SPLIT POT with {hand_category_name(r0)}", log)
            payoff0 = stacks[0] - self.STARTING_STACK
            payoff1 = stacks[1] - self.STARTING_STACK

        return HandResult(payoff0, payoff1, log)

    def play_match(self, n_hands=1000):
        total0, total1 = 0.0, 0.0
        for i in range(n_hands):
            button = i % 2
            res = self.play_hand(button=button)
            total0 += res.payoff_p0
            total1 += res.payoff_p1
        return total0, total1
