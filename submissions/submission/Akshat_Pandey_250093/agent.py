from engine import HandEvaluator

class BasePokerBot:
    def __init__(self, name):
        self.name = name

    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        raise NotImplementedError("Subclasses must implement get_action!")

class CustomPokerBot(BasePokerBot):
    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        # 1. Evaluate hand strength
        score = HandEvaluator.evaluate(hole_cards, community_cards)
        
        # 2. Normalize hand strength (Assuming 800 is the max possible score)
        win_prob = min(score / 800.0, 1.0)
        
        # 3. Calculate Pot Odds
        total_pot = pot_size + amount_to_call
        pot_odds = amount_to_call / total_pot if total_pot > 0 else 0
        
        # 4. Strategy: Bet when our win probability is higher than the pot odds
        if win_prob > pot_odds:
            if win_prob > 0.6 and 'RAISE' in legal_actions:
                return 'RAISE'
            if 'CALL' in legal_actions:
                return 'CALL'
        
        # 5. Safety Fallback
        if 'CHECK' in legal_actions:
            return 'CHECK'
        if 'CALL' in legal_actions:
            return 'CALL'
        return 'FOLD'