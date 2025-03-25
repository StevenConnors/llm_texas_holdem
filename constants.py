# Texas Hold'em constants

# Card suits
CLUBS = 'C'
DIAMONDS = 'D'
HEARTS = 'H'
SPADES = 'S'
SUITS = [CLUBS, DIAMONDS, HEARTS, SPADES]

# Card ranks
TWO = '2'
THREE = '3'
FOUR = '4'
FIVE = '5'
SIX = '6'
SEVEN = '7'
EIGHT = '8'
NINE = '9'
TEN = 'T'
JACK = 'J'
QUEEN = 'Q'
KING = 'K'
ACE = 'A'
RANKS = [TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, TEN, JACK, QUEEN, KING, ACE]

# Hand rankings
HIGH_CARD = 0
PAIR = 1
TWO_PAIR = 2
THREE_OF_A_KIND = 3
STRAIGHT = 4
FLUSH = 5
FULL_HOUSE = 6
FOUR_OF_A_KIND = 7
STRAIGHT_FLUSH = 8
ROYAL_FLUSH = 9
HAND_RANKINGS = {
    HIGH_CARD: "High Card",
    PAIR: "Pair",
    TWO_PAIR: "Two Pair",
    THREE_OF_A_KIND: "Three of a Kind",
    STRAIGHT: "Straight",
    FLUSH: "Flush",
    FULL_HOUSE: "Full House",
    FOUR_OF_A_KIND: "Four of a Kind",
    STRAIGHT_FLUSH: "Straight Flush",
    ROYAL_FLUSH: "Royal Flush"
}

# Game phases
PHASE_PREFLOP = 'pre_flop'
PHASE_FLOP = 'flop'
PHASE_TURN = 'turn'
PHASE_RIVER = 'river'
PHASE_SHOWDOWN = 'showdown'

# Player actions
ACTION_FOLD = 'fold'
ACTION_CHECK = 'check'
ACTION_CALL = 'call'
ACTION_BET = 'bet'
ACTION_RAISE = 'raise'
ACTION_ALL_IN = 'all_in' 