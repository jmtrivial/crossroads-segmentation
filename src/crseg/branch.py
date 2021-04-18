
from . import reliability as rl
from . import region as r
from . import utils as u


class Branch(r.Region):


    def __init__(self, G, node):
        r.Region.__init__(self, G)

        self.min_branch_length = { "motorway": 100, 
                                    "trunk": 100,
                                    "primary": 20, 
                                    "secondary": 20, 
                                    "tertiary": 15, 
                                    "unclassified": 10, 
                                    "residential": 10,
                                    "living_street": 10,
                                    "service": 5,
                                    "default": 5
                                    }

        self.propagate(node)

    def is_branch(self):
        return True


    def build_branches(G):
        branches = []

        # TODO: on trouve tous les chemins 2-segments sans weakly_boundary, éventuellement jusqu'aux crossings déjà repérés
        # on ne garde que ceux qui sont plus longs que le critère (ou qui relient deux passages piétons)
        # si deux chemins partagent un node, on fusionne ?
        # on repère les chemins parallèles (éventuellement parallèles), on les fusionne.
        # Attention aux configuration |├ pour lesquelles il faudra couper en deux le chemin le plus long...

        for e in G.edges:
            if r.Region.unknown_region_edge_in_graph(G, e):
                b = Branch(G, e)
                if b.is_valid_branch(b):
                    branches.append(b)
                else:
                    b.clear_region()
        return branches

    def is_valid_branch(self, b):
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

 