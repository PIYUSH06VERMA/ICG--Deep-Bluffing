"""
Heads-Up Limit Hold'em (HULHE) Game Engine.

Depends on: cards.py (Card, make_deck), hand_evaluator.py (evaluate_hand, compare_hands)


Rules implemented (per project spec):
- Heads-up, 100 chip stack reset every hand
- Blinds: SB = 1, BB = 2
- Streets: Preflop, Flop, Turn, River, Showdown
- Bet sizes: 2 chips (preflop/flop), 4 chips (turn/river)
- Bet cap: max 4 total bets per street (1 bet + 3 raises)
- Turn order: SB acts first preflop, BB acts first postflop
- Split pots on ties
"""

import random
from collections import deque

from cards import Card, make_deck
from hand_evaluator import evaluate_hand, compare_hands, hand_category_name

# ---- Constants ----------------------------------------------------------
STARTING_STACK = 100
SMALL_BLIND = 1
BIG_BLIND = 2
SMALL_BET = 2       # preflop & flop raise increment
BIG_BET = 4         # turn & river raise increment
MAX_BETS_PER_STREET = 4   # 1 initial bet + 3 raises

PREFLOP, FLOP, TURN, RIVER, SHOWDOWN = "PREFLOP", "FLOP", "TURN", "RIVER", "SHOWDOWN"
STREETS = [PREFLOP, FLOP, TURN, RIVER]

FOLD, CALL, RAISE = "FOLD", "CALL", "RAISE"


class Player:
    def __init__(self, name, agent, is_dealer):
        self.name = name
        self.agent = agent            # object with get_action(...)
        self.is_dealer = is_dealer    # dealer == small blind, heads-up
        self.stack = STARTING_STACK
        self.hole_cards = []
        self.folded = False
        self.total_committed = 0      # chips put into pot this HAND
        self.street_committed = 0     # chips put into pot THIS STREET

    def reset_for_hand(self):
        self.stack = STARTING_STACK
        self.hole_cards = []
        self.folded = False
        self.total_committed = 0
        self.street_committed = 0

    def reset_for_street(self):
        self.street_committed = 0


class HULHEEngine:
    """
    Runs a single heads-up limit hold'em hand (or many, via play_match)
    between two agents that expose:
        get_action(hole_cards, community_cards, pot_size, stack_size,
                   amount_to_call, legal_actions) -> 'FOLD' | 'CALL' | 'RAISE'
    """

    def __init__(self, agent_a, agent_b, name_a="A", name_b="B", verbose=False, seed=None):
        self.players = [
            Player(name_a, agent_a, is_dealer=True),
            Player(name_b, agent_b, is_dealer=False),
        ]
        self.verbose = verbose
        self.pot = 0
        self.community_cards = []
        self.deck = []
        self.rng = random.Random(seed)

    def _log(self, *args):
        if self.verbose:
            print(*args)

    # ---------------------------------------------------------------
    # Single hand
    # ---------------------------------------------------------------
    def play_hand(self):
        """
        Plays one full hand from blinds to showdown/fold.
        Alternates dealer button between calls via swap_dealer().
        Returns dict with results: {'winner': name or None (split),
                                     'pot': int, 'stacks': {name: stack}}
        """
        for p in self.players:
            p.reset_for_hand()

        self.pot = 0
        self.community_cards = []
        self.deck = make_deck()
        self.rng.shuffle(self.deck)

        dealer = self._dealer()
        other = self._non_dealer()

        # Post blinds
        self._post_blind(dealer, SMALL_BLIND)
        self._post_blind(other, BIG_BLIND)

        # Deal hole cards
        for p in self.players:
            p.hole_cards = [self.deck.pop(), self.deck.pop()]

        self._log(f"-- New hand -- Dealer(SB): {dealer.name}, BB: {other.name}")
        self._log(f"{dealer.name} hole cards: {dealer.hole_cards}")
        self._log(f"{other.name} hole cards: {other.hole_cards}")

        # Betting rounds
        for street in STREETS:
            if self._hand_over():
                break

            if street != PREFLOP:
                self._deal_community(street)

            self._run_betting_round(street)

        result = self._resolve_hand()
        self._log(f"Result: {result}\n")
        return result

    def swap_dealer(self):
        """Call between hands to alternate the button, as real matches do."""
        self.players[0].is_dealer, self.players[1].is_dealer = (
            self.players[1].is_dealer,
            self.players[0].is_dealer,
        )

    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------
    def _dealer(self):
        return self.players[0] if self.players[0].is_dealer else self.players[1]

    def _non_dealer(self):
        return self.players[1] if self.players[0].is_dealer else self.players[0]

    def _post_blind(self, player, amount):
        amount = min(amount, player.stack)  # can't post more than stack (edge case)
        player.stack -= amount
        player.street_committed += amount
        player.total_committed += amount
        self.pot += amount

    def _deal_community(self, street):
        # burn-free simplified dealing (spec doesn't mention burn cards)
        if street == FLOP:
            self.community_cards += [self.deck.pop() for _ in range(3)]
        elif street in (TURN, RIVER):
            self.community_cards.append(self.deck.pop())
        self._log(f"{street}: {self.community_cards}")

    def _hand_over(self):
        return any(p.folded for p in self.players)

    def _bet_increment(self, street):
        return SMALL_BET if street in (PREFLOP, FLOP) else BIG_BET

    def _active_and_other(self, first_actor):
        second_actor = self.players[0] if first_actor is self.players[1] else self.players[1]
        return first_actor, second_actor

    # ---------------------------------------------------------------
    # Betting round
    # ---------------------------------------------------------------
    def _run_betting_round(self, street):
        for p in self.players:
            p.reset_for_street()

        dealer = self._dealer()
        other = self._non_dealer()

        # Turn order: preflop SB(dealer) first; postflop BB(other) first
        first_actor = dealer if street == PREFLOP else other
        second_actor = other if street == PREFLOP else dealer

        increment = self._bet_increment(street)

        # On preflop, the blinds count as the "first bet" already in for BB;
        # current highest bet on the street = max street_committed so far.
        num_bets_this_street = 1 if street == PREFLOP else 0
        # (preflop: BB posting 2 counts as the opening "bet" for cap purposes)

        current_bettor = first_actor
        acted_since_last_raise = set()

        # We loop actions until betting is closed:
        # betting closes when both players have acted AND their
        # street_committed amounts are equal (or someone folded).
        while True:
            if self._hand_over():
                return

            opponent = second_actor if current_bettor is first_actor else first_actor
            amount_to_call = opponent.street_committed - current_bettor.street_committed
            amount_to_call = max(amount_to_call, 0)

            legal_actions = self._legal_actions(amount_to_call, num_bets_this_street)

            action = self._get_agent_action(current_bettor, amount_to_call, legal_actions)

            if action == FOLD:
                current_bettor.folded = True
                self._log(f"{current_bettor.name} folds")
                return

            elif action == CALL:
                pay = min(amount_to_call, current_bettor.stack)
                current_bettor.stack -= pay
                current_bettor.street_committed += pay
                current_bettor.total_committed += pay
                self.pot += pay
                self._log(f"{current_bettor.name} calls {pay}")
                acted_since_last_raise.add(current_bettor.name)

                # Round ends if both have now acted and bets are equal
                if opponent.street_committed == current_bettor.street_committed:
                    return

            elif action == RAISE:
                total_owed = amount_to_call + increment
                pay = min(total_owed, current_bettor.stack)
                current_bettor.stack -= pay
                current_bettor.street_committed += pay
                current_bettor.total_committed += pay
                self.pot += pay
                num_bets_this_street += 1
                acted_since_last_raise = {current_bettor.name}
                self._log(f"{current_bettor.name} raises to {current_bettor.street_committed} "
                          f"(bets this street: {num_bets_this_street})")

            else:
                raise ValueError(f"Illegal action returned by agent: {action!r}")

            # switch turn
            current_bettor = opponent

    def _legal_actions(self, amount_to_call, num_bets_this_street):
        actions = [FOLD, CALL]
        if num_bets_this_street < MAX_BETS_PER_STREET:
            actions.append(RAISE)
        return actions

    def _get_agent_action(self, player, amount_to_call, legal_actions):
        action = player.agent.get_action(
            hole_cards=[str(c) for c in player.hole_cards],
            community_cards=[str(c) for c in self.community_cards],
            pot_size=self.pot,
            stack_size=player.stack,
            amount_to_call=amount_to_call,
            legal_actions=legal_actions,
        )
        if action not in legal_actions:
            # Arena would crash/zero the bot; locally we just force a fold
            # so you notice the bug during testing instead of silently
            # corrupting the simulation.
            self._log(f"WARNING: {player.name} returned illegal action {action!r}, "
                      f"forcing FOLD")
            return FOLD
        return action

    # ---------------------------------------------------------------
    # Showdown / resolution
    # ---------------------------------------------------------------
    def _resolve_hand(self):
        p0, p1 = self.players

        if p0.folded or p1.folded:
            winner = p1 if p0.folded else p0
            winner.stack += self.pot
            return {
                "winner": winner.name,
                "pot": self.pot,
                "went_to_showdown": False,
                "stacks": {p.name: p.stack for p in self.players},
            }

        # Showdown
        score0 = evaluate_hand(p0.hole_cards + self.community_cards)
        score1 = evaluate_hand(p1.hole_cards + self.community_cards)
        cmp = compare_hands(score0, score1)

        if cmp == 0:
            split = self.pot // 2
            remainder = self.pot - split * 2
            p0.stack += split
            p1.stack += split + remainder  # give odd chip to p1 arbitrarily
            winner_name = None
        elif cmp == 1:
            p0.stack += self.pot
            winner_name = p0.name
        else:
            p1.stack += self.pot
            winner_name = p1.name

        return {
            "winner": winner_name,
            "pot": self.pot,
            "went_to_showdown": True,
            "p0_hand": hand_category_name(score0),
            "p1_hand": hand_category_name(score1),
            "stacks": {p.name: p.stack for p in self.players},
        }

    # ---------------------------------------------------------------
    # Match runner (many hands, alternating button)
    # ---------------------------------------------------------------
    def play_match(self, num_hands=100):
        results = []
        for i in range(num_hands):
            result = self.play_hand()
            results.append(result)
            self.swap_dealer()
        return results


# =========================================================================
# Simple demo agents so you can smoke-test the engine right now
# =========================================================================
class RandomAgent:
    """Plays a legal action at random. Useful as a baseline opponent."""
    def __init__(self, name="RandomBot", seed=None):
        self.name = name
        self.rng = random.Random(seed)

    def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                    amount_to_call, legal_actions):
        return self.rng.choice(legal_actions)


class AlwaysCallAgent:
    """Never folds or raises; calls/checks everything. Good sanity baseline."""
    def __init__(self, name="CallingStation"):
        self.name = name

    def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                    amount_to_call, legal_actions):
        return CALL if CALL in legal_actions else legal_actions[0]


if __name__ == "__main__":
    agent_a = RandomAgent("RandomA", seed=1)
    agent_b = AlwaysCallAgent("CallerB")

    engine = HULHEEngine(agent_a, agent_b, name_a="RandomA", name_b="CallerB",
                          verbose=True, seed=42)

    # Play a single verbose hand to inspect behaviour
    engine.play_hand()

    # Now run a silent multi-hand match and summarize results
    engine2 = HULHEEngine(RandomAgent("RandomA", seed=7), AlwaysCallAgent("CallerB"),
                           name_a="RandomA", name_b="CallerB", verbose=False, seed=123)
    results = engine2.play_match(num_hands=500)

    wins_a = sum(1 for r in results if r["winner"] == "RandomA")
    wins_b = sum(1 for r in results if r["winner"] == "CallerB")
    splits = sum(1 for r in results if r["winner"] is None)
    print(f"\nOver {len(results)} hands: RandomA won {wins_a}, "
          f"CallerB won {wins_b}, splits {splits}")
