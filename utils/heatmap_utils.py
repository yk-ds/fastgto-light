import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import os

# Define mappings between numeric ranks and display ranks
# Numeric ranks: 2-14 (2=2, 3=3, ..., 10=T, 11=J, 12=Q, 13=K, 14=A)
# Display ranks: '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'
NUMERIC_RANKS = list(range(2, 15))  # 2-14
DISPLAY_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
RANK_TO_NUM = {r: n for r, n in zip(DISPLAY_RANKS, NUMERIC_RANKS)}
NUM_TO_RANK = {n: r for r, n in zip(DISPLAY_RANKS, NUMERIC_RANKS)}

def load_range_data(position, action, opponent_type="標準"):
    """
    Load range data for a specific position and action
    
    Parameters:
    - position: Player position (UTG, MP, CO, BTN, SB, BB)
    - action: Action type (Open, Call, 3Bet)
    - opponent_type: Opponent type for exploit adjustments
    
    Returns:
    - DataFrame with hand frequencies
    """
    # Default range data (simplified for MVP)
    # In a real implementation, this would load from a database or file
    
    # Create a base matrix of zeros using numeric ranks (2-14)
    # We'll convert to display ranks when showing the heatmap
    # Use 0.0 to initialize with float64 dtype to avoid warnings when setting float values later
    range_data = pd.DataFrame(0.0, index=NUMERIC_RANKS, columns=NUMERIC_RANKS)
    
    # Define some basic ranges based on position and action
    # These are simplified approximations
    ranks = NUMERIC_RANKS  # Use numeric ranks for calculations
    
    # UTG Open Range (tight)
    if position == "UTG" and action == "Open":
        # Pocket pairs
        for rank in ranks:
            if rank >= 7:  # 77+ (pairs 77 and higher)
                range_data.loc[rank, rank] = 1.0
        
        # Broadway hands
        for rank1 in ranks[-4:]:  # A, K, Q, J (highest 4 ranks)
            for rank2 in ranks[-4:]:  # A, K, Q, J
                if rank1 != rank2:  # Not the same rank
                    if rank1 > rank2:  # Suited (higher rank first)
                        range_data.loc[rank1, rank2] = 1.0
                    else:  # Offsuit
                        range_data.loc[rank2, rank1] = 0.7 if rank2 >= 13 else 0.0  # K or higher
        
        # Suited Aces
        for rank in [8, 9, 10, 11]:  # 8, 9, T, J (Ace is 14)
            range_data.loc[14, rank] = 0.8  # A8s+
    
    # MP Open Range (medium)
    elif position == "MP" and action == "Open":
        # Pocket pairs
        for rank in ranks:
            if rank >= 5:  # 55+ (pairs 55 and higher)
                range_data.loc[rank, rank] = 1.0
        
        # Broadway hands
        for rank1 in ranks[-4:]:  # A, K, Q, J (highest 4 ranks)
            for rank2 in ranks[-5:]:  # A, K, Q, J, T (highest 5 ranks)
                if rank1 != rank2 and rank2 >= 10:  # Not the same rank, T or higher
                    if rank1 > rank2:  # Suited (higher rank first)
                        range_data.loc[rank1, rank2] = 1.0
                    else:  # Offsuit
                        range_data.loc[rank2, rank1] = 0.8 if rank2 >= 12 else 0.3  # Q or higher
        
        # Suited Aces and Kings
        for rank in [6, 7, 8, 9]:  # 6, 7, 8, 9
            range_data.loc[14, rank] = 0.9  # Suited Aces
            range_data.loc[13, rank] = 0.5 if rank >= 7 else 0.0  # Suited Kings
    
    # CO Open Range (medium-loose)
    elif position == "CO" and action == "Open":
        # Pocket pairs
        for rank in ranks:
            range_data.loc[rank, rank] = 1.0
        
        # Broadway hands
        for rank1 in ranks[-5:]:  # A, K, Q, J, T (highest 5 ranks)
            for rank2 in ranks[-5:]:  # A, K, Q, J, T
                if rank1 != rank2:  # Not the same rank
                    if rank1 > rank2:  # Suited (higher rank first)
                        range_data.loc[rank1, rank2] = 1.0
                    else:  # Offsuit
                        range_data.loc[rank2, rank1] = 0.9
        
        # Suited connectors and one-gappers
        for i in range(3, 9):  # 4 to 10
            range_data.loc[i+1, i] = 1.0  # Suited connectors
            if i < 8:
                range_data.loc[i+2, i] = 0.7  # Suited one-gappers
        
        # Suited Aces
        for rank in [5, 6, 7, 8, 9]:  # 5, 6, 7, 8, 9
            range_data.loc[14, rank] = 1.0  # Suited Aces
    
    # BTN Open Range (loose)
    elif position == "BTN" and action == "Open":
        # Almost all hands with some frequency
        for rank1 in ranks:
            for rank2 in ranks:
                if rank1 == rank2:  # Pocket pairs
                    range_data.loc[rank1, rank2] = 1.0
                elif rank1 > rank2:  # Suited (higher rank first)
                    range_data.loc[rank1, rank2] = 1.0 if rank1 >= 6 or rank2 >= 9 else 0.7
                else:  # Offsuit
                    range_data.loc[rank1, rank2] = 0.9 if rank1 >= 9 or rank2 >= 11 else 0.5
    
    # SB Open Range (polarized)
    elif position == "SB" and action == "Open":
        # Strong hands
        for rank1 in ranks[-6:]:  # A, K, Q, J, T, 9 (highest 6 ranks)
            for rank2 in ranks[-6:]:  # A, K, Q, J, T, 9
                if rank1 == rank2:  # Pocket pairs
                    range_data.loc[rank1, rank2] = 1.0
                elif rank1 > rank2:  # Suited (higher rank first)
                    range_data.loc[rank1, rank2] = 1.0
                else:  # Offsuit
                    range_data.loc[rank1, rank2] = 0.9 if rank1 >= 11 else 0.6  # J or higher
        
        # Medium pocket pairs
        for rank in range(5, 9):  # 5, 6, 7, 8
            range_data.loc[rank, rank] = 0.9
        
        # Suited Aces
        for rank in [2, 3, 4, 5, 6, 7, 8]:  # 2 to 8
            range_data.loc[14, rank] = 0.8  # Suited Aces
    
    # BB Call Range (vs BTN open)
    elif position == "BB" and action == "Call":
        # Most hands with some frequency
        for rank1 in ranks:
            for rank2 in ranks:
                if rank1 == rank2:  # Pocket pairs
                    range_data.loc[rank1, rank2] = 0.9 if rank1 <= 10 else 0.3  # Small-medium pairs
                elif rank1 > rank2:  # Suited (higher rank first)
                    range_data.loc[rank1, rank2] = 0.9 if rank1 >= 7 or rank2 >= 10 else 0.6
                else:  # Offsuit
                    range_data.loc[rank1, rank2] = 0.7 if rank1 >= 10 or rank2 >= 12 else 0.3
    
    # BB 3Bet Range (vs BTN open)
    elif position == "BB" and action == "3Bet":
        # Strong hands
        for rank1 in ranks[-3:]:  # A, K, Q (highest 3 ranks)
            for rank2 in ranks[-3:]:  # A, K, Q
                if rank1 == rank2:  # Pocket pairs
                    range_data.loc[rank1, rank2] = 1.0
                elif rank1 > rank2:  # Suited (higher rank first)
                    range_data.loc[rank1, rank2] = 0.9
                else:  # Offsuit
                    range_data.loc[rank1, rank2] = 0.8
        
        # Strong pocket pairs
        for rank in range(8, 12):  # 8, 9, T, J
            range_data.loc[rank, rank] = 0.8
        
        # Some bluffs
        for i in range(4, 9):  # 4 to 9
            range_data.loc[i+1, i] = 0.3  # Suited connectors
            range_data.loc[i+2, i] = 0.2  # Offsuit connectors
    
    # Default to a reasonable range if not specified
    else:
        # Medium-strength range
        for rank1 in ranks:
            for rank2 in ranks:
                if rank1 == rank2:  # Pocket pairs
                    range_data.loc[rank1, rank2] = 1.0 if rank1 >= 6 else 0.5
                elif rank1 > rank2:  # Suited (higher rank first)
                    range_data.loc[rank1, rank2] = 0.8 if rank1 >= 9 or rank2 >= 11 else 0.3
                else:  # Offsuit
                    range_data.loc[rank1, rank2] = 0.6 if rank1 >= 11 and rank2 >= 13 else 0.0
    
    # Apply opponent type adjustments
    if opponent_type != "標準":
        range_data = adjust_for_opponent_type(range_data, opponent_type, position, action)
    
    return range_data

def adjust_for_opponent_type(range_data, opponent_type, position, action):
    """
    Adjust range data based on opponent type
    
    Parameters:
    - range_data: Original range data DataFrame
    - opponent_type: Opponent type (タイト, ルーズ, パッシブ, アグレッシブ)
    - position: Player position
    - action: Action type
    
    Returns:
    - Adjusted range data DataFrame
    """
    # Use numeric ranks (2-14)
    ranks = NUMERIC_RANKS
    adjusted_data = range_data.copy()
    
    if opponent_type == "タイト":
        # Against tight players, we can open wider and 3bet more
        if action == "Open":
            # Increase frequency for medium-strength hands
            for rank1 in range(7, 12):  # 7, 8, 9, T, J
                for rank2 in range(5, 10):  # 5, 6, 7, 8, 9
                    if rank1 > rank2:  # Suited (higher rank first)
                        adjusted_data.loc[rank1, rank2] = min(1.0, range_data.loc[rank1, rank2] + 0.2)
        
        elif action == "3Bet":
            # Increase 3bet frequency for strong hands
            for rank1 in ranks[-4:]:  # A, K, Q, J
                for rank2 in ranks[-4:]:  # A, K, Q, J
                    if rank1 != rank2:
                        if rank1 > rank2:  # Suited (higher rank first)
                            adjusted_data.loc[rank1, rank2] = min(1.0, range_data.loc[rank1, rank2] + 0.3)
                        else:  # Offsuit
                            adjusted_data.loc[rank1, rank2] = min(1.0, range_data.loc[rank1, rank2] + 0.2)
    
    elif opponent_type == "ルーズ":
        # Against loose players, we tighten up opening but call and 3bet more
        if action == "Open":
            # Decrease frequency for marginal hands
            for rank1 in range(2, 10):  # 2 to 9
                for rank2 in range(2, 8):  # 2 to 7
                    if rank1 != rank2:  # Not pocket pairs
                        if rank1 > rank2:  # Suited (higher rank first)
                            adjusted_data.loc[rank1, rank2] = max(0.0, range_data.loc[rank1, rank2] - 0.3)
                        else:  # Offsuit
                            adjusted_data.loc[rank1, rank2] = max(0.0, range_data.loc[rank1, rank2] - 0.5)
        
        elif action == "Call":
            # Increase call frequency for strong hands
            for rank1 in ranks[-5:]:  # A, K, Q, J, T
                for rank2 in ranks[-5:]:  # A, K, Q, J, T
                    if rank1 != rank2:
                        adjusted_data.loc[rank1, rank2] = min(1.0, range_data.loc[rank1, rank2] + 0.2)
    
    elif opponent_type == "パッシブ":
        # Against passive players, we can bluff more
        if action == "Open" or action == "3Bet":
            # Increase frequency for speculative hands
            for i in range(4, 10):  # 4 to 9
                for j in range(i+1, min(i+4, 13)):  # Connected and one/two-gappers
                    if i+1 == j:  # Suited connectors
                        adjusted_data.loc[j, i] = min(1.0, range_data.loc[j, i] + 0.3)
    
    elif opponent_type == "アグレッシブ":
        # Against aggressive players, we tighten up and play stronger hands
        if action == "Open":
            # Decrease frequency for marginal hands
            for rank1 in range(2, 11):  # 2 to T
                for rank2 in range(2, 9):  # 2 to 8
                    if rank1 > rank2:  # Offsuit
                        adjusted_data.loc[rank1, rank2] = max(0.0, range_data.loc[rank1, rank2] - 0.4)
        
        elif action == "Call":
            # Decrease call frequency, increase 3bet frequency
            for rank1 in ranks:
                for rank2 in ranks:
                    if rank1 != rank2 and ((rank1 > rank2 and rank1 <= 11) or (rank1 < rank2 and rank2 <= 11)):  # Medium strength hands
                        adjusted_data.loc[rank1, rank2] = max(0.0, range_data.loc[rank1, rank2] - 0.3)
    
    return adjusted_data

def create_heatmap(range_data, position, action, opponent_type="標準"):
    """
    Create a Plotly heatmap visualization from range data
    
    Parameters:
    - range_data: DataFrame with hand frequencies
    - position: Player position
    - action: Action type
    - opponent_type: Opponent type
    
    Returns:
    - Plotly figure object
    """
    # Convert numeric ranks to display ranks for visualization
    display_tickvals = range_data.columns[::-1]  # Reverse for display
    display_ticktext = [NUM_TO_RANK[n] for n in display_tickvals]  # Convert to A, K, Q, etc.
    
    # Create the heatmap with more gradation levels
    fig = go.Figure(data=go.Heatmap(
        z=range_data.values[::-1, ::-1],  # Reverse both rows and columns
        x=display_tickvals,  # Numeric ranks (reversed)
        y=display_tickvals,  # Numeric ranks (reversed)
        colorscale=[
            [0.00, 'rgb(40, 40, 40)'],      # Dark gray/Black for 0% (FOLD)
            [0.16, 'rgb(60, 60, 140)'],     # Dark blue for ~16% (FOLD)
            [0.33, 'rgb(80, 120, 180)'],    # Medium blue for ~33% (FOLD/CALL混合)
            [0.50, 'rgb(60, 160, 120)'],    # Teal/Green for ~50% (CALL)
            [0.67, 'rgb(180, 160, 60)'],    # Gold for ~67% (CALL/RAISE混合)
            [0.84, 'rgb(220, 120, 60)'],    # Orange for ~84% (RAISE)
            [1.00, 'rgb(200, 50, 50)']      # Red for 100% (ALL-IN)
        ],
        showscale=True,
        colorbar=dict(
            title=dict(
                text="アクション頻度",
                side="right"
            ),
            tickmode="array",
            tickvals=[0, 0.16, 0.33, 0.5, 0.67, 0.84, 1],
            ticktext=["FOLD", "FOLD", "FOLD/CALL", "CALL", "CALL/RAISE", "RAISE", "ALL-IN"]
        ),
        hovertemplate='%{y}%{x}: %{z:.0%}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=f"{position}ポジションからの{action}レンジ (相手: {opponent_type})",
        xaxis=dict(
            title="2枚目のカード",
            tickvals=display_tickvals,
            ticktext=display_ticktext,  # Display A, K, Q, etc.
            constrain="domain"  # Ensure all ticks are visible
        ),
        yaxis=dict(
            title="1枚目のカード",
            tickvals=display_tickvals,
            ticktext=display_ticktext,  # Display A, K, Q, etc.
            constrain="domain"  # Ensure all ticks are visible
        ),
        # Responsive width for mobile compatibility
        autosize=True,
        height=700,  # Increase height
        width=700,   # Set explicit width
        margin=dict(l=50, r=50, t=80, b=50),  # Increase margins
        font=dict(size=12)  # Increase font size
    )
    
    # Add annotations for hand types - adjust for reversed indices
    reversed_rows = range_data.index[::-1]
    reversed_cols = range_data.columns[::-1]
    
    for i, row in enumerate(reversed_rows):
        for j, col in enumerate(reversed_cols):
            # Find the corresponding indices in the original dataframe
            orig_i = len(range_data.index) - 1 - i
            orig_j = len(range_data.columns) - 1 - j
            
            # Convert numeric ranks to display ranks
            row_display = NUM_TO_RANK[row]
            col_display = NUM_TO_RANK[col]
            
            # Determine hand type
            if row == col:  # Pocket pair
                hand_type = f"{row_display}{row_display}"
            elif row > col:  # Suited (higher rank first)
                hand_type = f"{row_display}{col_display}s"
            else:  # Offsuit
                hand_type = f"{col_display}{row_display}o"
            
            # Add hand type and frequency text
            freq = range_data.iloc[orig_i, orig_j]
            
            # Always show hand type, even if frequency is 0
            fig.add_annotation(
                x=col,
                y=row,
                text=hand_type,
                showarrow=False,
                font=dict(
                    color="white" if freq < 0.3 or freq > 0.7 else "black",
                    size=10
                )
            )
            
            # Add frequency text below hand type if frequency > 0
            if freq > 0:
                fig.add_annotation(
                    x=col,
                    y=row,
                    text=f"{freq:.0%}",
                    showarrow=False,
                    font=dict(
                        color="white" if freq < 0.3 or freq > 0.7 else "black",
                        size=8
                    ),
                    yshift=-10  # Shift down to avoid overlapping with hand type
                )
    
    return fig

def get_action_description(hand_type, frequency, position, action):
    """
    Get a description of the recommended action for a hand
    
    Parameters:
    - hand_type: Hand type (e.g., 'AKs', 'QJo', '88')
    - frequency: Action frequency (0-1)
    - position: Player position
    - action: Action type
    
    Returns:
    - Description string
    """
    if frequency >= 0.95:
        return f"{hand_type}は常に{action}すべきハンドです。"
    elif frequency >= 0.7:
        return f"{hand_type}は高頻度で{action}すべきハンドです。"
    elif frequency >= 0.3:
        return f"{hand_type}は時々{action}すべきハンドです（{frequency:.0%}の頻度）。"
    elif frequency > 0:
        return f"{hand_type}はまれに{action}できますが、通常は避けるべきです（{frequency:.0%}の頻度）。"
    else:
        return f"{hand_type}は{action}すべきではありません。"

def get_exploit_suggestion(hand_type, std_freq, exploit_freq, opponent_type, action):
    """
    Get a suggestion for exploitative play
    
    Parameters:
    - hand_type: Hand type (e.g., 'AKs', 'QJo', '88')
    - std_freq: Standard GTO frequency
    - exploit_freq: Exploitative frequency
    - opponent_type: Opponent type
    - action: Action type
    
    Returns:
    - Suggestion string
    """
    diff = exploit_freq - std_freq
    
    if abs(diff) < 0.1:
        return f"{hand_type}は{opponent_type}相手でも標準的なプレイが最適です。"
    
    if diff > 0:
        if std_freq == 0:
            return f"{opponent_type}相手には{hand_type}を{action}レンジに追加できます（{exploit_freq:.0%}の頻度）。"
        else:
            return f"{opponent_type}相手には{hand_type}の{action}頻度を上げるべきです（{std_freq:.0%}→{exploit_freq:.0%}）。"
    else:
        if exploit_freq == 0:
            return f"{opponent_type}相手には{hand_type}を{action}レンジから除外すべきです。"
        else:
            return f"{opponent_type}相手には{hand_type}の{action}頻度を下げるべきです（{std_freq:.0%}→{exploit_freq:.0%}）。"
