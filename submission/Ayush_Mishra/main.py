"""
main.py

Runs a Heads-Up Limit Texas Hold'em match
between two poker agents.
"""

from agent import PokerAgent
from engine.game import PokerGame


def main():

    game = PokerGame(starting_chips=100)

    bot1 = PokerAgent(simulations=1000)
    bot2 = PokerAgent(simulations=1000)

    hand = 1

    while all(player.chips > 0 for player in game.players):

        print(f"\n{'=' * 50}")
        print(f"Hand {hand}")
        print(f"{'=' * 50}")

        winner = game.play_hand([bot1, bot2])

        if winner is None:
            print("Result: Tie")
        else:
            print(f"Winner: {winner.name}")

        for player in game.players:
            print(f"{player.name}: {player.chips} chips")

        hand += 1

    print("\nMatch Over!")

    winner = max(game.players, key=lambda p: p.chips)

    print(f"Overall Winner: {winner.name}")


if __name__ == "__main__":
    main()