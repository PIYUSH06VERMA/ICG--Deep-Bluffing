"""
agent.py
---------
CRITICAL FILE: this is the exact entry point the tournament arena loads.
Do not rename this file or change the BasePokerBot class signature.

STRATEGY OVERVIEW (v3 — adds a trained CFR strategy on top of v2):

0. CFR STRATEGY (primary, when available):
   cfr_trainer.py trains a Counterfactual Regret Minimization strategy over
   an ABSTRACTED version of the game (5 hand-strength buckets instead of
   exact cards -- see cfr_trainer.py for the full methodology). The
   resulting lookup table (cfr_strategy.json) maps an infoset
   (bucket, street, bets_count, facing_bet) to a trained action
   probability distribution. When the current game state matches a
   trained infoset, we sample our action from that distribution -- this
   is the game-theoretically grounded part of the bot.

   IMPORTANT CAVEAT: the arena's get_action() signature does not expose
   the betting history for the current street (how many bets/raises have
   happened so far), so we reconstruct `bets_count` and `facing_bet`
   internally using the fact that this bot instance persists across a
   whole hand and turns strictly alternate heads-up (see
   _update_street_tracking below). This is an approximation, not a
   perfect reconstruction -- documented here for the report.

   If no trained entry matches the current infoset (or the strategy file
   is missing), we fall back to the EV heuristic below -- so the bot is
   never left without a legal move.

1. PREFLOP STRENGTH via the Chen Formula (classic, well-known poker heuristic):
   Running a Monte Carlo simulation before any community cards are dealt is
   both slow and noisy (only 2 known cards out of 7, so variance is high).
   Instead, preflop we use the Chen Formula — a fast, well-established
   scoring system professional players use to rank starting hands (see
   Chen, 2003). It scores a starting hand 0-20 based on:
     - the rank of the highest card
     - whether the hand is a pocket pair
     - whether the two cards are suited
     - the "gap" between the two card ranks (connectedness, straight potential)
   We then linearly map that score onto an approximate heads-up win
   probability, calibrated against known heads-up equity ranges (roughly
   0.30 for the weakest hands, 0.85 for pocket Aces).

2. POSTFLOP STRENGTH via Monte Carlo simulation (unchanged from baseline):
   Once community cards are visible, there's real information to simulate
   over, so we roll out random opponent hole cards + random remaining board
   cards hundreds of times and measure our win rate directly.

3. EXPECTED VALUE decision:
   Same pot-odds logic as before: compare win_probability against
   amount_to_call / (pot_size + amount_to_call) to decide FOLD / CALL / RAISE.

4. CONTROLLED BLUFFING:
   A purely EV-based bot is exploitable — an opponent (or the tournament's
   baseline bots) can learn "this bot only continues with a real hand" and
   play around it. To stay less predictable, in spots where we'd otherwise
   fold to a *cheap* bet, we occasionally (8% of the time) raise instead as
   a bluff. We cap this so it only fires when the cost is small relative to
   our stack, so a bad bluff can't meaningfully damage our bankroll.

NOTE ON POSITION: the arena's get_action() signature does not expose whether
we're Small Blind or Big Blind, so true position-based strategy isn't
directly implementable without breaking the required interface. The Chen
Formula thresholds below are deliberately calibrated to be reasonable
regardless of position.
"""

import json
import os
import random
from card import Card, RANKS, SUITS
from hand_evaluator import best_hand

CFR_STRATEGY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cfr_strategy.json")


def load_cfr_strategy():
    """Load the trained CFR strategy table if present. Never crashes -
    returns an empty dict (falls back to EV heuristic everywhere) if the
    file is missing or malformed."""
    try:
        with open(CFR_STRATEGY_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


class BasePokerBot:
    def __init__(self, name):
        self.name = name

    def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                    amount_to_call, legal_actions):
        """
        Parameters:
        - hole_cards (list): Your two private cards, e.g., ['Ah', 'Kd']
        - community_cards (list): Shared public cards, e.g., ['7s', '7c', '2d']
        - pot_size (int): Total chips currently in the middle pot
        - stack_size (int): Your remaining chips in your stack
        - amount_to_call (int): Chips required to put in to stay in the hand
        - legal_actions (list): Available valid moves, e.g., ['FOLD', 'CALL', 'RAISE']

        Returns:
        - A string exactly matching ONE of the elements in legal_actions.
        """
        raise NotImplementedError("Your bot logic goes here!")


# ----------------------------------------------------------------------
# Chen Formula: fast, well-known preflop starting-hand strength heuristic
# ----------------------------------------------------------------------
def chen_score(hole_cards):
    """
    hole_cards: list of 2 card strings, e.g. ['Ah', 'Kd']
    Returns a numeric score roughly 0-20 (higher = stronger starting hand).
    """
    cards = [Card(c) for c in hole_cards]
    cards.sort(key=lambda c: c.value, reverse=True)
    high, low = cards[0], cards[1]

    # Base points from the highest card
    face_points = {14: 10, 13: 8, 12: 7, 11: 6}
    points = face_points.get(high.value, high.value / 2.0)

    is_pair = high.value == low.value
    if is_pair:
        points = max(points * 2, 5)

    is_suited = (high.suit == low.suit) and not is_pair
    if is_suited:
        points += 2

    if not is_pair:
        gap = high.value - low.value - 1
        if gap == 1:
            points -= 1
        elif gap == 2:
            points -= 2
        elif gap == 3:
            points -= 4
        elif gap >= 4:
            points -= 5
        # small bonus for 0-1 gap connectors that can make a straight
        if gap <= 1 and high.value < 12:
            points += 1

    return max(points, 0)


def chen_score_to_win_prob(score):
    """
    Rough calibration: in heads-up play, starting-hand equity vs a random
    hand ranges roughly from 0.30 (weakest hands) to 0.85 (pocket Aces).
    This avoids running an expensive/noisy Monte Carlo simulation when only
    2 of 7 cards are known.
    """
    normalized = min(score, 20) / 20.0
    return 0.30 + normalized * 0.55


class CustomPokerBot(BasePokerBot):
    # Bluff a fraction of the spots where we'd otherwise fold to a cheap bet
    BLUFF_FREQUENCY = 0.08
    # Never bluff if it would risk more than this fraction of our stack
    BLUFF_MAX_COST_RATIO = 0.20

    def __init__(self, name="DeepBluffer", simulations=100):
        super().__init__(name)
        # More simulations = more accurate postflop win_probability estimate,
        # but slower. 100 keeps the bot fast enough for a 10,000-hand
        # tournament while still giving a stable estimate.
        self.simulations = simulations
        self.cfr_strategy = load_cfr_strategy()
        self._reset_hand_state()

    # ------------------------------------------------------------------
    # Internal state tracking for CFR infoset reconstruction.
    # The arena calls get_action() repeatedly on the SAME bot instance
    # throughout a hand, so we can track street/bet progress ourselves.
    # ------------------------------------------------------------------
    def _reset_hand_state(self):
        self._last_community_len = -1
        self._bets_count_this_street = 0
        self._decisions_this_street = 0

    def _update_street_tracking(self, community_cards, pot_size):
        community_len = len(community_cards)

        # Fresh hand detection: preflop, pot == exactly the two blinds (3),
        # and we haven't already flagged this as the start of a hand.
        is_fresh_hand_start = (community_len == 0 and pot_size == 3
                                and self._last_community_len != 0)

        if is_fresh_hand_start or self._last_community_len == -1:
            self._reset_hand_state()
            self._last_community_len = 0
            self._bets_count_this_street = 1  # BB's blind counts as bet #1
            self._decisions_this_street = 0
        elif community_len != self._last_community_len:
            # A new street started (flop/turn/river dealt)
            self._last_community_len = community_len
            self._decisions_this_street = 0
            self._bets_count_this_street = 0
        elif self._decisions_this_street >= 1:
            # We're being asked again on the SAME street: given heads-up
            # strict turn alternation, the only way that happens is if the
            # opponent raised since our last decision (a call/fold would
            # have ended the street or the hand).
            self._bets_count_this_street = min(self._bets_count_this_street + 1,
                                                 4)

        self._decisions_this_street += 1

    @staticmethod
    def _win_prob_to_bucket(win_prob):
        return min(int(win_prob * 5), 4)

    # ------------------------------------------------------------------
    # STEP 1: Estimate win probability
    #   - Preflop: Chen Formula (fast, stable)
    #   - Postflop: Monte Carlo rollout (uses real board information)
    # ------------------------------------------------------------------
    def estimate_win_probability(self, hole_cards, community_cards):
        if not community_cards:
            return chen_score_to_win_prob(chen_score(hole_cards))
        return self._monte_carlo_win_probability(hole_cards, community_cards)

    def _monte_carlo_win_probability(self, hole_cards, community_cards):
        my_cards = [Card(c) for c in hole_cards]
        known_community = [Card(c) for c in community_cards]

        known_strs = {str(c) for c in my_cards + known_community}
        unseen_deck = [Card(r + s) for r in RANKS for s in SUITS
                        if (r + s) not in known_strs]

        cards_needed_for_board = 5 - len(known_community)

        wins = 0.0
        trials = 0

        for _ in range(self.simulations):
            random.shuffle(unseen_deck)
            draw = unseen_deck[:cards_needed_for_board + 2]

            sim_board = known_community + draw[:cards_needed_for_board]
            opp_hole = draw[cards_needed_for_board:cards_needed_for_board + 2]

            my_score = best_hand(my_cards + sim_board)
            opp_score = best_hand(opp_hole + sim_board)

            if my_score > opp_score:
                wins += 1.0
            elif my_score == opp_score:
                wins += 0.5  # split pot counts as half a win
            trials += 1

        return wins / trials if trials > 0 else 0.5

    # ------------------------------------------------------------------
    # STEP 2: Decide an action -- try the trained CFR strategy first,
    #         fall back to the EV heuristic if no trained entry matches.
    # ------------------------------------------------------------------
    STREET_INDEX = {0: 0, 3: 1, 4: 2, 5: 3}

    def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                    amount_to_call, legal_actions):

        self._update_street_tracking(community_cards, pot_size)

        win_prob = self.estimate_win_probability(hole_cards, community_cards)
        chosen_action = None

        if self.cfr_strategy:
            street = self.STREET_INDEX.get(len(community_cards),
                                             min(len(community_cards), 3))
            bucket = self._win_prob_to_bucket(win_prob)
            is_facing_bet = int(amount_to_call > 0)
            infoset_key = f"{bucket}|{street}|{self._bets_count_this_street}|{is_facing_bet}"

            probs = self.cfr_strategy.get(infoset_key)
            if probs is not None:
                # Restrict to actions that are actually legal right now and
                # renormalize, then sample proportionally to the trained
                # probabilities (this is the theoretically correct way to
                # play an average CFR strategy -- it's a mixed strategy).
                filtered = {a: probs.get(a, 0.0) for a in legal_actions}
                total = sum(filtered.values())
                if total > 0:
                    r = random.random() * total
                    cum = 0.0
                    for a, p in filtered.items():
                        cum += p
                        if r <= cum:
                            chosen_action = a
                            break

        if chosen_action is None:
            chosen_action = self._ev_heuristic_action(
                win_prob, pot_size, stack_size, amount_to_call, legal_actions)

        if chosen_action == "RAISE":
            self._bets_count_this_street = min(self._bets_count_this_street + 1, 4)

        return chosen_action

    def _ev_heuristic_action(self, win_prob, pot_size, stack_size,
                               amount_to_call, legal_actions):
        """Fallback decision logic (pot-odds / EV with controlled bluffing),
        used whenever the CFR strategy has no trained entry for the current
        infoset, or the strategy file wasn't found."""

        # Free to continue (this is a "check" situation) -> never fold for free.
        if amount_to_call == 0:
            if win_prob > 0.70 and "RAISE" in legal_actions:
                return "RAISE"
            if "CALL" in legal_actions:   # CALL with amount_to_call==0 means CHECK
                return "CALL"
            return legal_actions[0]

        # Pot odds: minimum win probability needed for calling to break even
        pot_odds_needed = amount_to_call / (pot_size + amount_to_call)

        # Strong hand -> raise for value
        if win_prob > 0.75 and "RAISE" in legal_actions:
            return "RAISE"

        # Profitable call (win_prob comfortably above what's needed)
        if win_prob >= pot_odds_needed and "CALL" in legal_actions:
            return "CALL"

        # Marginal: give a small buffer before folding, to avoid folding
        # too tightly to noise in the win-probability estimate
        if win_prob >= pot_odds_needed - 0.05 and "CALL" in legal_actions:
            return "CALL"

        # About to fold -- consider a cheap bluff-raise to stay unpredictable
        cost_ratio = (amount_to_call / stack_size) if stack_size > 0 else 1.0
        if ("RAISE" in legal_actions
                and cost_ratio < self.BLUFF_MAX_COST_RATIO
                and random.random() < self.BLUFF_FREQUENCY):
            return "RAISE"

        # Not profitable enough -> fold if possible
        if "FOLD" in legal_actions:
            return "FOLD"

        # Safety net: should rarely hit this, but never return an illegal action
        if "CALL" in legal_actions:
            return "CALL"
        return legal_actions[0]
