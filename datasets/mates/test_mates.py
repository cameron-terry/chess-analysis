from random import choice
mates = [_.replace('\n', '') for _ in open('mates4.txt', 'r').readlines()]
density_score = {}
for mate in mates:
    ds = 1
    fen_no_ply_info = mate.split("||")[0]  # remove ply information

    for char in fen_no_ply_info:
        if char.isdigit() and char != "0":
            ds *= int(char)
    density_score[mate] = 1 / ds

density_score = {k: v for k, v in sorted(density_score.items(), key=lambda item: item[1], reverse=True)}

for key, value in density_score.items():
    print(key, ':', value)

# while input("Press [enter] to continue, quit to stop: ") != "quit":
#     print(choice(mates3))
