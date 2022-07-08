################### core.py #####################
# The fundamental building block of the project #
# Features:
# DatabaseTool -- connects to the database, provides functions for queries

import chess.pgn
import chess.svg
import database
import pandas as pd
import io


user = "roudiere"
games_list = []  # save games_list locally for faster and easier accessing (at cost of memory)


class DatabaseTool():
    def __init__(self):
        self.conn = database.conn
        self.cur = database.cur
        self.full_collection = self.get()

    # TODO: add derived filters
    def get(self, filters=None, db="games"):
        """
        Sample usage:
            dbt.get({"TimeControl": "600", "ECO": "C00", "Black": user, "Result": "0-1"})
                will return all French defense rapid games where I played as black and won
        :param filters: a dictionary of all filters to apply
        :return: DataFrame of games that match filter
        """
        if filters is not None:
            query = "SELECT * FROM {} WHERE ".format(db)
            for f in filters:
                query += "{} = {} AND ".format(f, "\'{}\'".format(filters[f]))
            query = query[:-len(" AND ")]  # remove extra " AND "

            df = pd.read_sql_query(query, self.conn)
            return df
        else:
            df = None
            if db == "games":
                df = pd.read_sql_query("SELECT * FROM games", self.conn)
            elif db == "calculated_stats":
                df = pd.read_sql_query("SELECT * FROM calculated_stats", self.conn)
            else:
                print("[!] database does not exist")
                exit(0)

            return df

    def get_by_column_name(self, col_name, table):
        query = "SELECT {} FROM {}".format(col_name, table)
        df = pd.read_sql_query(query, self.conn)
        return df

    def get_from_calculated_stats(self, link):
        query = "SELECT * FROM calculated_stats WHERE game = '{}'".format(link)
        df = pd.read_sql_query(query, self.conn)
        return df

    def get_by_line(self, line):
        found_matches = []
        df = self.get()
        for i in range(len(df)):
            pgn = df.iloc[i]["PGN"].split(' ')
            line_lst = line.split(' ')

            # create a list of indices where moves match, then return a DataFrame containing only the matching indices
            # idea from: https://datascience.stackexchange.com/questions/77033/creating-a-new-dataframe-with-specific-row-numbers-from-another
            moves_match = True
            for move in range(len(line_lst)):
                try:
                    if line_lst[move] != pgn[move]:
                        moves_match = False
                        break
                except IndexError:
                    moves_match = False
                    break

            if moves_match:
                found_matches.append(i)

        matches_df = df.iloc[found_matches, :]
        return matches_df

    def get_wins_df(self):
        df = self.get()

        wins_mask = ((df["White"] == user) & (df["Result"] == "1-0")) | (
                (df["Black"] == user) & (df["Result"] == "0-1"))

        wins_df = df[wins_mask]

        return wins_df

    def find_wins_by_move(self, move):
        wins_df = self.get_wins_df()

        indices = [_ for _ in range(len(wins_df)) if move in wins_df.iloc[_]["PGN"]]

        # https://datascience.stackexchange.com/questions/77033/creating-a-new-dataframe-with-specific-row-numbers-from-another
        return wins_df.iloc[indices, :]

def build_game_list(add_new=False):
    if add_new:
        updated_pgn = open("datasets/{}.pgn".format(user))
        links = list(pd.read_sql_query("SELECT Link FROM games", DatabaseTool().conn).values[:, 0])

        game = chess.pgn.read_game(updated_pgn)
        while game is not None:
            if game.headers["Link"] not in links:
                games_list.append(game)

            game = chess.pgn.read_game(updated_pgn)

        print("(core) {} new games found".format(len(games_list)))
    else:
        pgn = [io.StringIO(g) for g in dbt.get()["PGN"].values]
        for game in pgn:
            g_2 = chess.pgn.read_game(game)
            games_list.append(g_2)

dbt = DatabaseTool()
evals = dbt.get()["StateEvaluations"].values


def df_game_to_pgn(game: pd.Series):
    """
    Adds to a PGN file given a game from the database.
    :param game: entry in table 'games' from database
    :return: none (writes to PGN file named [user]_dbcopy.pgn)
    """

    # https://readthedocs.org/projects/python-chess/downloads/pdf/stable/
    # 8.2 PGN Parsing and Writing
    pgn_game = chess.pgn.read_game(io.StringIO(game.loc["PGN"]))

    for index in range(len(game)):
        pgn_game.headers[game.index[index]] = game.loc[game.index[index]]

    print(pgn_game, file=open('datasets/{}_dbcopy.pgn'.format(user), 'a'), end='\n\n')

def write_pgn_from_db():
    """
    Write a PGN from the database.
    :return: none (writes a PGN file to datasets named [user]_dbcopy.pgn
    """
    dbt = DatabaseTool()
    db = dbt.get()
    for i in range(len(db)):
        df_game_to_pgn(db.iloc[i])


if __name__ == '__main__':
    def show_dbt_get():
        # demonstrating dbt.get()
        print("Average opponent elo in games I won playing as white in the Alapin in rapid (10|0) games: ",
              int(dbt.get({"TimeControl": "600",
                           "ECO": "B22",
                           "White": user,
                           "Result": "1-0"})['BlackElo'].astype(int).mean()
                  )
              )

        # calculate score in specific variation (e.g. Scotch Gambit within C45
        wins = dbt.get({"ECO": "C45", "White": user, "Result": "1-0"})
        wins = len(wins.loc[wins["ECOUrl"].str.contains("Scotch-Gambit")])

        losses = dbt.get({"ECO": "C45", "White": user, "Result": "0-1"})
        losses = len(losses.loc[losses["ECOUrl"].str.contains("Scotch-Gambit")])

        draws = dbt.get({"ECO": "C45", "White": user, "Result": "1/2-1/2"})
        draws = len(draws.loc[draws["ECOUrl"].str.contains("Scotch-Gambit")])

        score = (wins + 0.5 * draws) / (wins + losses + draws)
        print("My score with the Scotch Gambit: {:.2f}%".format(score * 100))

    def show_dbt_get_by_line(line, color):

        line_df = dbt.get_by_line(line)

        def get_white():
            # https://stackoverflow.com/questions/36921951/truth-value-of-a-series-is-ambiguous-use-a-empty-a-bool-a-item-a-any-o
            # basically use bitwise and/or operations instead of "and", "or"
            white_wins = (line_df["Result"] == "1-0") & (line_df["White"] == "roudiere")
            white_draws = (line_df["Result"] == "1/2-1/2") & (line_df["White"] == "roudiere")
            white_losses = (line_df["Result"] == "0-1") & (line_df["White"] == "roudiere")

            # print(line_df[white_wins].to_string())
            return line_df[white_wins], line_df[white_draws], line_df[white_losses]

        def get_black():
            # https://stackoverflow.com/questions/36921951/truth-value-of-a-series-is-ambiguous-use-a-empty-a-bool-a-item-a-any-o
            # basically use bitwise and/or operations instead of "and", "or"
            black_wins = (line_df["Result"] == "0-1") & (line_df["Black"] == "roudiere")
            black_draws = (line_df["Result"] == "1/2-1/2") & (line_df["Black"] == "roudiere")
            black_losses = (line_df["Result"] == "1-0") & (line_df["Black"] == "roudiere")

            # print(line_df[black_wins].to_string())
            return line_df[black_wins], line_df[black_draws], line_df[black_losses]

        user_wins_df, user_draws_df, user_losses_df = get_black() if color == 'black' else get_white()

        score = (100 * len(user_wins_df) + 0.5 * len(user_draws_df)) / ((len(user_wins_df) + len(user_draws_df) + len(user_losses_df)))

        print("Score when playing {} as {}: {:.2f}%".format(line, color, score))


    lines = {
        "scotch_gambit": "1.e4 e5 2.Nf3 Nc6 3.d4 exd4 4.Bc4",
        "FE": "1.e4 e6 2.Nf3 d5 3.exd5 exd5 4.d4 Nc6 5.Bb5 a6 6.Bxc6+",
        "d4e6": "1.d4 e6"
    }

    show_dbt_get_by_line(lines["scotch_gambit"], 'white')
    show_dbt_get_by_line(lines["FE"], 'black')
    show_dbt_get_by_line(lines["d4e6"], 'black')
    # write_pgn_from_db()