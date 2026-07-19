import random
import itertools
from collections import Counter

# =====================================================================
# CORE ENGINE DATA & DICTIONARIES
# =====================================================================
RANKS = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
SUITS = ["h", "d", "c", "s"]
RANK_CHARS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]

# Helper functions for processing card strings
def get_rank(card): return RANKS[card[0]]
def get_suit(card): return card[1]
def create_deck(): return [rank + suit for rank in RANK_CHARS for suit in SUITS]
def remove_known_cards(deck, known_cards): return [card for card in deck if card not in known_cards]
def get_all_ranks(cards): return sorted([get_rank(c) for c in cards], reverse=True)
def get_all_suits(cards): return [get_suit(c) for c in cards]
def rank_counter(cards): return Counter(get_all_ranks(cards))
def is_flush(cards): return len(set(get_all_suits(cards))) == 1

def is_straight(cards):
    ranks = sorted(list(set(get_all_ranks(cards))))
    if ranks == [2, 3, 4, 5, 14]: return True  # Ace-low straight
    if len(ranks) != 5: return False
    for i in range(4):
        if ranks[i + 1] != ranks[i] + 1: return False
    return True

# =====================================================================
# PURE PYTHON HAND EVALUATOR (No External Libraries Used)
# =====================================================================
def evaluate_five_cards(cards):
    ranks = get_all_ranks(cards)
    counter = rank_counter(cards)
    values = sorted(counter.values(), reverse=True)
    flush = is_flush(cards)
    straight = is_straight(cards)

    if flush and sorted(ranks) == [10, 11, 12, 13, 14]: return (10, ranks)  # Royal Flush
    if flush and straight:
        actual_ranks = sorted(ranks)
        max_val = 5 if actual_ranks == [2, 3, 4, 5, 14] else max(ranks)
        return (9, [max_val])  # Straight Flush
    if values == [4, 1]:
        four = [r for r, count in counter.items() if count == 4][0]
        kicker = [r for r, count in counter.items() if count == 1][0]
        return (8, [four, kicker])  # Four of a Kind
    if values == [3, 2]:
        triple = [r for r, count in counter.items() if count == 3][0]
        pair = [r for r, count in counter.items() if count == 2][0]
        return (7, [triple, pair])  # Full House
    if flush: return (6, ranks)  # Flush
    if straight:
        actual_ranks = sorted(ranks)
        max_val = 5 if actual_ranks == [2, 3, 4, 5, 14] else max(ranks)
        return (5, [max_val])  # Straight
    if values == [3, 1, 1]:
        triple = [r for r, count in counter.items() if count == 3][0]
        kickers = sorted([r for r, count in counter.items() if count == 1], reverse=True)
        return (4, [triple] + kickers)  # Three of a Kind
    if values == [2, 2, 1]:
        pairs = sorted([r for r, count in counter.items() if count == 2], reverse=True)
        kicker = [r for r, count in counter.items() if count == 1][0]
        return (3, pairs + [kicker])  # Two Pair
    if values == [2, 1, 1, 1]:
        pair = [r for r, count in counter.items() if count == 2][0]
        kickers = sorted([r for r, count in counter.items() if count == 1], reverse=True)
        return (2, [pair] + kickers)  # One Pair
    return (1, ranks)  # High Card

def best_hand(cards):
    if len(cards) < 5: return (1, get_all_ranks(cards))
    best = None
    for hand in itertools.combinations(cards, 5):
        score = evaluate_five_cards(list(hand))
        if best is None or score > best: best = score
    return best

# =====================================================================
# MONTE CARLO SIMULATION ENGINE
# =====================================================================
def estimate_win_probability(hole_cards, community_cards, simulations=400):
    wins, ties = 0, 0
    base_deck = create_deck()
    cleaned_deck = remove_known_cards(base_deck, hole_cards + community_cards)
    
    for _ in range(simulations):
        deck = cleaned_deck[:]
        random.shuffle(deck)
        opponent = [deck.pop(), deck.pop()]
        board = community_cards[:]
        while len(board) < 5: 
            board.append(deck.pop())
            
        my_score = best_hand(hole_cards + board)
        opp_score = best_hand(opponent + board)
        
        if my_score > opp_score: wins += 1
        elif my_score == opp_score: ties += 1
        
    return (wins + 0.5 * ties) / simulations

# =====================================================================
# SUBMISSION BASE CLASS
# =====================================================================
class BasePokerBot:
    def __init__(self, name):
        self.name = name
    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        raise NotImplementedError("Override this method")

# =====================================================================
# YOUR CUSTOM AGENT IMPLEMENTATION
# =====================================================================
class CustomPokerBot(BasePokerBot):
    def __init__(self, name="DeepBluff"):
        super().__init__(name)

    def get_action(self, hole_cards, community_cards, pot_size, stack_size, amount_to_call, legal_actions):
        # Fallback guard rule
        if not legal_actions: return "FOLD"
        
        # -----------------------------------------------------------------
        # Stage A: PRE-FLOP DECISION TREE (No community cards out yet)
        # -----------------------------------------------------------------
        if len(community_cards) == 0:
            r1, r2 = get_rank(hole_cards[0]), get_rank(hole_cards[1])
            is_pair = (r1 == r2)
            is_suited = (get_suit(hole_cards[0]) == get_suit(hole_cards[1]))
            high_cards = (r1 >= 10 or r2 >= 10)
            gap = abs(r1 - r2)
            
            # Premium pairs (T Tens and above) -> Aggressive push
            if is_pair and r1 >= 10: 
                return "RAISE" if "RAISE" in legal_actions else "CALL"
            
            # Speculative hands (Pairs, high connectors, suited connectors)
            if is_pair or (high_cards and gap <= 3) or (is_suited and gap <= 2):
                if "RAISE" in legal_actions and random.random() < 0.35: 
                    return "RAISE"
                return "CALL" if "CALL" in legal_actions else legal_actions[0]
            else:
                # Trash hands -> Check if free, else Fold
                return "CALL" if amount_to_call == 0 else ("FOLD" if "FOLD" in legal_actions else legal_actions[0])

        # -----------------------------------------------------------------
        # Stage B: POST-FLOP MATHEMATICAL MATRICES (Flop, Turn, River)
        # -----------------------------------------------------------------
        street = len(community_cards)
        # Optimize simulation depth dynamically based on street compute budget
        simulations = 400 if street == 3 else 600
        
        win_prob = estimate_win_probability(hole_cards, community_cards, simulations)
        pot_odds = amount_to_call / max(pot_size + amount_to_call, 1)
        ev = (win_prob * pot_size) - ((1 - win_prob) * amount_to_call)

        # 1. Ultra-Strong Nuts Equity Threshold
        if win_prob >= 0.78:
            return "RAISE" if "RAISE" in legal_actions else "CALL"
            
        # 2. Strong Positive Value Equity
        if win_prob >= 0.58:
            if "RAISE" in legal_actions and random.random() < 0.60: 
                return "RAISE"
            return "CALL" if "CALL" in legal_actions else legal_actions[0]
            
        # 3. Marginal Pot-Odds Speculation Loop
        if win_prob >= 0.35:
            if amount_to_call == 0: 
                return "CALL"
            if win_prob >= pot_odds or ev > 0: 
                return "CALL"
            return "FOLD" if "FOLD" in legal_actions else legal_actions[0]
            
        # 4. Weak Hand Threshold -> Fold unless it's a free Check/Call
        if amount_to_call == 0: 
            return "CALL"
        return "FOLD" if "FOLD" in legal_actions else legal_actions[0]