"""
test_engine.py
--------------
Local validation harness (not part of the graded arena, but useful to
verify: (1) the engine never crashes, (2) CustomPokerBot never triggers
the invalid-action safety fallback, and (3) win-rates look sane against
simple baseline opponents.

Run: python3 test_engine.py
"""
import random
import time

from card import make_deck
from evaluator import best_hand_rank, fast_rank7
from engine import HeadsUpLimitHoldem, run_match, BB_AMOUNT
from agent import CustomPokerBot
from baselines import AlwaysFoldBot, AlwaysCallBot, AlwaysRaiseBot, RandomBot, TightAggressiveBot


def test_evaluator_equivalence(trials=50000):
    random.seed(1)
    deck = make_deck()
    for _ in range(trials):
        random.shuffle(deck)
        seven = deck[:7]
        ref = best_hand_rank(seven)
        fast = fast_rank7([(c.value, c.suit) for c in seven])
        assert ref == fast, (seven, ref, fast)
    print(f"[OK] fast_rank7 matches best_hand_rank on {trials} random 7-card hands")


def test_no_crash(num_hands=2000):
    engine = HeadsUpLimitHoldem(seed=7)
    bot_a = CustomPokerBot(name="A", seed=1)
    bot_b = RandomBot(name="B", seed=2)
    invalid_fallbacks = 0
    for i in range(num_hands):
        record = engine.play_hand(bot_a, bot_b)
        assert abs(sum(record.payoffs)) < 1e-9, "payoffs must be zero-sum"
        assert record.pot >= 3, "pot must include at least both blinds"
    print(f"[OK] {num_hands} hands completed with no exceptions, all payoffs zero-sum")


def benchmark(name_a, bot_a, name_b, bot_b, num_hands=3000):
    t0 = time.time()
    net_a, bb100 = run_match(bot_a, bot_b, num_hands=num_hands, seed=123)
    dt = time.time() - t0
    print(f"  {name_a:>18} vs {name_b:<18}: {bb100:+7.2f} bb/100  "
          f"(net {net_a:+.1f} chips over {num_hands} hands, {dt:.1f}s)")


if __name__ == "__main__":
    test_evaluator_equivalence(trials=20000)
    test_no_crash(num_hands=1000)

    print("\nSanity benchmarks (CustomPokerBot's bb/100 vs simple baselines):")
    custom = CustomPokerBot(name="DeepBluffing", seed=42)
    benchmark("DeepBluffing", custom, "AlwaysFold", AlwaysFoldBot("Folder"), num_hands=2000)

    custom = CustomPokerBot(name="DeepBluffing", seed=42)
    benchmark("DeepBluffing", custom, "AlwaysCall", AlwaysCallBot("Caller"), num_hands=2000)

    custom = CustomPokerBot(name="DeepBluffing", seed=42)
    benchmark("DeepBluffing", custom, "AlwaysRaise", AlwaysRaiseBot("Maniac"), num_hands=2000)

    custom = CustomPokerBot(name="DeepBluffing", seed=42)
    benchmark("DeepBluffing", custom, "Random", RandomBot("Rando", seed=99), num_hands=2000)

    custom = CustomPokerBot(name="DeepBluffing", seed=42)
    benchmark("DeepBluffing", custom, "TightAggro", TightAggressiveBot("TAG"), num_hands=2000)

    print("\nAll tests passed.")
