import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from treys import Card, Evaluator, Deck
import json
import os
import random
from datetime import datetime

# Import utility modules
from utils.poker_utils import card_to_treys, treys_to_card, get_hand_type, get_hand_strength
from utils.heatmap_utils import load_range_data, create_heatmap, get_action_description, get_exploit_suggestion
from utils.winrate_utils import calculate_win_rate, create_win_rate_chart, get_win_rate_description

# Page configuration
st.set_page_config(
    page_title="FastGTO Light - ポーカー戦略シミュレーター",
    page_icon="♠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a more professional look
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #2c3e50;
        --secondary-color: #3498db;
        --accent-color: #e74c3c;
        --background-color: #f8f9fa;
        --text-color: #2c3e50;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: var(--primary-color);
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
    }
    
    h1 {
        border-bottom: 2px solid var(--secondary-color);
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* Card-like containers */
    .stCard {
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: var(--secondary-color);
        color: white;
        border-radius: 4px;
        border: none;
        padding: 8px 16px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #2980b9;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--primary-color);
    }
    
    /* Tooltip styling */
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted #ccc;
        cursor: help;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: var(--primary-color);
    }
    
    /* Table styling */
    .dataframe {
        border-collapse: collapse;
        width: 100%;
        border-radius: 5px;
        overflow: hidden;
    }
    
    .dataframe th {
        background-color: var(--secondary-color);
        color: white;
        text-align: left;
        padding: 12px;
    }
    
    .dataframe td {
        padding: 12px;
        border-bottom: 1px solid #ddd;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    
    .dataframe tr:hover {
        background-color: #ddd;
    }
</style>
""", unsafe_allow_html=True)

# Application title with professional styling
st.markdown("<h1 style='text-align: center;'>FastGTO Light</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; margin-bottom: 30px;'>プロフェッショナルなポーカー戦略分析ツール</p>", unsafe_allow_html=True)

# Poker terminology tooltips
poker_terms = {
    "ポジション": "テーブル上のあなたの位置。ディーラーボタンからの相対的な位置によって決まります。",
    "UTG": "アンダー・ザ・ガン。最初に行動するポジション。",
    "MP": "ミドルポジション。UTGの次に行動するポジション。",
    "CO": "カットオフ。ボタンの右隣のポジション。",
    "BTN": "ボタン。ディーラーポジション。最後に行動する有利なポジション。",
    "SB": "スモールブラインド。強制ベットを支払うポジション。",
    "BB": "ビッグブラインド。スモールブラインドの2倍の強制ベットを支払うポジション。",
    "アクション": "プレイヤーが取る行動（ベット、レイズ、コールなど）。",
    "Open": "誰もまだベットしていない状況で最初にポットにチップを入れる行動。",
    "Call": "前のプレイヤーのベット/レイズと同額をポットに入れる行動。",
    "3Bet": "誰かがすでにレイズした後に、さらに再レイズすること。",
    "相手タイプ": "対戦相手のプレイスタイル。",
    "タイト": "強いハンドだけをプレイする慎重なプレイヤー。",
    "ルーズ": "多くの弱いハンドもプレイする寛容なプレイヤー。",
    "パッシブ": "ベットやレイズをあまりせず、主にコールで対応するプレイヤー。",
    "アグレッシブ": "頻繁にベットやレイズをするプレイヤー。",
    "GTO": "Game Theory Optimal（ゲーム理論的最適解）。相手の戦略に関係なく最も搾取されにくい戦略。",
    "レンジ": "プレイヤーが持ちうるハンドの集合。",
    "エクスプロイト": "相手の弱点を突くための調整戦略。"
}

# Brief introduction
st.markdown("""
<div class="stCard">
ポーカーのプリフロップ戦略をヒートマップで可視化し、状況に応じた最適な行動を提案します。
ハンドの勝率計算やエクスプロイト戦略の提案も可能です。
</div>
""", unsafe_allow_html=True)

# Help expander for first-time users
with st.expander("📚 使い方ガイド（初めての方はこちら）"):
    st.markdown("""
    ### FastGTO Lightの使い方
    
    このアプリは、ポーカーのプリフロップ戦略を視覚化し、最適なプレイを提案するツールです。
    
    **主な機能：**
    
    1. **シミュレーションモード**
       - **レンジヒートマップ**: 異なるポジションとアクションに基づくGTOレンジを表示
       - **勝率計算**: 特定のハンドとボードの組み合わせの勝率をシミュレーション
       - **エクスプロイト提案**: 相手のプレイスタイルに応じた調整を提案
    
    2. **クイズモード**
       - ランダムなシナリオでポーカー戦略を学習
       - 正解と解説で理解を深める
    
    **基本用語：**
    - **GTO**: Game Theory Optimal（ゲーム理論的最適解）
    - **レンジ**: プレイヤーが持ちうるハンドの集合
    - **エクスプロイト**: 相手の弱点を突くための調整戦略
    
    サイドバーの設定を変更して、様々な状況でのプレイを探索してみましょう！
    """)

# Mode selection tabs
tab1, tab2 = st.tabs(["シミュレーションモード", "クイズモード"])

# Sidebar for controls
with st.sidebar:
    st.header("設定")
    
    # Position selection
    st.subheader("ポジション選択")
    position = st.selectbox(
        "あなたのポジション:",
        ["UTG", "MP", "CO", "BTN", "SB", "BB"],
        help="UTG=アンダーザガン（最初のポジション）、MP=ミドルポジション、CO=カットオフ、BTN=ボタン、SB=スモールブラインド、BB=ビッグブラインド"
    )
    
    # Action selection
    st.subheader("アクション選択")
    action = st.selectbox(
        "アクション:",
        ["Open", "Call", "3Bet"],
        help="Open=最初のレイズ、Call=コール（相手のベットに応じる）、3Bet=リレイズ（相手のレイズに対してさらにレイズ）"
    )
    
    # Opponent type (for exploit suggestions)
    st.subheader("相手タイプ")
    opponent_type = st.selectbox(
        "相手の傾向:",
        ["標準", "タイト", "ルーズ", "パッシブ", "アグレッシブ"],
        help="タイト=強いハンドのみプレイ、ルーズ=多くのハンドをプレイ、パッシブ=ベットやレイズが少ない、アグレッシブ=ベットやレイズが多い"
    )
    
    # Simulation count for win rate calculator
    st.subheader("シミュレーション設定")
    simulation_count = st.slider(
        "シミュレーション回数:", 
        1000, 10000, 5000, 1000,
        help="多いほど正確ですが、計算に時間がかかります"
    )
    
    # Display settings
    st.subheader("表示設定")
    mobile_mode = st.checkbox(
        "モバイル最適化表示", 
        value=True,
        help="スマートフォンでの表示に最適化します"
    )
    
    # About section
    st.markdown("---")
    st.markdown("### FastGTO Light")
    st.markdown("Version 0.2.1")
    st.markdown("© 2025 All Rights Reserved")

# Simulation Mode Tab
with tab1:
    # Define all possible ranks and suits
    all_ranks = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]
    all_suits = ["♠", "♥", "♦", "♣"]
    
    # Create tooltips for poker terms
    def create_tooltip(term, explanation):
        return f"""<span class="tooltip">{term}<span class="tooltiptext">{explanation}</span></span>"""
    
    # Determine layout based on mobile mode
    if mobile_mode:
        # Mobile-friendly layout (stacked)
        # Load range data
        range_data = load_range_data(position, action, opponent_type)
        
        # Heatmap visualization first (as per user's latest feedback)
        st.markdown(f"""
        <div class="stCard">
            <h2>GTOレンジヒートマップ</h2>
            <p>
                {create_tooltip("ポジション", poker_terms["ポジション"])}: <b>{position}</b> | 
                {create_tooltip("アクション", poker_terms["アクション"])}: <b>{action}</b> | 
                {create_tooltip("相手タイプ", poker_terms["相手タイプ"])}: <b>{opponent_type}</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create heatmap
        heatmap_fig = create_heatmap(range_data, position, action, opponent_type)
        st.plotly_chart(heatmap_fig, use_container_width=False)  # Set to False to prevent resizing
        
        # Hand input section
        st.markdown("""
        <div class="stCard">
            <h2>ハンド分析</h2>
            <p>分析したいハンドを選択してください</p>
        </div>
        """, unsafe_allow_html=True)
        
        col_hand1, col_hand2 = st.columns(2)
        
        with col_hand1:
            card1_rank = st.selectbox("1枚目のランク:", all_ranks, key="card1_rank")
            card1_suit = st.selectbox("1枚目のスート:", all_suits, key="card1_suit")
        
        with col_hand2:
            # For the second card, if the same rank is selected, don't allow the same suit
            card2_rank = st.selectbox("2枚目のランク:", all_ranks, key="card2_rank")
            
            # If same rank is selected, remove the suit that's already selected for the first card
            available_suits = all_suits.copy()
            if card1_rank == card2_rank:
                if card1_suit in available_suits:
                    available_suits.remove(card1_suit)
            
            card2_suit = st.selectbox("2枚目のスート:", available_suits, key="card2_suit")
        
        # Get hand type
        hand_type = get_hand_type(card1_rank, card1_suit, card2_rank, card2_suit)
        st.markdown(f"""
        <div style="background-color: #f0f8ff; padding: 10px; border-radius: 5px; margin: 10px 0;">
            <h3 style="margin: 0;">選択したハンド: <b>{hand_type}</b></h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Convert display ranks to numeric ranks
        from utils.heatmap_utils import RANK_TO_NUM
        
        # Determine row and column in the matrix
        if card1_rank == card2_rank:  # Pocket pair
            # For pocket pairs, both row and column are the same rank
            row_idx = RANK_TO_NUM[card1_rank]
            col_idx = row_idx
        else:
            # Convert display ranks to numeric ranks
            rank1_num = RANK_TO_NUM[card1_rank]
            rank2_num = RANK_TO_NUM[card2_rank]
            
            # Determine if suited
            suited = card1_suit == card2_suit
            
            if suited:
                # For suited hands, higher rank is row, lower rank is column
                if rank1_num > rank2_num:
                    row_idx, col_idx = rank1_num, rank2_num
                else:
                    row_idx, col_idx = rank2_num, rank1_num
            else:
                # For offsuit hands, higher rank is column, lower rank is row
                if rank1_num > rank2_num:
                    row_idx, col_idx = rank2_num, rank1_num
                else:
                    row_idx, col_idx = rank1_num, rank2_num
        
        # Get frequency from range data - use .loc instead of .iloc to access by index value, not position
        try:
            frequency = range_data.loc[row_idx, col_idx]
            
            # Get standard GTO frequency (without opponent type adjustment)
            std_range_data = load_range_data(position, action, "標準")
            std_frequency = std_range_data.loc[row_idx, col_idx]
            
            # Display GTO analysis
            st.markdown(f"""
            <div class="stCard">
                <h3>{create_tooltip("GTO", poker_terms["GTO"])}戦略分析</h3>
                <p>{get_action_description(hand_type, frequency, position, action)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display exploit suggestion if opponent type is not standard
            if opponent_type != "標準":
                st.markdown(f"""
                <div class="stCard">
                    <h3>{create_tooltip("エクスプロイト", poker_terms["エクスプロイト"])}提案</h3>
                    <p>{get_exploit_suggestion(hand_type, std_frequency, frequency, opponent_type, action)}</p>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"有効なハンドを選択してください。エラー: {str(e)}")
        
        # Win rate calculator
        st.header("勝率シミュレーション")
        
        # Board input
        st.subheader("ボード")
        use_board = st.checkbox("ボードカードを指定", value=False)
        
        board_ranks = [""] * 5
        board_suits = [""] * 5
        board_cards = []
        
        if use_board:
            col_board1, col_board2, col_board3 = st.columns(3)
            
            with col_board1:
                board_ranks[0] = st.selectbox("フロップ1のランク:", ["", "A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"], key="board1_rank")
                board_suits[0] = st.selectbox("フロップ1のスート:", ["", "♠", "♥", "♦", "♣"], key="board1_suit")
            
            with col_board2:
                board_ranks[1] = st.selectbox("フロップ2のランク:", ["", "A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"], key="board2_rank")
                board_suits[1] = st.selectbox("フロップ2のスート:", ["", "♠", "♥", "♦", "♣"], key="board2_suit")
            
            with col_board3:
                board_ranks[2] = st.selectbox("フロップ3のランク:", ["", "A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"], key="board3_rank")
                board_suits[2] = st.selectbox("フロップ3のスート:", ["", "♠", "♥", "♦", "♣"], key="board3_suit")
            
            col_board4, col_board5 = st.columns(2)
            
            with col_board4:
                board_ranks[3] = st.selectbox("ターンのランク:", ["", "A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"], key="board4_rank")
                board_suits[3] = st.selectbox("ターンのスート:", ["", "♠", "♥", "♦", "♣"], key="board4_suit")
            
            with col_board5:
                board_ranks[4] = st.selectbox("リバーのランク:", ["", "A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"], key="board5_rank")
                board_suits[4] = st.selectbox("リバーのスート:", ["", "♠", "♥", "♦", "♣"], key="board5_suit")
            
            # Create board cards list for description
            for i in range(5):
                if board_ranks[i] and board_suits[i]:
                    board_cards.append((board_ranks[i], board_suits[i]))
        
        # Opponent count
        st.subheader("対戦相手")
        opponent_count = st.slider("対戦相手数:", 1, 8, 1)
        
        # Calculate button
        if st.button("勝率計算", type="primary"):
            # Check if we have valid hole cards
            if card1_rank and card1_suit and card2_rank and card2_suit:
                with st.spinner("計算中..."):
                    # Calculate win rate
                    win_rate_data = calculate_win_rate(
                        card1_rank, card1_suit, card2_rank, card2_suit,
                        board_ranks, board_suits, opponent_count, simulation_count
                    )
                    
                    if 'error' in win_rate_data and win_rate_data['error']:
                        st.error(win_rate_data['error'])
                    else:
                        # Display results
                        st.success("計算完了!")
                        
                        # Create and display chart
                        win_rate_chart = create_win_rate_chart(win_rate_data)
                        st.plotly_chart(win_rate_chart, use_container_width=True)
                        
                        # Display description
                        st.markdown(get_win_rate_description(
                            win_rate_data, card1_rank, card1_suit, card2_rank, card2_suit,
                            opponent_count, board_cards
                        ))
            else:
                st.error("ホールカードを入力してください。")
    else:
        # Desktop layout (side by side)
        # Load range data
        range_data = load_range_data(position, action, opponent_type)
        
        # Desktop layout (side by side)
        col1, col2 = st.columns([3, 2])
        
        # Column 1: Heatmap visualization first (as per user's latest feedback)
        with col1:
            st.markdown(f"""
            <div class="stCard">
                <h2>GTOレンジヒートマップ</h2>
                <p>
                    {create_tooltip("ポジション", poker_terms["ポジション"])}: <b>{position}</b> | 
                    {create_tooltip("アクション", poker_terms["アクション"])}: <b>{action}</b> | 
                    {create_tooltip("相手タイプ", poker_terms["相手タイプ"])}: <b>{opponent_type}</b>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create heatmap
            heatmap_fig = create_heatmap(range_data, position, action, opponent_type)
            st.plotly_chart(heatmap_fig, use_container_width=True)
        
        # Column 2: Hand input and analysis
        with col2:
            # Hand input section
            st.markdown("""
            <div class="stCard">
                <h2>ハンド分析</h2>
                <p>分析したいハンドを選択してください</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_hand1, col_hand2 = st.columns(2)
            
            with col_hand1:
                card1_rank = st.selectbox("1枚目のランク:", all_ranks, key="card1_rank")
                card1_suit = st.selectbox("1枚目のスート:", all_suits, key="card1_suit")
            
            with col_hand2:
                # For the second card, if the same rank is selected, don't allow the same suit
                card2_rank = st.selectbox("2枚目のランク:", all_ranks, key="card2_rank")
                
                # If same rank is selected, remove the suit that's already selected for the first card
                available_suits = all_suits.copy()
                if card1_rank == card2_rank:
                    if card1_suit in available_suits:
                        available_suits.remove(card1_suit)
                
                card2_suit = st.selectbox("2枚目のスート:", available_suits, key="card2_suit")
            
            # Get hand type
            hand_type = get_hand_type(card1_rank, card1_suit, card2_rank, card2_suit)
            st.markdown(f"""
            <div style="background-color: #f0f8ff; padding: 10px; border-radius: 5px; margin: 10px 0;">
                <h3 style="margin: 0;">選択したハンド: <b>{hand_type}</b></h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Convert display ranks to numeric ranks
            from utils.heatmap_utils import RANK_TO_NUM
            
            # Determine row and column in the matrix
            if card1_rank == card2_rank:  # Pocket pair
                # For pocket pairs, both row and column are the same rank
                row_idx = RANK_TO_NUM[card1_rank]
                col_idx = row_idx
            else:
                # Convert display ranks to numeric ranks
                rank1_num = RANK_TO_NUM[card1_rank]
                rank2_num = RANK_TO_NUM[card2_rank]
                
                # Determine if suited
                suited = card1_suit == card2_suit
                
                if suited:
                    # For suited hands, higher rank is row, lower rank is column
                    if rank1_num > rank2_num:
                        row_idx, col_idx = rank1_num, rank2_num
                    else:
                        row_idx, col_idx = rank2_num, rank1_num
                else:
                    # For offsuit hands, higher rank is column, lower rank is row
                    if rank1_num > rank2_num:
                        row_idx, col_idx = rank2_num, rank1_num
                    else:
                        row_idx, col_idx = rank1_num, rank2_num
            
            # Get frequency from range data
            try:
                frequency = range_data.loc[row_idx, col_idx]
                
                # Get standard GTO frequency (without opponent type adjustment)
                std_range_data = load_range_data(position, action, "標準")
                std_frequency = std_range_data.loc[row_idx, col_idx]
                
                # Display GTO analysis
                st.markdown(f"""
                <div class="stCard">
                    <h3>{create_tooltip("GTO", poker_terms["GTO"])}戦略分析</h3>
                    <p>{get_action_description(hand_type, frequency, position, action)}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Display exploit suggestion if opponent type is not standard
                if opponent_type != "標準":
                    st.markdown(f"""
                    <div class="stCard">
                        <h3>{create_tooltip("エクスプロイト", poker_terms["エクスプロイト"])}提案</h3>
                        <p>{get_exploit_suggestion(hand_type, std_frequency, frequency, opponent_type, action)}</p>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"有効なハンドを選択してください。エラー: {str(e)}")
            
            # Win rate calculator
            st.header("勝率シミュレーター")
            
            # Board input
            st.subheader("ボード")
            use_board = st.checkbox("ボードカードを指定", value=False)
            
            board_ranks = [""] * 5
            board_suits = [""] * 5
            board_cards = []
            
            if use_board:
                col_board1, col_board2, col_board3 = st.columns(3)
                
                with col_board1:
                    board_ranks[0] = st.selectbox("フロップ1のランク:", ["", "A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"], key="board1_rank")
                    board_suits[0] = st.selectbox("フロップ1のスート:", ["", "♠", "♥", "♦", "♣"], key="board1_suit")
                
                with col_board2:
                    board_ranks[1] = st.selectbox("フロップ2のランク:", ["", "A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"], key="board2_rank")
                    board_suits[1] = st.selectbox("フロップ2のスート:", ["", "♠", "♥", "♦", "♣"], key="board2_suit")
                
                with col_board3:
                    board_ranks[2] = st.selectbox("フロップ3のランク:", ["", "A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"], key="board3_rank")
                    board_suits[2] = st.selectbox("フロップ3のスート:", ["", "♠", "♥", "♦", "♣"], key="board3_suit")
                                
                col_board4, col_board5 = st.columns(2)
                
                with col_board4:
                    board_ranks[3] = st.selectbox("ターンのランク:", ["", "A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"], key="board4_rank")
                    board_suits[3] = st.selectbox("ターンのスート:", ["", "♠", "♥", "♦", "♣"], key="board4_suit")
                
                with col_board5:
                    board_ranks[4] = st.selectbox("リバーのランク:", ["", "A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"], key="board5_rank")
                    board_suits[4] = st.selectbox("リバーのスート:", ["", "♠", "♥", "♦", "♣"], key="board5_suit")
                
                # Create board cards list for description
                for i in range(5):
                    if board_ranks[i] and board_suits[i]:
                        board_cards.append((board_ranks[i], board_suits[i]))
            
            # Opponent count
            st.subheader("対戦相手")
            opponent_count = st.slider("対戦相手数:", 1, 8, 1)
            
            # Calculate button
            if st.button("勝率計算", type="primary"):
                # Check if we have valid hole cards
                if card1_rank and card1_suit and card2_rank and card2_suit:
                    with st.spinner("計算中..."):
                        # Calculate win rate
                        win_rate_data = calculate_win_rate(
                            card1_rank, card1_suit, card2_rank, card2_suit,
                            board_ranks, board_suits, opponent_count, simulation_count
                        )
                        
                        if 'error' in win_rate_data and win_rate_data['error']:
                            st.error(win_rate_data['error'])
                        else:
                            # Display results
                            st.success("計算完了!")
                            
                            # Create and display chart
                            win_rate_chart = create_win_rate_chart(win_rate_data)
                            st.plotly_chart(win_rate_chart, use_container_width=True)
                            
                            # Display description
                            st.markdown(get_win_rate_description(
                                win_rate_data, card1_rank, card1_suit, card2_rank, card2_suit,
                                opponent_count, board_cards
                            ))
                else:
                    st.error("ホールカードを入力してください。")

# Quiz Mode Tab
with tab2:
    st.header("ポーカー戦略クイズ")
    st.markdown("ランダムなシナリオでポーカー戦略を学習しましょう。正解と解説で理解を深めることができます。")
    
    # Generate random scenario
    if 'quiz_scenario' not in st.session_state:
        positions = ["UTG", "MP", "CO", "BTN", "SB", "BB"]
        actions = ["Open", "Call", "3Bet"]
        opponent_types = ["標準", "タイト", "ルーズ", "パッシブ", "アグレッシブ"]
        
        st.session_state.quiz_scenario = {
            "position": random.choice(positions),
            "action": random.choice(actions),
            "opponent_type": random.choice(opponent_types)
        }
    
    # Display scenario
    scenario_pos = st.session_state.quiz_scenario["position"]
    scenario_action = st.session_state.quiz_scenario["action"]
    scenario_opp = st.session_state.quiz_scenario["opponent_type"]
    
    st.subheader("シナリオ")
    
    # Visual representation of the poker table
    st.markdown(f"""
    ### テーブル状況
    
    あなたは **{scenario_pos}** ポジションにいます。
    
    **アクション**: {scenario_action}
    
    **相手タイプ**: {scenario_opp}
    """)
    
    # Load range data for this scenario
    quiz_range_data = load_range_data(scenario_pos, scenario_action, scenario_opp)
    
    # Generate random hand for quiz
    if 'quiz_hand' not in st.session_state:
        ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        suits = ["♠", "♥", "♦", "♣"]
        
        rank1 = random.choice(ranks)
        rank2 = random.choice(ranks)
        suit1 = random.choice(suits)
        suit2 = random.choice(suits)
        
        # Ensure the hand is valid (not the same card)
        while rank1 == rank2 and suit1 == suit2:
            rank2 = random.choice(ranks)
            suit2 = random.choice(suits)
        
        st.session_state.quiz_hand = {
            "rank1": rank1,
            "suit1": suit1,
            "rank2": rank2,
            "suit2": suit2
        }
    
    # Display the hand
    quiz_rank1 = st.session_state.quiz_hand["rank1"]
    quiz_suit1 = st.session_state.quiz_hand["suit1"]
    quiz_rank2 = st.session_state.quiz_hand["rank2"]
    quiz_suit2 = st.session_state.quiz_hand["suit2"]
    
    st.markdown(f"### あなたのハンド: **{quiz_rank1}{quiz_suit1} {quiz_rank2}{quiz_suit2}**")
    
    # Quiz question
    st.markdown(f"### 質問: このハンドでどうプレイしますか？")
    
    # Answer options
    answer = st.radio(
        "選択してください:",
        ["Raise/Bet", "Call", "Fold"],
        key="quiz_answer"
    )
    
    # Check answer button
    if st.button("回答を確認", type="primary"):
        # Get the correct GTO play
        hand_type = get_hand_type(quiz_rank1, quiz_suit1, quiz_rank2, quiz_suit2)
        
        # Convert display ranks to numeric ranks
        from utils.heatmap_utils import RANK_TO_NUM
        
        # Determine row and column in the matrix
        if quiz_rank1 == quiz_rank2:  # Pocket pair
            # For pocket pairs, both row and column are the same rank
            row_idx = RANK_TO_NUM[quiz_rank1]
            col_idx = row_idx
        else:
            # Convert display ranks to numeric ranks
            rank1_num = RANK_TO_NUM[quiz_rank1]
            rank2_num = RANK_TO_NUM[quiz_rank2]
            
            # Determine if suited
            suited = quiz_suit1 == quiz_suit2
            
            if suited:
                # For suited hands, higher rank is row, lower rank is column
                if rank1_num > rank2_num:
                    row_idx, col_idx = rank1_num, rank2_num
                else:
                    row_idx, col_idx = rank2_num, rank1_num
            else:
                # For offsuit hands, higher rank is column, lower rank is row
                if rank1_num > rank2_num:
                    row_idx, col_idx = rank2_num, rank1_num
                else:
                    row_idx, col_idx = rank1_num, rank2_num
        
        # Get frequency from range data
        frequency = quiz_range_data.iloc[row_idx, col_idx]
        
        # Determine correct answer based on frequency
        correct_answer = ""
        if scenario_action == "Open" or scenario_action == "3Bet":
            if frequency >= 0.7:
                correct_answer = "Raise/Bet"
            elif frequency >= 0.3:
                correct_answer = "Call"  # Mixed strategy
            else:
                correct_answer = "Fold"
        else:  # Call
            if frequency >= 0.7:
                correct_answer = "Call"
            elif frequency >= 0.3:
                correct_answer = "Call"  # Mixed strategy
            else:
                correct_answer = "Fold"
        
        # Display result
        if answer == correct_answer:
            st.success(f"正解です！ {hand_type}は{frequency:.0%}の頻度で{correct_answer}すべきハンドです。")
        else:
            st.error(f"不正解です。{hand_type}は{frequency:.0%}の頻度で{correct_answer}すべきハンドです。")
        
        # Explanation
        st.markdown("### 解説")
        st.markdown(get_action_description(hand_type, frequency, scenario_pos, scenario_action))
        
        # Show heatmap for reference
        st.subheader("参考: レンジヒートマップ")
        quiz_heatmap = create_heatmap(quiz_range_data, scenario_pos, scenario_action, scenario_opp)
        st.plotly_chart(quiz_heatmap, use_container_width=False)  # Set to False to prevent resizing
        
        # New quiz button
        if st.button("新しいクイズ"):
            # Reset session state to generate new quiz
            del st.session_state.quiz_scenario
            del st.session_state.quiz_hand
            st.experimental_rerun()


# Footer
st.markdown("---")
st.markdown("**注意**: このツールはポーカー学習を支援するためのものであり、実際のプレイでの結果を保証するものではありません。")