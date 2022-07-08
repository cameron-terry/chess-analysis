helpers = None
spec = None

def get_total_games_by_filter(f, spec=None):
    filter_headers_dict = {}

    for game in helpers.games_list:
        try:
            key = game.headers[f]
            if (spec is not None and game.headers[spec[0]] == spec[1]) or spec is None:
                if key not in filter_headers_dict:
                    filter_headers_dict[key] = 1
                else:
                    filter_headers_dict[key] += 1
        except KeyError:  # means a game with no moves has been found
            print(game.headers["White"])
            print(game.headers["Black"])

    return filter_headers_dict