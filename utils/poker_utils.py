import numpy as np
from treys import Card, Evaluator, Deck
import pandas as pd

# Card rank and suit mappings
RANK_MAP = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
}

RANK_MAP_REVERSE = {v: k for k, v in RANK_MAP.items()}

SUIT_MAP = {
    '♠': 's', '♥': 'h', '♦': 'd', '♣': 'c'
}

SUIT_MAP_REVERSE = {
    's': '♠', 'h': '♥', 'd': '♦', 'c': '♣'
}

# Treys card conversion utilities
def card_to_treys(rank, suit):
    """Convert a card's rank and suit to treys Card integer representation"""
    if not rank or not suit:
        return None
    
    suit_char = SUIT_MAP.get(suit, suit.lower())
    return Card.new(rank + suit_char)

def treys_to_card(card_int):
    """Convert a treys Card integer back to rank and suit"""
    if card_int is None:
        return None, None
    
    card_str = Card.int_to_str(card_int)
    rank = card_str[0]
    suit_char = card_str[1]
    suit = SUIT_MAP_REVERSE.get(suit_char, suit_char)
    
    return rank, suit

# Hand type utilities
def generate_hand_matrix():
    """Generate a 13x13 matrix of all possible starting hands"""
    ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
    
    # Create empty matrix
    hand_matrix = []
    
    for i, rank1 in enumerate(ranks):
        row = []
        for j, rank2 in enumerate(ranks):
            # Determine if suited or offsuit
            if i < j:  # Suited
                hand = f"{rank1}{rank2}s"
            elif i > j:  # Offsuit
                hand = f"{rank2}{rank1}o"
            else:  # Pocket pair
                hand = f"{rank1}{rank2}"
            
            row.append(hand)
        hand_matrix.append(row)
    
    return pd.DataFrame(hand_matrix, index=ranks, columns=ranks)

def get_hand_type(card1_rank, card1_suit, card2_rank, card2_suit):
    """Determine the hand type (e.g., 'AKs', 'QJo', '88')"""
    if card1_rank == card2_rank:
        return f"{card1_rank}{card2_rank}"  # Pocket pair
    
    # Determine higher card
    rank1_value = RANK_MAP.get(card1_rank, 0)
    rank2_value = RANK_MAP.get(card2_rank, 0)
    
    if rank1_value > rank2_value:
        high_rank, low_rank = card1_rank, card2_rank
    else:
        high_rank, low_rank = card2_rank, card1_rank
    
    # Determine if suited
    if card1_suit == card2_suit:
        return f"{high_rank}{low_rank}s"  # Suited
    else:
        return f"{high_rank}{low_rank}o"  # Offsuit

def get_hand_strength(hand_type):
    """Get a numerical strength value for a hand type (for sorting)"""
    if len(hand_type) == 2:  # Pocket pair
        rank = hand_type[0]
        return 13 * 13 - (13 - RANK_MAP.get(rank, 0)) * 13
    
    high_rank = hand_type[0]
    low_rank = hand_type[1]
    suited = hand_type.endswith('s')
    
    high_value = RANK_MAP.get(high_rank, 0)
    low_value = RANK_MAP.get(low_rank, 0)
    
    # Suited hands are stronger than offsuit
    if suited:
        return 13 * high_value + low_value
    else:
        return 13 * high_value + low_value - 50  # Penalty for offsuit

def monte_carlo_simulation(hole_cards, board_cards, num_opponents, num_simulations):
    """
    Run Monte Carlo simulation to calculate win probability
    
    Parameters:
    - hole_cards: List of treys Card integers [card1, card2]
    - board_cards: List of treys Card integers [card1, card2, ...] (can be empty)
    - num_opponents: Number of opponents
    - num_simulations: Number of simulations to run
    
    Returns:
    - Dictionary with win, tie, and loss probabilities
    """
    evaluator = Evaluator()
    wins = 0
    ties = 0
    
    for _ in range(num_simulations):
        # Create a new deck for each simulation
        deck = Deck()
        
        # Remove hole cards and known board cards from the deck
        for card in hole_cards + board_cards:
            if card is not None:
                deck.cards.remove(card)
        
        # Complete the board if needed
        current_board = [c for c in board_cards if c is not None]
        remaining_board = 5 - len(current_board)
        
        if remaining_board > 0:
            current_board += deck.draw(remaining_board)
        
        # Deal cards to opponents
        opponents_hole_cards = []
        for _ in range(num_opponents):
            opponents_hole_cards.append(deck.draw(2))
        
        # Evaluate hands
        player_score = evaluator.evaluate(current_board, hole_cards)
        opponent_scores = [evaluator.evaluate(current_board, opp_cards) for opp_cards in opponents_hole_cards]
        
        # In treys, lower score is better
        if all(player_score < score for score in opponent_scores):
            wins += 1
        elif any(player_score == score for score in opponent_scores):
            ties += 1
    
    win_prob = wins / num_simulations
    tie_prob = ties / num_simulations
    loss_prob = 1 - win_prob - tie_prob
    
    return {
        'win': win_prob,
        'tie': tie_prob,
        'loss': loss_prob
    }
