"""
agent.py
--------
Entry point for the tournament arena.

Strategy Archetype
==================
`CustomPokerBot` is a Monte-Carlo-rollout Expected-Value (EV) agent:

1.  STATE REPRESENTATION: at every decision point the bot knows its own
    2 hole cards and the public community cards. It does NOT know the
    opponent's hole cards (imperfect information), so it treats the
    opponent's hand as a uniformly random 2-card hand drawn from the
    cards it hasn't seen.

2.  EQUITY ESTIMATION (Monte Carlo Rollouts): the bot repeatedly samples
    a plausible opponent hand and a random completion of the board
    (using the same from-scratch `evaluator.py` used by the game
    engine itself), and records how often its own hand wins / ties /
    loses. Averaging over many samples gives an unbiased Monte Carlo
    estimate of the bot's win probability ("equity") in the hand:

        equity = P(win) + 0.5 * P(tie)

    On the river, when only the opponent's 2 hole cards are unknown,
    the bot switches to EXACT enumeration (every remaining 2-card
    combination) instead of sampling, since this is cheap (at most
    C(45,2) = 990 combinations) and removes all sampling noise exactly
    when precision matters most.

3.  EV-BASED DECISION RULE: given the pot size and the amount required
    to call, the bot computes the pot odds

        pot_odds = amount_to_call / (pot_size + amount_to_call)

    which is the break-even equity needed to make calling profitable
    in isolation (EV_call = equity * pot - (1 - equity) * amount_to_call
    >= 0  <=>  equity >= pot_odds). The bot then chooses:

        - RAISE  for value when equity comfortably clears a high
          value-betting threshold (it wants to build the pot while
          ahead), and occasionally as a balanced semi-bluff with
          moderate equity so it can't be exploited by always
          folding/checking with a weak range (game-theoretic mixing).
        - CALL   when equity clears pot odds but not the raise
          threshold.
        - FOLD   when equity is below pot odds (negative EV to call).

Only `random`, `itertools`, `collections`, and `math` (all explicitly
whitelisted by the assignment) are used -- no external poker libraries,
no hard-coded downloaded strategy tables.
"""

import random
import math

from card import Card, Deck, RANK_CHAR_TO_VALUE, VALID_SUITS, parse_cards
from evaluator import best_hand_rank, compare_hands


class BasePokerBot:
    def __init__(self, name):
        self.name = name

    def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                   amount_to_call, legal_actions):
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


class CustomPokerBot(BasePokerBot):
    """Monte-Carlo-rollout EV agent (see module docstring)."""

    # --- Tunable strategy hyper-parameters ---------------------------------
    SIMS_PREFLOP = 120
    SIMS_FLOP = 200
    SIMS_TURN = 300
    # River uses exact enumeration instead of a sim count.

    RAISE_THRESHOLD = 0.68   # value-raise when equity clears this
    BLUFF_LOW = 0.32         # semi-bluff/raise equity window (balances range)
    BLUFF_HIGH = 0.45
    BLUFF_FREQUENCY = 0.30   # how often we execute the balanced semi-bluff
    POT_ODDS_BUFFER = 0.02   # small safety margin against pure break-even calls

    def __init__(self, name="CustomPokerBot", seed=None):
        super().__init__(name)
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------ #
    # Public API required by the arena
    # ------------------------------------------------------------------ #
    def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                    amount_to_call, legal_actions):
        equity = self._estimate_equity(hole_cards, community_cards)
        return self._decide(equity, pot_size, amount_to_call, legal_actions)

    # ------------------------------------------------------------------ #
    # Equity estimation
    # ------------------------------------------------------------------ #
    def _estimate_equity(self, hole_card_strs, community_card_strs):
        hole = parse_cards(hole_card_strs)
        community = parse_cards(community_card_strs)
        known = hole + community

        full_deck = [Card(r, s) for r in RANK_CHAR_TO_VALUE for s in VALID_SUITS]
        remaining = [c for c in full_deck if c not in known]

        cards_needed_on_board = 5 - len(community)

        if cards_needed_on_board == 0:
            return self._exact_river_equity(hole, community, remaining)
        return self._monte_carlo_equity(hole, community, remaining, cards_needed_on_board)

    def _exact_river_equity(self, hole, community, remaining):
        """River: only the opponent's 2 hole cards are unknown. Enumerate exactly."""
        wins = ties = total = 0
        n = len(remaining)
        for i in range(n):
            for j in range(i + 1, n):
                opp_hole = (remaining[i], remaining[j])
                outcome = compare_hands(hole + community, list(opp_hole) + community)
                if outcome == 1:
                    wins += 1
                elif outcome == 0:
                    ties += 1
                total += 1
        if total == 0:
            return 0.5
        return (wins + 0.5 * ties) / total

    def _monte_carlo_equity(self, hole, community, remaining, cards_needed_on_board):
        street_sims = {0: self.SIMS_PREFLOP, 3: self.SIMS_PREFLOP,
                       2: self.SIMS_FLOP, 1: self.SIMS_TURN}
        n_sims = street_sims.get(cards_needed_on_board, self.SIMS_FLOP)

        wins = ties = 0
        pool = list(remaining)
        for _ in range(n_sims):
            sample = self._rng.sample(pool, 2 + cards_needed_on_board)
            opp_hole = sample[:2]
            board_fill = sample[2:]
            full_community = community + board_fill
            outcome = compare_hands(hole + full_community, opp_hole + full_community)
            if outcome == 1:
                wins += 1
            elif outcome == 0:
                ties += 1
        return (wins + 0.5 * ties) / n_sims

    # ------------------------------------------------------------------ #
    # EV-based decision rule
    # ------------------------------------------------------------------ #
    def _decide(self, equity, pot_size, amount_to_call, legal_actions):
        can_raise = "RAISE" in legal_actions
        can_fold = "FOLD" in legal_actions

        if amount_to_call > 0:
            pot_odds = amount_to_call / (pot_size + amount_to_call)
        else:
            pot_odds = 0.0

        # 1) Strong value hands: raise/bet for value.
        if can_raise and equity >= self.RAISE_THRESHOLD:
            return "RAISE"

        # 2) Balanced semi-bluff / value-bet mixing with medium equity so the
        #    bot cannot be trivially exploited by "fold to any aggression".
        if can_raise and self.BLUFF_LOW <= equity <= self.BLUFF_HIGH:
            if self._rng.random() < self.BLUFF_FREQUENCY:
                return "RAISE"

        # 3) Facing a bet: call only if equity clears pot odds (positive EV).
        if amount_to_call > 0:
            if not can_fold or equity >= pot_odds + self.POT_ODDS_BUFFER:
                return "CALL"
            return "FOLD"

        # 4) No bet facing us (checked to us): check back.
        return "CALL"  # CALL with amount_to_call == 0 means CHECK


if __name__ == "__main__":
    # Minimal smoke test: run one decision on a made-up spot so that
    # `python agent.py` never crashes and gives a sanity-check readout.
    bot = CustomPokerBot("SmokeTestBot", seed=42)
    action = bot.get_action(
        hole_cards=["Ah", "Kh"],
        community_cards=["Qh", "Jh", "2c"],
        pot_size=20,
        stack_size=80,
        amount_to_call=4,
        legal_actions=["FOLD", "CALL", "RAISE"],
    )
    print(f"Example decision with nut-flush draw + straight draw: {action}")
