# merge_black_white_files.py
# merges PGNs from openingtree into one PGN
# inputs: roudiere-black.pgn, roudiere-white.pgn
# outputs: roudiere.pgn

# create new file
to_fp = open('roudiere.pgn', 'w')


# copy file into new file
def copy_into_new_file(pgn):
    with open(pgn, 'r') as from_fp:
        for line in from_fp:
            to_fp.write(line)


copy_into_new_file('roudiere-white.pgn')
copy_into_new_file('roudiere-black.pgn')

to_fp.close()
