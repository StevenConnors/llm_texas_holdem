from constants import (
    PHASE_PREFLOP, PHASE_FLOP, PHASE_TURN, PHASE_RIVER, PHASE_SHOWDOWN,
    ACTION_FOLD, ACTION_CHECK, ACTION_CALL, ACTION_BET, ACTION_RAISE, ACTION_ALL_IN,
    HAND_RANKINGS
)
from card import Deck, Card
from player import Player
from hand_evaluator import HandEvaluator

class TexasHoldemGame:
    """Main class for managing a Texas Hold'em poker game."""
    
    def __init__(self, small_blind=1, big_blind=2, max_players=9):
        """
        Initialize a Texas Hold'em game.
        
        Args:
            small_blind (int, optional): Small blind amount. Defaults to 1.
            big_blind (int, optional): Big blind amount. Defaults to 2.
            max_players (int, optional): Maximum number of players. Defaults to 9.
        """
        self.players = []
        self.deck = Deck()
        self.community_cards = []
        self.pots = [{'amount': 0, 'eligible_players': []}]  # Main pot
        self.current_phase = None
        self.active_player_index = None
        self.dealer_position = None
        self.small_blind_position = None
        self.big_blind_position = None
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.current_bet = 0
        self.hand_evaluator = HandEvaluator()
        self.max_players = max_players
        
    def add_player(self, name, chips):
        """
        Add a player to the game.
        
        Args:
            name (str): Player's name
            chips (int): Starting chip count
            
        Returns:
            int: The player's ID
        """
        if len(self.players) >= self.max_players:
            raise ValueError(f"Cannot add more than {self.max_players} players")
            
        player_id = len(self.players)
        player = Player(name=name, chips=int(chips), player_id=player_id)
        self.players.append(player)
        
        return player_id
    
    def remove_player(self, player_id):
        """
        Remove a player from the game.
        
        Args:
            player_id (int): ID of the player to remove
            
        Returns:
            bool: True if player was removed, False if not found
        """
        for i, player in enumerate(self.players):
            if player.player_id == player_id:
                self.players.pop(i)
                return True
        return False
    
    def start_new_hand(self):
        """
        Start a new hand of poker.
        
        Returns:
            bool: True if the hand was started successfully, False otherwise
        """
        # Check if we have enough players
        active_players = [p for p in self.players if p.chips > 0]
        if len(active_players) < 2:
            return False
            
        # Reset game state
        self.deck.reset()
        self.deck.shuffle()
        self.community_cards = []
        self.pots = [{'amount': 0, 'eligible_players': active_players.copy()}]
        self.current_phase = PHASE_PREFLOP
        self.current_bet = 0
        
        # Reset player states
        for player in self.players:
            player.reset_for_new_hand()
            
        # Rotate dealer position
        if self.dealer_position is None:
            self.dealer_position = 0
        else:
            self.dealer_position = (self.dealer_position + 1) % len(self.players)
            # Skip players who are not active
            while self.players[self.dealer_position].chips <= 0:
                self.dealer_position = (self.dealer_position + 1) % len(self.players)
            
        # Assign positions and post blinds
        self._assign_positions()
        self._post_blinds()
        
        # Deal hole cards
        self._deal_hole_cards()
        
        # Set the active player (first to act pre-flop)
        if len(active_players) == 2:  # Heads-up
            self.active_player_index = self.dealer_position  # Small blind acts first
        else:
            # Under the gun (first player after big blind)
            self.active_player_index = (self.big_blind_position + 1) % len(self.players)
            while not self.players[self.active_player_index].is_active:
                self.active_player_index = (self.active_player_index + 1) % len(self.players)
                
        return True
    
    def _assign_positions(self):
        """Assign dealer, small blind, and big blind positions."""
        active_indices = [i for i, p in enumerate(self.players) if p.chips > 0]
        
        # Find the dealer position among active players
        dealer_index = self.dealer_position
        while dealer_index not in active_indices:
            dealer_index = (dealer_index + 1) % len(self.players)
        
        self.dealer_position = dealer_index
        self.players[dealer_index].position = 'dealer'
        
        # Assign small blind
        small_blind_index = (dealer_index + 1) % len(self.players)
        while small_blind_index not in active_indices:
            small_blind_index = (small_blind_index + 1) % len(self.players)
        
        self.small_blind_position = small_blind_index
        self.players[small_blind_index].position = 'small_blind'
        
        # Assign big blind
        big_blind_index = (small_blind_index + 1) % len(self.players)
        while big_blind_index not in active_indices:
            big_blind_index = (big_blind_index + 1) % len(self.players)
            
        self.big_blind_position = big_blind_index
        self.players[big_blind_index].position = 'big_blind'
    
    def _post_blinds(self):
        """Collect small and big blinds from the designated players."""
        # Small blind
        sb_player = self.players[self.small_blind_position]
        _, amount = sb_player.bet(self.small_blind)
        self.pots[0]['amount'] += amount
        
        # Big blind
        bb_player = self.players[self.big_blind_position]
        _, amount = bb_player.bet(self.big_blind)
        self.pots[0]['amount'] += amount
        
        self.current_bet = self.big_blind
    
    def _deal_hole_cards(self):
        """Deal two hole cards to each active player."""
        for player in self.players:
            if player.is_active:
                # Deal two cards to each player
                player.cards.append(self.deck.deal_card())
                player.cards.append(self.deck.deal_card())
    
    def _deal_community_cards(self, count):
        """
        Deal a specific number of community cards.
        
        Args:
            count (int): Number of cards to deal
        """
        for _ in range(count):
            self.community_cards.append(self.deck.deal_card())
    
    def process_player_action(self, player_id, action, amount=0):
        """
        Process a player's action during the betting round.
        
        Args:
            player_id: The ID of the player making the action.
            action: The action being performed (bet, call, fold, etc.)
            amount: The amount to bet or raise (if applicable).
            
        Returns:
            A dictionary with the result of the action.
        """
        print(f"Processing action: {action} for player {player_id} with amount {amount}")
        
        if player_id != self.active_player_index:
            raise ValueError(f"It's not player {player_id}'s turn. Active player is {self.active_player_index}")
        
        player = self.players[self.active_player_index]
        result = {'action': action, 'active_player': self.active_player_index}
        
        # Process the action
        if action == ACTION_FOLD:
            player.fold()
            result['folded'] = True
        elif action == ACTION_CHECK:
            if self.current_bet > player.current_bet:
                raise ValueError("Cannot check when there's a bet to call")
            player.check()
        elif action == ACTION_CALL:
            # Calculate how much to call
            call_amount = self.current_bet - player.current_bet
            print(f"Player {player_id} calling amount: {call_amount}")
            
            if call_amount <= 0:
                # Nothing to call, treat as check
                player.check()
            else:
                action_result = player.call(call_amount)
                # Add to pot - handle tuple result
                if isinstance(action_result, tuple):
                    actual_amount = action_result[1]
                else:
                    actual_amount = call_amount
                self._add_to_pot(actual_amount)
        elif action == ACTION_BET:
            if self.current_bet > 0:
                raise ValueError("Cannot bet when there's already a bet. Use raise instead.")
            if amount < self.big_blind:
                raise ValueError(f"Bet must be at least the big blind ({self.big_blind})")
            
            action_result = player.bet(amount)
            # Handle tuple result
            if isinstance(action_result, tuple):
                actual_amount = action_result[1]
            else:
                actual_amount = amount
            self.current_bet = player.current_bet
            # Add to pot
            self._add_to_pot(actual_amount)
        elif action == ACTION_RAISE:
            if self.current_bet == 0:
                raise ValueError("Cannot raise when there's no bet. Use bet instead.")
            if amount <= self.current_bet:
                raise ValueError(f"Raise must be greater than current bet ({self.current_bet})")
            
            # Calculate actual amount player adds to their bet
            raise_amount = amount - player.current_bet
            action_result = player.raise_bet(raise_amount)
            # Handle tuple result
            if isinstance(action_result, tuple):
                actual_amount = action_result[1]
            else:
                actual_amount = raise_amount
            self.current_bet = player.current_bet
            # Add to pot
            self._add_to_pot(actual_amount)
        elif action == ACTION_ALL_IN:
            action_result = player.all_in()
            # Handle tuple result
            if isinstance(action_result, tuple):
                actual_amount = action_result[1]
            else:
                actual_amount = player.chips
            
            # If this all in is higher than current bet, update current bet
            if player.current_bet > self.current_bet:
                self.current_bet = player.current_bet
            
            # Add to pot
            self._add_to_pot(actual_amount)
        else:
            raise ValueError(f"Invalid action: {action}")
        
        # Add round info to result
        result['current_bet'] = self.current_bet
        result['pot'] = sum(pot['amount'] for pot in self.pots)
        
        # Check if round is complete
        round_complete = self._is_betting_round_complete()
        print(f"After {action}, round complete: {round_complete}")
        
        if round_complete:
            result['phase_complete'] = True
            # Move to next phase
            self._advance_game_phase()
            
            # Reset for next betting round
            self._reset_betting_round()
            
            # Update the result with new phase info
            result['new_phase'] = self.current_phase
            
            if self.current_phase == PHASE_FLOP:
                self._deal_community_cards(3)
                result['community_cards'] = self.community_cards
            elif self.current_phase == PHASE_TURN:
                self._deal_community_cards(1)
                result['community_cards'] = self.community_cards
            elif self.current_phase == PHASE_RIVER:
                self._deal_community_cards(1)
                result['community_cards'] = self.community_cards
            elif self.current_phase == PHASE_SHOWDOWN:
                # Determine winner and distribute pot
                winners = self._determine_winners()
                result['winners'] = winners
                
                # Distribute pot
                self._distribute_pot(winners)
                result['showdown'] = True
        else:
            # Find next active player
            self._move_to_next_active_player()
            result['active_player'] = self.active_player_index
        
        # Print final result dictionary to debug
        print(f"Result dictionary: {result}")
        return result
    
    def _get_next_active_player(self, current_index):
        """Find the next active player after the current one."""
        index = (current_index + 1) % len(self.players)
        
        # Keep moving until we find an active player who isn't all-in
        while (not self.players[index].is_active or self.players[index].is_all_in) and index != current_index:
            index = (index + 1) % len(self.players)
            
        # If we've gone all the way around and found no one, return None
        if index == current_index and (not self.players[index].is_active or self.players[index].is_all_in):
            # Everyone is folded or all-in, so advance to the next phase
            return None
            
        return index
    
    def _is_betting_round_complete(self):
        """
        Check if the current betting round is complete.
        
        Returns:
            bool: True if the betting round is complete, False otherwise.
        """
        # If fewer than 2 active players, round is complete
        active_players = [p for p in self.players if p.is_active]
        if len(active_players) < 2:
            print("Less than 2 active players, betting round complete")
            return True
        
        # If all active players have acted and either:
        #   1. Matched the current bet, or
        #   2. Gone all-in with less than the current bet, or
        #   3. Folded
        
        for player in self.players:
            if player.is_active and not player.is_all_in:
                # If player hasn't acted yet or hasn't matched the current bet
                if not player.has_acted or player.current_bet < self.current_bet:
                    print(f"Player {player.player_id} has not completed betting: acted = {player.has_acted}, current_bet = {player.current_bet}, game current_bet = {self.current_bet}")
                    return False
        
        print("All active players have completed betting, round complete")
        return True
    
    def _advance_game_phase(self):
        """Advance to the next phase of the game."""
        if self.current_phase == PHASE_PREFLOP:
            self.current_phase = PHASE_FLOP
            self._deal_community_cards(3)
        elif self.current_phase == PHASE_FLOP:
            self.current_phase = PHASE_TURN
            self._deal_community_cards(1)
        elif self.current_phase == PHASE_TURN:
            self.current_phase = PHASE_RIVER
            self._deal_community_cards(1)
        elif self.current_phase == PHASE_RIVER:
            self.current_phase = PHASE_SHOWDOWN
    
    def _start_new_betting_round(self):
        """Start a new betting round after advancing to a new phase."""
        # Reset player bet amounts for the new round
        for player in self.players:
            player.reset_for_new_round()
            
        # Reset the current bet
        self.current_bet = 0
        
        # Set the first active player
        # In post-flop rounds, start with the first active player after the dealer
        self.active_player_index = (self.dealer_position + 1) % len(self.players)
        
        # Find the first active player who isn't all-in
        active_not_all_in = [i for i, p in enumerate(self.players) 
                            if p.is_active and not p.is_all_in]
        
        if not active_not_all_in:
            # Everyone is all-in or folded, go to showdown
            self._advance_to_showdown()
            return
            
        # Find the first active player after the dealer
        while (not self.players[self.active_player_index].is_active or 
               self.players[self.active_player_index].is_all_in):
            self.active_player_index = (self.active_player_index + 1) % len(self.players)
    
    def _advance_to_showdown(self):
        """Advance directly to showdown (when all players are all-in or all but one have folded)."""
        # Deal any remaining community cards
        cards_needed = 5 - len(self.community_cards)
        if cards_needed > 0:
            self._deal_community_cards(cards_needed)
            
        self.current_phase = PHASE_SHOWDOWN
    
    def _determine_winners(self):
        """
        Determine the winner(s) of the hand.
        
        Returns:
            list: List of winner dictionaries with player, hand_rank, and hand_name
        """
        active_players = [p for p in self.players if p.is_active]
        
        # If only one active player, they win by default
        if len(active_players) == 1:
            return [{
                'player': active_players[0],
                'hand_rank': 0,  # No hand evaluation needed
                'hand_name': 'Default Win'
            }]
            
        # Evaluate each player's hand
        player_hands = []
        for player in active_players:
            # Combine hole cards and community cards
            all_cards = player.cards + self.community_cards
            
            # Get the best 5-card hand
            hand_rank, hand_name = self.hand_evaluator.evaluate_hand(all_cards)
            
            player_hands.append({
                'player': player,
                'hand_rank': hand_rank,
                'hand_name': hand_name
            })
            
        # Sort by hand rank (higher is better)
        player_hands.sort(key=lambda x: x['hand_rank'], reverse=True)
        
        # Find winners (players with the highest ranked hand)
        best_rank = player_hands[0]['hand_rank']
        winners = [h for h in player_hands if h['hand_rank'] == best_rank]
        
        return winners
    
    def _distribute_pot(self, winners):
        """
        Distribute the pot to the winner(s).
        
        Args:
            winners (list): List of winner dictionaries from _determine_winners
        """
        if not winners:
            return
            
        # If there's only one winner, they get the entire pot
        if len(winners) == 1:
            total_pot = sum(pot['amount'] for pot in self.pots)
            winners[0]['player'].add_chips(total_pot)
            winners[0]['amount'] = total_pot
            return
            
        # For multiple winners, distribute the pot based on eligibility
        for pot in self.pots:
            # Find the winners eligible for this pot
            eligible_winners = [w for w in winners if w['player'] in pot['eligible_players']]
            
            # If no eligible winners, skip this pot
            if not eligible_winners:
                continue
                
            # Split the pot equally among eligible winners
            share = pot['amount'] // len(eligible_winners)
            remainder = pot['amount'] % len(eligible_winners)
            
            # Distribute the shares
            for winner in eligible_winners:
                # Add extra chip to early winners if there's a remainder
                extra = 1 if remainder > 0 else 0
                amount = share + extra
                remainder -= extra
                
                winner['player'].add_chips(amount)
                
                # Add the amount to the winner's total if 'amount' key exists, otherwise create it
                if 'amount' in winner:
                    winner['amount'] += amount
                else:
                    winner['amount'] = amount
    
    def create_side_pots(self):
        """
        Create side pots when one or more players are all-in.
        This should be called after a player goes all-in.
        """
        all_in_players = sorted(
            [p for p in self.players if p.is_active and p.is_all_in],
            key=lambda p: p.total_bet
        )
        
        if not all_in_players:
            return
            
        # Create a list of all active players
        active_players = [p for p in self.players if p.is_active]
        
        # Calculate the total pot amount before recreating pots
        total_pot_amount = sum(pot['amount'] for pot in self.pots)
        
        # Clear existing pots
        self.pots = []
        
        # Create new pots
        previous_bet = 0
        for all_in_player in all_in_players:
            all_in_amount = all_in_player.total_bet
            
            # Skip if this player's all-in amount is the same as the previous one
            if all_in_amount == previous_bet:
                continue
                
            # Create a pot for bets up to this all-in amount
            pot_contribution = 0
            pot_contributors = []
            
            for player in active_players:
                contribution = min(all_in_amount, player.total_bet) - previous_bet
                if contribution > 0:
                    pot_contribution += contribution
                    pot_contributors.append(player)
            
            if pot_contribution > 0:
                self.pots.append({
                    'amount': pot_contribution,
                    'eligible_players': pot_contributors
                })
                
            previous_bet = all_in_amount
            
        # Create a main pot for remaining bets
        main_pot_contribution = 0
        main_pot_contributors = []
        
        for player in active_players:
            contribution = player.total_bet - previous_bet
            if contribution > 0:
                main_pot_contribution += contribution
                main_pot_contributors.append(player)
                
        if main_pot_contribution > 0:
            self.pots.append({
                'amount': main_pot_contribution,
                'eligible_players': main_pot_contributors
            })
            
        # Verify that the sum of all pots equals the original pot amount
        new_total = sum(pot['amount'] for pot in self.pots)
        if new_total != total_pot_amount:
            # Adjust the last pot if there's a discrepancy (due to rounding or other issues)
            if self.pots:
                self.pots[-1]['amount'] += (total_pot_amount - new_total)
    
    def get_valid_actions(self, player_id):
        """
        Get the valid actions for a player.
        
        Args:
            player_id (int): ID of the player
            
        Returns:
            dict: Dictionary of valid actions and their parameters
        """
        if self.active_player_index is None or self.players[self.active_player_index].player_id != player_id:
            return {'error': 'Not your turn'}
            
        player = self.players[self.active_player_index]
        
        valid_actions = {}
        
        # Folding is always an option
        valid_actions[ACTION_FOLD] = {}
        
        # Check if player can check
        if self.current_bet <= player.current_bet:
            valid_actions[ACTION_CHECK] = {}
        
        # Call
        amount_to_call = self.current_bet - player.current_bet
        if amount_to_call > 0:
            valid_actions[ACTION_CALL] = {'amount': amount_to_call}
        
        # Bet or raise
        if player.chips > 0:
            if self.current_bet == 0:
                valid_actions[ACTION_BET] = {
                    'min': self.big_blind,
                    'max': player.chips
                }
            else:
                min_raise = self.current_bet * 2 - player.current_bet
                if min_raise <= player.chips:
                    valid_actions[ACTION_RAISE] = {
                        'min': min_raise,
                        'max': player.chips + player.current_bet
                    }
                
        return valid_actions
    
    def get_game_state(self):
        """
        Get the current state of the game.
        
        Returns:
            dict: Current game state
        """
        active_player = None
        if self.active_player_index is not None:
            active_player = self.players[self.active_player_index].player_id
            
        return {
            'phase': self.current_phase,
            'community_cards': [str(card) for card in self.community_cards],
            'pots': [{'amount': pot['amount'], 
                      'eligible_players': [p.player_id for p in pot['eligible_players']]} 
                     for pot in self.pots],
            'current_bet': self.current_bet,
            'active_player': active_player,
            'dealer': self.dealer_position,
            'small_blind': self.small_blind_position,
            'big_blind': self.big_blind_position,
            'players': [{
                'id': player.player_id,
                'name': player.name,
                'chips': player.chips,
                'current_bet': player.current_bet,
                'total_bet': player.total_bet,
                'is_active': player.is_active,
                'is_all_in': player.is_all_in,
                'position': player.position
            } for player in self.players]
        }
    
    def _move_to_next_active_player(self):
        """
        Find the next active player who isn't all-in and update self.active_player_index.
        """
        original_index = self.active_player_index
        
        # Move to the next player
        self.active_player_index = (self.active_player_index + 1) % len(self.players)
        
        # Find the next active player who isn't all-in
        while (not self.players[self.active_player_index].is_active or 
               self.players[self.active_player_index].is_all_in):
            self.active_player_index = (self.active_player_index + 1) % len(self.players)
            
            # If we've gone all the way around and found no eligible players,
            # then everyone is either all-in or folded
            if self.active_player_index == original_index:
                # Force the betting round to complete
                return None
        
        return self.active_player_index
    
    def _add_to_pot(self, amount):
        """
        Add chips to the main pot.
        
        Args:
            amount: The amount to add to the pot.
        """
        # Add to the main pot (pots[0])
        self.pots[0]['amount'] += amount
        
        # If any players are all-in, create side pots as needed
        all_in_players = [p for p in self.players if p.is_all_in and p.is_active]
        if all_in_players:
            self._create_side_pots()
            
    def _reset_betting_round(self):
        """
        Reset the betting round state.
        """
        # Reset the current bet
        self.current_bet = 0
        
        # Reset players for new betting round
        for player in self.players:
            if player.is_active:
                player.reset_for_new_betting_round()
    
    def _create_side_pots(self):
        """
        Create side pots based on all-in players.
        """
        # Sort players by current bet (all-in players first)
        all_in_players = sorted(
            [p for p in self.players if p.is_all_in and p.is_active],
            key=lambda p: p.current_bet
        )
        
        # If no all-in players, no need for side pots
        if not all_in_players:
            return
        
        # Start with just the main pot
        if len(self.pots) == 1:
            # Convert main pot to first "level" pot
            self.pots[0]['eligible_players'] = self.players.copy()
        
        # For each all-in player, create a side pot
        for i, all_in_player in enumerate(all_in_players):
            # Current bet level
            current_level = all_in_player.current_bet
            
            # If this is lower than the highest bet, create a side pot
            if current_level < max(p.current_bet for p in self.players if p.is_active):
                # Players with higher bets contribute to this side pot
                higher_bettors = [p for p in self.players if p.is_active and p.current_bet > current_level]
                
                # Calculate amount for this side pot
                side_pot_amount = sum(min(p.current_bet, current_level) for p in higher_bettors)
                
                # Create side pot
                side_pot = {
                    'amount': side_pot_amount,
                    'eligible_players': [p for p in self.players if p.is_active and p.current_bet >= current_level]
                }
                
                # Add side pot
                if i + 1 >= len(self.pots):
                    self.pots.append(side_pot)
                else:
                    # Update existing side pot
                    self.pots[i + 1] = side_pot