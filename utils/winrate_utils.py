import pandas as pd
import numpy as np
import plotly.graph_objects as go
from treys import Card, Evaluator, Deck
from utils.poker_utils import card_to_treys, treys_to_card, monte_carlo_simulation

def validate_cards(card1_rank, card1_suit, card2_rank, card2_suit, board_cards):
    """
    Validate that all cards are unique
    
    Parameters:
    - card1_rank, card1_suit: First hole card
    - card2_rank, card2_suit: Second hole card
    - board_cards: List of (rank, suit) tuples for board cards
    
    Returns:
    - (is_valid, error_message)
    """
    # Convert to string representation for comparison
    cards = []
    
    # Add hole cards
    if card1_rank and card1_suit:
        cards.append(f"{card1_rank}{card1_suit}")
    
    if card2_rank and card2_suit:
        cards.append(f"{card2_rank}{card2_suit}")
    
    # Add board cards
    for rank, suit in board_cards:
        if rank and suit:
            cards.append(f"{rank}{suit}")
    
    # Check for duplicates
    if len(cards) != len(set(cards)):
        return False, "同じカードが複数選択されています。すべてのカードは一意である必要があります。"
    
    return True, ""

def calculate_win_rate(card1_rank, card1_suit, card2_rank, card2_suit, 
                      board_ranks, board_suits, num_opponents, num_simulations):
    """
    Calculate win rate using Monte Carlo simulation
    
    Parameters:
    - card1_rank, card1_suit: First hole card
    - card2_rank, card2_suit: Second hole card
    - board_ranks, board_suits: Lists of ranks and suits for board cards
    - num_opponents: Number of opponents
    - num_simulations: Number of simulations to run
    
    Returns:
    - Dictionary with win, tie, and loss probabilities
    """
    # Convert hole cards to treys format
    hole_card1 = card_to_treys(card1_rank, card1_suit)
    hole_card2 = card_to_treys(card2_rank, card2_suit)
    
    if not hole_card1 or not hole_card2:
        return {
            'win': 0,
            'tie': 0,
            'loss': 0,
            'error': "ホールカードが正しく指定されていません。"
        }
    
    # Convert board cards to treys format
    board_cards = []
    for i in range(len(board_ranks)):
        if board_ranks[i] and board_suits[i]:
            card = card_to_treys(board_ranks[i], board_suits[i])
            if card:
                board_cards.append(card)
    
    # Validate all cards are unique
    all_cards = [(card1_rank, card1_suit), (card2_rank, card2_suit)]
    all_cards.extend([(board_ranks[i], board_suits[i]) for i in range(len(board_ranks)) if board_ranks[i] and board_suits[i]])
    
    is_valid, error_message = validate_cards(card1_rank, card1_suit, card2_rank, card2_suit, 
                                           [(board_ranks[i], board_suits[i]) for i in range(len(board_ranks)) if board_ranks[i] and board_suits[i]])
    
    if not is_valid:
        return {
            'win': 0,
            'tie': 0,
            'loss': 0,
            'error': error_message
        }
    
    # Run Monte Carlo simulation
    result = monte_carlo_simulation([hole_card1, hole_card2], board_cards, num_opponents, num_simulations)
    
    return result

def create_win_rate_chart(win_rate_data):
    """
    Create a pie chart visualization of win rate data
    
    Parameters:
    - win_rate_data: Dictionary with win, tie, and loss probabilities
    
    Returns:
    - Plotly figure object
    """
    labels = ['勝ち', '引き分け', '負け']
    values = [win_rate_data['win'], win_rate_data['tie'], win_rate_data['loss']]
    colors = ['rgb(100, 200, 100)', 'rgb(200, 200, 100)', 'rgb(200, 100, 100)']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.4,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textposition='outside',
        textfont=dict(size=14),
        hoverinfo='label+percent',
        showlegend=False
    )])
    
    fig.update_layout(
        title="勝率シミュレーション結果",
        height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def get_win_rate_description(win_rate_data, card1_rank, card1_suit, card2_rank, card2_suit, num_opponents, board_cards=None):
    """
    Get a description of the win rate results
    
    Parameters:
    - win_rate_data: Dictionary with win, tie, and loss probabilities
    - card1_rank, card1_suit: First hole card
    - card2_rank, card2_suit: Second hole card
    - num_opponents: Number of opponents
    - board_cards: Optional list of (rank, suit) tuples for board cards
    
    Returns:
    - Description string
    """
    hand_type = f"{card1_rank}{card1_suit} {card2_rank}{card2_suit}"
    
    if 'error' in win_rate_data and win_rate_data['error']:
        return f"エラー: {win_rate_data['error']}"
    
    win_pct = win_rate_data['win'] * 100
    tie_pct = win_rate_data['tie'] * 100
    
    if board_cards and any(board_cards):
        board_str = " ".join([f"{rank}{suit}" for rank, suit in board_cards if rank and suit])
        description = f"ハンド **{hand_type}** は、ボード **{board_str}** で **{num_opponents}人** の相手に対して **{win_pct:.1f}%** の勝率があります。"
    else:
        description = f"ハンド **{hand_type}** は、**{num_opponents}人** の相手に対して **{win_pct:.1f}%** の勝率があります。"
    
    # Add interpretation
    if win_pct >= 80:
        description += "\n\n**非常に強い**ハンドです。積極的にプレイすべきです。"
    elif win_pct >= 60:
        description += "\n\n**強い**ハンドです。通常はレイズやベットを検討すべきです。"
    elif win_pct >= 45:
        description += "\n\n**平均的な強さ**のハンドです。状況に応じてプレイを判断しましょう。"
    elif win_pct >= 30:
        description += "\n\n**弱い**ハンドです。慎重にプレイし、良いオッズがある場合のみ継続を検討しましょう。"
    else:
        description += "\n\n**非常に弱い**ハンドです。通常はフォールドを検討すべきです。"
    
    return description

def get_hand_strength_category(win_rate):
    """
    Get a category description based on win rate
    
    Parameters:
    - win_rate: Win probability (0-1)
    
    Returns:
    - Category string
    """
    if win_rate >= 0.8:
        return "モンスターハンド"
    elif win_rate >= 0.65:
        return "プレミアムハンド"
    elif win_rate >= 0.5:
        return "強いハンド"
    elif win_rate >= 0.4:
        return "平均的なハンド"
    elif win_rate >= 0.3:
        return "弱いハンド"
    else:
        return "非常に弱いハンド"
