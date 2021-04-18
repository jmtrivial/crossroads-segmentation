

from . import reliability as rl
from . import region as r
from . import utils as u


class Crossroad(r.Region):

    def __init__(self, G, node):
        super().__init__(G)

        self.max_distance_boundary_polyline = 15
        self.max_distance_inner_polyline = 8

        self.propagate(node)

    def is_crossroad(self):
        return True

    def is_branch(self):
        return False

    def build_crossroads(G):
        crossroads = []
        for n in G.nodes:
            if r.Region.unknown_region_node_in_graph(G, n):
                if Crossroad.is_reliable_crossroad_node(G, n):
                    c = Crossroad(G, n)
                    if len(c.nodes) == 1 and len(c.edges) == 0 and len(list(G.neighbors(n))) == 2:
                        r.Region.clear_node_region_in_grah(G, n)
                    else:
                        crossroads.append(c)
        return crossroads



    def is_reliable_crossroad_node(G, n):
        if rl.Reliability.is_weakly_in_crossroad(G, n):
            return True

        for nb in G.neighbors(n):
            if rl.Reliability.is_weakly_in_crossroad_edge(G, (nb, n)):
                return True
        
        return False

    def propagate(self, n):

        self.add_node(n)

        stack = [n]

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


    def add_path(self, path):
        for p1, p2 in zip(path, path[1:]):
            self.add_edge((p1, p2))

    def is_correct_inner_node(self, node):
        return rl.Reliability.is_weakly_in_crossroad(self.G, node)

    def is_correct_inner_path(self, path):
        if len(path) < 2:
            return False

        first = path[0]
        last = path[len(path) - 1]

        d =  u.Util.distance(self.G, first, last)
        if rl.Reliability.is_weakly_in_crossroad(self.G, first) and rl.Reliability.is_weakly_boundary(self.G, last):
            if d < self.max_distance_boundary_polyline:
                return True
            else:
                return False
        
        if rl.Reliability.is_weakly_in_crossroad(self.G, first) and rl.Reliability.is_weakly_in_crossroad(self.G, last):
            if d < self.max_distance_inner_polyline:
                return True
            else:
                return False

        return False

    def get_possible_path(self, n1, n2):

        path = [n1, n2]

        while self.is_middle_path_node(path[len(path) - 1]):
            next = self.get_next_node_along_polyline(path[len(path) - 1], path[len(path) - 2])                

            if next == None:
                print("ERROR: cannot follow a path")
                return None
            path.append(next)

            # if we reach a known region, we stop the expension process
            if not self.unknown_region_node(next):
                break

        
        return path
    
    def is_middle_path_node(self, node):
        if len(list(self.G.neighbors(node))) != 2:
            return False

        return not (rl.Reliability.is_weakly_boundary(self.G, node) \
                or rl.Reliability.is_weakly_in_branch(self.G, node) \
                or rl.Reliability.is_weakly_in_crossroad(self.G, node))

    def get_next_node_along_polyline(self, current, pred):
        for n in self.G.neighbors(current):
            if n != pred:
                return n
        # cannot append
        return None

