"""
simulate.py
-------------
A local, standalone game engine that implements the exact HULHE rules from
the assignment (blinds, fixed-limit betting, bet caps, turn order). This is
NOT part of your submission -- it's just for YOU to watch your bot play and
sanity-check its behavior before the real tournament arena runs it.

Two modes:
1. Watch a single hand play out, printed street by street.
2. Run many hands in bulk and report win rate / average chip result.

Usage:
    python3 simulate.py --watch          # play and print one hand
    python3 simulate.py --hands 2000     # run 2000 hands, report win rate
"""

import argparse
import random

from card import Card, RANKS, SUITS
from hand_evaluator import best_hand, describe
from agent import CustomPokerBot, BasePokerBot

SB_AMOUNT = 1
BB_AMOUNT = 2
BET_SIZE = {0: 2, 1: 2, 2: 4, 3: 4}  # preflop, flop, turn, river
MAX_BETS_PER_STREET = 4
STREET_NAMES = ["Pre-Flop", "Flop", "Turn", "River"]


class RandomBaselineBot(BasePokerBot):
    """A simple baseline opponent: calls most of the time, occasionally
    folds or raises at random. Useful as a punching bag to sanity-check
    that your bot behaves sensibly (folds trash, raises strong hands)."""

    def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                    amount_to_call, legal_actions):
        r = random.random()
        if "RAISE" in legal_actions and r < 0.15:
            return "RAISE"
        if "FOLD" in legal_actions and r < 0.25:
            return "FOLD"
        if "CALL" in legal_actions:
            return "CALL"
        return legal_actions[0]


def deal_new_hand():
    deck = [Card(r + s) for r in RANKS for s in SUITS]
    random.shuffle(deck)
    hole0 = [str(deck.pop()), str(deck.pop())]
    hole1 = [str(deck.pop()), str(deck.pop())]
    board = [str(deck.pop()) for _ in range(5)]
    return hole0, hole1, board


def play_betting_round(bots, hole_cards, community_cards, street, contrib,
                         first_to_act, verbose):
    """
    Plays one street of fixed-limit betting between the two bots.
    Returns (folded_player or None, updated contrib).
    """
    bets_count = 1 if street == 0 else 0  # preflop blind counts as bet #1
    acted_count = 0
    to_act = first_to_act
    facing_bet = (street == 0)  # preflop: SB faces the BB's blind

    while True:
        other = 1 - to_act
        amount_to_call = max(contrib[other] - contrib[to_act], 0)

        legal = []
        if facing_bet:
            legal.append("FOLD")
        legal.append("CALL")
        if bets_count < MAX_BETS_PER_STREET:
            legal.append("RAISE")

        pot_size = contrib[0] + contrib[1]
        stack_size = 100 - contrib[to_act]

        action = bots[to_act].get_action(
            hole_cards[to_act], community_cards, pot_size, stack_size,
            amount_to_call, legal)

        if action not in legal:
            # Defensive: treat an illegal return as a fold (arena would
            # likely disqualify -- this just protects the local simulator)
            action = "FOLD" if "FOLD" in legal else "CALL"

        if verbose:
            print(f"    Player {to_act} ({bots[to_act].name}): {action}"
                  + (f" (owed {amount_to_call})" if amount_to_call else ""))

        if action == "FOLD":
            return to_act, contrib

        if action == "CALL":
            contrib[to_act] += amount_to_call
            acted_count += 1
            if acted_count >= 2:
                return None, contrib  # street closed
            facing_bet = False
            to_act = other
        else:  # RAISE
            contrib[to_act] += amount_to_call + BET_SIZE[street]
            bets_count += 1
            acted_count += 1
            facing_bet = True
            to_act = other


def play_hand(bots, verbose=False):
    hole_cards, board = None, None
    hole0, hole1, full_board = deal_new_hand()
    hole_cards = [hole0, hole1]

    contrib = [SB_AMOUNT, BB_AMOUNT]  # player 0 = SB/dealer, player 1 = BB
    community_cards = []

    street_boundaries = {0: 0, 1: 3, 2: 4, 3: 5}
    first_to_act = {0: 0, 1: 1, 2: 1, 3: 1}  # SB first preflop, BB first postflop

    for street in range(4):
        community_cards = full_board[:street_boundaries[street]]
        if verbose:
            print(f"  -- {STREET_NAMES[street]} -- board={community_cards} pot={sum(contrib)}")

        folder, contrib = play_betting_round(
            bots, hole_cards, community_cards, street, contrib,
            first_to_act[street], verbose)

        if folder is not None:
            winner = 1 - folder
            pot = contrib[0] + contrib[1]
            if verbose:
                print(f"    Player {folder} folds. Player {winner} wins pot of {pot}.\n")
            result = [0, 0]
            result[winner] = pot - contrib[winner]
            result[folder] = -contrib[folder]
            return result

    # Showdown
    community_cards = full_board
    h0 = [Card(c) for c in hole_cards[0]] 
    h1 = [Card(c) for c in hole_cards[1]]
    board_cards = [Card(c) for c in community_cards]
    score0 = best_hand(h0 + board_cards)
    score1 = best_hand(h1 + board_cards)
    pot = contrib[0] + contrib[1]

    if verbose:
        print(f"  -- Showdown -- board={community_cards} pot={pot}")
        print(f"    Player 0: {hole_cards[0]} -> {describe(score0)}")
        print(f"    Player 1: {hole_cards[1]} -> {describe(score1)}")

    result = [0, 0]
    if score0 > score1:
        result[0] = pot - contrib[0]
        result[1] = -contrib[1]
        if verbose:
            print("    Player 0 wins!\n")
    elif score1 > score0:
        result[1] = pot - contrib[1]
        result[0] = -contrib[0]
        if verbose:
            print("    Player 1 wins!\n")
    else:
        # split pot
        result[0] = pot / 2 - contrib[0]
        result[1] = pot / 2 - contrib[1]
        if verbose:
            print("    Split pot (tie)!\n")

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true", help="Play and print a single hand")
    parser.add_argument("--hands", type=int, default=1000, help="Number of hands to simulate")
    args = parser.parse_args()

    my_bot = CustomPokerBot(name="MyBot")
    opponent = RandomBaselineBot(name="RandomBaseline")

    if args.watch:
        print("Watching one hand: Player 0 = MyBot (SB), Player 1 = RandomBaseline (BB)\n")
        result = play_hand([my_bot, opponent], verbose=True)
        print(f"Net result this hand -> MyBot: {result[0]:+.1f}  RandomBaseline: {result[1]:+.1f}")
        return

    total_hands = args.hands
    my_bot_net = 0.0
    wins = 0
    for i in range(total_hands):
        bots = [my_bot, opponent] if i % 2 == 0 else [opponent, my_bot]
        result = play_hand(bots, verbose=False)
        my_index = 0 if i % 2 == 0 else 1
        my_bot_net += result[my_index]
        if result[my_index] > 0:
            wins += 1

    print(f"Simulated {total_hands} hands: MyBot vs RandomBaseline")
    print(f"MyBot net chips: {my_bot_net:+.1f}")
    print(f"MyBot win rate (hands won): {wins / total_hands * 100:.1f}%")
    print(f"Average chips/hand (a common poker metric, in big blinds): "
          f"{(my_bot_net / total_hands) / BB_AMOUNT:+.3f} bb/hand")


if __name__ == "__main__":
    main()
