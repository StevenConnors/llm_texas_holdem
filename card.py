import random
from constants import SUITS, RANKS

class Card:
    """Represents a playing card with a suit and rank."""
    
    def __init__(self, suit, rank):
        """
        Initialize a card with a suit and rank.
        
        Args:
            suit (str): The card suit (C, D, H, S)
            rank (str): The card rank (2-10, J, Q, K, A)
        """
        self.suit = suit
        self.rank = rank
        
    def __str__(self):
        """String representation of a card (e.g., 'AH' for Ace of Hearts)."""
        return f"{self.rank}{self.suit}"
    
    def __repr__(self):
        """Formal string representation of a card object."""
        return f"Card('{self.suit}', '{self.rank}')"
    
    def __eq__(self, other):
        """Compare two cards for equality."""
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank
    
    @property
    def rank_value(self):
        """Return the numerical value of the card's rank."""
        return RANKS.index(self.rank)


class Deck:
    """Represents a standard deck of 52 playing cards."""
    
    def __init__(self):
        """Initialize a standard deck of 52 cards."""
        self.cards = []
        self.reset()
        
    def reset(self):
        """Reset the deck to a complete, unshuffled state."""
        self.cards = [Card(suit, rank) for suit in SUITS for rank in RANKS]
        
    def shuffle(self):
        """Shuffle the deck using the Fisher-Yates algorithm."""
        random.shuffle(self.cards)
        
    def deal(self, num_cards=1):
        """
        Deal a specified number of cards from the deck.
        
        Args:
            num_cards (int): Number of cards to deal
            
        Returns:
            list: A list of Card objects
            
        Raises:
            ValueError: If there are not enough cards left in the deck
        """
        if len(self.cards) < num_cards:
            raise ValueError(f"Not enough cards in deck. Requested: {num_cards}, Available: {len(self.cards)}")
        
        dealt_cards = []
        for _ in range(num_cards):
            dealt_cards.append(self.cards.pop())
            
        return dealt_cards
    
    def deal_card(self):
        """
        Deal a single card from the deck.
        
        Returns:
            Card: A single Card object
            
        Raises:
            ValueError: If there are no cards left in the deck
        """
        if len(self.cards) == 0:
            raise ValueError("No cards left in the deck")
        
        return self.cards.pop()
    
    def __len__(self):
        """Return the number of cards remaining in the deck."""
        return len(self.cards) 