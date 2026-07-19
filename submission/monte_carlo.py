import random

from deck import Deck
from hand_evaluator import evaluate_seven_cards, compare_hands


def remove_known_cards(hole_cards, community_cards):
    """
    Build the pool of cards that could still be in the deck,
    given the cards we can already see (our hole cards + the
    current community cards).
    """
    deck = Deck()
    known_cards = set(hole_cards + community_cards)

    remaining_cards = [
        card for card in deck.cards
        if card not in known_cards
    ]

    return remaining_cards


def complete_board(community_cards, remaining_cards):
    """
    Pad the community cards up to 5 using cards drawn from the
    front of `remaining_cards` (which must already be shuffled
    by the caller).
    """
    completed_board = community_cards.copy()
    cards_needed = 5 - len(completed_board)
    completed_board.extend(remaining_cards[:cards_needed])
    return completed_board


def simulate_once(hole_cards, community_cards, remaining_cards):
    """
    Simulate a single random completion of the hand: deal a
    random 2-card hand to the opponent, complete the board if
    needed, and compare hands.

    Returns
    -------
    int
        1  -> we win this simulated outcome
        0  -> tie
       -1  -> we lose
    """
    deck = random.sample(remaining_cards, len(remaining_cards))

    opponent_hole_cards = deck[:2]
    deck = deck[2:]

    if len(community_cards) == 5:
        full_board = community_cards
    else:
        full_board = complete_board(community_cards, deck)

    our_hand = evaluate_seven_cards(hole_cards + full_board)
    opponent_hand = evaluate_seven_cards(opponent_hole_cards + full_board)

    result = compare_hands(our_hand, opponent_hand)

    if result > 0:
        return 1
    elif result < 0:
        return -1
    else:
        return 0


def estimate_win_probability(hole_cards, community_cards, num_simulations=1000):
    """
    Runs a Monte Carlo simulation to estimate this hand's equity
    against a single random opponent hand, given the current board.

    Returns
    -------
    dict
        {
            "win": float,     fraction of simulations won outright
            "tie": float,     fraction tied
            "loss": float,    fraction lost
            "equity": float,  win + 0.5 * tie  (standard EV convention)
        }
    """
    remaining_cards = remove_known_cards(hole_cards, community_cards)

    wins = ties = losses = 0

    for _ in range(num_simulations):
        result = simulate_once(hole_cards, community_cards, remaining_cards)
        if result == 1:
            wins += 1
        elif result == -1:
            losses += 1
        else:
            ties += 1

    win_rate = wins / num_simulations
    tie_rate = ties / num_simulations
    loss_rate = losses / num_simulations

    return {
        "win": win_rate,
        "tie": tie_rate,
        "loss": loss_rate,
        "equity": win_rate + 0.5 * tie_rate,
    }
