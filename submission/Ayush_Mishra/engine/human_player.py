from engine.player import Player


class HumanPlayer(Player):
    """
    Human-controlled poker player.
    """

    def choose_action(self, legal_actions):
        print("\nYour available actions:")

        for i, action in enumerate(legal_actions, 1):
            print(f"{i}. {action.upper()}")

        while True:
            try:
                choice = int(input("\nChoose action: "))

                if 1 <= choice <= len(legal_actions):
                    return legal_actions[choice - 1]

                print("Invalid choice.")

            except ValueError:
                print("Enter a valid number.")