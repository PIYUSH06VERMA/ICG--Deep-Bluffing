import random
from agent import CustomPokerBot

def simulate_arena_turn():
    bot = CustomPokerBot(name="LocalDeepBluff")
    hole_cards = ['Ah', 'Kd']
    community_cards = ['7s', '7c', '2d']
    pot_size = 12
    stack_size = 88
    amount_to_call = 2
    legal_actions = ['FOLD', 'CALL', 'RAISE']
    
    print("=== DeepBluff Arena Simulator ===")
    decision = bot.get_action(
        hole_cards=hole_cards,
        community_cards=community_cards,
        pot_size=pot_size,
        stack_size=stack_size,
        amount_to_call=amount_to_call,
        legal_actions=legal_actions
    )
    print(f"? Bot Action Executed Successfully: {decision}")

if __name__ == "__main__":
    simulate_arena_turn()
