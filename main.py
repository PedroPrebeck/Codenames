import streamlit as st
import sqlite3
import random
import os

# Function to initialize the database
def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            played BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()

# Function to get all unplayed words
def get_unplayed_words(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT word FROM words WHERE played = 0')
    unplayed_words = [row[0] for row in c.fetchall()]
    conn.close()
    return unplayed_words

# Function to get all words
def get_all_words(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT word, played FROM words')
    all_words = c.fetchall()
    conn.close()
    return all_words

# Function to add or remove a word
def add_or_remove_word(db_path, word):
    word = word.strip().upper()  # Normalize to uppercase
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT word FROM words WHERE word = ?', (word,))
    result = c.fetchone()
    if result:
        c.execute('DELETE FROM words WHERE word = ?', (word,))
        conn.commit()
        st.sidebar.success(f"Word '{word}' removed successfully!")
    else:
        try:
            c.execute('INSERT INTO words (word, played) VALUES (?, 0)', (word,))
            conn.commit()
            st.sidebar.success(f"Word '{word}' added successfully!")
        except sqlite3.IntegrityError:
            st.sidebar.error(f"Word '{word}' already exists.")
    conn.close()

# Function to mark words as played
def mark_words_as_played(db_path, words):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for word in words:
        c.execute('UPDATE words SET played = 1 WHERE word = ?', (word,))
    conn.commit()
    conn.close()

# Function to reset the word list
def reset_word_list(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('UPDATE words SET played = 0')
    conn.commit()
    conn.close()

# Function to update the word list from words.txt
def update_word_list(db_path, words_file):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    if os.path.exists(words_file):
        with open(words_file, 'r', encoding='utf-8') as file:
            words = file.read().splitlines()
        for word in words:
            word = word.strip().upper()  # Normalize to uppercase
            try:
                c.execute('INSERT INTO words (word, played) VALUES (?, 0)', (word,))
            except sqlite3.IntegrityError:
                pass  # Ignore if the word is already in the database
    conn.commit()
    conn.close()

# Function to pick 25 unique words and assign roles
def pick_words(words, team_with_9_words):
    selected_words = random.sample(words, 25)
    
    if team_with_9_words == 'Team 1':
        team_1_words = random.sample(selected_words, 9)
        remaining_words = list(set(selected_words) - set(team_1_words))
        team_2_words = random.sample(remaining_words, 8)
    else:
        team_2_words = random.sample(selected_words, 9)
        remaining_words = list(set(selected_words) - set(team_2_words))
        team_1_words = random.sample(remaining_words, 8)
    
    remaining_words = list(set(remaining_words) - set(team_1_words) - set(team_2_words))
    teamless_words = random.sample(remaining_words, 7)
    lose_turn_word = list(set(remaining_words) - set(teamless_words))[0]
    
    return selected_words, team_1_words, team_2_words, teamless_words, lose_turn_word

# Define paths
db_path = 'words.db'
words_file = 'words.txt'

# Initialize the database
init_db(db_path)

# Streamlit app setup
st.title("Codenames Game")

# Sidebar for word management
st.sidebar.title("Word Management")

# Buttons and descriptions for Reset and Update Word List
st.sidebar.write("### Manage Word List")
if st.sidebar.button("Reset Word List"):
    reset_word_list(db_path)
    st.sidebar.success("Word list has been reset!")
st.sidebar.write("Reset the word list to mark all words as not played.")

if st.sidebar.button("Update Word List"):
    update_word_list(db_path, words_file)
    st.sidebar.success("Word list has been updated!")
    st.sidebar.write("Update the word list to add words from 'words.txt' without duplicates.")

# Add/Remove word input
st.sidebar.write("### Add/Remove Word")
new_word = st.sidebar.text_input("Enter a new word").strip().upper().replace(" ", "")
if st.sidebar.button("Add/Remove"):
    if new_word and " " not in new_word:
        add_or_remove_word(db_path, new_word)
    else:
        st.sidebar.error("Please enter a valid single word without spaces.")

# Toggle to show all words or available words
show_all_words = st.sidebar.checkbox("Show all words", value=True)
if show_all_words:
    all_words = get_all_words(db_path)
    st.sidebar.write("### All Words")
    for word, played in all_words:
        status = "Played" if played else "Not Played"
        st.sidebar.write(f"{word} - {status}")
else:
    available_words = get_unplayed_words(db_path)
    st.sidebar.write("### Available Words")
    for word in available_words:
        st.sidebar.write(word)

if 'team_with_9_words' not in st.session_state:
    st.session_state.team_with_9_words = 0

# Define a callback function to toggle the team selection
def toggle_team_selection():
    if st.session_state.team_with_9_words == 0:
        st.session_state.team_with_9_words = 1
    else:
        st.session_state.team_with_9_words = 0

# Radio button to select the team with 9 cards, bind to session state
team_with_9_words = st.radio(
    "Select the team with 9 cards:",
    ('Team 1', 'Team 2'),
    index=0 if st.session_state.team_with_9_words == 0 else 1,
    horizontal=True,
    on_change=toggle_team_selection
)

if st.session_state.team_with_9_words == 0:
    first_team = 'Team 2'
else:
    first_team = 'Team 1'

if st.button("Generate New Board", on_click=toggle_team_selection):
    unplayed_words = get_unplayed_words(db_path)
    if len(unplayed_words) < 25:
        st.error("Not enough words in the list to generate a new board!")
    else:
        selected_words, team_1_words, team_2_words, teamless_words, lose_turn_word = pick_words(unplayed_words, first_team)

        # Mark the selected words as played
        mark_words_as_played(db_path, selected_words)
        
        # Display the board
        board = []
        for word in selected_words:
            if word in team_1_words:
                board.append((word, 'Team 1', '#1E90FF'))  # Blue
            elif word in team_2_words:
                board.append((word, 'Team 2', '#FF4500'))  # Red
            elif word in teamless_words:
                board.append((word, 'Teamless', '#7D7D7D'))  # Dark Gray
            elif word == lose_turn_word:
                board.append((word, 'Lose Turn', '#FFFFFF'))  # White
        
        random.shuffle(board)  # Shuffle the board to randomize word positions
        
        st.write("### Codenames Board")
        cols = st.columns(5)
        for i, (word, role, color) in enumerate(board):
            col = cols[i % 5]
            col.markdown(f"<div style='text-align: center; color: {color};'><strong>{word}</strong><br>({role})</div>", unsafe_allow_html=True)
            col.write("")

# Add a note to inform user about the word list refresh
# st.info("Ensure the words list is refreshed manually to have enough words for new rounds.")
