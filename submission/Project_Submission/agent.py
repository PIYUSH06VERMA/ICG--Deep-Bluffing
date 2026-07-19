import random
import itertools
from collections import Counter

RANK_ORDER = "23456789TJQKA"
RANK_VALUE = {r: i + 2 for i, r in enumerate(RANK_ORDER)}
SUITS = "hdcs"

class Card:
    __slots__ = ("rank_char", "suit", "rank")

    def __init__(self, card_str):
        self.rank_char = card_str[0].upper()
        self.suit = card_str[1].lower()
        self.rank = RANK_VALUE[self.rank_char]

    def __repr__(self):
        return f"{self.rank_char}{self.suit}"

    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self):
        return hash((self.rank, self.suit))

    def __lt__(self, other):
        return self.rank < other.rank

    def __gt__(self, other):
        return self.rank > other.rank

def full_deck():
    return [Card(r + s) for r in RANK_ORDER for s in SUITS]

def _straight_high(unique_ranks_desc):
    if len(unique_ranks_desc) >= 5:
        for i in range(len(unique_ranks_desc) - 4):
            window = unique_ranks_desc[i:i + 5]
            if window[0] - window[4] == 4:
                return window[0]
    if set([14, 2, 3, 4, 5]).issubset(set(unique_ranks_desc)):
        return 5
    return None

def eval_5(cards):
    ranks = sorted((c.rank for c in cards), reverse=True)
    suits = [c.suit for c in cards]
    is_flush = len(set(suits)) == 1

    rank_counts = Counter(ranks)
    groups = sorted(rank_counts.items(), key=lambda kv: (-kv[1], -kv[0]))
    unique_desc = sorted(rank_counts.keys(), reverse=True)
    straight_high = _straight_high(unique_desc)

    if is_flush and straight_high is not None:
        return (8, straight_high)
    if groups[0][1] == 4:
        four = groups[0][0]
        kicker = max(r for r in ranks if r != four)
        return (7, four, kicker)
    if groups[0][1] == 3 and len(groups) > 1 and groups[1][1] == 2:
        return (6, groups[0][0], groups[1][0])
    if is_flush:
        return (5,) + tuple(ranks)
    if straight_high is not None:
        return (4, straight_high)
    if groups[0][1] == 3:
        trips = groups[0][0]
        kickers = tuple(sorted((r for r in ranks if r != trips), reverse=True)[:2])
        return (3, trips) + kickers
    if groups[0][1] == 2 and len(groups) > 1 and groups[1][1] == 2:
        hi_pair = max(groups[0][0], groups[1][0])
        lo_pair = min(groups[0][0], groups[1][0])
        kicker = max(r for r in ranks if r != hi_pair and r != lo_pair)
        return (2, hi_pair, lo_pair, kicker)
    if groups[0][1] == 2:
        pair = groups[0][0]
        kickers = tuple(sorted((r for r in ranks if r != pair), reverse=True)[:3])
        return (1, pair) + kickers
    return (0,) + tuple(ranks)

def best_hand_7(cards7):
    best = None
    for combo in itertools.combinations(cards7, 5):
        score = eval_5(combo)
        if best is None or score > best:
            best = score
    return best

def estimate_equity(hole_cards, community_cards, num_simulations):
    known = hole_cards + community_cards
    deck = [c for c in full_deck() if c not in known]
    needed_community = 5 - len(community_cards)
    draw_size = needed_community + 2

    if draw_size > len(deck) or num_simulations <= 0:
        return 0.5

    wins = 0.0
    for _ in range(num_simulations):
        sample = random.sample(deck, draw_size)
        opp_hole = sample[:2]
        extra_community = sample[2:2 + needed_community]
        board = community_cards + extra_community

        my_score = best_hand_7(hole_cards + board)
        opp_score = best_hand_7(opp_hole + board)

        if my_score > opp_score:
            wins += 1.0
        elif my_score == opp_score:
            wins += 0.5

    return wins / num_simulations

class BasePokerBot:
    def __init__(self, name):
        self.name = name

    def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                    amount_to_call, legal_actions):
        raise NotImplementedError("Your bot logic goes here!")

class CustomPokerBot(BasePokerBot):
    SIMS_BY_STREET = {
        0: 80,    
        3: 250,   
        4: 300,   
        5: 400,   
    }

    VALUE_RAISE_EQUITY = 0.60
    THIN_RAISE_EQUITY = 0.50
    BLUFF_RAISE_EQUITY = 0.35

    def _safe(self, action, legal_actions):
        if action in legal_actions:
            return action
        if "CALL" in legal_actions:
            return "CALL"
        return legal_actions[0]

    def get_action(self, hole_cards, community_cards, pot_size, stack_size,
                    amount_to_call, legal_actions):
        
        hole = [Card(c) for c in hole_cards]
        board = [Card(c) for c in community_cards]


        if len(board) == 0:
            h1, h2 = hole[0], hole[1]
            is_pair = h1.rank == h2.rank
            high_cards = (h1.rank >= 10 and h2.rank >= 10)
            
            if is_pair and h1.rank >= 9: 
                return self._safe("RAISE", legal_actions)
            if high_cards and "CALL" in legal_actions and amount_to_call <= 4:
                return "CALL"

        equity = estimate_equity(hole, board, self.SIMS_BY_STREET.get(len(board), 200))
        
        can_raise = "RAISE" in legal_actions
        facing_bet = amount_to_call > 0

        if facing_bet:
            pot_odds = amount_to_call / (pot_size + amount_to_call)

            
            if equity > self.VALUE_RAISE_EQUITY:
                return self._safe("RAISE" if can_raise else "CALL", legal_actions)

            if equity > (pot_odds + 0.03):
                if can_raise and equity > 0.63 and random.random() < 0.30:
                    return self._safe("RAISE", legal_actions)
                return self._safe("CALL", legal_actions)

            if can_raise and equity > self.BLUFF_RAISE_EQUITY and random.random() < 0.07:
                return self._safe("RAISE", legal_actions)

            return self._safe("FOLD", legal_actions)

        else:
            if equity > self.VALUE_RAISE_EQUITY:
                return self._safe("RAISE" if can_raise else "CALL", legal_actions)
            if can_raise and equity > self.THIN_RAISE_EQUITY and random.random() < 0.40:
                return self._safe("RAISE", legal_actions)
            
            return self._safe("CALL", legal_actions)
        
        