import sqlite3
import sqlite3 as sq3
import urllib.error
import progress_bar

import pandas as pd
import pandas.io.sql

from datasets.scraping import get_opponent_country
conn = sq3.connect('datasets/chess_games.db')
cur = conn.cursor()

def build_db(games_lst, evals):
    conn = sq3.connect('datasets/chess_games.db')
    cur = conn.cursor()
    l = len(games_lst)

    progress_bar.printProgressBar(0, l, prefix='(database) Adding games, evals to database:', suffix='Complete', length=50)
    for i, game in enumerate(games_lst):
        move_list = []
        board = game.board()

        white = True
        j = 1
        for move in game.mainline_moves():
            if white:
                move_list.append(str(j) + "." + board.san(move))
                j += 1
            else:
                move_list.append(board.san(move))

            board.push(move)
            white = not white

        move_list_str = " ".join(move_list)

        try:
            cur.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (game.headers["Event"], game.headers["Site"], game.headers["Date"], game.headers["Round"], game.headers["White"],
                        game.headers["Black"], game.headers["Result"], game.headers["CurrentPosition"], game.headers["Timezone"], game.headers["ECO"],
                        game.headers["ECOUrl"], game.headers["UTCDate"], game.headers["UTCTime"], game.headers["WhiteElo"], game.headers["BlackElo"],
                        game.headers["TimeControl"], game.headers["Termination"], game.headers["StartTime"], game.headers["EndDate"], game.headers["EndTime"],
                         game.headers["Link"], move_list_str, evals[i]))
        except sqlite3.IntegrityError:
            continue
        except KeyError:
            print("[!] Game was probably abandoned early and has no ECO: ", game.headers["Link"])
            print("[!] Please remove this game from the dataset and rerun any code that calls this function.")
        except IndexError:
            continue

        progress_bar.printProgressBar(i + 1, l, prefix='(database) Adding games, evals to database:', suffix='Complete', length=50)

    conn.commit()
    conn.close()

def build_opp_country_table():
    conn = sq3.connect('datasets/chess_games.db')
    cur = conn.cursor()

    players_df = pd.read_sql_query("SELECT White, Black FROM games", conn)
    already_existing = pd.read_sql_query("SELECT username FROM players", conn).values[:,0]

    players = set(list(players_df['White'].values) + list(players_df['Black'].values))
    players = [_ for _ in players if _ != 'roudiere']

    not_found = []
    l = len(players)

    progress_bar.printProgressBar(0, l, prefix='(database) Updating opponent country table:', suffix='Complete',
                                  length=50)
    for i, p in enumerate(players):
        white_games = []
        black_games = []

        try:
            query = "SELECT * FROM games WHERE White = '{}'".format(p)
            white_games = pd.read_sql_query(query, conn)
        except pd.io.sql.DatabaseError:
            pass

        try:
            query = "SELECT * FROM games WHERE Black = '{}'".format(p)
            black_games = pd.read_sql_query(query, conn)
        except pd.io.sql.DatabaseError:
            pass

        wins, losses, draws = 0, 0, 0

        for game in range(len(white_games)):
            if white_games.iloc[game]['Result'] == '0-1':
                wins += 1
            elif white_games.iloc[game]['Result'] == '1-0':
                losses += 1
            else:
                draws += 1

        for game in range(len(black_games)):
            if black_games.iloc[game]['Result'] == '1-0':
                wins += 1
            elif black_games.iloc[game]['Result'] == '0-1':
                losses += 1
            else:
                draws += 1

        country = 'Unknown'
        no_change = False
        if p in already_existing:
            query = "SELECT * FROM players WHERE username = '{}'".format(p)
            p_df = pd.read_sql_query(query, conn)
            no_change = (p_df['wins'].values[0] == wins) and \
                        (p_df['losses'].values[0] == losses) and \
                        (p_df['draws'].values[0] == draws)

        if no_change:
            progress_bar.printProgressBar(i + 1, l, prefix='(database) Updating opponent country table:', suffix='Complete', length=50)
            continue
        elif p in already_existing:
            cur.execute("UPDATE players SET wins = ?, losses = ?, draws = ? WHERE username = ?",
                        (wins, losses, draws, p))
        else:
            try:
                country = get_opponent_country.get_country_of_origin(p)
            except urllib.error.HTTPError:
                not_found.append(p)

            cur.execute("INSERT INTO players VALUES (?, ?, ?, ?, ?)", (p, country, wins, losses, draws))

        conn.commit()
        progress_bar.printProgressBar(i + 1, l, prefix='(database) Updating opponent country table:', suffix='Complete', length=50)

    print("(database) opponents not found:", not_found if len(not_found) > 0 else None)
    conn.close()

def update_calculated_stats_table():
    conn = sq3.connect('datasets/chess_games.db')
    cur = conn.cursor()

    df = pd.read_csv("game_heuristics_new.csv")
    l = len(df)
    progress_bar.printProgressBar(0, l, prefix='(database) Updating "calculated_stats" table:', suffix='Complete',
                                  length=50)

    for index, row in df.iterrows():
        try:
            if row['moves'] > 1:
                cur.execute("INSERT INTO calculated_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (row['game'], row['moves'], row['cp_loss'],
                             row['punish_rate'], row['smoothness'], row['opponent'], row['date'], row['description']))
            else:
                cur.execute("INSERT INTO calculated_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (row['game'], row['moves'], row['cp_loss'],
                             row['punish_rate'], -1, row['opponent'], row['date'], row['description']))

        except sq3.IntegrityError:
            pass

        progress_bar.printProgressBar(index + 1, l, prefix='(database) Updating "calculated_stats" table:',
                                      suffix='Complete',
                                      length=50)

    conn.commit()

def update_descriptions_calculated_stats():
    descriptions_df = pd.read_csv("checked_games.csv")
    print(descriptions_df)
    for idx, row in descriptions_df.iterrows():
        cur.execute("UPDATE calculated_stats SET description = ? WHERE game = ?", (row["description"], row["link"]))

    conn.commit()

if __name__ == '__main__':
    # update_calculated_stats_table()
    update_descriptions_calculated_stats()