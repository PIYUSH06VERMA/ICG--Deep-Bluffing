"""
agent.py
--------
Entry point for the Deep-Bluffing tournament arena.

Strategy archetype chosen: Monte-Carlo equity estimation + closed-form
Expected-Value decision rule, balanced with a game-theoretically motivated
bluffing frequency (the "Minimum Defense Frequency" / optimal-bluff-ratio
idea from simplified poker game theory). This is the "deep mathematical
EV heuristics" archetype explicitly permitted by the assignment, and it
needs no external poker libraries or pretrained lookup tables - only
`random`, `itertools`/`collections` (via evaluator.py) and `math`.

See report.pdf for the full mathematical derivation and justification.
"""

import math
import random
from functools import lru_cache

from card import Card, RANK_TO_VALUE
from evaluator import fast_rank7

# ---------------------------------------------------------------------
# Tunable constants (all justified in report.pdf, Section 3)
# ---------------------------------------------------------------------
ROLLOUTS_PREFLOP = 60      # more streets left -> cheaper per-call budget needed
ROLLOUTS_POSTFLOP = 80     # fewer unknown cards -> rollouts converge faster anyway

VALUE_RAISE_MARGIN = 0.06   # how far above breakeven equity must be to raise for value
FOLD_MARGIN = 0.04          # how far below breakeven equity before we fold outright
BLUFF_SCALE = 0.9           # scales the game-theoretic optimal bluff frequency down
                             # (0.9 = slightly under-bluff to stay robust to weak calling stations)

_ALL_CARD_STRS = [f"{r}{s}" for r in "23456789TJQKA" for s in "hdcs"]


class BasePokerBot:
    def __init__(self, name):
        self.name = name

    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        """
        Calculates the optimal move for Limit Texas Hold'em.

        Parameters:
        - hole_cards (list): Your two private cards, e.g., ['Ah', 'Kd']
        - community_cards (list): Shared public cards, e.g., ['7s', '7c', '2d'] (Empty pre-flop)
        - pot_size (int): Total chips currently in the middle pot
        - stack_size (int): Your remaining chips in your stack
        - amount_to_call (int): Chips required to put in to stay in the hand
        - legal_actions (list): Available valid moves, e.g., ['FOLD', 'CALL', 'RAISE']

        Returns:
        - A string exactly matching ONE of the elements in legal_actions.
        """
        raise NotImplementedError("Your bot logic goes here!")


# -----------------------------------------------------------------------
# Equity estimation
# -----------------------------------------------------------------------
def _remaining_deck(known_card_strs):
    known = set(known_card_strs)
    return [c for c in _ALL_CARD_STRS if c not in known]


def _to_pair(card_str):
    return (RANK_TO_VALUE[card_str[0].upper()], card_str[1].lower())


def estimate_equity(hole_cards, community_cards, rollouts, rng):
    """
    Monte-Carlo estimate of P(win) + 0.5 * P(tie) against a *uniformly
    random* opponent holding, given the cards seen so far.

    This is the standard "hand equity via rollout" technique: repeatedly
    sample a plausible completion of the unknown information (opponent's
    hole cards + the remaining board) and average the resulting win/lose/
    tie outcome. By the Law of Large Numbers this converges to the true
    equity as rollouts -> inf, with standard error ~ sqrt(p(1-p)/N)
    (derived and used in report.pdf to choose N).

    Uses `fast_rank7` (a single-pass, combination-free evaluator, verified
    equivalent to the reference combos-based evaluator by a 200k-hand
    randomised test) since this function is the hot path, called
    thousands of times per hand across a large tournament.
    """
    known = set(hole_cards) | set(community_cards)
    deck = [c for c in _ALL_CARD_STRS if c not in known]

    my_pairs = [_to_pair(c) for c in hole_cards]
    board_pairs = [_to_pair(c) for c in community_cards]
    n_board_needed = 5 - len(board_pairs)

    wins = 0.0
    for _ in range(rollouts):
        sample = rng.sample(deck, 2 + n_board_needed)
        opp_pairs = [_to_pair(c) for c in sample[:2]]
        extra_board = [_to_pair(c) for c in sample[2:2 + n_board_needed]]
        full_board = board_pairs + extra_board

        my_rank = fast_rank7(my_pairs + full_board)
        opp_rank = fast_rank7(opp_pairs + full_board)
        if my_rank > opp_rank:
            wins += 1.0
        elif my_rank == opp_rank:
            wins += 0.5
    return wins / rollouts


# -----------------------------------------------------------------------
# Decision policy
# -----------------------------------------------------------------------
class CustomPokerBot(BasePokerBot):
    """
    Decision rule (fully derived in report.pdf):

    1. Estimate equity `e` = P(win) via Monte-Carlo rollout against a
       random opponent hand.
    2. Compute break-even equity (pot odds) `p* = amount_to_call /
       (pot_size + amount_to_call)`  -- calling is +EV iff e > p*.
    3. If e is comfortably above p* (by VALUE_RAISE_MARGIN) -> RAISE for value.
       If e is comfortably below p* (by FOLD_MARGIN) -> FOLD, UNLESS a
       balanced bluff-raise is warranted (see step 4).
       Otherwise -> CALL (indifference zone / pot-odds justified call).
    4. Bluffing frequency: when facing a bet, a game-theoretically balanced
       opponent must sometimes call even against a bet with weak holdings,
       and a well-balanced bettor must sometimes bet weak hands too, or
       they become exploitable by always-fold / always-raise counters.
       We use the classic simplified-game optimal-bluff ratio
           bluff_freq = bet_size / (pot_size_after_bet)
       (the same ratio that sets an opponent's Minimum Defense Frequency)
       scaled down slightly by BLUFF_SCALE for robustness, and roll a
       weighted die on weak hands to occasionally raise as a bluff instead
       of folding outright.
    """

    def __init__(self, name="DeepBluffingBot", seed=None):
        super().__init__(name)
        self.rng = random.Random(seed)
        self._equity_cache = {}
        self._cached_hole = None

    def _cached_equity(self, hole_cards, community_cards, rollouts):
        # Repeated raise/re-raise exchanges on the *same* street call
        # get_action multiple times with identical hole+board cards; caching
        # avoids re-running Monte-Carlo rollouts for information that hasn't
        # changed, which matters a lot at 10,000-hand tournament scale.
        key = (tuple(sorted(hole_cards)), tuple(sorted(community_cards)))
        if key not in self._equity_cache:
            self._equity_cache[key] = estimate_equity(hole_cards, community_cards, rollouts, self.rng)
        return self._equity_cache[key]

    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        hole_key = tuple(sorted(hole_cards))
        if hole_key != self._cached_hole:
            # New hole cards -> a brand new hand -> stale cache entries
            # (from the previous hand) are useless; clear it.
            self._equity_cache.clear()
            self._cached_hole = hole_key
        rollouts = ROLLOUTS_PREFLOP if len(community_cards) == 0 else ROLLOUTS_POSTFLOP
        equity = self._cached_equity(hole_cards, community_cards, rollouts)

        can_raise = "RAISE" in legal_actions
        can_fold = "FOLD" in legal_actions

        if amount_to_call == 0:
            # We can CHECK (encoded as CALL) or bet out (RAISE).
            if equity >= 0.5 + VALUE_RAISE_MARGIN and can_raise:
                return "RAISE"
            if equity < 0.35 and can_raise:
                # Semi-bluff / lead out with a weak hand at low frequency to
                # stay unpredictable and to fold-equity-harvest.
                bluff_freq = BLUFF_SCALE * 0.15
                if self.rng.random() < bluff_freq:
                    return "RAISE"
            return "CALL"  # i.e. check

        # Facing a bet: compute break-even equity (pot odds threshold).
        break_even = amount_to_call / (pot_size + amount_to_call)

        if equity >= break_even + VALUE_RAISE_MARGIN and can_raise:
            return "RAISE"

        if equity < break_even - FOLD_MARGIN:
            if can_raise:
                # Game-theoretic bluff-raise frequency: the ratio that keeps
                # a rational opponent indifferent to calling, derived from
                # the simplified one-street betting game (see report.pdf,
                # Section 4.2): bluff_freq = amount_to_call / (pot_size + 2*amount_to_call)
                bluff_freq = BLUFF_SCALE * (amount_to_call / (pot_size + 2 * amount_to_call))
                if self.rng.random() < bluff_freq:
                    return "RAISE"
            if can_fold:
                return "FOLD"
            return "CALL"

        # Indifference zone: pot odds (marginally) justify continuing.
        return "CALL"


if __name__ == "__main__":
    # Tiny smoke test so the module can be sanity-checked in isolation.
    bot = CustomPokerBot(name="SmokeTest", seed=1)
    action = bot.get_action(
        hole_cards=["Ah", "Kh"],
        community_cards=[],
        pot_size=3,
        stack_size=99,
        amount_to_call=1,
        legal_actions=["FOLD", "CALL", "RAISE"],
    )
    print("Preflop action with AhKh facing a 1-chip call:", action)
