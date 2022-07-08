import core
import engine_analysis
import database

## this is code just for how I compile the PGN
## UPDATE -- MAY 15, 2022: I compiled the code into a bash file
# from subprocess import call
#
# def call_script(s):
#     print('calling \'{}\''.format(s))
#     call(s, shell=True)
#
# call_script("rm -f datasets/roudiere.pgn")
# call_script("cat datasets/{}-white.pgn datasets/{}-black.pgn > datasets/{}.pgn".format(core.user, core.user, core.user))

core.build_game_list(add_new=True)

print("\n[*] Generating evaluations for each game using Stockfish 14...")
engine_analysis.generate_evaluations_for_dataset()
new_evals = [_.replace('\n', '') for _ in open('datasets/evaluations.txt').readlines() if _ != '\n']

print("[*] Adding games to database...")
database.build_db(core.games_list, new_evals)

print("[*] Updating status of opponents...")
database.build_opp_country_table()
