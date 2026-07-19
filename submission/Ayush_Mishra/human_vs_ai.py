from engine.game import PokerGame
from engine.player import Player
from engine.human_player import HumanPlayer
from agent import PokerAgent

human = HumanPlayer("You", 100)
ai_player = Player("Computer", 100)

game = PokerGame(players=[human, ai_player])

bot = PokerAgent(simulations=500)
bots = [human, bot]

hand = 1

while human.chips > 0 and ai_player.chips > 0:

    print("\n" + "=" * 50)
    print(f"HAND {hand}")
    print("=" * 50)

    winner = game.play_hand(bots)

    if winner is None:
        print("\nHand tied.")
    else:
        print(f"\nWinner: {winner.name}")

    print("\nChip Counts")
    print(f"{human.name}: {human.chips}")
    print(f"{ai_player.name}: {ai_player.chips}")

    hand += 1

    again = input("\nPlay next hand? (y/n): ").strip().lower()

    if again != "y":
        break

print("\nGame Over!")