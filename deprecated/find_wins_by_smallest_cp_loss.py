def find_wins_with_smallest_cp_loss(moves=(-np.inf, np.inf), ends_in_mate=False, f=None):
    game_links_cp_loss = {}
    for i, game in enumerate(helpers.games_list):
        if not ((game.headers["White"] == helpers.user and game.headers["Result"] == "1-0") or
                (game.headers["Black"] == helpers.user and game.headers["Result"] == "0-1")):
            continue

        conditions_met = True
        for spec_filter in f:
            if game.headers[spec_filter[0]] != spec_filter[1]:
                conditions_met = False
                break

        if not conditions_met:
            continue

        _, stats = get_test_game(i + 1, 'white') \
            if game.headers["White"] == helpers.user else get_test_game(i + 1, 'black')

        j, board = count_moves(game)
        if ends_in_mate and board.is_checkmate():
            if moves[0] < j < moves[1]:
                game_links_cp_loss[game.headers["Link"] +
                                   " ({} vs {})".format(game.headers["White"], game.headers["Black"])] \
                    = stats["avg_cp_loss"]
        elif not ends_in_mate:
            if moves[0] < j < moves[1]:
                game_links_cp_loss[game.headers["Link"] +
                                   " ({} vs {})".format(game.headers["White"], game.headers["Black"])] \
                    = stats["avg_cp_loss"]

    return {k: v for k, v in sorted(game_links_cp_loss.items(), key=lambda item: item[1])}