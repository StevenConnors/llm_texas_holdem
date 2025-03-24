import unittest
from hand_evaluator import HandEvaluator
from card import Card
from constants import (
    ROYAL_FLUSH, STRAIGHT_FLUSH, FOUR_OF_A_KIND, FULL_HOUSE,
    FLUSH, STRAIGHT, THREE_OF_A_KIND, TWO_PAIR, PAIR, HIGH_CARD,
    HAND_RANKINGS
)

class TestHandEvaluator(unittest.TestCase):
    """Test cases for the HandEvaluator class."""
    
    def setUp(self):
        """Initialize the HandEvaluator for testing."""
        self.evaluator = HandEvaluator()
    
    def test_evaluate_hand(self):
        """Table-driven tests for evaluating different poker hands."""
        # Test case format:
        # {
        #    'name': descriptive name of the test case,
        #    'cards': list of 7 Card objects (hole cards + community cards),
        #    'expected_rank': expected hand rank constant,
        #    'expected_name': expected hand name string
        # }
        
        test_cases = [
            # Royal Flush
            {
                'name': 'Royal Flush - Hearts',
                'cards': [
                    Card('H', 'A'), Card('H', 'K'),  # Hole cards
                    Card('H', 'Q'), Card('H', 'J'), Card('H', 'T'),  # Community cards
                    Card('S', '2'), Card('D', '3')   # Extra community cards
                ],
                'expected_rank': ROYAL_FLUSH,
                'expected_name': HAND_RANKINGS[ROYAL_FLUSH]
            },
            
            # Straight Flush
            {
                'name': 'Straight Flush - 9 high',
                'cards': [
                    Card('C', '5'), Card('C', '6'),  # Hole cards
                    Card('C', '7'), Card('C', '8'), Card('C', '9'),  # Community cards
                    Card('H', 'A'), Card('S', 'K')   # Extra community cards
                ],
                'expected_rank': STRAIGHT_FLUSH,
                'expected_name': HAND_RANKINGS[STRAIGHT_FLUSH]
            },
            {
                'name': 'Straight Flush - 6 high',
                'cards': [
                    Card('D', '2'), Card('D', '3'),  # Hole cards
                    Card('D', '4'), Card('D', '5'), Card('D', '6'),  # Community cards
                    Card('H', 'T'), Card('S', 'J')   # Extra community cards
                ],
                'expected_rank': STRAIGHT_FLUSH,
                'expected_name': HAND_RANKINGS[STRAIGHT_FLUSH]
            },
            
            # Four of a Kind
            {
                'name': 'Four of a Kind - Aces',
                'cards': [
                    Card('H', 'A'), Card('D', 'A'),  # Hole cards
                    Card('C', 'A'), Card('S', 'A'), Card('H', 'K'),  # Community cards
                    Card('D', 'Q'), Card('C', 'J')   # Extra community cards
                ],
                'expected_rank': FOUR_OF_A_KIND,
                'expected_name': HAND_RANKINGS[FOUR_OF_A_KIND]
            },
            {
                'name': 'Four of a Kind - Eights',
                'cards': [
                    Card('H', '8'), Card('D', '8'),  # Hole cards
                    Card('C', '8'), Card('S', '8'), Card('H', '2'),  # Community cards
                    Card('D', '3'), Card('C', '4')   # Extra community cards
                ],
                'expected_rank': FOUR_OF_A_KIND,
                'expected_name': HAND_RANKINGS[FOUR_OF_A_KIND]
            },
            
            # Full House
            {
                'name': 'Full House - Aces full of Kings',
                'cards': [
                    Card('H', 'A'), Card('D', 'A'),  # Hole cards
                    Card('C', 'A'), Card('S', 'K'), Card('H', 'K'),  # Community cards
                    Card('D', '2'), Card('C', '3')   # Extra community cards
                ],
                'expected_rank': FULL_HOUSE,
                'expected_name': HAND_RANKINGS[FULL_HOUSE]
            },
            {
                'name': 'Full House - Tens full of Nines',
                'cards': [
                    Card('H', 'T'), Card('D', 'T'),  # Hole cards
                    Card('C', 'T'), Card('S', '9'), Card('H', '9'),  # Community cards
                    Card('D', '2'), Card('C', '3')   # Extra community cards
                ],
                'expected_rank': FULL_HOUSE,
                'expected_name': HAND_RANKINGS[FULL_HOUSE]
            },
            
            # Flush
            {
                'name': 'Flush - Ace high',
                'cards': [
                    Card('D', 'A'), Card('D', 'J'),  # Hole cards
                    Card('D', '8'), Card('D', '6'), Card('D', '2'),  # Community cards
                    Card('H', 'K'), Card('S', 'Q')   # Extra community cards
                ],
                'expected_rank': FLUSH,
                'expected_name': HAND_RANKINGS[FLUSH]
            },
            {
                'name': 'Flush - King high',
                'cards': [
                    Card('S', 'K'), Card('S', 'J'),  # Hole cards
                    Card('S', '9'), Card('S', '7'), Card('S', '2'),  # Community cards
                    Card('H', 'A'), Card('D', 'Q')   # Extra community cards
                ],
                'expected_rank': FLUSH,
                'expected_name': HAND_RANKINGS[FLUSH]
            },
            
            # Straight
            {
                'name': 'Straight - Ace high',
                'cards': [
                    Card('H', 'A'), Card('D', 'K'),  # Hole cards
                    Card('C', 'Q'), Card('S', 'J'), Card('H', 'T'),  # Community cards
                    Card('D', '2'), Card('C', '3')   # Extra community cards
                ],
                'expected_rank': STRAIGHT,
                'expected_name': HAND_RANKINGS[STRAIGHT]
            },
            {
                'name': 'Straight - 8 high',
                'cards': [
                    Card('H', '4'), Card('D', '5'),  # Hole cards
                    Card('C', '6'), Card('S', '7'), Card('H', '8'),  # Community cards
                    Card('D', 'A'), Card('C', 'K')   # Extra community cards
                ],
                'expected_rank': STRAIGHT,
                'expected_name': HAND_RANKINGS[STRAIGHT]
            },
            {
                'name': 'Straight - 5 high (wheel)',
                'cards': [
                    Card('H', 'A'), Card('D', '2'),  # Hole cards
                    Card('C', '3'), Card('S', '4'), Card('H', '5'),  # Community cards
                    Card('D', 'J'), Card('C', 'Q')   # Extra community cards
                ],
                'expected_rank': STRAIGHT,
                'expected_name': HAND_RANKINGS[STRAIGHT]
            },
            
            # Three of a Kind
            {
                'name': 'Three of a Kind - Queens',
                'cards': [
                    Card('H', 'Q'), Card('D', 'Q'),  # Hole cards
                    Card('C', 'Q'), Card('S', '8'), Card('H', '2'),  # Community cards
                    Card('D', '3'), Card('C', '4')   # Extra community cards
                ],
                'expected_rank': THREE_OF_A_KIND,
                'expected_name': HAND_RANKINGS[THREE_OF_A_KIND]
            },
            
            # Two Pair
            {
                'name': 'Two Pair - Aces and Kings',
                'cards': [
                    Card('H', 'A'), Card('D', 'A'),  # Hole cards
                    Card('C', 'K'), Card('S', 'K'), Card('H', '2'),  # Community cards
                    Card('D', '3'), Card('C', '4')   # Extra community cards
                ],
                'expected_rank': TWO_PAIR,
                'expected_name': HAND_RANKINGS[TWO_PAIR]
            },
            {
                'name': 'Two Pair - Jacks and Fives',
                'cards': [
                    Card('H', 'J'), Card('D', 'J'),  # Hole cards
                    Card('C', '5'), Card('S', '5'), Card('H', 'A'),  # Community cards
                    Card('D', '3'), Card('C', '4')   # Extra community cards
                ],
                'expected_rank': TWO_PAIR,
                'expected_name': HAND_RANKINGS[TWO_PAIR]
            },
            
            # One Pair
            {
                'name': 'One Pair - Tens',
                'cards': [
                    Card('H', 'T'), Card('D', 'T'),  # Hole cards
                    Card('C', 'A'), Card('S', 'K'), Card('H', 'Q'),  # Community cards
                    Card('D', '3'), Card('C', '2')   # Extra community cards
                ],
                'expected_rank': PAIR,
                'expected_name': HAND_RANKINGS[PAIR]
            },
            {
                'name': 'One Pair - Threes with high kickers',
                'cards': [
                    Card('H', '3'), Card('D', '3'),  # Hole cards
                    Card('C', 'A'), Card('S', 'K'), Card('H', 'Q'),  # Community cards
                    Card('D', 'J'), Card('C', 'T')   # Extra community cards
                ],
                'expected_rank': PAIR,
                'expected_name': HAND_RANKINGS[PAIR]
            },
            
            # High Card
            {
                'name': 'High Card - Ace high with good kickers',
                'cards': [
                    Card('H', 'A'), Card('D', 'K'),  # Hole cards
                    Card('C', 'Q'), Card('S', 'J'), Card('H', '9'),  # Community cards
                    Card('D', '7'), Card('C', '5')   # Extra community cards
                ],
                'expected_rank': HIGH_CARD,
                'expected_name': HAND_RANKINGS[HIGH_CARD]
            },
            {
                'name': 'High Card - King high with mediocre kickers',
                'cards': [
                    Card('H', 'K'), Card('D', 'J'),  # Hole cards
                    Card('C', '8'), Card('S', '6'), Card('H', '4'),  # Community cards
                    Card('D', '3'), Card('C', '2')   # Extra community cards
                ],
                'expected_rank': HIGH_CARD,
                'expected_name': HAND_RANKINGS[HIGH_CARD]
            },
            
            # Near misses - testing boundary conditions
            {
                'name': 'Near miss - Almost Straight Flush',
                'cards': [
                    Card('H', '2'), Card('H', '3'),  # Hole cards
                    Card('H', '4'), Card('H', '5'), Card('D', '6'),  # Community cards - D instead of H for 6
                    Card('C', 'A'), Card('S', 'K')   # Extra community cards
                ],
                'expected_rank': FLUSH,  # It's still a flush, not a straight flush
                'expected_name': HAND_RANKINGS[FLUSH]
            },
            {
                'name': 'Near miss - Almost Flush',
                'cards': [
                    Card('D', 'A'), Card('D', 'K'),  # Hole cards
                    Card('D', 'Q'), Card('D', 'J'), Card('C', 'T'),  # Community cards - C instead of D for T
                    Card('H', '2'), Card('S', '3')   # Extra community cards
                ],
                'expected_rank': FLUSH,  # It's still a flush, not a royal flush
                'expected_name': HAND_RANKINGS[FLUSH]
            }
        ]
        
        # Run each test case
        for tc in test_cases:
            with self.subTest(name=tc['name']):
                rank, name = self.evaluator.evaluate_hand(tc['cards'])
                self.assertEqual(rank, tc['expected_rank'], f"Expected rank {tc['expected_rank']} ({HAND_RANKINGS[tc['expected_rank']]}), got {rank} ({name})")
                self.assertEqual(name, tc['expected_name'])
    
    def test_compare_hands(self):
        """Test comparing hands to determine winners."""
        # Test case format:
        # {
        #    'name': descriptive name of the test case,
        #    'hand1': (rank, value, name) tuple for hand 1,
        #    'hand2': (rank, value, name) tuple for hand 2,
        #    'expected_result': expected comparison result (1 if hand1 wins, -1 if hand2 wins, 0 if tie)
        # }
        
        test_cases = [
            # Different hand ranks
            {
                'name': 'Full House beats Flush',
                'hand1': (FULL_HOUSE, (12, 11), "Full House"),  # Aces full of Kings
                'hand2': (FLUSH, (12, 11, 10, 9, 8), "Flush"),  # Ace-high flush
                'expected_result': 1  # Hand1 wins
            },
            {
                'name': 'Straight beats Three of a Kind',
                'hand1': (STRAIGHT, (12, 11, 10, 9, 8), "Straight"),  # Ace-high straight
                'hand2': (THREE_OF_A_KIND, (12, (11, 10)), "Three of a Kind"),  # Three Aces
                'expected_result': 1  # Hand1 wins
            },
            
            # Same hand rank, different values
            {
                'name': 'Higher Four of a Kind wins',
                'hand1': (FOUR_OF_A_KIND, (12, 11), "Four of a Kind"),  # Four Aces, King kicker
                'hand2': (FOUR_OF_A_KIND, (11, 10), "Four of a Kind"),  # Four Kings, Queen kicker
                'expected_result': 1  # Hand1 wins
            },
            {
                'name': 'Higher Full House wins',
                'hand1': (FULL_HOUSE, (12, 11), "Full House"),  # Aces full of Kings
                'hand2': (FULL_HOUSE, (11, 12), "Full House"),  # Kings full of Aces
                'expected_result': 1  # Hand1 wins
            },
            {
                'name': 'Higher kicker wins in same Three of a Kind',
                'hand1': (THREE_OF_A_KIND, (12, (11, 10)), "Three of a Kind"),  # Three Aces, K-Q kickers
                'hand2': (THREE_OF_A_KIND, (12, (10, 9)), "Three of a Kind"),  # Three Aces, Q-J kickers
                'expected_result': 1  # Hand1 wins
            },
            {
                'name': 'Higher pair wins in One Pair',
                'hand1': (PAIR, (12, (11, 10, 9)), "Pair"),  # Pair of Aces, K-Q-J kickers
                'hand2': (PAIR, (11, (12, 10, 9)), "Pair"),  # Pair of Kings, A-Q-J kickers
                'expected_result': 1  # Hand1 wins
            },
            
            # Tie scenarios
            {
                'name': 'Identical hands tie',
                'hand1': (FLUSH, (12, 11, 10, 9, 8), "Flush"),  # Ace-high flush
                'hand2': (FLUSH, (12, 11, 10, 9, 8), "Flush"),  # Identical Ace-high flush
                'expected_result': 0  # Tie
            }
        ]
        
        # Run each test case
        for tc in test_cases:
            with self.subTest(name=tc['name']):
                result = self.evaluator.compare_hands(tc['hand1'], tc['hand2'])
                self.assertEqual(result, tc['expected_result'], 
                                f"{tc['name']}: Expected {tc['expected_result']}, got {result}")
    
    def test_evaluate_specific_scenarios(self):
        """Test specific poker scenarios that might be edge cases."""
        # Test case format:
        # {
        #    'name': descriptive name of the test case,
        #    'cards': list of 7 Card objects,
        #    'expected_rank': expected hand rank,
        #    'description': detailed description of the scenario
        # }
        
        test_cases = [
            # The case where A can be low in a straight
            {
                'name': 'A-5 Straight (wheel)',
                'cards': [
                    Card('H', 'A'), Card('D', '2'),  # Hole cards
                    Card('C', '3'), Card('S', '4'), Card('H', '5'),  # Community cards
                    Card('D', 'K'), Card('C', 'Q')   # Extra community cards
                ],
                'expected_rank': STRAIGHT,
                'description': 'A can be low in a straight, making A-2-3-4-5 (the wheel)'
            },
            
            # Testing that suits don't matter for most hand rankings
            {
                'name': 'Mixed Suit Straight',
                'cards': [
                    Card('H', '6'), Card('D', '7'),  # Hole cards
                    Card('C', '8'), Card('S', '9'), Card('H', 'T'),  # Community cards
                    Card('D', '2'), Card('C', '3')   # Extra community cards
                ],
                'expected_rank': STRAIGHT,
                'description': 'Straight with mixed suits is still a straight'
            },
            
            # Testing that we find the best hand from the 7 cards
            {
                'name': 'Best 5 from 7 cards',
                'cards': [
                    Card('H', 'A'), Card('D', 'A'),  # Hole cards - pair of Aces
                    Card('C', 'K'), Card('S', 'K'), Card('H', 'K'),  # Community cards - three Kings
                    Card('D', '2'), Card('C', '2')   # Extra community cards - pair of 2s
                ],
                'expected_rank': FULL_HOUSE,
                'description': 'Should find Kings full of Aces as the best hand, not using the pair of 2s'
            },
            
            # Test with the same rank in different suits
            {
                'name': 'Same Rank Different Suits',
                'cards': [
                    Card('H', 'T'), Card('D', 'T'),  # Hole cards
                    Card('C', 'T'), Card('S', 'T'), Card('H', '9'),  # Community cards
                    Card('D', '8'), Card('C', '7')   # Extra community cards
                ],
                'expected_rank': FOUR_OF_A_KIND,
                'description': 'Four of a kind with all four tens'
            }
        ]
        
        # Run each test case
        for tc in test_cases:
            with self.subTest(name=tc['name']):
                rank, name = self.evaluator.evaluate_hand(tc['cards'])
                self.assertEqual(rank, tc['expected_rank'], 
                              f"{tc['name']} ({tc['description']}): Expected {HAND_RANKINGS[tc['expected_rank']]}, got {name}")

if __name__ == '__main__':
    unittest.main() 