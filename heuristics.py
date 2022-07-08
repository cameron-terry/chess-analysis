import core
import progress_bar
import numpy as np
import pandas as pd
import io, os
import basic_stats

def calculate_new_games_heuristic(win=True):
    df = core.dbt.get_wins_df() if win else core.dbt.get()
    calculated_games = core.dbt.get_by_column_name("game", "calculated_stats").values[:,0]

    game_links_heuristics = {}

    l = len(df)
    i = 1
    progress_bar.printProgressBar(0, l, prefix='(heuristics) Calculating heuristics for games:', suffix='Complete',
                                  length=50)
    for index, row in df.iterrows():
        if row["Link"] not in calculated_games:
                (white, w_stats), (black, b_stats) = basic_stats.get_stats_by_link(row["Link"])

                h_df = pd.DataFrame()
                game = core.chess.pgn.read_game(io.StringIO(row["PGN"]))
                j, board = basic_stats.count_moves(game)

                w_stats['cp_loss'] = [0] + w_stats['cp_loss']
                b_stats['cp_loss'] = b_stats['cp_loss'] + [0]
                largest_lst = max(len(w_stats['cp_loss']), len(b_stats['cp_loss']))
                h_df['move'] = [i for i in range(1, largest_lst + 1)]

                h_df[white] = [w_stats['cp_loss'][i] if i < len(w_stats['cp_loss']) else 0 for i in range(largest_lst)]
                h_df[black] = [b_stats['cp_loss'][i] if i < len(b_stats['cp_loss']) else 0 for i in range(largest_lst)]

                h_df['{}_blundercheck'.format(white)] = np.nan_to_num(h_df[white].shift(-1))
                h_df['{}_blundercheck'.format(black)] = np.nan_to_num(h_df[black].shift(1))

                h_df['white_luck'] = np.where(h_df[white] < h_df[black], 1, 0)
                h_df['white_opportunistic'] = np.where(h_df[white] <= h_df['{}_blundercheck'.format(black)], 1, 0)

                h_df['black_luck'] = np.where(h_df[black] < h_df['{}_blundercheck'.format(white)], 1, 0)
                h_df['black_opportunistic'] = np.where(h_df[black] <= h_df[white], 1, 0)

                # white_luck_percent = h_df['white_luck'].sum() / len(h_df['white_luck'])
                white_opportunistic_percent = h_df['white_opportunistic'].sum() / len(h_df['white_opportunistic'])
                # black_luck_percent = h_df['black_luck'].sum() / len(h_df['black_luck'])
                black_opportunistic_percent = h_df['black_opportunistic'].sum() / len(h_df['black_opportunistic'])

                if core.user == white:
                    game_links_heuristics[row["Link"]] = [j, w_stats["avg_cp_loss"],
                                                                 white_opportunistic_percent,
                                                                 1/w_stats["avg_cp_loss"] * white_opportunistic_percent]
                    game_links_heuristics[row["Link"]].append(row["Black"])
                    # print("{} not punished by {} %: {}".format(white, black, white_luck_percent))
                    # print("{} punished {} %: {}".format(white, black, white_opportunistic_percent))
                else:
                    game_links_heuristics[row["Link"]] = [j, b_stats["avg_cp_loss"],
                                                                 black_opportunistic_percent,
                                                                 1/b_stats["avg_cp_loss"]*black_opportunistic_percent]
                    game_links_heuristics[row["Link"]].append(row["White"])
                    # print("{} not punished by {} %: {}".format(black, white, black_luck_percent))
                    # print("{} punished {} %: {}".format(black, white, black_opportunistic_percent))
                game_links_heuristics[row["Link"]].append(row["Date"])

                progress_bar.printProgressBar(i + 1, l, prefix='(heuristics) Calculating heuristics for games:', suffix='Complete',
                                              length=50)
                i += 1

    glh_df = pd.DataFrame(game_links_heuristics).T

    if len(glh_df) == 0:
        progress_bar.printProgressBar(l, l, prefix='(heuristics) Calculating heuristics for games:',
                                      suffix='Complete',
                                      length=50)
        return

    glh_df['rank'] = [i + 1 for i in range(len(glh_df))]
    glh_df['description'] = None
    glh_df.columns = ['moves', 'cp_loss', 'punish_rate', 'smoothness', 'opponent', 'date', 'rank', 'description']

    glh_df_to_csv = glh_df.to_csv()
    with open('game_heuristics_new.csv', 'w') as glh_fp:
        glh_fp.write('game' + glh_df_to_csv)

    core.database.update_calculated_stats_table()
    os.remove('game_heuristics_new.csv')

def find_games_by_heuristic(moves=(-np.inf, np.inf), h=None, time_control=None):
    if time_control is not None:
        query = "select game,moves,cp_loss,punish_rate,smoothness,opponent,date,description from (select * from calculated_stats inner join games on games.link = calculated_stats.game) where TimeControl = {}".format(time_control)
        df = pd.read_sql_query(query, core.dbt.conn)
    else:
        df = core.dbt.get(db="calculated_stats")

    if h is None:
        h = 'cp_loss'

    indices = []
    for index, row in df.iterrows():
        if row['smoothness'] > 0 and moves[0] <= row['moves'] <= moves[1]:
            indices.append(index)

    glh_df = df.iloc[indices, :]

    reverse = True if '-' in h else False
    if 'cp_loss' in h:
        glh_df = glh_df.sort_values(by=['cp_loss'], ascending=not reverse)
    elif 'punish_rate' in h:
        glh_df = glh_df.sort_values(by=['punish_rate'], ascending=reverse)
    elif 'smoothness' in h:
        glh_df = glh_df.sort_values(by=['smoothness'], ascending=reverse)

    glh_df["rank"] = range(1, len(glh_df)+1)

    glh_df.to_csv('game_heuristics.csv', index=False)
    print(glh_df)

    # return {k: v for k, v in sorted(glh_df.items(), key=lambda item: item[1][h], reverse=reverse)}

if __name__ == '__main__':
    min_moves, max_moves = (11, 30)
    heuristic = 'smoothness'

    print('(heuristics) maximum smoothness of games between {} and {} moves'.format(min_moves, max_moves))
    calculate_new_games_heuristic()
    find_games_by_heuristic(h=heuristic, time_control='600')