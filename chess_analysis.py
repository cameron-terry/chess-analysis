import core
import io
import numpy as np
from scipy import ndimage
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import basic_stats
import progress_bar

# TODO: refactor to use database
def get_total_games_by_phase_end():
    """
    Counts the number of games that finish in the opening, middle, and endgame.
    :return: dictionary of games
    """
    if len(core.games_list) == 0:
        core.build_game_list()

    not_in_middlegame = []

    opening_ends = []
    opening_wins = 0
    for game in core.games_list:
        board = game.board()
        i = 0
        for move in game.mainline_moves():
            board.push(move)
            i += 1
        if i <= 24:
            if (game.headers["Result"] == "1-0" and game.headers["White"] == core.user) or \
                    (game.headers["Result"] == "0-1" and game.headers["Black"] == core.user):
                opening_wins += 1

            not_in_middlegame.append(game.headers["Link"])
            opening_ends.append(game)

    end_games = []
    endgame_wins = 0
    for game in core.games_list:
        end = game.end()
        board = end.board()
        fen = board.fen()
        major_minor_pieces_count = sum([fen.count(piece) for piece in 'RNBQrnbq'])
        if major_minor_pieces_count <= 6:
            if (game.headers["Result"] == "1-0" and game.headers["White"] == core.user) or \
                    (game.headers["Result"] == "0-1" and game.headers["Black"] == core.user):
                endgame_wins += 1

            not_in_middlegame.append(game.headers["Link"])
            end_games.append(game)

    middlegames = []
    middlegame_wins = 0
    for game in core.games_list:
        if game.headers["Link"] not in not_in_middlegame:
            if (game.headers["Result"] == "1-0" and game.headers["White"] == core.user) or \
                    (game.headers["Result"] == "0-1" and game.headers["Black"] == core.user):
                middlegame_wins += 1

            middlegames.append(game)

    return (opening_ends, opening_wins), (middlegames, middlegame_wins), (end_games, endgame_wins)

# TODO: move to another file
def calculate_wl_elo(opening_key, time_control):
    total_opponent_elo = int(core.dbt.get({"TimeControl": time_control,
                                              "ECO": opening_key, "White": core.user})
                             ['BlackElo'].astype(int).sum()
                             ) + \
                         int(core.dbt.get({"TimeControl": time_control,
                                              "ECO": opening_key, "Black": core.user})
                             ['WhiteElo'].astype(int).sum()
                             )

    white_wins = len(core.dbt.get({"TimeControl": time_control,
                                      "ECO": opening_key, "White": core.user,
                                      "Result": "1-0"})
                     )

    black_wins = len(core.dbt.get({"TimeControl": time_control,
                                      "ECO": opening_key, "Black": core.user,
                                      "Result": "0-1"})
                     )

    white_losses = len(core.dbt.get({"TimeControl": time_control,
                                        "ECO": opening_key, "White": core.user,
                                        "Result": "0-1"})
                       )

    black_losses = len(core.dbt.get({"TimeControl": time_control,
                                        "ECO": opening_key, "Black": core.user,
                                        "Result": "1-0"})
                       )

    draws = len(core.dbt.get({"TimeControl": time_control,
                                 "ECO": opening_key, "Result": "1/2-1/2"}))

    wins = white_wins + black_wins
    losses = white_losses + black_losses

    elo = int((total_opponent_elo + 400 * (wins - losses)) / (wins + losses + draws))

    return {
        "wins": wins,
        "white_wins": white_wins,
        "black_wins": black_wins,
        "losses": losses,
        "white_losses": white_losses,
        "black_losses": black_losses,
        "draws": draws,
        "score": (0.5 * draws + wins) / (wins + losses + draws),
        "elo": elo
    }


# TODO: move to another file
def get_all_forced_mates(game, eval_str, till_mate=""):
    board = game.board()
    e = eval_str.split(",")
    for i, move in enumerate(game.mainline_moves()):
        board.push(move)
        if ("#+{}".format(till_mate) in e[i] or "#-{}".format(till_mate) in e[i]) and not board.is_check():
            with open("datasets/mates/mates{}.txt".format(till_mate), "a") as f:
                f.write(board.fen() + "||" + game.headers["Link"])
                f.write("\n")
        else:
            pass


# TODO: move to another file
def get_castle_side(game, color):
    """
    returns the side that player [color] castled on
    :param game: id
    :param color: side to examine (White, Black)
    :return: 0 if kingside, 1 if queenside, -1 if none
    """
    board = game.board()
    for i, move in enumerate(game.mainline_moves()):
        move_str = board.san(move)
        # print("{}: {}".format(i, move_str))
        if color == "White":
            if i % 2 == 0:
                if move_str == 'O-O':
                    return 0
                elif move_str == 'O-O-O':
                    return 1
        elif color == "Black":
            if i % 2 == 1:
                if move_str == 'O-O':
                    return 0
                elif move_str == 'O-O-O':
                    return 1

        board.push(move)

    return -1


# TODO: move to another file
def get_user_castle_stats():
    castle_stats = {
        "wins": {
            "kingside": 0,
            "queenside": 0,
            "uncastled": 0
        },

        "losses": {
            "kingside": 0,
            "queenside": 0,
            "uncastled": 0
        },

        "draws": {
            "kingside": 0,
            "queenside": 0,
            "uncastled": 0
        }
    }

    spec_castle_stats = {
        "wins": {
            "O-O|O-O": 0,
            "O-O|O-O-O": 0,
            "O-O|none": 0,
            "O-O-O|O-O": 0,
            "O-O-O|O-O-O": 0,
            "O-O-O|none": 0,
            "none|O-O": 0,
            "none|O-O-O": 0,
            "none|none": 0
        },

        "losses": {
            "O-O|O-O": 0,
            "O-O|O-O-O": 0,
            "O-O|none": 0,
            "O-O-O|O-O": 0,
            "O-O-O|O-O-O": 0,
            "O-O-O|none": 0,
            "none|O-O": 0,
            "none|O-O-O": 0,
            "none|none": 0
        },

        "draws": {
            "O-O|O-O": 0,
            "O-O|O-O-O": 0,
            "O-O|none": 0,
            "O-O-O|O-O": 0,
            "O-O-O|O-O-O": 0,
            "O-O-O|none": 0,
            "none|O-O": 0,
            "none|O-O-O": 0,
            "none|none": 0
        }
    }

    for i in range(len(core.games_list)):
        if core.games_list[i].headers["White"] == core.user:
            castle_side_user = get_castle_side(core.games_list[i], "White")
            castle_side_opp = get_castle_side(core.games_list[i], "Black")
            if castle_side_user == 0:
                if core.games_list[i].headers["Result"] == "1-0":
                    castle_stats["wins"]["kingside"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["wins"]["O-O|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["wins"]["O-O|O-O-O"] += 1
                    else:
                        spec_castle_stats["wins"]["O-O|none"] += 1
                elif core.games_list[i].headers["Result"] == "0-1":
                    castle_stats["losses"]["kingside"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["losses"]["O-O|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["losses"]["O-O|O-O-O"] += 1
                    else:
                        spec_castle_stats["losses"]["O-O|none"] += 1
                else:
                    castle_stats["draws"]["kingside"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["draws"]["O-O|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["draws"]["O-O|O-O-O"] += 1
                    else:
                        spec_castle_stats["draws"]["O-O|none"] += 1
            elif castle_side_user == 1:
                if core.games_list[i].headers["Result"] == "1-0":
                    castle_stats["wins"]["queenside"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["wins"]["O-O-O|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["wins"]["O-O-O|O-O-O"] += 1
                    else:
                        spec_castle_stats["wins"]["O-O-O|none"] += 1
                elif core.games_list[i].headers["Result"] == "0-1":
                    castle_stats["losses"]["queenside"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["losses"]["O-O-O|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["losses"]["O-O-O|O-O-O"] += 1
                    else:
                        spec_castle_stats["losses"]["O-O-O|none"] += 1
                else:
                    castle_stats["draws"]["queenside"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["draws"]["O-O-O|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["draws"]["O-O-O|O-O-O"] += 1
                    else:
                        spec_castle_stats["draws"]["O-O-O|none"] += 1
            else:
                if core.games_list[i].headers["Result"] == "1-0":
                    castle_stats["wins"]["uncastled"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["wins"]["none|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["wins"]["none|O-O-O"] += 1
                    else:
                        spec_castle_stats["wins"]["none|none"] += 1
                elif core.games_list[i].headers["Result"] == "0-1":
                    castle_stats["losses"]["uncastled"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["wins"]["none|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["wins"]["none|O-O-O"] += 1
                    else:
                        spec_castle_stats["wins"]["none|none"] += 1
                else:
                    castle_stats["draws"]["uncastled"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["wins"]["none|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["wins"]["none|O-O-O"] += 1
                    else:
                        spec_castle_stats["wins"]["none|none"] += 1
        else:
            castle_side_user = get_castle_side(core.games_list[i], "Black")
            castle_side_opp = get_castle_side(core.games_list[i], "White")
            if castle_side_user == 0:
                if core.games_list[i].headers["Result"] == "0-1":
                    castle_stats["wins"]["kingside"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["wins"]["O-O|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["wins"]["O-O|O-O-O"] += 1
                    else:
                        spec_castle_stats["wins"]["O-O|none"] += 1
                elif core.games_list[i].headers["Result"] == "1-0":
                    castle_stats["losses"]["kingside"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["losses"]["O-O|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["losses"]["O-O|O-O-O"] += 1
                    else:
                        spec_castle_stats["losses"]["O-O|none"] += 1
                else:
                    castle_stats["draws"]["kingside"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["draws"]["O-O|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["draws"]["O-O|O-O-O"] += 1
                    else:
                        spec_castle_stats["draws"]["O-O|none"] += 1
            elif castle_side_user == 1:
                if core.games_list[i].headers["Result"] == "0-1":
                    castle_stats["wins"]["queenside"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["wins"]["O-O-O|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["wins"]["O-O-O|O-O-O"] += 1
                    else:
                        spec_castle_stats["wins"]["O-O-O|none"] += 1
                elif core.games_list[i].headers["Result"] == "1-0":
                    castle_stats["losses"]["queenside"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["losses"]["O-O-O|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["losses"]["O-O-O|O-O-O"] += 1
                    else:
                        spec_castle_stats["losses"]["O-O-O|none"] += 1
                else:
                    castle_stats["draws"]["queenside"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["draws"]["O-O-O|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["draws"]["O-O-O|O-O-O"] += 1
                    else:
                        spec_castle_stats["draws"]["O-O-O|none"] += 1
            else:
                if core.games_list[i].headers["Result"] == "0-1":
                    castle_stats["wins"]["uncastled"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["wins"]["none|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["wins"]["none|O-O-O"] += 1
                    else:
                        spec_castle_stats["wins"]["none|none"] += 1
                elif core.games_list[i].headers["Result"] == "1-0":
                    castle_stats["losses"]["uncastled"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["losses"]["none|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["losses"]["none|O-O-O"] += 1
                    else:
                        spec_castle_stats["losses"]["none|none"] += 1
                else:
                    castle_stats["draws"]["uncastled"] += 1
                    if castle_side_opp == 0:
                        spec_castle_stats["draws"]["none|O-O"] += 1
                    elif castle_side_opp == 1:
                        spec_castle_stats["draws"]["none|O-O-O"] += 1
                    else:
                        spec_castle_stats["draws"]["none|none"] += 1

    df = pd.DataFrame.from_dict(castle_stats)
    df["score"] = (df["wins"] + 0.5 * df["draws"]) / (df["wins"] + df["losses"] + df["draws"])

    df2 = pd.DataFrame.from_dict(spec_castle_stats)
    df2["score"] = (df2["wins"] + 0.5 * df2["draws"]) / (df2["wins"] + df2["losses"] + df2["draws"])

    return df, df2


# TODO: move to another file
def get_pawn_moves(game, evals, color):
    board = game.board()
    bs = basic_stats.basic_stats_from_eval(basic_stats.clean_eval_list(evals), color)

    opening = []
    middle = []
    end = []

    for i, move in enumerate(game.mainline_moves()):
        if color == "White" and i % 2 == 0:
            if board.piece_type_at(move.from_square) == core.chess.PAWN:
                # print("move: {}, cp_loss: {}".format(board.san(move), bs['cp_loss'][i//2]))
                fen = board.fen()
                try:
                    if i <= 20:
                        opening.append(bs['cp_loss'][i//2])
                    elif sum([fen.count(piece) for piece in 'RNBQrnbq']) <= 6:
                        end.append(bs['cp_loss'][i//2])
                    else:
                        middle.append(bs['cp_loss'][i//2])
                except IndexError:
                    pass

        elif color == "Black" and i % 2 == 1:
            if board.piece_type_at(move.from_square) == core.chess.PAWN:
                # print("move: {}, cp_loss: {}".format(board.san(move), bs['cp_loss'][i // 2]))

                fen = board.fen()
                try:
                    if i <= 20:
                        opening.append(bs['cp_loss'][i // 2])
                    elif sum([fen.count(piece) for piece in 'RNBQrnbq']) <= 6:
                        end.append(bs['cp_loss'][i // 2])
                    else:
                        middle.append(bs['cp_loss'][i // 2])
                except IndexError:
                    pass

        board.push(move)

    opening_avg_diff = np.nan if len(opening) == 0 else sum(opening)/len(opening)
    middle_avg_diff = np.nan if len(middle) == 0 else sum(middle)/len(middle)
    end_avg_diff = np.nan if len(end) == 0 else sum(end)/len(end)

    return np.array([opening_avg_diff, middle_avg_diff, end_avg_diff])


# TODO: move to another file
def get_all_games_pawn_moves():
    total_acc = np.array([get_pawn_moves(core.games_list[j], j+1, "White")
                          if core.games_list[j].headers["White"] == core.user
                          else get_pawn_moves(core.games_list[j], j+1, "Black")
                          for j in range(len(core.games_list))])

    all_games_pm = pd.DataFrame(total_acc, columns=['opening', 'middle', 'end'])
    print(all_games_pm.opening.mean())
    print(all_games_pm.middle.mean())
    print(all_games_pm.end.mean())


# TODO: move to another file
def queen_trade_before_endgame(game, color):
    board = game.board()

    for i, move in enumerate(game.mainline_moves()):
        if color == "White":
            if board.piece_type_at(move.from_square) == core.chess.QUEEN and \
                    board.piece_type_at(move.to_square) == core.chess.QUEEN and i % 2 == 0:

                fen = board.fen()
                major_minor_pieces_count = sum([fen.count(piece) for piece in 'RNBQrnbq'])
                if major_minor_pieces_count > 6:
                    return 1
                else:
                    return -1
        else:
            if board.piece_type_at(move.from_square) == core.chess.QUEEN and \
                    board.piece_type_at(move.to_square) == core.chess.QUEEN and i % 2 == 1:

                fen = board.fen()
                major_minor_pieces_count = sum([fen.count(piece) for piece in 'RNBQrnbq'])
                if major_minor_pieces_count > 6:
                    return 1
                else:
                    return -1

        board.push(move)
    return 0


# TODO: move to another file
def get_queen_trade_before_endgame_score():
    qtbe_wins, qtbe_draws, qtbe_losses, qtbe_total_avg_cp_loss = 0, 0, 0, 0
    nqtbe_wins, nqtbe_draws, nqtbe_losses, nqtbe_total_avg_cp_loss = 0, 0, 0, 0
    for i, g in enumerate(core.games_list):
        c = "White" if g.headers["White"] == core.user else "Black"
        qtbe = queen_trade_before_endgame(g, c)
        bs = basic_stats.basic_stats_from_eval(basic_stats.clean_eval_list(i + 1), c)
        if qtbe == 1:
            qtbe_total_avg_cp_loss = qtbe_total_avg_cp_loss if bs['avg_cp_loss'] == np.nan else \
                qtbe_total_avg_cp_loss + bs['avg_cp_loss']
            if g.headers["Result"] == "1-0" and c == "White":
                qtbe_wins += 1
            elif g.headers["Result"] == "0-1" and c == "Black":
                qtbe_wins += 1
            elif g.headers["Result"] == "1-0" and c == "Black":
                qtbe_losses += 1
            elif g.headers["Result"] == "0-1" and c == "White":
                qtbe_losses += 1
            elif g.headers["Result"] == "1/2-1/2":
                qtbe_draws += 1
        else:
            nqtbe_total_avg_cp_loss = nqtbe_total_avg_cp_loss if bs['avg_cp_loss'] == np.nan else \
                nqtbe_total_avg_cp_loss + bs['avg_cp_loss']
            if g.headers["Result"] == "1-0" and c == "White":
                nqtbe_wins += 1
            elif g.headers["Result"] == "0-1" and c == "Black":
                nqtbe_wins += 1
            elif g.headers["Result"] == "1-0" and c == "Black":
                nqtbe_losses += 1
            elif g.headers["Result"] == "0-1" and c == "White":
                nqtbe_losses += 1
            elif g.headers["Result"] == "1/2-1/2":
                nqtbe_draws += 1

    print("When I trade queens before the endgame: ")
    print("wins: {}, losses: {}, draws: {}".format(qtbe_wins, qtbe_losses, qtbe_draws))
    print("score: {}".format((qtbe_wins + 0.5 * qtbe_draws) / (qtbe_wins + qtbe_losses + qtbe_draws)))
    print("overall average cp_loss: {}".format(qtbe_total_avg_cp_loss / (qtbe_wins + qtbe_losses + qtbe_draws)))

    print("="*20)

    print("When I don't trade queens before the endgame: ")
    print("wins: {}, losses: {}, draws: {}".format(nqtbe_wins, nqtbe_losses, nqtbe_draws))
    print("score: {}".format((nqtbe_wins + 0.5 * nqtbe_draws) / (nqtbe_wins + nqtbe_losses + nqtbe_draws)))
    print("overall average cp_loss: {}".format(nqtbe_total_avg_cp_loss / (nqtbe_wins + nqtbe_losses + nqtbe_draws)))

# TODO: move to another file
def square_usage_by_win():
    dbt = core.DatabaseTool()
    wins_df = dbt.get_wins_df()
    squares_white = {}
    squares_black = {}
    squares = {}

    for _ in range(len(wins_df)):
        move_pgn = core.chess.pgn.read_game(io.StringIO(wins_df.iloc[_]["PGN"]))
        board = move_pgn.board()

        user_color = core.chess.WHITE if wins_df.iloc[_]["White"] == core.user else core.chess.BLACK
        user_color_name = "white" if wins_df.iloc[_]["White"] == core.user else "black"

        for move in move_pgn.mainline_moves():
            if board.turn == user_color:
                san = board.san(move)\
                    .replace("+", "")\
                    .replace("#", "")\
                    .replace("=Q", "")\
                    .replace("=N", "")\
                    .replace("=R", "")\
                    .replace("=B", "")

                edited_san = san[-2:]

                san_trans_dict = {
                    "O-O_white": ["f1", "g1"],
                    "O-O-O_white": ["c1", "d1"],
                    "O-O_black": ["f8", "g8"],
                    "O-O-O_black": ["c8", "d8"]
                }

                try:
                    san_lookup = san_trans_dict[san + "_" + user_color_name]
                    for square in san_lookup:
                        if user_color == core.chess.WHITE:
                            try:
                                squares_white[square] += 1
                            except KeyError:
                                squares_white[square] = 1
                        else:
                            try:
                                squares_black[square] += 1
                            except KeyError:
                                squares_black[square] = 1

                        try:
                            squares[square] += 1
                        except KeyError:
                            squares[square] = 1

                except KeyError:
                    if user_color == core.chess.WHITE:
                        try:
                            squares_white[edited_san] += 1
                        except KeyError:
                            squares_white[edited_san] = 1
                    else:
                        try:
                            squares_black[edited_san] += 1
                        except KeyError:
                            squares_black[edited_san] = 1

                    try:
                        squares[edited_san] += 1
                    except KeyError:
                        squares[edited_san] = 1

            board.push(move)

    # Make a 8x8 grid...
    nrows, ncols = 8, 8
    image_white = np.zeros(nrows * ncols)
    image_black = np.zeros(nrows * ncols)
    image = np.zeros(nrows * ncols)

    # https://www.delftstack.com/howto/matplotlib/how-to-display-multiple-images-in-one-figure-correctly-in-matplotlib/

    # Set cells to value (from white POV)
    let_to_num = {"a": 8, "b": 7, "c": 6, "d": 5, "e": 4, "f": 3, "g": 2, "h": 1}

    for sq in squares_white:
        image_white[(8 - int(sq[1])) * 8 + (8 - let_to_num[sq[0]])] = squares_white[sq]

    for sq in squares_black:
        image_black[(8 - int(sq[1])) * 8 + (8 - let_to_num[sq[0]])] = squares_black[sq]

    for sq in squares:
        image[(8 - int(sq[1])) * 8 + (8 - let_to_num[sq[0]])] = squares[sq]

    # Reshape things into a 8x8 grid.
    image_white = image_white.reshape((nrows, ncols))
    image_black = ndimage.rotate(image_black.reshape((nrows, ncols)), 180)
    image = image.reshape((nrows, ncols))

    images = [image_white, image_black, image]
    subplot_names = ["White", "Black", "Both"]

    row_labels = list(range(nrows, 0, -1))
    col_labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

    axes = []
    fig = plt.figure()

    # plt.xticks(range(ncols), col_labels)
    # plt.yticks(range(nrows), row_labels)

    # https://www.delftstack.com/howto/matplotlib/how-to-hide-axis-text-ticks-and-or-tick-labels-in-matplotlib/
    for a in range(3):
        axes.append(fig.add_subplot(1, 3, a+1))
        subplot_title = (subplot_names[a])
        axes[-1].set_title(subplot_title)
        axes[-1].xaxis.set_ticks(range(ncols))
        axes[-1].yaxis.set_ticks(range(nrows))

        if subplot_title == 'Black':
            axes[-1].xaxis.set_ticklabels(col_labels[::-1])
            axes[-1].yaxis.set_ticklabels(row_labels[::-1])
        else:
            axes[-1].xaxis.set_ticklabels(col_labels)
            axes[-1].yaxis.set_ticklabels(row_labels)

        plt.imshow(images[a])

    fig.tight_layout()

    plt.show()

def score_by_time():
    df = core.dbt.get()
    # https://stackoverflow.com/questions/49561989/pandas-rounding-to-nearest-hour
    df['hour'] = pd.to_datetime(df['StartTime']).dt.round('H').dt.hour
    dfh = df.groupby(['hour'])

    hour_histogram = {
        "hour": [_ for _ in range(24)],
        "score": [0 for _ in range(24)]
    }

    for key, item in dfh:
        group = dfh.get_group(key)
        wins = len(group[((group["White"] == core.user) & (group["Result"] == "1-0")) | ((group["Black"] == core.user) & (group["Result"] == "0-1"))])
        losses = len(group[((group["White"] == core.user) & (group["Result"] == "0-1")) | ((group["Black"] == core.user) & (group["Result"] == "1-0"))])
        draws = len(group[group["Result"] == "1/2-1/2"])

        score = ((wins + 0.5 * draws) / (wins + losses + draws))

        hour_histogram["score"][group['hour'].values[0]] = score

    hour_histogram_df = pd.DataFrame(hour_histogram["score"], index=["8PM", "9PM", "10PM", "11PM", "12AM", "1AM", "2AM", "3AM", "4AM", "5AM", "6AM", "7AM",
                                                                     "8AM", "9AM", "10AM", "11AM", "12PM", "1PM", "2PM", "3PM", "4PM", "5PM", "6PM", "7PM"])
    hour_histogram_df.columns = ['hour']
    print(hour_histogram_df)
    hour_histogram_df.plot(kind='bar')
    plt.show()

if __name__ == "__main__":
    def plot_evaluation_chart(eval_lst):
        df = pd.DataFrame(dict(ply=np.arange(1, len(core.evals) + 1), advantage=np.array(eval_lst)))
        sns.relplot(x="ply", y="advantage", kind="line", data=df)
        plt.axvline(16, 0, 10)

        plt.title("rligloo (1180) vs roudiere (1124) 0-1")
        plt.show()

    def plot_accuracy_chart(link):
        (white, w_stats), (black, b_stats) = basic_stats.get_stats_by_link(link)

        df = pd.DataFrame()

        w_stats['cp_loss'] = [0] + w_stats['cp_loss']   # why does this need to be zero padded in this way?
        b_stats['cp_loss'] = b_stats['cp_loss'] + [0]   # why does this need to be zero padded in this way?
        largest_lst = max(len(w_stats['cp_loss']), len(b_stats['cp_loss']))
        df['move'] = [i for i in range(1, largest_lst + 1)]

        df[white] = [w_stats['cp_loss'][i] if i < len(w_stats['cp_loss']) else 0 for i in range(largest_lst)]
        df[black] = [b_stats['cp_loss'][i] if i < len(b_stats['cp_loss']) else 0 for i in range(largest_lst)]

        fig, ax1 = plt.subplots(figsize=(10, 10))
        tidy = df.melt(id_vars='move').rename(columns=str.title)
        sns.barplot(x='Move', y='Value', hue='Variable', data=tidy, ax=ax1)
        sns.despine(fig)

        plt.show()

    # show histogram of openings
    def get_most_played_openings(f):
        return {k: v for k, v in sorted(core.dbt.get(f).groupby(by=['ECO']).count()["Event"].to_dict().items(),
                                        key=lambda item: item[1], reverse=True)}


    def calc_all_openings_basic_stats(f=None, time_control="600"):
        df = core.dbt.get()
        all_openings = {}
        most_played_openings = get_most_played_openings(f)
        core.build_game_list()

        l = len(most_played_openings.keys())

        progress_bar.printProgressBar(0, l, prefix='(analysis) Finding games for all ECO codes:',
                                      suffix='Complete',
                                      length=50)

        t = 0
        for key in most_played_openings:
            wl_elo_dict = calculate_wl_elo(key, time_control=time_control)
            all_openings[key] = {
                "games": most_played_openings[key],
                "elo": wl_elo_dict["elo"],
                "score": wl_elo_dict["score"],
                "white_win_percent": np.nan,
                "black_win_percent": np.nan,
                "avg_cp_loss/game": 0,
                "inaccuracies/game": 0,
                "mistakes/game": 0,
                "blunders/game": 0
            }

            try:
                all_openings[key]["white_win_percent"] = \
                    wl_elo_dict["white_wins"] / (wl_elo_dict["white_wins"] + wl_elo_dict["white_losses"])
            except ZeroDivisionError:
                pass
            try:
                all_openings[key]["black_win_percent"] = \
                    wl_elo_dict["black_wins"] / (wl_elo_dict["black_wins"] + wl_elo_dict["black_losses"])
            except ZeroDivisionError:
                pass

            total_avg_cp_loss, total_inaccuracies, total_mistakes, total_blunders = 0, 0, 0, 0
            total_games = all_openings[key]["games"]

            for i, game in enumerate(core.games_list):
                try:
                    if df.iloc[i]["ECO"] == key:
                        if (f is not None and df.iloc[i]["TimeControl"] == f["TimeControl"]) or f is None:
                            _, stats = basic_stats.get_test_game(i + 1, 'white') if game.headers["White"] == core.user else \
                                basic_stats.get_test_game(i + 1, 'black')

                            if len(stats['cp_loss']) == 0:
                                continue

                            total_avg_cp_loss += stats["avg_cp_loss"]
                            total_inaccuracies += stats["inaccuracies"]
                            total_mistakes += stats["mistakes"]
                            total_blunders += stats["blunders"]
                except KeyError:  # game was abandoned before an opening was determined
                    continue
                except IndexError:
                    continue

            all_openings[key]["avg_cp_loss/game"] = total_avg_cp_loss / total_games
            all_openings[key]["inaccuracies/game"] = total_inaccuracies / total_games
            all_openings[key]["mistakes/game"] = total_mistakes / total_games
            all_openings[key]["blunders/game"] = total_blunders / total_games

            progress_bar.printProgressBar(t+1, l, prefix='(analysis) Finding games for all ECO codes:',
                                          suffix='Complete',
                                          length=50)
            t += 1

        # save data
        all_openings_csv = pd.DataFrame(all_openings).to_csv()

        if f is None:
            f = {"TimeControl", "all"}

        with open("datasets/openings/all_openings_basic_stats{}.csv".format("TimeControl_" + f["TimeControl"]),
                  "w") as aocsv:
            aocsv.write("opening" + all_openings_csv)


    def calculate_game_stage_basic_stats():
        (ogs, ows), (mgs, mws), (egs, ews) = get_total_games_by_phase_end()

        print("Opening game endings: ", len(ogs) / len(core.games_list))
        print("Opening game ending wins: ", ows / len(ogs))

        print("Middlegame endings: ", len(mgs) / len(core.games_list))
        print("Middlegame ending wins: ", mws / len(mgs))

        print("Endgame endings: ", len(egs) / len(core.games_list))
        print("Endgame ending wins: ", ews / len(egs))


    def calculate_forced_mates_in_n(n='4'):
        for i in range(len(core.games_list)):
            test_game, _ = basic_stats.get_test_game(i + 1, 'black')  # doesn't matter which color we are looking at -- no stats
            get_all_forced_mates(test_game, core.evals[i], till_mate=n)


    def show_descriptive_stats_by_opening(f, n=1):
        eco_codes_df = pd.read_csv("datasets/scraping/eco_codes.csv")
        all_openings_df = pd.read_csv(
            "datasets/openings/all_openings_basic_stats{}.csv".format("TimeControl_" + f["TimeControl"]))

        # get all opening names from all_openings_df
        opening_names = [opening + "--" + eco_codes_df.loc[eco_codes_df['ECO'] == opening]['opening'].values[0] for
                         opening in all_openings_df.columns if
                         not eco_codes_df.loc[eco_codes_df['ECO'] == opening]['opening'].empty]

        all_openings_df = all_openings_df.set_index('opening').T
        all_openings_df.index = opening_names

        all_openings_df['familiarity'] = np.sqrt(all_openings_df['games']) / all_openings_df['avg_cp_loss/game']
        all_openings_df['sharpness'] = all_openings_df['score'] / all_openings_df['avg_cp_loss/game']
        all_openings_df['best'] = all_openings_df['familiarity'] * all_openings_df['sharpness'] / \
                                  (np.sqrt(all_openings_df['familiarity']**2 + all_openings_df['sharpness']**2))

        all_openings_df = all_openings_df.sort_values(['best'], ascending=False)

        at_least_n = all_openings_df['games'] >= n
        all_openings_df_games_filtered = all_openings_df[at_least_n]

        last_played = []
        for opening in all_openings_df_games_filtered.index:
            games = core.dbt.get({
                "ECO": opening[:3],
                "TimeControl": f["TimeControl"]
            })

            last_played.append(games['Date'].max())

        last_played = pd.Series(last_played)
        last_played.index = all_openings_df_games_filtered.index

        all_openings_df_games_filtered.insert(2, 'last_played', last_played)
        print(all_openings_df_games_filtered.to_string())

        all_openings_df_games_filtered_csv = all_openings_df_games_filtered.to_csv()
        file_name = "datasets/openings/all_openings_descriptive_stats{}.csv".format("TimeControl_" + f["TimeControl"])
        with open(file_name, 'w') as aocsv:
            aocsv.write("opening" + all_openings_df_games_filtered_csv)

    # test functions
    # score_by_time()

    # 1. for testing lookup / search function
    # print(get_most_played_openings([["TimeControl", "600"]]))
    # print(find_wins_by_move("Nf5").to_string())
    # square_usage_by_win()
    # gets smoothest wins that are 12-25 moves long (excluding most games that are decisive after 4-5 moves)
    # find_games_by_heuristic(h='smoothness', moves=(12, 25)) # , line="1.e4 e5 2.Nf3 Nc6 3.d4 exd4 4.Bc4"
    # for getting castle stats
    # castle_stats, spc = get_user_castle_stats()
    # print(castle_stats)
    # print('\n')
    # print(spc.sort_values(by='score', ascending=False))
    # get_all_games_pawn_moves()
    # get_queen_trade_before_endgame_score()

    # 2. for getting individual stats of games
    # sample_games = {"Emiya_kisuke": "https://www.chess.com/game/live/16848914483",
    #                 "rligloo": "https://www.chess.com/game/live/18914145515",
    #                 "nabil19661102": "https://www.chess.com/game/live/15609216859",
    #                 "EtherealArk": "https://www.chess.com/game/live/35094592177",
    #                 "Bizon1960": "https://www.chess.com/game/live/35243769603",
    #                 "tiago_2013": "https://www.chess.com/game/live/35684762057",
    #                 "MarchingBagpipe": "https://www.chess.com/game/live/36105058111"}
    #
    # (white, w_stats), (black, b_stats) = get_stats_by_link(sample_games["MarchingBagpipe"])
    # print('white: {}, stats: {}'.format(white, w_stats))
    # print('black: {}, stats: {}'.format(black, b_stats))

    # 3. for building spreadsheet
    calc_all_openings_basic_stats({"TimeControl": "300"}, time_control="300")
    show_descriptive_stats_by_opening({"TimeControl": "300"}, n=3)
