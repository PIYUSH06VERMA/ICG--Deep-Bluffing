"""
agent.py -- CRITICAL main entry point for the tournament arena.

Strategy: Monte Carlo rollout hand-strength estimation + Expected Value
heuristics, with a randomized bluffing/slowplay layer so the bot isn't
purely "honest" and can't be trivially exploited by always folding/calling.

NEW: Opponent-adaptive bluffing. Since the arena API does not expose the
opponent's actions directly, we INFER opponent tendencies from indirect
signals available to us call-to-call:
  - When our hole cards change, a new hand has started -- we can compare
    our stack now vs our stack at the start of the previous hand to see
    whether we won or lost that hand overall.
  - If we attempted a "pure bluff" raise (weak hand, low win_prob) at some
    point during a hand, and we ended that hand with a net stack GAIN,
    the most likely explanation is the opponent folded to our bluff.
  - We track this as a rolling estimate of the opponent's fold tendency
    and use it to scale how often we bluff: bluff more against players
    who seem to fold a lot, bluff less against calling stations.

Depends on: cards.py, hand_evaluator.py  (must sit in the same folder)
"""

import random

from cards import Card, make_deck
from hand_evaluator import evaluate_hand, compare_hands

FOLD, CALL, RAISE = "FOLD", "CALL", "RAISE"


# =========================================================================
# Base class -- exact signature required by the arena. Do not change.
# =========================================================================
class BasePokerBot:
    def __init__(self, name):
        self.name = name

    def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                    amount_to_call, legal_actions):
        """
        Calculates the optimal move for Limit Texas Hold'em.

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


# =========================================================================
# Your bot
# =========================================================================
class CustomPokerBot(BasePokerBot):

    # How many random rollouts to run per decision when estimating win
    # probability. Higher = more accurate but slower over 10,000 hands.
    NUM_SIMULATIONS = 300

    # Base bluffing / slowplay frequencies -- these are the STARTING points;
    # actual bluff frequency used each decision is scaled by our live
    # estimate of the opponent's fold tendency (see _adaptive_bluff_freq).
    BASE_BLUFF_RAISE_FREQ = 0.12   # chance to raise anyway with a weak hand
    SEMI_BLUFF_FREQ = 0.30         # chance to raise a medium hand for fold equity
    SLOWPLAY_FREQ = 0.15           # chance to just call instead of raising a monster

    # Bounds on how much opponent-adaptation can scale the bluff frequency.
    MIN_BLUFF_SCALE = 0.15   # vs. a pure calling station, bluff far less
    MAX_BLUFF_SCALE = 2.00   # vs. a very foldy opponent, bluff much more

    # Exponential moving average smoothing for the fold-rate estimate.
    FOLD_RATE_EMA_ALPHA = 0.15
    DEFAULT_FOLD_RATE_ESTIMATE = 0.5   # neutral prior before we have data

    def __init__(self, name):
        super().__init__(name)
        self.rng = random.Random()

        # ---- Opponent modeling state (persists across the whole match,
        #      since the arena reuses the same bot instance hand-to-hand) ----
        self.opponent_fold_rate = self.DEFAULT_FOLD_RATE_ESTIMATE
        self.observed_bluff_outcomes = 0  # count of inferred data points (for logging/debug only)

        # Bookkeeping to detect "a new hand has started" and to infer
        # whether our last hand ended in a fold-win, since the API gives
        # us no explicit hand-end signal.
        self._current_hole_cards = None
        self._hand_start_stack = None
        self._bluffed_this_hand = False
        # Board length (# community cards) at the moment of our most recent
        # bluff raise this hand, and the max board length we've observed
        # since -- used to detect whether the opponent called (board kept
        # advancing) or folded (hand ended, no further cards ever dealt).
        self._bluff_board_len = None
        self._max_board_len_this_hand = 0

    # ---------------------------------------------------------------
    # Main decision function
    # ---------------------------------------------------------------
    def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                    amount_to_call, legal_actions):
        try:
            self._maybe_update_opponent_model(hole_cards, stack_size)
            self._max_board_len_this_hand = max(self._max_board_len_this_hand,
                                                 len(community_cards))

            win_prob = self._estimate_win_probability(hole_cards, community_cards)

            # IMPORTANT: what we actually risk by calling is capped at our
            # remaining stack (the engine only ever takes min(amount_to_call,
            # stack_size) from us -- an all-in call). Using the *nominal*
            # amount_to_call here would badly overstate our risk whenever
            # amount_to_call > stack_size (classic short-stack / all-in-for-
            # cheap spot), causing us to fold hands that are actually
            # trivially +EV calls because we can only lose our last chip(s).
            effective_call = min(amount_to_call, stack_size)

            pot_odds_needed = (effective_call / (pot_size + effective_call)
                                if effective_call > 0 else 0.0)

            action = self._decide(win_prob, pot_odds_needed, effective_call,
                                   legal_actions, len(community_cards))

            if action not in legal_actions:
                action = self._safe_fallback(legal_actions)

            return action

        except Exception:
            # Absolute safety net -- NEVER let an exception escape, or the
            # arena crashes the bot and scores it 0.
            return self._safe_fallback(legal_actions, prefer=CALL)

    # ---------------------------------------------------------------
    # Opponent modeling: detect new hands, infer bluff outcomes
    # ---------------------------------------------------------------
    def _maybe_update_opponent_model(self, hole_cards, stack_size):
        """
        Called at the top of every get_action(). Uses the fact that
        hole_cards change only when a brand-new hand begins to detect
        hand boundaries, then infers whether our previous hand's bluff
        (if any) likely succeeded based on our stack delta.
        """
        is_new_hand = (self._current_hole_cards is not None and
                        hole_cards != self._current_hole_cards)

        if is_new_hand:
            self._finalize_previous_hand(stack_size)

        if self._current_hole_cards is None or is_new_hand:
            self._current_hole_cards = list(hole_cards)
            self._hand_start_stack = stack_size
            self._bluffed_this_hand = False
            self._bluff_board_len = None
            self._max_board_len_this_hand = 0

    def _finalize_previous_hand(self, current_stack_size):
        """
        Infer whether the previous hand's bluff (if we made one) was
        called or folded to, using how far the community cards progressed
        AFTER our bluff as the signal:
          - If the board NEVER advanced past the street where we bluffed,
            the hand ended immediately after our raise -> the opponent
            almost certainly folded (they never got to see/call into a
            new street).
          - If the board DID advance further (more community cards were
            dealt after our bluff), the opponent must have called to see
            those cards -> our bluff did NOT get an immediate fold.

        This is far less noisy than using stack deltas, which conflate
        "opponent folded" with "we simply won at showdown" -- both look
        like a stack increase but only one of them is evidence the
        opponent is foldable. The one edge case this can't resolve is a
        bluff made ON THE RIVER (board already at 5 cards, so there's no
        further street to observe); in that case we fall back to a
        neutral (no-update) skip rather than guess.
        """
        if not self._bluffed_this_hand or self._bluff_board_len is None:
            return  # nothing to learn from this hand

        if self._bluff_board_len >= 5:
            # River bluff -- no further street can reveal a call vs fold,
            # so we don't have a reliable signal. Skip updating.
            return

        board_advanced = self._max_board_len_this_hand > self._bluff_board_len
        inferred_fold = not board_advanced

        target = 1.0 if inferred_fold else 0.0
        self.opponent_fold_rate = (
            (1 - self.FOLD_RATE_EMA_ALPHA) * self.opponent_fold_rate
            + self.FOLD_RATE_EMA_ALPHA * target
        )
        self.observed_bluff_outcomes += 1

    def _adaptive_bluff_freq(self):
        """
        Scale the base bluff frequency by how often the opponent seems to
        fold. opponent_fold_rate in [0, 1]; 0.5 is neutral (no scaling).
        """
        if self.opponent_fold_rate >= 0.5:
            t = (self.opponent_fold_rate - 0.5) / 0.5
            scale = 1.0 + t * (self.MAX_BLUFF_SCALE - 1.0)
        else:
            t = (0.5 - self.opponent_fold_rate) / 0.5
            scale = 1.0 - t * (1.0 - self.MIN_BLUFF_SCALE)

        freq = self.BASE_BLUFF_RAISE_FREQ * scale
        return max(0.0, min(freq, 0.9))  # hard safety clamp

    # ---------------------------------------------------------------
    # Core decision logic
    # ---------------------------------------------------------------
    def _decide(self, win_prob, pot_odds_needed, amount_to_call, legal_actions,
                board_len):
        can_raise = RAISE in legal_actions
        bluff_freq = self._adaptive_bluff_freq()

        def _mark_bluff():
            self._bluffed_this_hand = True
            self._bluff_board_len = board_len

        # ---- Strong hand: value bet/raise, occasionally slowplay ----
        if win_prob >= 0.70:
            if can_raise and self.rng.random() > self.SLOWPLAY_FREQ:
                return RAISE
            return self._safe_fallback(legal_actions, prefer=CALL)

        # ---- Medium hand: follow pot odds, sprinkle in semi-bluff raises ----
        if win_prob >= 0.45:
            if amount_to_call == 0:
                if can_raise and win_prob >= 0.55 and self.rng.random() < self.SEMI_BLUFF_FREQ:
                    _mark_bluff()
                    return RAISE
                return self._safe_fallback(legal_actions, prefer=CALL)

            if win_prob > pot_odds_needed:
                if can_raise and win_prob >= 0.58 and self.rng.random() < self.SEMI_BLUFF_FREQ:
                    _mark_bluff()
                    return RAISE
                return self._safe_fallback(legal_actions, prefer=CALL)

            return self._safe_fallback(legal_actions, prefer=FOLD)

        # ---- Weak hand ----
        # Adaptive pure-bluff raise: frequency now depends on how often
        # this specific opponent has been folding to us.
        if can_raise and self.rng.random() < bluff_freq:
            _mark_bluff()
            return RAISE

        if amount_to_call == 0:
            return self._safe_fallback(legal_actions, prefer=CALL)

        # Real EV check first: if win_prob already clears the odds we're
        # being offered, this is a straightforward +EV call -- not a coin
        # flip. This matters most in short-stack / all-in-for-cheap spots
        # (e.g. pot_odds_needed == 0.01 because we're risking our last
        # chip into a big pot), where a flat 50% gate would incorrectly
        # fold a near-guaranteed-correct call half the time.
        if win_prob >= pot_odds_needed:
            return self._safe_fallback(legal_actions, prefer=CALL)

        # Otherwise we're a genuine bluff-catch candidate (win_prob below
        # what odds demand). Only worth doing occasionally, and the
        # cheaper the odds, the more often it's worth defending our range
        # even at a slight technical loss (protects against being
        # exploited by pure over-betting/bluffing opponents).
        if pot_odds_needed < 0.15 and self.rng.random() < 0.5:
            return self._safe_fallback(legal_actions, prefer=CALL)

        return self._safe_fallback(legal_actions, prefer=FOLD)

    def _safe_fallback(self, legal_actions, prefer=None):
        """Return `prefer` if it's legal; else CALL; else FOLD; else first legal action."""
        if prefer and prefer in legal_actions:
            return prefer
        if CALL in legal_actions:
            return CALL
        if FOLD in legal_actions:
            return FOLD
        return legal_actions[0]

    # ---------------------------------------------------------------
    # Monte Carlo win-probability estimation
    # ---------------------------------------------------------------
    def _estimate_win_probability(self, hole_cards, community_cards):
        """
        Simulate NUM_SIMULATIONS random opponent hole cards + random
        completions of the remaining board, drawn from unseen cards.
        Returns P(win) + 0.5 * P(tie).
        """
        my_hole = Card.parse_list(hole_cards)
        board = Card.parse_list(community_cards)

        known = {str(c) for c in my_hole} | {str(c) for c in board}
        remaining = [c for c in make_deck() if str(c) not in known]

        needed_board_cards = 5 - len(board)
        wins = 0.0

        for _ in range(self.NUM_SIMULATIONS):
            sample = remaining[:]
            self.rng.shuffle(sample)

            opp_hole = sample[:2]
            extra_board = sample[2:2 + needed_board_cards]
            full_board = board + extra_board

            my_score = evaluate_hand(my_hole + full_board)
            opp_score = evaluate_hand(opp_hole + full_board)

            result = compare_hands(my_score, opp_score)
            if result == 1:
                wins += 1.0
            elif result == 0:
                wins += 0.5

        return wins / self.NUM_SIMULATIONS


if __name__ == "__main__":
    bot = CustomPokerBot("TestBot")

    scenarios = [
        (['Ah', 'Kh'], [], 3, 99, 2, ['FOLD', 'CALL', 'RAISE']),
        (['2c', '7d'], ['Ah', 'Kd', 'Qs'], 10, 90, 4, ['FOLD', 'CALL', 'RAISE']),
        (['Th', 'Td'], ['Ts', '2d', '3c', '9h'], 20, 60, 0, ['CALL', 'RAISE']),
        (['5h', '6d'], ['2c', '9d', 'Kd', 'Ah', '3s'], 30, 40, 4, ['FOLD', 'CALL']),
        (['9s', '9h'], [], 3, 105, 2, ['FOLD', 'CALL', 'RAISE']),
    ]

    for hole, board, pot, stack, to_call, legal in scenarios:
        action = bot.get_action(hole, board, pot, stack, to_call, legal)
        assert action in legal, f"ILLEGAL ACTION RETURNED: {action}"
        print(f"hole={hole} board={board} pot={pot} to_call={to_call} "
              f"legal={legal} -> action={action}")

    print(f"\nOpponent fold-rate estimate after scenarios: {bot.opponent_fold_rate:.3f}")
    print("All smoke tests passed -- agent always returns a legal action.")