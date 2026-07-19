"""
Test suite for Project Deep-Bluffing components built so far:
card.py, deck.py, constants.py, player.py, hand_evaluator.py,
game_engine.py.

Run with:  python test_everything.py
"""

import random
import traceback

from card import Card
from deck import Deck
from player import Player
from hand_evaluator import (
    evaluate_five_cards, evaluate_seven_cards, compare_hands
)
from game_engine import GameEngine
from constants import PRE_FLOP, FLOP, TURN, RIVER, FOLD, CALL, RAISE


PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


def cards(spec):
    """'Ah Kd 5c' -> [Card, Card, Card]"""
    return [Card.from_string(s) for s in spec.split()]


# =====================================================
# Card tests
# =====================================================

def test_card():
    print("\n--- Card ---")
    c1 = Card('A', 'h')
    c2 = Card.from_string('Ah')
    check("from_string round-trip", c1 == c2)
    check("str format", str(Card('T', 's')) == 'Ts')
    check("ordering", Card('K', 'h') > Card('2', 'd'))
    check("invalid rank raises", _raises(lambda: Card('1', 'h')))
    check("invalid suit raises", _raises(lambda: Card('A', 'x')))
    check("hashable", len({Card('A', 'h'), Card('A', 'h'), Card('A', 'd')}) == 2)


def _raises(fn):
    try:
        fn()
        return False
    except ValueError:
        return True


# =====================================================
# Deck tests
# =====================================================

def test_deck():
    print("\n--- Deck ---")
    d = Deck()
    check("starts with 52 cards", len(d) == 52)
    all_cards = d.get_cards()
    check("no duplicate cards", len(set(all_cards)) == 52)

    d.shuffle()
    dealt = [d.deal() for _ in range(52)]
    check("deals all 52 uniquely", len(set(dealt)) == 52)
    check("empty deck raises on deal", _raises_index(d))

    d2 = Deck()
    d2.shuffle()
    hole = d2.deal_hole_cards()
    flop = d2.deal_flop()
    turn = d2.deal_turn()
    river = d2.deal_river()
    check("deal_hole_cards returns 2", len(hole) == 2)
    check("deal_flop returns 3", len(flop) == 3)
    check("deal_turn returns Card", isinstance(turn, Card))
    check("deal_river returns Card", isinstance(river, Card))
    check("remaining after full deal = 52-2-3-1-1",
          len(d2) == 52 - 2 - 3 - 1 - 1)


def _raises_index(deck):
    try:
        deck.deal()
        return False
    except IndexError:
        return True


# =====================================================
# Hand evaluator tests
# =====================================================

def test_hand_evaluator():
    print("\n--- Hand Evaluator (5-card) ---")

    royal = evaluate_five_cards(cards("Ah Kh Qh Jh Th"))
    check("royal flush category", royal.hand_name == "ROYAL_FLUSH")

    sflush = evaluate_five_cards(cards("9h 8h 7h 6h 5h"))
    check("straight flush category", sflush.hand_name == "STRAIGHT_FLUSH")

    wheel_sflush = evaluate_five_cards(cards("5h 4h 3h 2h Ah"))
    check("wheel straight flush category", wheel_sflush.hand_name == "STRAIGHT_FLUSH")
    check("wheel straight flush high=5", wheel_sflush.tiebreakers == [5])

    quads = evaluate_five_cards(cards("9h 9d 9c 9s 2h"))
    check("four of a kind category", quads.hand_name == "FOUR_OF_A_KIND")

    fh = evaluate_five_cards(cards("Kh Kd Ks 2h 2d"))
    check("full house category", fh.hand_name == "FULL_HOUSE")
    check("full house tiebreak order", fh.tiebreakers == [13, 2])

    flush = evaluate_five_cards(cards("2h 5h 9h Jh Kh"))
    check("flush category", flush.hand_name == "FLUSH")

    straight = evaluate_five_cards(cards("6h 7d 8h 9c Ts"))
    check("straight category", straight.hand_name == "STRAIGHT")

    wheel = evaluate_five_cards(cards("Ah 2d 3h 4c 5s"))
    check("wheel straight category", wheel.hand_name == "STRAIGHT")
    check("wheel straight high=5", wheel.tiebreakers == [5])

    trips = evaluate_five_cards(cards("7h 7d 7c 2h 9d"))
    check("three of a kind category", trips.hand_name == "THREE_OF_A_KIND")

    two_pair = evaluate_five_cards(cards("Jh Jd 4c 4h 9s"))
    check("two pair category", two_pair.hand_name == "TWO_PAIR")

    one_pair = evaluate_five_cards(cards("3h 3d 9c Kh 2s"))
    check("one pair category", one_pair.hand_name == "ONE_PAIR")

    high = evaluate_five_cards(cards("2h 5d 9c Jh Kh"))
    check("high card category", high.hand_name == "HIGH_CARD")

    # ranking order sanity: flush beats straight beats trips
    check("flush > straight", flush > straight)
    check("straight > trips", straight > trips)
    check("quads > full house", quads > fh)

    print("\n--- Hand Evaluator (7-card, best-of-7) ---")

    seven = cards("Ah Kh Qh Jh Th 2c 3d")  # royal flush hidden in 7
    score = evaluate_seven_cards(seven)
    check("finds royal flush in 7 cards", score.hand_name == "ROYAL_FLUSH")

    # Split pot: both play the same board straight, no better hand possible
    board = cards("9h Th Jd Qc Ks")
    p1_hole = cards("2c 3d")
    p2_hole = cards("2h 3h")
    s1 = evaluate_seven_cards(p1_hole + board)
    s2 = evaluate_seven_cards(p2_hole + board)
    check("board-play tie -> compare_hands returns 0",
          compare_hands(s1, s2) == 0,
          detail=f"s1={s1}, s2={s2}")

    # Clear win: pair of aces vs pair of kings (no overlapping cards)
    s3 = evaluate_seven_cards(cards("Ah Ad 2c 5d 9h Jc 3s"))
    s4 = evaluate_seven_cards(cards("Kh Kd 2c 5d 9h Jc 3s"))
    check("AA beats KK", compare_hands(s3, s4) == 1)


# =====================================================
# Player tests
# =====================================================

def test_player():
    print("\n--- Player ---")
    p = Player("Test")
    check("starts with 100 stack", p.stack == 100)
    check("starts with bot=None", p.bot is None)

    p.receive_cards(cards("Ah Kd"))
    check("receive_cards adds 2", len(p.hole_cards) == 2)
    check("receive 3rd card raises", _raises(lambda: p.receive_card(Card('2', 'h'))))

    committed = p.place_bet(30)
    check("place_bet commits full amount when affordable", committed == 30)
    check("stack reduced correctly", p.stack == 70)

    committed2 = p.place_bet(1000)  # more than remaining stack
    check("place_bet caps at remaining stack (no crash)", committed2 == 70)
    check("stack now 0", p.stack == 0)

    p.reset_for_new_hand()
    check("reset clears hole cards", p.hole_cards == [])
    check("reset does NOT touch stack (engine's job)", p.stack == 0)


# =====================================================
# Game engine tests
# =====================================================

class ScriptedBot:
    """Returns actions from a fixed list, in order, one per call."""
    def __init__(self, actions):
        self.actions = list(actions)
        self.calls = 0

    def get_action(self, hole_cards, community_cards, pot_size,
                    stack_size, amount_to_call, legal_actions):
        self.calls += 1
        if self.calls > len(self.actions):
            return CALL if CALL in legal_actions else FOLD
        action = self.actions[self.calls - 1]
        if action not in legal_actions:
            # scripted action illegal at this point; fall back
            return CALL if CALL in legal_actions else FOLD
        return action


class RandomLegalBot:
    """Always returns a random legal action (used for stress-testing)."""
    def get_action(self, hole_cards, community_cards, pot_size,
                    stack_size, amount_to_call, legal_actions):
        return random.choice(legal_actions)


def test_engine_check_check_showdown():
    print("\n--- GameEngine: check-check every street to showdown ---")
    p1 = Player("P1", bot=ScriptedBot([CALL] * 10))
    p2 = Player("P2", bot=ScriptedBot([CALL] * 10))
    engine = GameEngine(p1, p2)
    engine.play_hand()

    check("chip conservation (sums to 200)", p1.stack + p2.stack == 200,
          detail=f"p1={p1.stack} p2={p2.stack}")
    check("community cards = 5 at showdown", len(engine.community_cards) == 5)


def test_engine_fold_preflop():
    print("\n--- GameEngine: immediate fold pre-flop ---")
    p1 = Player("P1", bot=ScriptedBot([FOLD]))
    p2 = Player("P2", bot=ScriptedBot([CALL] * 10))
    engine = GameEngine(p1, p2)
    winner = engine.play_hand()

    check("winner is P2", winner is p2)
    check("chip conservation (sums to 200)", p1.stack + p2.stack == 200,
          detail=f"p1={p1.stack} p2={p2.stack}")
    check("loser stack decreased", p1.stack < 100)
    check("winner stack increased", p2.stack > 100)


def test_engine_raise_war_to_cap():
    print("\n--- GameEngine: raise war up to the 4-bet cap (pre-flop) ---")
    # Both players keep raising as long as it's legal; engine must
    # enforce the cap rather than allow infinite raising.
    p1 = Player("P1", bot=ScriptedBot([RAISE] * 10 + [CALL] * 10))
    p2 = Player("P2", bot=ScriptedBot([RAISE] * 10 + [CALL] * 10))
    engine = GameEngine(p1, p2)
    engine.play_hand()

    check("chip conservation (sums to 200)", p1.stack + p2.stack == 200,
          detail=f"p1={p1.stack} p2={p2.stack}")


def test_engine_many_random_hands():
    print("\n--- GameEngine: 500 hands with random legal actions (stress test) ---")
    p1 = Player("P1", bot=RandomLegalBot())
    p2 = Player("P2", bot=RandomLegalBot())
    engine = GameEngine(p1, p2)

    ok = True
    error_detail = ""
    for i in range(500):
        # Each hand is isolated: reset stacks to 100 per the spec.
        p1.stack = 100
        p2.stack = 100
        try:
            engine.play_hand()
        except Exception as e:
            ok = False
            error_detail = f"hand {i}: {type(e).__name__}: {e}\n{traceback.format_exc()}"
            break
        if p1.stack + p2.stack != 200:
            ok = False
            error_detail = f"hand {i}: chip mismatch p1={p1.stack} p2={p2.stack}"
            break

    check("500 random hands run without crashing, chips always conserved", ok, detail=error_detail)


def test_engine_dealer_alternates():
    print("\n--- GameEngine: dealer alternates each hand ---")
    p1 = Player("P1", bot=ScriptedBot([CALL] * 10))
    p2 = Player("P2", bot=ScriptedBot([CALL] * 10))
    engine = GameEngine(p1, p2)

    d0 = engine.dealer_index
    engine.play_hand()
    d1 = engine.dealer_index
    check("dealer switches after one hand", d0 != d1)


# =====================================================
# Run everything
# =====================================================

if __name__ == "__main__":
    test_card()
    test_deck()
    test_hand_evaluator()
    test_player()
    test_engine_check_check_showdown()
    test_engine_fold_preflop()
    test_engine_raise_war_to_cap()
    test_engine_dealer_alternates()
    test_engine_many_random_hands()

    print(f"\n{'='*50}")
    print(f"TOTAL: {PASS} passed, {FAIL} failed")
    print(f"{'='*50}")
