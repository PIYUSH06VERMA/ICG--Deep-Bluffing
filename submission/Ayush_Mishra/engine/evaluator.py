"""
engine/evaluator.py

Poker hand evaluator for Texas Hold'em.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations

from collections import Counter
from itertools import combinations

from engine.card import Card

from engine.card import Card


class Evaluator:
    """
    Static poker hand evaluator.
    """

    # ==========================================================
    # Basic Helper Functions
    # ==========================================================

    @staticmethod
    def _rank_counts(cards):
        """
        Returns:
            Counter(rank -> frequency)
        """

        return Counter(card.rank for card in cards)

    @staticmethod
    def _suit_counts(cards):
        """
        Returns:
            Counter(suit -> frequency)
        """

        return Counter(card.suit for card in cards)

    @staticmethod
    def _sorted_ranks(cards):
        """
        Returns ranks sorted in descending order.

        Example:
            Ah Kd Js 8c 6h

        Returns:
            [14,13,11,8,6]
        """

        return sorted(
            (card.rank for card in cards),
            reverse=True
        )

    # ==========================================================
    # Flush Detection
    # ==========================================================

    @staticmethod
    def _is_flush(cards):
        """
        Returns True if all cards are same suit.
        """

        return len(Evaluator._suit_counts(cards)) == 1

    # ==========================================================
    # Straight Detection
    # ==========================================================

    @staticmethod
    def _is_straight(cards):
        """
        Returns:
            (True, high_card)

        or

            (False, None)
        """

        ranks = sorted(
            {card.rank for card in cards},
            reverse=True
        )

        if len(ranks) != 5:
            return False, None

        # Wheel straight
        # A 2 3 4 5

        if ranks == [14, 5, 4, 3, 2]:
            return True, 5

        if ranks[0] - ranks[-1] == 4:
            return True, ranks[0]

        return False, None

    # ==========================================================
    # Sorting Helpers
    # ==========================================================

    @staticmethod
    def _ranks_by_frequency(cards):
        """
        Returns ranks sorted by

        frequency
        then
        rank

        Example

        AAAKK

        returns

        [14,13]
        """

        counts = Evaluator._rank_counts(cards)

        return sorted(
            counts.keys(),
            key=lambda r: (counts[r], r),
            reverse=True
        )

    @staticmethod
    def _kickers(cards, excluded):
        """
        Returns remaining ranks after excluding some.

        Parameters
        ----------
        excluded : iterable
            ranks to ignore
        """

        excluded = set(excluded)

        return sorted(
            (
                card.rank
                for card in cards
                if card.rank not in excluded
            ),
            reverse=True
        )

    # ==========================================================
    # Public Interface (implemented later)
    # ==========================================================

    @staticmethod
    def evaluate_five(cards):
        """
        Evaluate exactly five cards.
        """

        raise NotImplementedError

    @staticmethod
    def evaluate_best(cards):
        """
        Evaluate best hand from 5–7 cards.
        """

        cards = list(cards)

        if not (5 <= len(cards) <= 7):
            raise ValueError("Must evaluate between 5 and 7 cards.")

        best = None

        for hand in combinations(cards, 5):
            score = Evaluator.evaluate_five(hand)

            if best is None or score > best:
                best = score

        return best

    @staticmethod
    def compare(cards1, cards2):
        """
        Compare two hands.

        Returns

        1
            first wins

        0
            tie

        -1
            second wins
        """

        score1 = Evaluator.evaluate_best(cards1)
        score2 = Evaluator.evaluate_best(cards2)

        if score1 > score2:
            return 1

        if score2 > score1:
            return -1

        return 0

    @staticmethod
    def evaluate_five(cards):
        """
        Evaluate exactly five cards.

        Returns
        -------
        tuple

        Larger tuple = better hand.
        """

        if len(cards) != 5:
            raise ValueError("Exactly five cards required.")

        rank_counts = Evaluator._rank_counts(cards)

        frequencies = sorted(
            rank_counts.values(),
            reverse=True
        )

        flush = Evaluator._is_flush(cards)

        straight, straight_high = Evaluator._is_straight(cards)

        ranks = Evaluator._sorted_ranks(cards)

        # ---------------------------------------------------------
        # Royal Flush
        # ---------------------------------------------------------

        if flush and straight and straight_high == 14:
            return (9,)

        # ---------------------------------------------------------
        # Straight Flush
        # ---------------------------------------------------------

        if flush and straight:
            return (8, straight_high)

        # ---------------------------------------------------------
        # Four of a Kind
        # ---------------------------------------------------------

        if frequencies == [4, 1]:
            quad = max(rank for rank, count in rank_counts.items()
                       if count == 4)

            kicker = max(rank for rank, count in rank_counts.items()
                         if count == 1)

            return (7, quad, kicker)

        # ---------------------------------------------------------
        # Full House
        # ---------------------------------------------------------

        if frequencies == [3, 2]:
            trip = max(rank for rank, count in rank_counts.items()
                       if count == 3)

            pair = max(rank for rank, count in rank_counts.items()
                       if count == 2)

            return (6, trip, pair)

        # ---------------------------------------------------------
        # Flush
        # ---------------------------------------------------------

        if flush:
            return (5, *ranks)

        # ---------------------------------------------------------
        # Straight
        # ---------------------------------------------------------

        if straight:
            return (4, straight_high)

        # ---------------------------------------------------------
        # Three of a Kind
        # ---------------------------------------------------------

        if frequencies == [3, 1, 1]:
            trip = max(rank for rank, count in rank_counts.items()
                       if count == 3)

            kickers = sorted(
                (rank for rank, count in rank_counts.items()
                 if count == 1),
                reverse=True
            )

            return (3, trip, *kickers)

        # ---------------------------------------------------------
        # Two Pair
        # ---------------------------------------------------------

        if frequencies == [2, 2, 1]:
            pairs = sorted(
                (rank for rank, count in rank_counts.items()
                 if count == 2),
                reverse=True
            )

            kicker = max(
                rank for rank, count in rank_counts.items()
                if count == 1
            )

            return (2, pairs[0], pairs[1], kicker)

        # ---------------------------------------------------------
        # One Pair
        # ---------------------------------------------------------

        if frequencies == [2, 1, 1, 1]:
            pair = max(
                rank for rank, count in rank_counts.items()
                if count == 2
            )

            kickers = sorted(
                (rank for rank, count in rank_counts.items()
                 if count == 1),
                reverse=True
            )

            return (1, pair, *kickers)

        # ---------------------------------------------------------
        # High Card
        # ---------------------------------------------------------

        return (0, *ranks)

if __name__ == "__main__":

    tests = {
        "Royal Flush": ["Ah", "Kh", "Qh", "Jh", "Th"],
        "Straight Flush": ["9h", "8h", "7h", "6h", "5h"],
        "Four Kind": ["Ah", "Ad", "Ac", "As", "Kh"],
        "Full House": ["Ah", "Ad", "Ac", "Kh", "Kd"],
        "Flush": ["Ah", "Jh", "8h", "5h", "2h"],
        "Straight": ["9h", "8d", "7c", "6s", "5h"],
        "Wheel Straight": ["Ah", "2d", "3c", "4s", "5h"],
        "Trips": ["Ah", "Ad", "Ac", "Kh", "2d"],
        "Two Pair": ["Ah", "Ad", "Kh", "Kd", "2c"],
        "Pair": ["Ah", "Ad", "Kh", "Qc", "2c"],
        "High Card": ["Ah", "Kd", "Qc", "8h", "2c"],
    }

    for name, hand in tests.items():
        cards = [Card.from_string(card) for card in hand]
        print(name)
        print(Evaluator.evaluate_five(cards))
        print("-" * 40)

    print("\nTesting 7-card evaluation")

    cards = [
        Card.from_string("Ah"),
        Card.from_string("Ad"),
        Card.from_string("Ac"),
        Card.from_string("Kh"),
        Card.from_string("Kd"),
        Card.from_string("2c"),
        Card.from_string("3d"),
    ]

    print(Evaluator.evaluate_best(cards))