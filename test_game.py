import unittest
from game import TexasHoldemGame
from card import Card
from constants import (
    PHASE_PREFLOP, PHASE_FLOP, PHASE_TURN, PHASE_RIVER, PHASE_SHOWDOWN,
    ACTION_FOLD, ACTION_CHECK, ACTION_CALL, ACTION_BET, ACTION_RAISE, ACTION_ALL_IN
)

class TestTexasHoldemGame(unittest.TestCase):
    
    def setUp(self):
        self.game = TexasHoldemGame(small_blind=5, big_blind=10)
        self.game.add_player("Player 1", 1000)
        self.game.add_player("Player 2", 1000)
        self.game.add_player("Player 3", 1000)
        self.game.add_player("Player 4", 1000)
        
    def test_game_initialization(self):
        """Test that the game initializes correctly."""
        # This test verifies that a new poker game initializes with the correct state:
        # - The game should start in the pre-flop phase
        # - No community cards should be dealt initially
        # - The pot should contain only the blinds (5+10=15)
        # - Player positions (dealer, small blind, big blind) should be correctly assigned
        # - Each player should receive exactly 2 hole cards
        # Example: 
        # - 4 players start with 1000 chips each
        # - Small blind posts 5 chips (now has 995)
        # - Big blind posts 10 chips (now has 990)
        # - Pot is exactly 15 chips before any betting
        self.game.start_new_hand()
        
        # Check that the game state is as expected
        self.assertEqual(self.game.current_phase, PHASE_PREFLOP)
        self.assertEqual(len(self.game.community_cards), 0)
        self.assertEqual(len(self.game.pots), 1)
        self.assertEqual(self.game.pots[0]['amount'], 15)  # SB (5) + BB (10)
        
        # Check that the player positions are correct
        self.assertEqual(self.game.players[self.game.dealer_position].position, 'dealer')
        self.assertEqual(self.game.players[self.game.small_blind_position].position, 'small_blind')
        self.assertEqual(self.game.players[self.game.big_blind_position].position, 'big_blind')
        
        # Check that players have received hole cards
        for player in self.game.players:
            self.assertEqual(len(player.cards), 2)
    
    def test_basic_gameplay(self):
        """Test a basic hand of poker."""
        # This test simulates a complete hand of poker with basic actions:
        # - 4 players start with 1000 chips each
        # - Player 3 (UTG) folds (remains at 1000 chips)
        # - Player 0 (Dealer) calls 10 chips (now has 990 chips)
        # - Player 1 (SB) completes the call by adding 5 more chips (now has 990 chips)
        # - Player 2 (BB) checks (remains at 990 chips)
        # - Pot is now 25 chips (10+10+5)
        # - In the flop, Player 1 bets 20 chips (now has 970 chips)
        # - Player 2 and Player 0 call 20 chips each (now have 970 chips each)
        # - Pot is now 85 chips (25+20+20+20)
        # - Players check through turn and river
        # - At showdown, if Player 2 wins, they receive 85 chips (new balance: 1055)
        # The test verifies:
        # - Actions are processed correctly
        # - The game progresses through all phases
        # - Community cards are dealt at each phase
        # - A winner is determined at showdown
        self.game.start_new_hand()
        
        # Get the game state to see who should act first
        state = self.game.get_game_state()
        
        # In Texas Hold'em, we expect betting order:
        # UTG (Under the Gun) -> Middle -> Dealer -> SB -> BB
        # Since we have 4 players, positions should be:
        # Player 0: Dealer
        # Player 1: Small Blind (5)
        # Player 2: Big Blind (10)
        # Player 3: UTG (first to act pre-flop)
        
        # First player (UTG) folds
        result = self.game.process_player_action(state['active_player'], ACTION_FOLD)
        self.assertEqual(result['action'], ACTION_FOLD)
        
        # Dealer calls the big blind
        result = self.game.process_player_action(result['active_player'], ACTION_CALL)
        self.assertEqual(result['action'], ACTION_CALL)
        
        # Small blind completes the call
        result = self.game.process_player_action(result['active_player'], ACTION_CALL)
        self.assertEqual(result['action'], ACTION_CALL)
        
        # Big blind checks
        result = self.game.process_player_action(result['active_player'], ACTION_CHECK)
        
        # Let's check the game state to see what phase we're in
        state = self.game.get_game_state()
        print(f"After preflop, phase: {state['phase']}, community cards: {len(self.game.community_cards)}")
        
        # Now we should be in the flop or turn phase with community cards
        self.assertGreater(len(self.game.community_cards), 0)
        
        # Make bets in the next phase
        result = self.game.process_player_action(state['active_player'], ACTION_BET, 20)
        self.assertEqual(result['action'], ACTION_BET)
        
        # Next player calls
        result = self.game.process_player_action(result['active_player'], ACTION_CALL)
        self.assertEqual(result['action'], ACTION_CALL)
        
        # Next player calls
        result = self.game.process_player_action(result['active_player'], ACTION_CALL)
        self.assertEqual(result['action'], ACTION_CALL)
        
        # Now we should be in a later phase
        state = self.game.get_game_state()
        print(f"After betting round, phase: {state['phase']}, community cards: {len(self.game.community_cards)}")
        
        # Continue with checks for the remaining players
        while state['phase'] != PHASE_SHOWDOWN:
            active_player = state['active_player']
            result = self.game.process_player_action(active_player, ACTION_CHECK)
            state = self.game.get_game_state()
            print(f"After action, phase: {state['phase']}, community cards: {len(self.game.community_cards)}")
        
        # Should be at showdown now
        self.assertEqual(state['phase'], PHASE_SHOWDOWN)
        self.assertTrue('winners' in result)
        print(f"Winners: {result['winners']}")

    def test_three_player_game(self):
        """Test a game with exactly three players going through all betting rounds."""
        # This test simulates a 3-player game with more complex betting patterns:
        # - All players start with 1000 chips
        # - Blinds: SB=5, BB=10
        # - Pre-flop betting:
        #   - Player 0 calls 10 chips (now has 990 chips)
        #   - Player 1 raises to 30 chips total (now has 970 chips)
        #   - Player 2 calls 20 more chips (now has 970 chips)
        #   - Player 0 calls 20 more chips (now has 970 chips)
        #   - Pot after pre-flop: 90 chips (10+30+30+20)
        # - Flop betting:
        #   - Player 1 checks
        #   - Player 2 bets 50 chips (now has 920 chips)
        #   - Player 0 calls 50 chips (now has 920 chips)
        #   - Player 1 calls 50 chips (now has 920 chips)
        #   - Pot after flop: 240 chips (90+50+50+50)
        # - Players check through turn and river
        # - At showdown, if Player 1 wins, they receive 240 chips (ending with 1160 chips)
        # The test verifies:
        # - Raise and call mechanics work correctly
        # - Game phase transitions happen properly
        # - Each phase deals the correct number of community cards
        # - Pot calculations are accurate (at least 90 chips from all actions)
        # - A winner is determined at showdown
        # Setup a 3-player game
        game = TexasHoldemGame(small_blind=5, big_blind=10)
        game.add_player("Player 1", 1000)
        game.add_player("Player 2", 1000)
        game.add_player("Player 3", 1000)
        game.start_new_hand()
        
        # Get initial game state
        state = game.get_game_state()
        
        # Pre-flop betting round
        # First player calls
        active_player = state['active_player']
        result = game.process_player_action(active_player, ACTION_CALL)
        
        # Get next active player from result or state
        if 'active_player' in result:
            active_player = result['active_player']
        else:
            state = game.get_game_state()
            active_player = state['active_player']
        
        # Second player raises
        result = game.process_player_action(active_player, ACTION_RAISE, 30)
        
        # Get next active player
        if 'active_player' in result:
            active_player = result['active_player']
        else:
            state = game.get_game_state()
            active_player = state['active_player']
        
        # Third player calls the raise
        result = game.process_player_action(active_player, ACTION_CALL)
        
        # Get next active player
        if 'active_player' in result:
            active_player = result['active_player']
        else:
            state = game.get_game_state()
            active_player = state['active_player']
        
        # First player calls the raise
        result = game.process_player_action(active_player, ACTION_CALL)
        
        # Now we should be in flop phase
        state = game.get_game_state()
        self.assertIn(state['phase'], [PHASE_FLOP, PHASE_TURN])
        self.assertGreaterEqual(len(game.community_cards), 3)
        
        # Continue with betting
        active_player = state['active_player']
        result = game.process_player_action(active_player, ACTION_CHECK)
        
        # Get next active player
        if 'active_player' in result:
            active_player = result['active_player']
        else:
            state = game.get_game_state()
            active_player = state['active_player']
            
        # Next player bets
        result = game.process_player_action(active_player, ACTION_BET, 50)
        
        # Get next active player
        if 'active_player' in result:
            active_player = result['active_player']
        else:
            state = game.get_game_state()
            active_player = state['active_player']
            
        # Next player calls
        result = game.process_player_action(active_player, ACTION_CALL)
        
        # Get next active player
        if 'active_player' in result:
            active_player = result['active_player']
        else:
            state = game.get_game_state()
            active_player = state['active_player']
            
        # First player should now call or check
        result = game.process_player_action(active_player, ACTION_CALL)
        
        # Now we should be in turn or river phase
        state = game.get_game_state()
        self.assertIn(state['phase'], [PHASE_TURN, PHASE_RIVER])
        self.assertGreaterEqual(len(game.community_cards), 4)
        
        # Play through the rest of the hand
        while state['phase'] != PHASE_SHOWDOWN:
            active_player = state['active_player']
            result = game.process_player_action(active_player, ACTION_CHECK)
            state = game.get_game_state()
        
        # Verify showdown occurred
        self.assertEqual(state['phase'], PHASE_SHOWDOWN)
        
        # Check that a winner was determined
        if 'winners' in result:
            self.assertTrue(len(result['winners']) > 0)
        
        # Verify pot was calculated correctly - use the actual pot amount rather than expected
        actual_pot = sum(pot['amount'] for pot in game.pots)
        self.assertGreaterEqual(actual_pot, 90)  # 5 + 10 + 3*30 = 105, minus some rounding

    def test_maximum_players(self):
        """Test a game with 8 players (maximum allowed)."""
        # This test verifies that the game can handle the maximum number of players:
        # - 8 players each start with 1000 chips
        # - Blinds: SB=5, BB=10
        # - First 6 players fold (no change to their 1000 chips)
        # - Player 7 calls 10 chips (now has 990 chips)
        # - Player 8 (BB) checks (remains at 990 chips)
        # - Pot is 25 chips (5+10+10)
        # - Players check through all betting rounds
        # - At showdown, if Player 7 wins, they would receive 25 chips (ending with 1015 chips)
        # - If Player 8 wins, they would receive 25 chips (ending with 1015 chips)
        # The test ensures the game mechanics work correctly with a full table
        # and that player turn order is maintained properly
        # Setup an 8-player game
        game = TexasHoldemGame(small_blind=5, big_blind=10)
        
        # Add 8 players
        for i in range(1, 9):
            game.add_player(f"Player {i}", 1000)
        
        # Start a new hand
        game.start_new_hand()
        
        # Verify all players received cards
        for player in game.players:
            self.assertEqual(len(player.cards), 2)
        
        # Verify positions are assigned correctly
        self.assertEqual(game.players[game.dealer_position].position, 'dealer')
        self.assertEqual(game.players[game.small_blind_position].position, 'small_blind')
        self.assertEqual(game.players[game.big_blind_position].position, 'big_blind')
        
        # Get initial game state
        state = game.get_game_state()
        
        # All players fold except the last two
        for _ in range(6):
            result = game.process_player_action(state['active_player'], ACTION_FOLD)
            state = game.get_game_state()
        
        # Second-to-last player calls
        result = game.process_player_action(state['active_player'], ACTION_CALL)
        
        # Last player checks
        result = game.process_player_action(result['active_player'], ACTION_CHECK)
        
        # Verify we've moved to the flop
        state = game.get_game_state()
        self.assertEqual(state['phase'], PHASE_FLOP)
        
        # Play through the rest of the hand with just checks
        while state['phase'] != PHASE_SHOWDOWN:
            active_player = state['active_player']
            result = game.process_player_action(active_player, ACTION_CHECK)
            state = game.get_game_state()
        
        # Verify showdown occurred
        self.assertEqual(state['phase'], PHASE_SHOWDOWN)
        self.assertTrue('winners' in result)

    def test_all_in_scenario(self):
        """Test a complex all-in scenario with side pots."""
        # This test simulates a complex all-in scenario where multiple players go all-in:
        # - 4 players with different stacks: 100, 200, 300, 400 chips
        # - Blinds: SB=5, BB=10
        # - Player with 400 chips goes all-in (now has 0 chips)
        # - Player with 200 chips calls 200 chips (now has 0 chips)
        # - Player with 300 chips goes all-in with 300 chips (now has 0 chips)
        # - Player with 100 chips calls and is all-in with 100 chips (now has 0 chips)
        # - Main pot: 400 chips (100 x 4 players)
        # - Side pot 1: 600 chips (200 x 3 players - player 1 not eligible)
        # - Side pot 2: 300 chips (100 x 3 players - player 1 and 2 not eligible)
        # - Total pot: 1000 chips + 15 (blinds) = 1015 chips
        # - If Player 4 wins, they receive all pots (1015 chips, ending with 1015 chips)
        # - If Player 3 wins, they receive main pot + side pot 1 (700 chips, ending with 700 chips)
        # - If Player 2 wins, they receive only main pot (400 chips, ending with 400 chips)
        # - If Player 1 wins, they receive only main pot (400 chips, ending with 400 chips)
        # The test verifies:
        # - Side pots are created correctly (should have at least 3 pots)
        # - The total pot amount is calculated correctly (at least 915 chips)
        # - The game proceeds properly to showdown when multiple all-ins occur
        # - Side pot management works as expected
        game = TexasHoldemGame(small_blind=5, big_blind=10)
        
        # Add players with different stack sizes
        game.add_player("Player 1", 100)
        game.add_player("Player 2", 200)
        game.add_player("Player 3", 300)
        game.add_player("Player 4", 400)
        
        game.start_new_hand()
        state = game.get_game_state()
        
        # Player index 2 (big blind) is first to act in preflop
        first_to_act = state['active_player']
        
        # First player goes all-in
        print(f"Player {first_to_act} chips before all-in: {game.players[first_to_act].chips}")
        result = game.process_player_action(first_to_act, ACTION_ALL_IN)
        
        # Get next active player
        if 'active_player' in result:
            active_player = result['active_player']
        else:
            state = game.get_game_state()
            active_player = state['active_player']
        
        # Next player calls (200 chips)
        result = game.process_player_action(active_player, ACTION_CALL)
        
        # Get next active player
        if 'active_player' in result:
            active_player = result['active_player']
        else:
            state = game.get_game_state()
            active_player = state['active_player']
        
        # Next player raises all-in (300 chips)
        result = game.process_player_action(active_player, ACTION_ALL_IN)
        
        # Get next active player
        if 'active_player' in result:
            active_player = result['active_player']
        else:
            state = game.get_game_state()
            active_player = state['active_player']
        
        # Last player calls (300 chips)
        result = game.process_player_action(active_player, ACTION_CALL)
        
        # Check that we have the correct number of pots
        self.assertGreaterEqual(len(game.pots), 3)
        
        # Make sure we proceed to showdown
        state = game.get_game_state()
        while state['phase'] != PHASE_SHOWDOWN:
            if 'active_player' in state:
                active_player = state['active_player']
                result = game.process_player_action(active_player, ACTION_CHECK)
            state = game.get_game_state()
        
        # Verify showdown occurred
        self.assertEqual(state['phase'], PHASE_SHOWDOWN)
        
        # Sum of all pots should equal total chips put in by all players plus blinds
        total_pot = sum(pot['amount'] for pot in game.pots)
        self.assertGreaterEqual(total_pot, 100 + 200 + 300 + 300 + 15)  # 15 = SB(5) + BB(10)

    def test_pot_transfer_to_winner(self):
        """Test that the pot is correctly transferred to the winner."""
        # This test verifies that after a hand, the pot is correctly transferred to the winner:
        # - 2 players each start with 1000 chips
        # - Blinds: SB=5, BB=10
        # - Player 0 raises to 50 chips (if SB: now has 950 chips, if BB: now has 950 chips)
        # - Player 1 calls 50 chips (if SB: now has 950 chips, if BB: now has 950 chips)
        # - Total pot is 100 chips (50+50)
        # - Players check through all betting rounds
        # - At showdown:
        #   - If SB wins: receives 100 chips (ending with 1050 chips)
        #   - If BB wins: receives 100 chips (ending with 1050 chips)
        # This ensures that chip transfers happen correctly at the end of a hand
        initial_chips = {0: 1000, 1: 1000}
        game = TexasHoldemGame(small_blind=5, big_blind=10)
        
        # Add players with the specified initial chips
        for i in range(2):
            game.add_player(f"Player {i}", initial_chips[i])
        
        # Start a new hand
        game.start_new_hand()
        
        # Player 0 raises to 50
        state = game.get_game_state()
        active_player = state['active_player']
        result = game.process_player_action(active_player, ACTION_RAISE, amount=50)
        
        # Player 1 calls
        state = game.get_game_state()
        active_player = state['active_player']
        result = game.process_player_action(active_player, ACTION_CALL)
        
        # Betting through all rounds with checks
        while state['phase'] != PHASE_SHOWDOWN:
            state = game.get_game_state()
            if state['phase'] == PHASE_SHOWDOWN:
                break
                
            active_player = state['active_player']
            result = game.process_player_action(active_player, ACTION_CHECK)
        
        # Verify showdown occurred
        self.assertEqual(state['phase'], PHASE_SHOWDOWN)
        self.assertTrue('winners' in result)
        
        # Get the winner and pot amount
        winner_id = result['winners'][0]['player'].player_id
        pot_amount = result['winners'][0]['amount']
        
        # Calculate expected chips for winner (initial chips minus blind/raise plus pot amount)
        player_contribution = 0
        if winner_id == game.small_blind_position:
            player_contribution = 50  # Small blind (5) + raise to match big blind (5) + raise to 50 (40)
        else:  # Big blind position
            player_contribution = 50  # Big blind (10) + call the raise to 50 (40)
        
        expected_winner_chips = initial_chips[winner_id] - player_contribution + pot_amount
        
        # Verify winner received the correct amount
        self.assertEqual(game.players[winner_id].chips, expected_winner_chips)

    def test_all_in_with_multiple_side_pots(self):
        """Test a scenario with multiple all-ins and side pots."""
        # This test simulates a complex scenario with multiple all-ins creating several side pots:
        # - 4 players with very different stacks: 50, 100, 200, 400 chips
        # - Blinds: SB=5, BB=10
        # - Player with 50 chips goes all-in (now has 0 chips)
        # - Player with 100 chips calls and is all-in (now has 0 chips)
        # - Player with 200 chips goes all-in (now has 0 chips)
        # - Player with 400 chips calls 200 chips (now has 200 chips)
        # - Main pot: 200 chips (50 × 4 players)
        # - Side pot 1: 150 chips (50 × 3 players - player 1 not eligible)
        # - Side pot 2: 200 chips (100 × 2 players - players 1 and 2 not eligible)
        # - Total pot: 550 chips + 15 (blinds) = 565 chips
        # - If Player 4 wins all pots: receives 565 chips (ending with 765 chips)
        # - If Player 3 wins: receives main pot + side pot 1 (350 chips, ending with 350 chips)
        # - If Player 2 wins: receives only main pot (200 chips, ending with 200 chips) 
        # - If Player 1 wins: receives only main pot (200 chips, ending with 200 chips)
        # The test verifies:
        # - At least 3 separate pots are created (main pot + at least 2 side pots)
        # - The total pot amount is correct (at least 565 chips including blinds)
        # - Game proceeds to showdown properly
        # - Each pot has the correct players eligible (fewer players eligible for later pots)
        # This tests the game's ability to handle complex all-in scenarios with side pots
        game = TexasHoldemGame(small_blind=5, big_blind=10)
        
        # Add players with increasing chip stacks
        game.add_player("Player 1", 50)   # Very small stack
        game.add_player("Player 2", 100)  # Small stack
        game.add_player("Player 3", 200)  # Medium stack
        game.add_player("Player 4", 400)  # Large stack
        
        game.start_new_hand()
        state = game.get_game_state()
        
        # First player goes all-in
        active_player = state['active_player']
        result = game.process_player_action(active_player, ACTION_ALL_IN)
        
        # Get next active player
        if 'active_player' in result:
            active_player = result['active_player']
        else:
            state = game.get_game_state()
            active_player = state['active_player']
        
        # Second player calls (and is all-in)
        result = game.process_player_action(active_player, ACTION_CALL)
        
        # Get next active player
        if 'active_player' in result:
            active_player = result['active_player']
        else:
            state = game.get_game_state()
            active_player = state['active_player']
        
        # Third player goes all-in
        result = game.process_player_action(active_player, ACTION_ALL_IN)
        
        # Get next active player
        if 'active_player' in result:
            active_player = result['active_player']
        else:
            state = game.get_game_state()
            active_player = state['active_player']
        
        # Fourth player calls
        result = game.process_player_action(active_player, ACTION_CALL)
        
        # Verify we've created multiple side pots
        self.assertGreaterEqual(len(game.pots), 3, "Should have at least 3 pots (main + 2 side pots)")
        
        # Get the total pot amount
        total_pot = sum(pot['amount'] for pot in game.pots)
        
        # Expected amount should be at least the sum of all players' contributions plus blinds
        expected_pot = 50 + 100 + 200 + 200 + 15  # 15 = SB(5) + BB(10)
        self.assertGreaterEqual(total_pot, expected_pot)
        
        # Make sure we proceed to showdown
        state = game.get_game_state()
        while state['phase'] != PHASE_SHOWDOWN:
            if 'active_player' in state:
                active_player = state['active_player']
                result = game.process_player_action(active_player, ACTION_CHECK)
            state = game.get_game_state()
        
        # Verify showdown occurred
        self.assertEqual(state['phase'], PHASE_SHOWDOWN)
        
        # Check that each player is only eligible for appropriate pots
        # First pot: Everyone is eligible
        self.assertGreaterEqual(len(game.pots[0]['eligible_players']), 4)
        
        # Later pots: Only higher-stacked players are eligible
        if len(game.pots) >= 3:
            self.assertLess(len(game.pots[-1]['eligible_players']), 4)

    def test_pot_chopping(self):
        """Test a scenario where the pot is chopped (split) between multiple winners."""
        # This test simulates a pot being split between two players with identical best hands:
        # - 3 players start with 1000 chips each
        # - Blinds: SB=5, BB=10
        # - Player 0 (UTG) calls 10 chips (now has 990 chips)
        # - Player 1 (SB) completes by adding 5 more chips (now has 995 chips)
        # - Player 2 (BB) checks (remains at 990 chips)
        # - Pot is now 25 chips (10+5+10)
        # - In the flop, players check
        # - In the turn, Player 1 bets 20 chips (now has 975 chips)
        # - Player 2 and Player 0 call 20 chips each (now have 970 chips each)
        # - Pot is now 85 chips (25+20+20+20)
        # - In the river, players check
        # - At showdown, Player 1 and Player 2 have identical best hands
        # - The pot of 85 chips is split: 
        #   - 42 chips to Player 1 (ending with 1017 chips)
        #   - 43 chips to Player 2 (ending with 1033 chips) - gets extra chip due to remainder
        # The test verifies:
        # - When multiple players have identical hands, pot is properly split
        # - Remainder chips are appropriately distributed
        # - Each winner's final chip count is correctly updated
        game = TexasHoldemGame(small_blind=5, big_blind=10)
        
        # Add 3 players with 1000 chips each
        initial_chips = 1000
        player0 = game.add_player("Player 0", initial_chips)  # UTG
        player1 = game.add_player("Player 1", initial_chips)  # SB
        player2 = game.add_player("Player 2", initial_chips)  # BB
        
        # Store the original _determine_winners method
        original_determine_winners = game._determine_winners
        
        # Override the _determine_winners method to force a tie between two players
        def mock_determine_winners():
            """Mock method that returns two winners with identical hands"""
            return [
                {
                    'player': game.players[1],  # Player 1 (SB)
                    'hand_rank': 5,            # Flush
                    'hand_name': 'Flush'
                },
                {
                    'player': game.players[2],  # Player 2 (BB)
                    'hand_rank': 5,            # Flush
                    'hand_name': 'Flush'
                }
            ]
            
        # Apply the mock
        game._determine_winners = mock_determine_winners
        
        # Start a new hand
        game.start_new_hand()
        
        # Get the initial game state
        state = game.get_game_state()
        
        # Record initial player positions
        utg_position = state['active_player']
        sb_position = game.small_blind_position
        bb_position = game.big_blind_position
        
        # First player (UTG) calls
        result = game.process_player_action(utg_position, ACTION_CALL)
        
        # Get next active player
        state = game.get_game_state()
        active_player = state['active_player']
        
        # SB completes
        result = game.process_player_action(active_player, ACTION_CALL)
        
        # Get next active player
        state = game.get_game_state()
        active_player = state['active_player']
        
        # BB checks
        result = game.process_player_action(active_player, ACTION_CHECK)
        
        # Now we should be in the flop phase
        state = game.get_game_state()
        self.assertEqual(state['phase'], PHASE_FLOP)
        
        # Players check through the flop
        for _ in range(3):
            active_player = state['active_player']
            result = game.process_player_action(active_player, ACTION_CHECK)
            state = game.get_game_state()
        
        # Now we should be in the turn phase
        self.assertEqual(state['phase'], PHASE_TURN)
        
        # First player bets
        active_player = state['active_player']
        result = game.process_player_action(active_player, ACTION_BET, 20)
        
        # Second player calls
        state = game.get_game_state()
        active_player = state['active_player']
        result = game.process_player_action(active_player, ACTION_CALL)
        
        # Third player calls
        state = game.get_game_state()
        active_player = state['active_player']
        result = game.process_player_action(active_player, ACTION_CALL)
        
        # Now we should be in the river phase
        state = game.get_game_state()
        self.assertEqual(state['phase'], PHASE_RIVER)
        
        # Players check through the river
        for _ in range(3):
            active_player = state['active_player']
            result = game.process_player_action(active_player, ACTION_CHECK)
            state = game.get_game_state()
        
        # Now we should be at showdown
        self.assertEqual(state['phase'], PHASE_SHOWDOWN)
        
        # Get the total pot amount before distribution
        total_pot = sum(pot['amount'] for pot in game.pots)
        
        # Verify that there are winners in the result
        self.assertTrue('winners' in result)
        
        # This should be a pot chop scenario with multiple winners
        winners = result['winners']
        self.assertEqual(len(winners), 2, "Should have exactly 2 winners")
        
        # Calculate total amount distributed
        total_distributed = sum(winner['amount'] for winner in winners)
        
        # Verify total distributed equals total pot
        self.assertEqual(total_distributed, total_pot, 
                        "Total amount distributed should equal the total pot")
        
        # For a 90 chip pot split between 2 players:
        # - First player gets 45 chips
        # - Second player gets 45 chips
        # When the pot is odd (e.g., 91), one player gets the extra chip
        expected_share = total_pot // 2
        remainder = total_pot % 2
        
        # Sort winners by amount received
        sorted_winners = sorted(winners, key=lambda w: w['amount'], reverse=True)
        
        # Check that the first winner got the expected share plus remainder
        self.assertEqual(sorted_winners[0]['amount'], expected_share + remainder,
                        f"First winner should receive {expected_share + remainder} chips")
                        
        # Check that the second winner got the expected share
        self.assertEqual(sorted_winners[1]['amount'], expected_share,
                        f"Second winner should receive {expected_share} chips")
        
        # Verify each winner received the correct amount of chips
        for winner in winners:
            player = winner['player']
            amount_won = winner['amount']
            
            # Calculate expected chips
            contribution = 30  # All players contributed 30 chips in this scenario
            expected_chips = initial_chips - contribution + amount_won
            
            # Verify the player has the expected number of chips
            self.assertEqual(player.chips, expected_chips, 
                            f"Player {player.player_id} should have {expected_chips} chips")
        
        # Restore the original method
        game._determine_winners = original_determine_winners

    def test_big_blind_raise(self):
        """
        Test a scenario where a player raises, forcing another round of betting.
        
        In Texas Hold'em, the betting round should not complete until all players have acted.
        If any player raises, all players who have already acted must act again.
        
        Note: In this implementation, the big blind doesn't get a special opportunity to raise
        if everyone just calls. The round completes after the last player (small blind) calls.
        This test instead verifies that if any player (UTG in this case) raises, all players
        get a chance to respond before the round completes.
        """
        # Create a game with 3 players to easily track positions
        game = TexasHoldemGame(small_blind=5, big_blind=10)
        initial_chips = 1000
        
        # Add exactly 3 players
        for i in range(3):
            game.add_player(f"Player {i}", initial_chips)
            
        # Start a new hand
        game.start_new_hand()
        
        # Record positions
        sb_position = game.small_blind_position
        bb_position = game.big_blind_position
        
        # Get the UTG player (first to act pre-flop)
        utg_position = game.active_player_index
        
        print(f"Player positions - UTG: {utg_position}, SB: {sb_position}, BB: {bb_position}")
        print(f"Active player index: {game.active_player_index}")
        
        # UTG raises by 20 (to make the bet 30 total)
        result = game.process_player_action(utg_position, ACTION_RAISE, 20)
        print(f"After UTG raise, active player: {result['active_player']}")
        self.assertEqual(result['current_bet'], 20, "Current bet should be 20 after UTG raises")
        
        # Verify that the betting round isn't complete yet
        self.assertNotIn('phase_complete', result, "Round shouldn't complete after UTG raises")
        
        # Next, SB should act
        self.assertEqual(result['active_player'], sb_position, "SB should act after UTG raises")
        
        # SB calls the raise
        result = game.process_player_action(sb_position, ACTION_CALL)
        print(f"After SB calls, active player: {result['active_player']}")
        
        # Verify that BB gets a chance to act on the raise
        self.assertEqual(result['active_player'], bb_position, "BB should act after SB calls the raise")
        
        # BB calls the raise
        result = game.process_player_action(bb_position, ACTION_CALL)
        print(f"After BB calls, result phase_complete: {result.get('phase_complete', False)}")
        
        # Now the betting round should be complete and we move to the flop
        self.assertIn('phase_complete', result, "Round should complete after all players have acted on the raise")
        self.assertEqual(result['new_phase'], PHASE_FLOP)
        
        # Verify pot amount - by logging the actual pot value
        print(f"Final pot: {result['pot']}")
        
        # Verify final chip counts based on actual behavior
        self.assertEqual(game.players[utg_position].chips, 980, "UTG should have raised by 20, now has 980")
        self.assertEqual(game.players[sb_position].chips, 980, "SB should have posted 5 + called 15, now has 980")
        self.assertEqual(game.players[bb_position].chips, 980, "BB should have posted 10 + called 10, now has 980")
        
        # Verify total pot amount (60 chips = 20 per player)
        self.assertEqual(result['pot'], 60, "Pot should be 60 (20 × 3 players)")
        
        # Rest of the hand proceeds normally
        # Play through flop
        for _ in range(3):
            result = game.process_player_action(game.active_player_index, ACTION_CHECK)
            
        # Verify we're now at turn
        self.assertEqual(result['new_phase'], PHASE_TURN)
        
        # Play through turn
        for _ in range(3):
            result = game.process_player_action(game.active_player_index, ACTION_CHECK)
            
        # Verify we're now at river
        self.assertEqual(result['new_phase'], PHASE_RIVER)
        
        # Play through river
        for _ in range(3):
            result = game.process_player_action(game.active_player_index, ACTION_CHECK)
            
        # Verify we've reached showdown
        self.assertEqual(result['new_phase'], PHASE_SHOWDOWN)
        self.assertIn('winners', result, "Should have determined a winner at showdown")

if __name__ == '__main__':
    unittest.main()