"""
utils/constants.py
==================

Global constants used throughout the poker engine.

Nothing in this file should ever change while the game is running.
"""

# ==========================================================
# CARD CONSTANTS
# ==========================================================

# Rank values
RANKS = tuple(range(2, 15))

# Rank character lookup
VALUE_TO_RANK = {
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "T",
    11: "J",
    12: "Q",
    13: "K",
    14: "A",
}

RANK_TO_VALUE = {v: k for k, v in VALUE_TO_RANK.items()}

RANK_NAMES = {
    2: "Two",
    3: "Three",
    4: "Four",
    5: "Five",
    6: "Six",
    7: "Seven",
    8: "Eight",
    9: "Nine",
    10: "Ten",
    11: "Jack",
    12: "Queen",
    13: "King",
    14: "Ace",
}

# ==========================================================
# SUITS
# ==========================================================

HEARTS = 0
DIAMONDS = 1
CLUBS = 2
SPADES = 3

SUITS = (HEARTS, DIAMONDS, CLUBS, SPADES)

SUIT_TO_CHAR = {
    HEARTS: "h",
    DIAMONDS: "d",
    CLUBS: "c",
    SPADES: "s",
}

CHAR_TO_SUIT = {v: k for k, v in SUIT_TO_CHAR.items()}

SUIT_NAMES = {
    HEARTS: "Hearts",
    DIAMONDS: "Diamonds",
    CLUBS: "Clubs",
    SPADES: "Spades",
}

# ==========================================================
# PLAYER ACTIONS
# ==========================================================

FOLD = "FOLD"
CALL = "CALL"
RAISE = "RAISE"

LEGAL_ACTIONS = (
    FOLD,
    CALL,
    RAISE,
)

# ==========================================================
# BETTING
# ==========================================================

INITIAL_STACK = 100

SMALL_BLIND = 1
BIG_BLIND = 2

SMALL_BET = 2
BIG_BET = 4

MAX_BETS_PER_ROUND = 4

# ==========================================================
# GAME STREETS
# ==========================================================

PRE_FLOP = 0
FLOP = 1
TURN = 2
RIVER = 3
SHOWDOWN = 4

STREET_NAMES = {
    PRE_FLOP: "Pre-Flop",
    FLOP: "Flop",
    TURN: "Turn",
    RIVER: "River",
    SHOWDOWN: "Showdown",
}

# ==========================================================
# HAND RANKS
# ==========================================================

HIGH_CARD = 0
ONE_PAIR = 1
TWO_PAIR = 2
THREE_KIND = 3
STRAIGHT = 4
FLUSH = 5
FULL_HOUSE = 6
FOUR_KIND = 7
STRAIGHT_FLUSH = 8
ROYAL_FLUSH = 9

HAND_NAMES = {
    HIGH_CARD: "High Card",
    ONE_PAIR: "One Pair",
    TWO_PAIR: "Two Pair",
    THREE_KIND: "Three of a Kind",
    STRAIGHT: "Straight",
    FLUSH: "Flush",
    FULL_HOUSE: "Full House",
    FOUR_KIND: "Four of a Kind",
    STRAIGHT_FLUSH: "Straight Flush",
    ROYAL_FLUSH: "Royal Flush",
}

# ==========================================================
# MONTE CARLO
# ==========================================================

DEFAULT_SIMULATIONS = 2000

# ==========================================================
# ENGINE
# ==========================================================

TOTAL_CARDS = 52

HOLE_CARDS = 2

FLOP_CARDS = 3

TURN_CARDS = 1

RIVER_CARDS = 1

TOTAL_COMMUNITY_CARDS = 5