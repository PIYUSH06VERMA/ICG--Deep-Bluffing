"""
validate_agent.py -- Run this before submitting to catch anything that
would crash or zero-out your bot in the real arena.

Checks:
1. agent.py defines BasePokerBot and CustomPokerBot with the EXACT signature.
2. CustomPokerBot never raises an exception across thousands of random states.
3. CustomPokerBot NEVER returns an action outside legal_actions.
4. Runs a long multi-hand match through the engine and confirms stacks
   stay consistent (no chips created/destroyed out of thin air).
5. Times how long get_action() takes on average (arena likely has a
   per-decision time budget).
"""

import time
import random
import inspect

from cards import Card, make_deck
from agent import BasePokerBot, CustomPokerBot
from engine import HULHEEngine, RandomAgent, AlwaysCallAgent

FOLD, CALL, RAISE = "FOLD", "CALL", "RAISE"


def check_signature():
    print("== 1. Checking class / method signature ==")
    assert issubclass(CustomPokerBot, BasePokerBot), "CustomPokerBot must subclass BasePokerBot"

    sig = inspect.signature(CustomPokerBot.get_action)
    expected_params = ['self', 'hole_cards', 'community_cards', 'pot_size',
                        'stack_size', 'amount_to_call', 'legal_actions']
    actual_params = list(sig.parameters.keys())
    assert actual_params == expected_params, (
        f"get_action signature mismatch!\nExpected: {expected_params}\nGot: {actual_params}"
    )
    print("PASS: signature matches exactly.\n")


def check_no_crashes_and_legal_actions(num_trials=3000):
    print(f"== 2 & 3. Stress-testing get_action() across {num_trials} random states ==")
    bot = CustomPokerBot("StressTestBot")
    bot.NUM_SIMULATIONS = 100  # speed up the stress test
    rng = random.Random(0)

    illegal_count = 0
    exception_count = 0
    total_time = 0.0

    for i in range(num_trials):
        deck = make_deck()
        rng.shuffle(deck)

        num_hole = 2
        num_board = rng.choice([0, 3, 4, 5])  # preflop / flop / turn / river
        hole = [str(c) for c in deck[:num_hole]]
        board = [str(c) for c in deck[num_hole:num_hole + num_board]]

        pot_size = rng.randint(2, 60)
        stack_size = rng.randint(0, 100)
        amount_to_call = rng.choice([0, 1, 2, 3, 4, rng.randint(0, 20)])

        legal_actions = rng.choice([
            [FOLD, CALL],
            [FOLD, CALL, RAISE],
        ])

        start = time.perf_counter()
        try:
            action = bot.get_action(
                hole_cards=hole,
                community_cards=board,
                pot_size=pot_size,
                stack_size=stack_size,
                amount_to_call=amount_to_call,
                legal_actions=legal_actions,
            )
        except Exception as e:
            exception_count += 1
            print(f"  EXCEPTION on trial {i}: {e}")
            continue
        elapsed = time.perf_counter() - start
        total_time += elapsed

        if action not in legal_actions:
            illegal_count += 1
            print(f"  ILLEGAL ACTION on trial {i}: returned {action!r}, "
                  f"legal was {legal_actions}")

    avg_time_ms = (total_time / num_trials) * 1000
    print(f"Exceptions: {exception_count}/{num_trials}")
    print(f"Illegal actions: {illegal_count}/{num_trials}")
    print(f"Avg decision time: {avg_time_ms:.2f} ms")

    assert exception_count == 0, "Bot threw exceptions -- FIX BEFORE SUBMITTING"
    assert illegal_count == 0, "Bot returned illegal actions -- FIX BEFORE SUBMITTING"
    print("PASS: no exceptions, no illegal actions.\n")
    return avg_time_ms


def check_chip_conservation(num_hands=2000):
    print(f"== 4. Chip conservation check over {num_hands} hands ==")
    bot = CustomPokerBot("DeepBluff")
    bot.NUM_SIMULATIONS = 80
    opponent = RandomAgent("RandBot", seed=6)

    engine = HULHEEngine(bot, opponent, name_a="DeepBluff", name_b="RandBot",
                          verbose=False, seed=42)

    for _ in range(num_hands):
        result = engine.play_hand()
        total_chips = sum(result["stacks"].values())
        assert total_chips == 200, (
            f"Chip conservation violated! Total chips = {total_chips}, expected 200. "
            f"Stacks: {result['stacks']}"
        )
        engine.swap_dealer()

    print("PASS: total chips == 200 after every single hand (no leaks).\n")


def check_win_rate_vs_baselines():
    print("== 5. Win-rate sanity vs baseline bots ==")
    for opp_cls, opp_name in [(RandomAgent, "RandomAgent"), (AlwaysCallAgent, "AlwaysCallAgent")]:
        bot = CustomPokerBot("DeepBluff")
        bot.NUM_SIMULATIONS = 120
        opponent = opp_cls(opp_name, seed=1) if opp_cls is RandomAgent else opp_cls(opp_name)

        engine = HULHEEngine(bot, opponent, name_a="DeepBluff", name_b=opp_name,
                              verbose=False, seed=10)
        results = engine.play_match(num_hands=500)

        wins = sum(1 for r in results if r["winner"] == "DeepBluff")
        losses = sum(1 for r in results if r["winner"] == opp_name)
        splits = sum(1 for r in results if r["winner"] is None)
        final_stacks = results[-1]["stacks"]

        print(f"  vs {opp_name}: {wins}W / {losses}L / {splits}T   "
              f"final stacks: {final_stacks}")

    print()


if __name__ == "__main__":
    check_signature()
    avg_ms = check_no_crashes_and_legal_actions(num_trials=3000)
    check_chip_conservation(num_hands=2000)
    check_win_rate_vs_baselines()

    print("=" * 60)
    print("ALL VALIDATION CHECKS PASSED.")
    print(f"Average decision time: {avg_ms:.2f} ms "
          f"(make sure this is well within any arena time limit).")
    print("=" * 60)
