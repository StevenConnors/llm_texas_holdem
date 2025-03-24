from collections import defaultdict
from constants import (
    RANKS, HIGH_CARD, PAIR, TWO_PAIR, THREE_OF_A_KIND, STRAIGHT,
    FLUSH, FULL_HOUSE, FOUR_OF_A_KIND, STRAIGHT_FLUSH, ROYAL_FLUSH,
    HAND_RANKINGS
)

class HandEvaluator:
    """Evaluates poker hands to determine their ranking and value."""
    
    @staticmethod
    def evaluate_hand(cards):
        """
        Evaluate a 7-card poker hand to find the best 5-card hand.
        
        Args:
            cards (list): A list of 7 Card objects (5 community + 2 hole cards)
            
        Returns:
            tuple: (hand_rank, hand_name) - the rank and name of the best hand
        """
        # Check if we have enough cards
        if len(cards) < 5:
            raise ValueError("Need at least 5 cards to evaluate a hand")
            
        # Get all possible 5-card combinations from the 7 cards
        best_rank = -1
        best_value = None
        best_hand = None
        
        # Try all possible 5-card combinations
        from itertools import combinations
        for hand in combinations(cards, 5):
            rank, value = HandEvaluator._evaluate_five_card_hand(hand)
            if rank > best_rank or (rank == best_rank and value > best_value):
                best_rank = rank
                best_value = value
                best_hand = list(hand)
        
        # Get the hand name from the rank
        hand_name = HAND_RANKINGS[best_rank]
                
        return best_rank, hand_name
    
    @staticmethod
    def _evaluate_five_card_hand(hand):
        """
        Evaluate a 5-card hand and return its rank and value.
        
        Args:
            hand (list): A list of 5 Card objects
            
        Returns:
            tuple: (hand_rank, hand_value) where:
                  hand_rank is one of the hand ranking constants
                  hand_value is a tuple used for comparing hands of the same rank
        """
        # Check for flush
        suits = [card.suit for card in hand]
        is_flush = len(set(suits)) == 1
        
        # Get ranks and their counts
        ranks = [card.rank for card in hand]
        rank_values = [card.rank_value for card in hand]
        rank_values.sort(reverse=True)  # Sort in descending order
        
        rank_counts = defaultdict(int)
        for rank in ranks:
            rank_counts[rank] += 1
            
        # Check for straight
        is_straight = False
        if len(set(rank_values)) == 5:  # All ranks are different
            if max(rank_values) - min(rank_values) == 4:
                is_straight = True
            # Check for A-5 straight (special case)
            elif set(rank_values) == {0, 1, 2, 3, 12}:  # A-5 straight (A=12, 5=3, 4=2, 3=1, 2=0)
                is_straight = True
                # For A-5 straight, Ace is low
                rank_values = [3, 2, 1, 0, -1]  # Treating A as lower than 2
        
        # Determine hand rank and value
        if is_straight and is_flush:
            # Check for royal flush (T-J-Q-K-A of the same suit)
            if set(ranks) == {'T', 'J', 'Q', 'K', 'A'}:
                return ROYAL_FLUSH, tuple(rank_values)
            else:
                return STRAIGHT_FLUSH, tuple(rank_values)
        
        # Look for four of a kind
        if 4 in rank_counts.values():
            four_rank = next(r for r, count in rank_counts.items() if count == 4)
            kicker = next(r for r in ranks if r != four_rank)
            four_value = RANKS.index(four_rank)
            kicker_value = RANKS.index(kicker)
            return FOUR_OF_A_KIND, (four_value, kicker_value)
        
        # Look for full house
        if 3 in rank_counts.values() and 2 in rank_counts.values():
            three_rank = next(r for r, count in rank_counts.items() if count == 3)
            pair_rank = next(r for r, count in rank_counts.items() if count == 2)
            return FULL_HOUSE, (RANKS.index(three_rank), RANKS.index(pair_rank))
        
        if is_flush:
            return FLUSH, tuple(rank_values)
        
        if is_straight:
            return STRAIGHT, tuple(rank_values)
        
        # Look for three of a kind
        if 3 in rank_counts.values():
            three_rank = next(r for r, count in rank_counts.items() if count == 3)
            kickers = [r for r in ranks if r != three_rank]
            kicker_values = sorted([RANKS.index(r) for r in kickers], reverse=True)
            return THREE_OF_A_KIND, (RANKS.index(three_rank), tuple(kicker_values))
        
        # Look for two pair
        if list(rank_counts.values()).count(2) == 2:
            pairs = [r for r, count in rank_counts.items() if count == 2]
            pair_values = sorted([RANKS.index(r) for r in pairs], reverse=True)
            kicker = next(r for r in ranks if r not in pairs)
            return TWO_PAIR, (tuple(pair_values), RANKS.index(kicker))
        
        # Look for one pair
        if 2 in rank_counts.values():
            pair_rank = next(r for r, count in rank_counts.items() if count == 2)
            kickers = [r for r in ranks if r != pair_rank]
            kicker_values = sorted([RANKS.index(r) for r in kickers], reverse=True)
            return PAIR, (RANKS.index(pair_rank), tuple(kicker_values))
        
        # High card
        return HIGH_CARD, tuple(rank_values)
    
    @staticmethod
    def compare_hands(hand1, hand2):
        """
        Compare two evaluated hands to determine the winner.
        
        Args:
            hand1 (tuple): (rank, value) tuple from evaluate_hand
            hand2 (tuple): (rank, value) tuple from evaluate_hand
            
        Returns:
            int: 1 if hand1 wins, -1 if hand2 wins, 0 if tie
        """
        rank1, value1, _ = hand1
        rank2, value2, _ = hand2
        
        if rank1 > rank2:
            return 1
        elif rank1 < rank2:
            return -1
        else:
            # Same rank, compare values
            if value1 > value2:
                return 1
            elif value1 < value2:
                return -1
            else:
                return 0  # Tie 