import random
from itertools import combinations

from card import Card, RANK_ORDER, SUITS
from hand_evaluator import compare_hands


class BasePokerBot:
    def __init__(self, name):
        self.name = name

    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        raise NotImplementedError("Your bot logic goes here!")


_SAMPLES_BY_STREET = {0: 150, 3: 150, 4: 200, 5: 250}


def estimate_equity(hole_cards, community_cards, rng, num_samples=None):
    """
    Monte Carlo estimate of P(win) + 0.5*P(tie) against a uniformly random
    opponent hand, given the cards we can already see. Unseen cards
    (opponent's hole cards + not-yet-dealt community cards) are sampled
    consistently (without replacement) from the remaining deck each trial.
    """
    known = set(hole_cards) | set(community_cards)
    remaining_deck = [c for c in _FULL_DECK if c not in known]
    needed_community = 5 - len(community_cards)

    if num_samples is None:
        num_samples = _SAMPLES_BY_STREET.get(len(community_cards), 400)

    wins = ties = 0.0
    draw_size = 2 + needed_community
    for _ in range(num_samples):
        sample = rng.sample(remaining_deck, draw_size)
        opp_hole = sample[:2]
        rest_of_board = sample[2:]
        full_board = community_cards + rest_of_board

        my_cards = Card.parse_list(hole_cards + full_board)
        opp_cards = Card.parse_list(opp_hole + full_board)
        outcome = compare_hands(my_cards, opp_cards)
        if outcome > 0:
            wins += 1
        elif outcome == 0:
            ties += 1

    return (wins + 0.5 * ties) / num_samples


_FOLD_EQUITY_BY_STREET = {0: 0.12, 3: 0.18, 4: 0.20, 5: 0.22}


def _bet_increment(community_cards):
    return 2 if len(community_cards) < 4 else 4  


class CustomPokerBot(BasePokerBot):
    def __init__(self, name="MonteCarloEV", seed=None):
        super().__init__(name)
        self._rng = random.Random(seed)

    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        # Safety net: if for some reason only one action is legal, take it.
        if len(legal_actions) == 1:
            return legal_actions[0]

        equity = estimate_equity(hole_cards, community_cards, self._rng)
        bet = _bet_increment(community_cards)
        fold_equity = _FOLD_EQUITY_BY_STREET.get(len(community_cards), 0.15)

        ev = {"FOLD": 0.0}

        if "CALL" in legal_actions:
            ev["CALL"] = equity * (pot_size + amount_to_call) - amount_to_call

        if "RAISE" in legal_actions:
            to_call_after_raise = amount_to_call + bet
            pot_if_called = pot_size + amount_to_call + 2 * bet
            ev_if_called = equity * pot_if_called - to_call_after_raise
            ev["RAISE"] = fold_equity * pot_size + (1 - fold_equity) * ev_if_called

        preference_order = ["FOLD", "CALL", "RAISE"]
        best_action, best_ev = None, float("-inf")
        for action in preference_order:
            if action not in ev:
                continue
            if ev[action] > best_ev + 1e-9:
                best_action, best_ev = action, ev[action]

        return best_action if best_action in legal_actions else legal_actions[0]


if __name__ == "__main__":
    bot = CustomPokerBot("Test")
    action = bot.get_action(
        hole_cards=["Ah", "Ad"],
        community_cards=[],
        pot_size=3,
        stack_size=99,
        amount_to_call=2,
        legal_actions=["FOLD", "CALL", "RAISE"],
    )
    print("Pocket Aces preflop decision:", action)

    action2 = bot.get_action(
        hole_cards=["7c", "2d"],
        community_cards=["Ah", "Kd", "Qs"],
        pot_size=10,
        stack_size=95,
        amount_to_call=4,
        legal_actions=["FOLD", "CALL", "RAISE"],
    )
    print("7-2 offsuit vs AKQ board decision:", action2)
