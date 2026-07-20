import random
from itertools import combinations
from collections import Counter

class Card:
    RANK_MAP = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 
                'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

    def __init__(self, card_str):
        self.rank_str = card_str[0]
        self.suit = card_str[1]
        self.value = self.RANK_MAP[self.rank_str]

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

    # Added __gt__ to explicitly handle 'greater than' comparisons
    def __gt__(self, other):
        return self.value > other.value

    def __repr__(self):
        return f"{self.rank_str}{self.suit}"

class Deck:
    def __init__(self):
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        self.suits = ['h', 'd', 'c', 's']
        self.cards = [] # 
        for r in self.ranks:        
            for s in self.suits:   
                card_string = r + s 
                new_card = Card(card_string) 
                self.cards.append(new_card) 
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        if len(self.cards) > 0:
            return self.cards.pop()
        else:
            return None

    def __repr__(self):
        return f"Deck of {len(self.cards)} cards"
    
class GameEngine:
    def __init__(self):
        self.deck = Deck()
        self.pot = 0
        self.community_cards = []
        self.street = "Pre-Flop"  
        self.bets_this_street = 0 
        self.small_blind = 1
        self.big_blind = 2
        
    def start_hand(self):
        self.deck = Deck()
        self.pot = self.small_blind + self.big_blind 
        self.community_cards = []
        self.street = "Pre-Flop"
        
    def get_bet_increment(self):
        if self.street in ["Pre-Flop", "Flop"]:
            return 2
        return 4

    def process_action(self, action, player, amount_to_call):
        if action == "FOLD":
            pass
        elif action == "CALL":
            self.pot += amount_to_call
        elif action == "RAISE":
            increment = self.get_bet_increment()
            self.pot += (amount_to_call + increment)
            self.bets_this_street += 1
            
    def proceed_to_next_street(self):
        streets = ["Pre-Flop", "Flop", "Turn", "River", "Showdown"]
        current_idx = streets.index(self.street)
        if current_idx < len(streets) - 1:
            self.street = streets[current_idx + 1]
            self.bets_this_street = 0 


class HandEvaluator:
    @staticmethod
    def get_rank(card_str):
        # Maps '2'-'A' to 2-14
        ranks = '23456789TJQKA'
        return ranks.index(card_str[0]) + 2

    @staticmethod
    def evaluate(hole_cards, community_cards):
        # Convert all Card objects to their string representation (e.g., 'As', 'Kd')
        all_cards = [str(c) for c in (hole_cards + community_cards)]
        
        # Get all 21 possible 5-card combinations
        best_score = 0
        for combo in combinations(all_cards, 5):
            score = HandEvaluator.score_5_cards(combo)
            if score > best_score:
                best_score = score
        return best_score

    @staticmethod
    def score_5_cards(cards):
        ranks = sorted([HandEvaluator.get_rank(c) for c in cards], reverse=True)
        suits = [c[1] for c in cards]
        counts = Counter(ranks)
        
        # Check Flush
        is_flush = len(set(suits)) == 1
        
        # Check Straight (only works for sorted ranks)
        is_straight = (len(counts) == 5 and (max(ranks) - min(ranks) == 4))
        
        # Basic Ranking (Return a higher number for better hands)
        if is_flush and is_straight: return 800  # Straight Flush
        if 4 in counts.values():      return 700  # Four of a Kind
        if 3 in counts.values() and 2 in counts.values(): return 600 # Full House
        if is_flush:                  return 500  # Flush
        if is_straight:               return 400  # Straight
        if 3 in counts.values():      return 300  # Three of a Kind
        if list(counts.values()).count(2) == 2: return 200 # Two Pair
        if 2 in counts.values():      return 100  # Pair
        return ranks[0] # High Card