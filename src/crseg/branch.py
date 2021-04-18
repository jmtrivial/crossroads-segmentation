
from . import reliability as rl
from . import region as r
from . import utils as u


class Branch(r.Region):

    def __init__(self, G, node):
        super().__init__(G)

        self.propagate(node)

    def is_branch(self):
        return True

    def is_crossroad(self):
        return False

    def build_branches(G):
        branches = []
        for e in G.edges:
            if r.Region.unknown_region_edge_in_graph(G, e):
                if Branch.is_reliable_branch_edge(G, e):
                    branches.append(Branch(G, e))
        return branches

    def is_reliable_branch_edge(G, e):
        # TODO
        return True

    def propagate(self, e):

        self.add_edge(e)

        stack = [e[0], e[1]]

        return # TODO not finished
        while stack:
            parent = stack.pop()

            for nb in self.G.neighbors(parent):
                if self.unknown_region_edge((parent, nb)):
                    path = self.get_possible_path(parent, nb)
                    if path != None and self.is_correct_inner_path(path):
                        self.add_path(path)
                        next = path[len(path) - 1]
                        if self.is_correct_inner_node(next):
                            stack.append(next)

 