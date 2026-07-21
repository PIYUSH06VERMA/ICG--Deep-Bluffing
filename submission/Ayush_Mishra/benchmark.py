"""
benchmark.py

Benchmark script for Heads-Up Limit Texas Hold'em.
Runs multiple hands between two PokerAgents and reports statistics.
"""

from engine.game import PokerGame
from agent import PokerAgent

# -----------------------------
# Configuration
# -----------------------------
NUM_HANDS = 1000

bot1 = PokerAgent(simulations=500)
bot2 = PokerAgent(simulations=500)

game = PokerGame(starting_chips=100)

wins = [0, 0]
ties = 0

# -----------------------------
# Tournament
# -----------------------------
for hand in range(1, NUM_HANDS + 1):

    winner = game.play_hand([bot1, bot2])

    if winner is None:
        ties += 1
    elif winner.name == "Player 1":
        wins[0] += 1
    else:
        wins[1] += 1

    if hand % 50 == 0:
        print(f"Completed {hand}/{NUM_HANDS} hands")

# -----------------------------
# Results
# -----------------------------
print("\n==============================")
print("      TOURNAMENT RESULTS")
print("==============================")

print(f"Hands Played      : {NUM_HANDS}")
print(f"Player 1 Wins     : {wins[0]}")
print(f"Player 2 Wins     : {wins[1]}")
print(f"Ties              : {ties}")

print(f"\nPlayer 1 Win Rate : {wins[0] / NUM_HANDS:.2%}")
print(f"Player 2 Win Rate : {wins[1] / NUM_HANDS:.2%}")
print(f"Tie Rate          : {ties / NUM_HANDS:.2%}")

print("\nFinal Chip Counts")
print("------------------------------")
print(f"Player 1 : {game.players[0].chips}")
print(f"Player 2 : {game.players[1].chips}")