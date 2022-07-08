import io

import core
import chess.engine
import progress_bar

def generate_evaluations_for_dataset(games_list=core.games_list):
    if not len(games_list) > 0:  # check for empty dataset
        print('(engine) No games to analyze\n')
        exit(0)

    l = len(games_list)
    engine = chess.engine.SimpleEngine.popen_uci("/usr/local/opt/stockfish/bin/stockfish")

    # TODO: get Leela to work?
    # networks can be found here: http://training.lczero.org/networks/
    # also here (https://lczero.org/play/download/#macos) it says network 42850 is already loaded
    # engine = chess.engine.SimpleEngine.popen_uci("/usr/local/Cellar/lc0/0.27.0/bin/lc0")

    # generate evaluations for every position and save to a new file
    with open("datasets/evaluations.txt", "w") as eval_fp:
        try:
            progress_bar.printProgressBar(0, l, prefix='(engine) Analyzing games:', suffix='Complete', length=50)
            for i, game in enumerate(games_list):
                ev = iterate_through_moves(game, engine)
                for val in ev:
                    print(val, end="", file=eval_fp)
                    print(",", end="", file=eval_fp)
                print("\n", end="", file=eval_fp)
                progress_bar.printProgressBar(i + 1, l, prefix='(engine) Analyzing games:', suffix='Complete', length=50)
                # print("(engine) {}/{} evaluated".format(i+1, len(games_list)))
        except KeyboardInterrupt:
            engine.close()
            print("(engine) games computed: {}".format(i))
            exit(0)

    print("(engine) games computed: {}".format(l))
    engine.close()

def iterate_through_moves(game, engine, time=0.1):
    evaluations = []
    board = game.board()
    for move in game.mainline_moves():
        board.push(move)
        info = engine.analyse(board, chess.engine.Limit(time=time))
        evaluations.append(info["score"].white())  # to make analysis easier, only give white pov

    return evaluations


if __name__ == '__main__':
    pgn = core.dbt.get({"Link": "https://www.chess.com/game/live/36476433687"})["PGN"].values[0]
    game = core.chess.pgn.read_game(io.StringIO(pgn))

    # generate_evaluations_for_dataset()