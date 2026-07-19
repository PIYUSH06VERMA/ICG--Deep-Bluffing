"""
test_cfr_integration.py
-------------------------
Simulates a full multi-street hand to make sure the internal state
tracking (street detection, bets_count reconstruction) behaves sensibly
and the bot never crashes or returns an illegal action, whether or not
cfr_strategy.json is present.
"""

from agent import CustomPokerBot


def simulate_hand(bot, label):
    print(f"--- {label} ---")

    # Preflop: bot is SB, facing the BB's blind
    a = bot.get_action(['Ah', 'Kd'], [], 3, 99, 1, ['FOLD', 'CALL', 'RAISE'])
    print(f"Preflop (facing blind): street_bets={bot._bets_count_this_street} -> {a}")
    assert a in ['FOLD', 'CALL', 'RAISE']

    # Suppose opponent re-raised preflop -> bot asked again on same street
    a = bot.get_action(['Ah', 'Kd'], [], 9, 95, 4, ['FOLD', 'CALL', 'RAISE'])
    print(f"Preflop (facing re-raise): street_bets={bot._bets_count_this_street} -> {a}")
    assert a in ['FOLD', 'CALL', 'RAISE']

    # Flop dealt -> new street, bot is BB now, acts first, nothing to call
    a = bot.get_action(['Ah', 'Kd'], ['2h', '7s', '9d'], 18, 91, 0, ['CALL', 'RAISE'])
    print(f"Flop (first to act, check): street_bets={bot._bets_count_this_street} -> {a}")
    assert a in ['CALL', 'RAISE']

    # Turn dealt -> new street again
    a = bot.get_action(['Ah', 'Kd'], ['2h', '7s', '9d', '3c'], 18, 91, 0, ['CALL', 'RAISE'])
    print(f"Turn (first to act, check): street_bets={bot._bets_count_this_street} -> {a}")
    assert a in ['CALL', 'RAISE']

    # River dealt, facing a bet this time
    a = bot.get_action(['Ah', 'Kd'], ['2h', '7s', '9d', '3c', 'Kh'], 22, 87, 4,
                        ['FOLD', 'CALL', 'RAISE'])
    print(f"River (facing bet): street_bets={bot._bets_count_this_street} -> {a}")
    assert a in ['FOLD', 'CALL', 'RAISE']

    print("Hand simulation completed with no illegal actions.\n")


def main():
    bot = CustomPokerBot(simulations=200)
    print(f"CFR strategy loaded: {len(bot.cfr_strategy)} infosets\n")

    simulate_hand(bot, "Hand 1 (fresh bot)")

    # Start a brand new hand with the SAME bot instance (as the arena would)
    simulate_hand(bot, "Hand 2 (same instance, should reset state cleanly)")

    print("ALL CFR INTEGRATION TESTS PASSED")


if __name__ == "__main__":
    main()
