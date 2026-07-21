"""
edge_case_test.py -- Targeted stress test for short-stack / all-in / degenerate
states that validate_agent.py's *random* stress test likely under-samples
(random.randint(0,100) rarely lands exactly on 0, 1, 2 chips).

This directly targets:
  - stack_size == 0
  - stack_size == 1, 2, 3 (can't even cover a full raise)
  - amount_to_call > stack_size (forced all-in call)
  - amount_to_call == stack_size exactly
  - pot_size == 0
  - legal_actions == [FOLD, CALL] only (no raise allowed)
  - river with a nearly-exhausted deck (needed_board_cards == 0 edge)
  - preflop with huge pot_size relative to stack (weird ratios)
  - repeated identical state calls (make sure no hidden state corruption)
"""
import time
from agent import CustomPokerBot

FOLD, CALL, RAISE = "FOLD", "CALL", "RAISE"

bot = CustomPokerBot("EdgeTestBot")
bot.NUM_SIMULATIONS = 100

cases = []

# --- stack_size == 0 ---
cases.append(dict(hole_cards=['Ah','Kd'], community_cards=[], pot_size=10,
                   stack_size=0, amount_to_call=0, legal_actions=[FOLD, CALL]))
cases.append(dict(hole_cards=['2c','7d'], community_cards=['Ah','Kd','Qs'], pot_size=20,
                   stack_size=0, amount_to_call=0, legal_actions=[FOLD, CALL]))

# --- stack_size very small (1,2,3) with amount_to_call exceeding stack (all-in call) ---
cases.append(dict(hole_cards=['Th','Td'], community_cards=['9h','9c','2d'], pot_size=15,
                   stack_size=1, amount_to_call=4, legal_actions=[FOLD, CALL]))
cases.append(dict(hole_cards=['3h','3d'], community_cards=[], pot_size=3,
                   stack_size=2, amount_to_call=2, legal_actions=[FOLD, CALL, RAISE]))
cases.append(dict(hole_cards=['Ks','Qs'], community_cards=['2h','7d','9c','Jd'], pot_size=40,
                   stack_size=3, amount_to_call=20, legal_actions=[FOLD, CALL]))

# --- amount_to_call == stack_size exactly ---
cases.append(dict(hole_cards=['9h','9d'], community_cards=['2c','3d','4h'], pot_size=12,
                   stack_size=4, amount_to_call=4, legal_actions=[FOLD, CALL]))

# --- pot_size == 0 (very first preflop action edge, or degenerate test state) ---
cases.append(dict(hole_cards=['Ah','Ad'], community_cards=[], pot_size=0,
                   stack_size=100, amount_to_call=0, legal_actions=[FOLD, CALL, RAISE]))

# --- legal_actions == [FOLD, CALL] only (post-cap street) ---
cases.append(dict(hole_cards=['7h','2d'], community_cards=['Kd','Kc','Ks','2h'], pot_size=60,
                   stack_size=50, amount_to_call=4, legal_actions=[FOLD, CALL]))

# --- river, deck nearly exhausted, needed_board_cards == 0 ---
cases.append(dict(hole_cards=['5h','6h'], community_cards=['7h','8h','9c','2d','3s'], pot_size=30,
                   stack_size=25, amount_to_call=4, legal_actions=[FOLD, CALL, RAISE]))

# --- huge pot_size vs tiny stack (weird pot-odds ratio) ---
cases.append(dict(hole_cards=['4c','4d'], community_cards=['4h','9s','2c'], pot_size=500,
                   stack_size=1, amount_to_call=1, legal_actions=[FOLD, CALL]))

# --- negative-looking edge: amount_to_call == 0 but stack_size == 0 and no community cards yet ---
cases.append(dict(hole_cards=['2h','3d'], community_cards=[], pot_size=1,
                   stack_size=0, amount_to_call=0, legal_actions=[FOLD, CALL]))

# --- single legal action edge (degenerate legal_actions list) ---
cases.append(dict(hole_cards=['Ah','2d'], community_cards=['3c','4d','5h'], pot_size=10,
                   stack_size=0, amount_to_call=0, legal_actions=[CALL]))

print(f"Running {len(cases)} targeted edge cases...\n")
fail = 0
for i, c in enumerate(cases):
    start = time.perf_counter()
    try:
        action = bot.get_action(**c)
    except Exception as e:
        print(f"[{i}] EXCEPTION: {e}  -- state={c}")
        fail += 1
        continue
    elapsed = (time.perf_counter() - start) * 1000
    ok = action in c['legal_actions']
    status = "OK" if ok else "ILLEGAL!!"
    if not ok:
        fail += 1
    print(f"[{i}] stack={c['stack_size']:>4} to_call={c['amount_to_call']:>4} "
          f"pot={c['pot_size']:>4} legal={c['legal_actions']} -> {action} "
          f"({elapsed:.2f}ms) {status}")

# repeated identical calls -- make sure no hidden state corrupts a fixed state
print("\nRepeating case[3] 20x to check for state leakage / nondeterministic crashes...")
for _ in range(20):
    a = bot.get_action(**cases[3])
    if a not in cases[3]['legal_actions']:
        print("  ILLEGAL on repeat!", a)
        fail += 1
print("done.")

print(f"\n{'ALL EDGE CASES PASSED' if fail == 0 else f'{fail} FAILURES'}")
