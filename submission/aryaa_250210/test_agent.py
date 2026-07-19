"""
test_agent.py
---------------
Sanity checks for CustomPokerBot's decision-making, using realistic
game-state snapshots. Run: `python test_agent.py`
"""

from agent import CustomPokerBot


def run_case(label, hole, community, pot, stack, to_call, legal):
    bot = CustomPokerBot(simulations=400)
    win_prob = bot.estimate_win_probability(hole, community)
    action = bot.get_action(hole, community, pot, stack, to_call, legal)
    print(f"{label}")
    print(f"  hole={hole} board={community} pot={pot} to_call={to_call}")
    print(f"  estimated win_prob={win_prob:.2f}  -->  action = {action}")
    assert action in legal, "BUG: returned an illegal action!"
    print()
    return action


def main():
    # Case 1: Pocket Aces preflop, cheap to call -> should NOT fold
    run_case(
        "Pocket Aces preflop (should call/raise, never fold)",
        hole=['Ah', 'Ad'], community=[],
        pot=3, stack=99, to_call=2,
        legal=['FOLD', 'CALL', 'RAISE']
    )

    # Case 2: Garbage hand (7-2 offsuit, the worst starting hand) facing a big raise
    run_case(
        "7-2 offsuit facing a big bet (should likely fold)",
        hole=['7h', '2d'], community=['Kc', 'Qs', 'Jh'],
        pot=20, stack=80, to_call=8,
        legal=['FOLD', 'CALL']
    )

    # Case 3: Already made nut flush on the river -> should raise
    run_case(
        "Nut flush on the river (should raise for value)",
        hole=['Ah', 'Kh'], community=['2h', '5h', '9h', 'Jd', '3c'],
        pot=30, stack=70, to_call=4,
        legal=['FOLD', 'CALL', 'RAISE']
    )

    # Case 4: amount_to_call == 0 (checking is free) -> should never fold
    run_case(
        "Free check (to_call=0), weak-ish hand",
        hole=['9c', '4d'], community=['Ah', 'Kc', '2s'],
        pot=10, stack=90, to_call=0,
        legal=['CALL', 'RAISE']
    )

    print("ALL AGENT TESTS PASSED (no illegal actions returned)")


if __name__ == "__main__":
    main()
