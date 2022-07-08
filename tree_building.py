import core
import re

class OpeningTree:
    class Node:
        def __init__(self):
            self.move = None
            self.depth = None
            self.n = 0
            self.wins = 0
            self.losses = 0
            self.draws = 0

            self.children = []
            
        def score(self):
            return (self.wins + 0.5 * self.draws) / self.n

    def __init__(self):
        self.root = None
        self.move_names = []
        self.nodes_at_depths = {}
        
    def create_node(self, move, depth, res, parent_node):
        node = self.Node()
        node.move = move
        node.depth = depth
        node.n = 1

        if res != 0.5:
            node.wins += res
            node.losses += abs(1 - res)
        else:
            node.draws += 1

        parent_node.children.append(node)

class Parser:
    def __init__(self):
        self.tree = OpeningTree()
        self.dbt = core.DatabaseTool()

    def get_all_with_opening(self, pgn, depth):
        def determine_result(val):
            is_winner = True if val['Result'] != '1/2-1/2' else False
            user_white = True if val['White'] == core.user else False
            
            if is_winner:
                return 1 if (user_white and val['Result'] == '1-0') or (not user_white and val['Result'] == '0-1') else 0
            
            return 0.5
        # get all games matching line
        games = self.dbt.get_by_line(pgn)

        pgns_parsed = []
        scores = []
        depth_dict = {}
        for _, val in games.iterrows():
            # split the pgn into a list of moves (no move numbers preserved)
            pgn_parsed = [re.sub('\d+\.', '', _) for _ in val['PGN'].split(' ')]
            score = determine_result(val)

            scores.append(score)
            pgns_parsed.append(pgn_parsed)

        for i, game in enumerate(pgns_parsed):
            for idx, val in enumerate(game):
                try:
                    does_exist = False
                    for m in depth_dict[idx]:
                        if m['move'] == val:
                            does_exist = True

                            m['n'] += 1
                            m['scores'].append(scores[i])

                    if not does_exist:
                        depth_dict[idx].append({
                            'move': val,
                            'n': 1,
                            'scores': [scores[i]]
                        })

                except KeyError:
                    depth_dict[idx] = [{
                        'move': val,
                        'n': 1,
                        'scores': [scores[i]]
                    }]


        for key in depth_dict.keys():
            for move in depth_dict[key]:
                move['scores'] = sum(move['scores']) / len(move['scores'])
            print("{}: {}".format(key, depth_dict[key]))

        return depth_dict

if __name__ == '__main__':
    opening = "1.e4 e5 2.Nf3 Nc6 3.d4 exd4 4.Bc4"
    depth = len(str(re.sub('\d+\.', '', opening)).split())
    p = Parser()
    p.get_all_with_opening(opening, depth)