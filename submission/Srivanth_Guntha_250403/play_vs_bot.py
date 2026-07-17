import random
import sys

from agent import CustomPokerBot
from engine import HeadsUpLimitHoldem


class HumanBot:
    def __init__(self, name):
        self.name = name

    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        print(f"\nYour hole cards : {hole_cards}")
        print(f"Community cards : {community_cards if community_cards else '(none yet)'}")
        print(f"Pot size        : {pot_size}")
        print(f"Your stack      : {stack_size}")
        print(f"Amount to call  : {amount_to_call}")
        print(f"Legal actions   : {legal_actions}")

        alias = {
            "f": "FOLD", "fold": "FOLD",
            "c": "CALL", "call": "CALL", "check": "CALL", "k": "CALL",
            "r": "RAISE", "raise": "RAISE", "bet": "RAISE",
        }

        while True:
            raw = input("Your action (fold/call/raise): ").strip().lower()
            if raw in ("q", "quit", "exit"):
                print("Exiting game. Thanks for playing!")
                sys.exit(0)
            action = alias.get(raw)
            if action is None:
                print(f"  Didn't understand {raw!r}. Try: fold, call, raise, or quit.")
                continue
            if action not in legal_actions:
                print(f"  {action} isn't legal right now. Legal actions: {legal_actions}")
                continue
            return action


def main():
    print("=" * 60)
    print(" Deep-Bluffing: Heads-Up Limit Hold'em vs CustomPokerBot")
    print("=" * 60)
    print("Type 'fold', 'call' (also serves as check), or 'raise'.")
    print("Type 'quit' any time to stop.\n")

    try:
        n_hands = input("How many hands do you want to play? [default 10]: ").strip()
        n_hands = int(n_hands) if n_hands else 10
    except ValueError:
        n_hands = 10

    human = HumanBot("You")
    bot = CustomPokerBot("DeepBluff")

    engine = HeadsUpLimitHoldem(human, bot, rng=random.Random(), verbose=True)

    total_you, total_bot = 0.0, 0.0
    for i in range(n_hands):
        button = i % 2
        who_dealer = "You are" if button == 0 else "Bot is"
        print(f"\n\n########## HAND {i + 1}/{n_hands}  ({who_dealer} the dealer/small blind) ##########")
        result = engine.play_hand(button=button)
        total_you += result.payoff_p0
        total_bot += result.payoff_p1
        print(f"\nHand result: You {result.payoff_p0:+.1f}  |  Bot {result.payoff_p1:+.1f}")
        print(f"Running total: You {total_you:+.1f}  |  Bot {total_bot:+.1f}")

    print("\n" + "=" * 60)
    print(f"FINAL SCORE after {n_hands} hands: You {total_you:+.1f}  |  Bot {total_bot:+.1f}")
    print("=" * 60)


if __name__ == "__main__":
    main()