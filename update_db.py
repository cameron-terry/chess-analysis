import core
import engine_analysis
import database

core.build_game_list(add_new=True)

print("\n[*] Generating evaluations for each game using Stockfish 14...")
engine_analysis.generate_evaluations_for_dataset()
new_evals = [_.replace('\n', '') for _ in open('datasets/evaluations.txt').readlines() if _ != '\n']

print("[*] Adding games to database...")
database.build_db(core.games_list, new_evals)

print("[*] Updating status of opponents...")
database.build_opp_country_table()
