"""
equity.py
---------
Hand-strength ("equity") estimation used by CustomPokerBot.

This module contains exactly ONE technique, used identically on every
street (pre-flop, flop, turn, river): a Monte Carlo rollout built entirely
on top of our own deck (card.py) and our own hand evaluator (evaluator.py).
No external formulas, tables, or datasets of any kind are used here --
every number the bot relies on is produced at runtime by simulating random
hands and scoring them with our own code.

How it works
------------
We want p = P(win) + 0.5 * P(tie): the chance our hand beats a random
opponent hand, given whatever community cards are already known.

We estimate p by repeating this simple experiment n times:
    1. Look at every card that is still unknown to us: the opponent's
       2 hidden hole cards, plus however many community cards have not
       been dealt yet (5 pre-flop, 2 on the flop, 1 on the turn, 0 on
       the river).
    2. Deal those unknown cards uniformly at random from the remaining
       deck.
    3. Score both resulting 7-card hands with best_hand_rank() and see
       who wins.
Averaging the win/tie/loss outcomes over n trials gives an unbiased
Monte Carlo estimate of p. This is the same "simulate the possibilities
and count" idea used throughout Monte Carlo methods in general -- nothing
here is precomputed or looked up, it is simulated fresh for every single
decision.

Since pre-flop has the most unknown cards (7), each pre-flop trial is
slightly more expensive per trial than a river trial (2 unknown cards),
but the cost of scoring a hand with our evaluator does not depend on how
many cards were unknown, so in practice the extra cost is small.
"""

import random
from card import Deck

# Built once at import time and reused (read-only) on every call, instead
# of re-building a fresh 52-card deck for every single decision.
_FULL_DECK = Deck().cards

from evaluator import best_hand_rank


def estimate_equity(hole_cards, community_cards, n_iter=150, rng=None):
    """Monte Carlo estimate of P(win) + 0.5*P(tie) for `hole_cards` against
    one random opponent hand, given whatever `community_cards` are already
    known (an empty list pre-flop).

    Every trial samples only the cards that are genuinely still unknown:
    the opponent's 2 hole cards, and however many of the 5 community cards
    have not been dealt yet."""
    rng = rng or random
    known = list(hole_cards) + list(community_cards)
    known_set = set((c.value, c.suit) for c in known)

    unseen = [c for c in _FULL_DECK if (c.value, c.suit) not in known_set]

    n_missing_board = 5 - len(community_cards)
    wins = ties = 0

    for _ in range(n_iter):
        sample = rng.sample(unseen, 2 + n_missing_board)
        opp_hole = sample[:2]
        extra_board = sample[2:]
        full_board = list(community_cards) + extra_board

        hero_rank = best_hand_rank(list(hole_cards) + full_board)
        opp_rank = best_hand_rank(opp_hole + full_board)

        if hero_rank > opp_rank:
            wins += 1
        elif hero_rank == opp_rank:
            ties += 1

    return (wins + 0.5 * ties) / n_iter
