# HOW TO UPDATE DATABASE:

- place pgn file in datasets
- I use OpeningTree to pull my games, white and black
- then I run cat roudiere-white.pgn roudiere-black.pgn > roudiere.pgn
- run update_db.py :)

# HOW TO INSTALL ENGINE:

- run `brew install stockfish`

# HOW TO FIND ENGINE:

make sure you are in CHESS_ANALYSIS, and run:

`cd /usr/local/opt/`

# OPENINGS: DESCRIPTIVE INFORMATION

## how familiarity, sharpness, best are calculated

`familiarity = games / (avg_cp_loss / game)`

`sharpness = score / (avg_cp_loss / game)`

`best = familiarity _ sharpness / ||(familiarity, sharpness)||`

`= familiarity _ sharpness / (sqrt(familiarity**2 + sharpness**2))`

# GAME HEURISTICS

punish_rate: effectively when user's move deviated from best move less than the opponent's previous move

smoothness = punish_rate / avg_cp_loss

# CHESS ANALYSIS

This is an ongoing project, inspired from Lichess' analysis tools.
At the time of creation, Chess.com did not have an analysis feature, so I decided to implement some of the functions.
Additionally, this gave me the opportunity to analyze all of my games, which is a paid feature of Chess.com.

The folders enclosed contain the following tools:
--> datasets
_ This is where some of the generated data can be found, including:
--> mates
_ A collection of forced mates from my games.

Generated using calculate_forced_mates_in_n, found in chess_analysis.py
