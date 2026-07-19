# -----------------------------
# Card Definitions
# -----------------------------

RANKS = ['2', '3', '4', '5', '6', '7',
         '8', '9', 'T', 'J', 'Q', 'K', 'A']

SUITS = ['h', 'd', 'c', 's']

RANK_VALUES = {
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8,
    '9': 9,
    'T': 10,
    'J': 11,
    'Q': 12,
    'K': 13,
    'A': 14
}

# -----------------------------
# Poker Hand Rankings
# -----------------------------

HAND_RANKINGS = {
    "HIGH_CARD": 0,
    "ONE_PAIR": 1,
    "TWO_PAIR": 2,
    "THREE_OF_A_KIND": 3,
    "STRAIGHT": 4,
    "FLUSH": 5,
    "FULL_HOUSE": 6,
    "FOUR_OF_A_KIND": 7,
    "STRAIGHT_FLUSH": 8,
    "ROYAL_FLUSH": 9
}

# -----------------------------
# Betting Constants
# -----------------------------

INITIAL_STACK = 100

SMALL_BLIND = 1
BIG_BLIND = 2

SMALL_BET = 2
BIG_BET = 4

MAX_RAISES = 3

# -----------------------------
# Streets
# -----------------------------

PRE_FLOP = "PRE_FLOP"
FLOP = "FLOP"
TURN = "TURN"
RIVER = "RIVER"
SHOWDOWN = "SHOWDOWN"

# -----------------------------
# Player Actions
# -----------------------------

FOLD = "FOLD"
CALL = "CALL"
RAISE = "RAISE"