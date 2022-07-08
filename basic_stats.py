import core
import numpy as np

def count_total_games(f=None):
    print("total games:", len(core.dbt.get(f)))

def count_moves(g):
    j = 0
    board = g.board()
    for move in g.mainline_moves():
        board.push(move)
        j += 1

    return np.ceil(j / 2), board

def basic_stats_from_eval(eval_lst, color):
    stats = {"cp_loss": [],
             "avg_cp_loss": 0,
             "inaccuracies": 0,
             "mistakes": 0,
             "blunders": 0}

    if color.lower() == 'white':
        stats["cp_loss"] = [abs(eval_lst[i + 1] - eval_lst[i]) if eval_lst[i + 1] < eval_lst[i] else 0
                            for i in range(1, len(eval_lst) - 1, 2)]
    elif color.lower() == 'black':
        stats["cp_loss"] = [abs(eval_lst[i + 1] - eval_lst[i]) if eval_lst[i + 1] > eval_lst[i] else 0
                            for i in range(0, len(eval_lst) - 1, 2)]

    stats["avg_cp_loss"] = np.nan_to_num(np.average(stats["cp_loss"]) / 100)

    # calculate inaccuracies, mistakes, blunders
    for i, cpl in enumerate(stats["cp_loss"]):
        # don't count inaccuracies, mistakes, blunders if a move is made that directly increases the advantage

        # move was more positive than the one before it
        if color == 'white' and eval_lst[2 * (i + 1)] > eval_lst[2 * (i + 1) - 1]:
            continue
        # move was more negative than the one before it
        elif color == 'black' and eval_lst[2 * (i + 1) - 1] < eval_lst[2 * (i + 1) - 2]:
            continue

        if cpl < 100:
            continue
        elif 100 <= cpl < 150:
            stats["inaccuracies"] += 1
        elif 150 <= cpl < 400:
            stats["mistakes"] += 1
        elif cpl >= 400:
            stats["blunders"] += 1

    return stats

def clean_eval_list(n):
    """
    Turn the nth evaluation list in chess_games.db from a string into a sequence of numbers
    especially fitted to encode smoothness with respect to calculating centipawn loss.
        e.g. "+12,+25,+47,+21,-65,-45,-300,-3500,-#3,-250,-249,+300,+#1,+#0" gets transformed into
             [12,25,47,21,-65,-45,-300,-3500,-3500,-250,-249,+300,+1800,+1800]

    Runtime: O(n)

    :param n: game number to choose
    :return: list of evaluations (ints)
    """
    # mark mates
    cp_limits = 1800

    eval_lst = core.evals[n - 1].split(",")

    eval_lst = [_ for _ in eval_lst if _ != '']
    eval_lst = [_ if "-#" not in _ else "black_mate" for _ in eval_lst]
    eval_lst = [_ if "#" not in _ else "white_mate" for _ in eval_lst]

    # calculate biggest advantages for either side
    biggest_black_adv = min([0 if _ in ["black_mate", "white_mate"] else int(_) for _ in eval_lst])
    biggest_white_adv = max([0 if _ in ["black_mate", "white_mate"] else int(_) for _ in eval_lst])

    # set mate to either max of position or 18 pawns if position is worse than 18 pawns (2 queens)
    eval_lst = [_ if _ != "black_mate" else str(min(-cp_limits, biggest_black_adv)) for _ in eval_lst]
    eval_lst = [_ if _ != "white_mate" else str(max(cp_limits, biggest_white_adv)) for _ in eval_lst]

    # convert to integers
    eval_lst = [int(_[1:]) if "+" in _ else int(_) for _ in eval_lst]

    return eval_lst

def get_test_game(x, color):
    player = "White" if color.lower() == 'white' else "Black"
    # get test game's eval
    return core.dbt.full_collection.iloc[x - 1][player], basic_stats_from_eval(clean_eval_list(x), color)

def get_stats_by_link(link):
    df = core.dbt.full_collection
    for index, row in df.iterrows():
        if df.iloc[index]["Link"] == link:
            white, w_stats = get_test_game(index + 1, 'white')
            black, b_stats = get_test_game(index + 1, 'black')

            return (white, w_stats), (black, b_stats)

    return -1