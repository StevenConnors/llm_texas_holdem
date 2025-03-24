from constants import ACTION_FOLD, ACTION_CHECK, ACTION_CALL, ACTION_BET, ACTION_RAISE, ACTION_ALL_IN

class Player:
    """Represents a player in a Texas Hold'em poker game."""
    
    def __init__(self, name, chips, player_id=None):
        """
        Initialize a player.
        
        Args:
            name (str): Player's name
            chips (int): Starting chip count
            player_id (int, optional): Player ID
        """
        self.name = name
        self.chips = chips
        self.player_id = player_id
        self.cards = []
        self.is_active = True  # If the player is still in the current hand
        self.is_all_in = False  # If the player has gone all-in
        self.current_bet = 0    # Amount bet in the current betting round
        self.total_bet = 0      # Total amount bet in the current hand
        self.has_acted = False  # Whether the player has taken an action in the current betting round
        self.position = None  # Position at the table (e.g., 'dealer', 'small_blind', 'big_blind')
        
    def reset_for_new_hand(self):
        """Reset player state for a new hand."""
        self.cards = []
        self.is_active = True
        self.is_all_in = False
        self.current_bet = 0
        self.total_bet = 0
        
    def reset_for_new_round(self):
        """Reset player state for a new betting round."""
        self.current_bet = 0
        
    def add_hole_card(self, card):
        """Add a hole card to the player's hand."""
        self.cards.append(card)
        
    def add_chips(self, amount):
        """Add chips to the player's stack."""
        self.chips += amount
        
    def remove_chips(self, amount):
        """
        Remove chips from the player's stack.
        
        Args:
            amount (int): Amount to remove
            
        Returns:
            int: Actual amount removed (may be less if not enough chips)
            
        Raises:
            ValueError: If requested amount is negative
        """
        if amount < 0:
            raise ValueError("Cannot remove negative amount of chips")
            
        if amount > self.chips:
            actual_amount = self.chips
            self.chips = 0
            return actual_amount
        else:
            self.chips -= amount
            return amount
    
    def fold(self):
        """
        Fold the current hand.
        
        Returns:
            Tuple of (action, 0) - no chips added to pot
        """
        self.is_active = False
        self.has_acted = True
        return ACTION_FOLD, 0
    
    def check(self):
        """
        Check (do nothing).
        
        Returns:
            Tuple of (action, 0) - no chips added to pot
        """
        self.has_acted = True
        return ACTION_CHECK, 0
    
    def call(self, call_amount):
        """
        Call the current bet.
        
        Args:
            call_amount: The amount needed to call.
            
        Returns:
            Tuple of (action, amount actually called)
        """
        print(f"Player {self.player_id} calling {call_amount}")
        # If call amount exceeds chips, go all-in
        if call_amount >= self.chips:
            return self.all_in()
            
        self.current_bet += call_amount
        self.chips -= call_amount
        self.has_acted = True
        
        return ACTION_CALL, call_amount
    
    def bet(self, amount):
        """
        Place a bet.
        
        Args:
            amount: Amount to bet.
            
        Returns:
            Tuple of (action, amount actually bet)
        """
        # If bet amount exceeds chips, go all-in
        if amount >= self.chips:
            return self.all_in()
            
        self.current_bet = amount
        self.chips -= amount
        self.has_acted = True
        
        # Check if all-in
        if self.chips == 0:
            self.is_all_in = True
            
        return ACTION_BET, amount
    
    def raise_bet(self, raise_amount):
        """
        Raise the current bet.
        
        Args:
            raise_amount: The amount to raise beyond the player's current bet.
            
        Returns:
            Tuple of (action, amount actually raised)
        """
        print(f"Player {self.player_id} raising by {raise_amount}")
        # Check if player has enough chips
        if raise_amount > self.chips:
            # Player doesn't have enough, go all-in instead
            return self.all_in()
            
        # Add the raise amount to the player's current bet
        self.current_bet += raise_amount
        self.chips -= raise_amount
        self.has_acted = True
        
        # Check if all-in
        if self.chips == 0:
            self.is_all_in = True
            
        return (ACTION_RAISE, raise_amount)
    
    def all_in(self):
        """
        Go all-in.
        
        Returns:
            Tuple of (action, amount) - the amount added to the current bet
        """
        amount = self.chips
        self.current_bet += amount
        self.chips = 0
        self.is_all_in = True
        self.has_acted = True
        
        return ACTION_ALL_IN, amount
    
    def reset_for_new_betting_round(self):
        """
        Reset the player's state for a new betting round.
        Resets the current bet but keeps the player's active status and all-in status.
        """
        self.has_acted = False
        self.current_bet = 0
    
    def __str__(self):
        """String representation of a player."""
        return f"{self.name} (Chips: {self.chips})" 