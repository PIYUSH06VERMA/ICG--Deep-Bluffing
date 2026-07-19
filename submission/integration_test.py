"""
End-to-end integration test for the real submission file: plays
many hands using agent.CustomPokerBot (exactly what the tournament
arena will load) through game_engine.py, and checks for crashes,
chip conservation, and reasonable timing.

Run with: python integration_test.py
"""

import time

from player import Player
from game_engine import GameEngine
from agent import CustomPokerBot


def run_match(num_hands=300):
    p1 = Player("Bot1", bot=CustomPokerBot("Bot1"))
    p2 = Player("Bot2", bot=CustomPokerBot("Bot2"))
    engine = GameEngine(p1, p2)

    start = time.time()
    errors = 0
    error_detail = ""

    for i in range(num_hands):
        # Each hand is an isolated episode: fresh 100-chip stacks.
        p1.stack = 100
        p2.stack = 100
        try:
            engine.play_hand()
        except Exception as e:
            errors += 1
            error_detail = f"hand {i}: {type(e).__name__}: {e}"
            break

        if p1.stack + p2.stack != 200:
            errors += 1
            error_detail = f"hand {i}: chip mismatch p1={p1.stack} p2={p2.stack}"
            break

    elapsed = time.time() - start
    hands_run = i + 1 if errors else num_hands

    print(f"Hands attempted: {hands_run}")
    print(f"Errors: {errors}  {error_detail}")
    print(f"Time: {elapsed:.2f}s ({elapsed/hands_run*1000:.1f} ms/hand)")
    print(f"Projected time for 10,000 hands: {elapsed/hands_run*10000/60:.1f} minutes")

    if errors == 0:
        print("Chip conservation held on every hand. No crashes.")
    else:
        print("FAILED — see error above.")


if __name__ == "__main__":
    run_match(300)
