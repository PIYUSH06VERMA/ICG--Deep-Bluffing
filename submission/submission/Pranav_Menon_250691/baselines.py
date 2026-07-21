"""
baselines.py
------------
Simple opponent bots used only for local validation / benchmarking of
CustomPokerBot. These are NOT part of the graded submission; they mimic
the kind of baseline agents the tournament arena is likely to include.
"""
import random
from agent import BasePokerBot


class AlwaysFoldBot(BasePokerBot):
    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        if "FOLD" in legal_actions:
            return "FOLD"
        return "CALL"


class AlwaysCallBot(BasePokerBot):
    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        return "CALL"


class AlwaysRaiseBot(BasePokerBot):
    """A maximally aggressive maniac: raises whenever legal."""
    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        if "RAISE" in legal_actions:
            return "RAISE"
        return "CALL"


class RandomBot(BasePokerBot):
    def __init__(self, name="RandomBot", seed=None):
        super().__init__(name)
        self.rng = random.Random(seed)

    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        return self.rng.choice(legal_actions)


class TightAggressiveBot(BasePokerBot):
    """A crude but non-trivial heuristic baseline: plays premium hole cards
    aggressively preflop, otherwise folds to any bet; check/calls small
    postflop bets with any pair-or-better made hand. Useful as a slightly
    stronger sanity-check opponent than the purely static bots above."""
    PREMIUM_RANKS = set("AKQJT")

    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        ranks = [c[0].upper() for c in hole_cards]
        is_pair = ranks[0] == ranks[1]
        is_premium = is_pair or all(r in self.PREMIUM_RANKS for r in ranks)
        if len(community_cards) == 0:
            if is_premium:
                return "RAISE" if "RAISE" in legal_actions else "CALL"
            if amount_to_call == 0:
                return "CALL"
            return "FOLD" if "FOLD" in legal_actions else "CALL"
        # postflop: just call small amounts, fold to big ones
        if amount_to_call == 0:
            return "CALL"
        if amount_to_call <= 4:
            return "CALL"
        return "FOLD" if "FOLD" in legal_actions else "CALL"
