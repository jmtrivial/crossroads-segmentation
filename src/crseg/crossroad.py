

from . import reliability as rl
from . import region as r
from . import utils as u


class Crossroad(r.Region):

    def __init__(self, G, node):
        r.Region.__init__(self, G)

        self.max_distance_boundary_polyline = { "motorway": 50, 
                                                "trunk": 50,
                                                "primary": 30, 
                                                "secondary": 25, 
                                                "tertiary": 20, 
                                                "unclassified": 15, 
                                                "residential": 10,
                                                "living_street": 10,
                                                "service": 10,
                                                "default": 10
                                                }
        self.max_distance_inner_polyline = { "motorway": 15, 
                                                "trunk": 15,
                                                "primary": 10, 
                                                "secondary": 7, 
                                                "tertiary": 7, 
                                                "unclassified": 5, 
                                                "residential": 3,
                                                "living_street": 3,
                                                "service": 3,
                                                "default": 3
                                                }

        self.propagate(node)

    def is_crossroad(self):
        return True


    def build_crossroads(G):
        crossroads = []
        for n in G.nodes:
            if r.Region.unknown_region_node_in_graph(G, n):
                if Crossroad.is_reliable_crossroad_node(G, n):
                    c = Crossroad(G, n)

                    if c.is_straight_crossing():
                        c.clear_region()
                    else:
                        crossroads.append(c)
        return crossroads

    def is_straight_crossing(self):
        for n in self.nodes:
            if len(list(self.G.neighbors(n))) > 2:
                return False
        
        return True


    def is_reliable_crossroad_node(G, n):
        if rl.Reliability.is_weakly_in_crossroad(G, n):
            return True

        for nb in G.neighbors(n):
            if rl.Reliability.is_weakly_in_crossroad_edge(G, (nb, n)):
                return True
        
        return False

    def propagate(self, n):

        # TODO: détection des triangles ? Détection des cercles ?

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
        for p in path:
            self.add_node(p)
        for p1, p2 in zip(path, path[1:]):
            self.add_edge((p1, p2))

    def is_correct_inner_node(self, node):
        return not rl.Reliability.is_weakly_boundary(self.G, node)

    def get_highway_classification(self, path):
        edge = self.G[path[0]][path[1]][0]
        if not "highway" in edge:
            return "default"
        highway = edge["highway"]
        highway_link = highway + "_link"
        if highway_link in self.max_distance_boundary_polyline:
            highway = highway_link
        if not highway in self.max_distance_boundary_polyline:
            highway = "default"
        return highway

    def is_inner_path_by_osmdata(self, path):
        for p1, p2 in zip(path, path[1:]):
            if not "junction" in self.G[p1][p2][0]:
                return False
        return True

    def is_correct_inner_path_with_boundary(self, path):

        # remove loops
        if path[0] == path[len(path) - 1]:
            return False

        if self.is_inner_path_by_osmdata(path):
            return True

        first = path[0]
        last = path[len(path) - 1]
        if rl.Reliability.is_weakly_in_crossroad(self.G, first) and rl.Reliability.is_weakly_boundary(self.G, last):
            d =  u.Util.distance(self.G, first, last) # TODO: use path length
            highway = self.get_highway_classification(path)
            if d < self.max_distance_boundary_polyline[highway]:
                return True
            else:
                return False

    def is_correct_inner_path_without_boundary(self, path):
        if self.is_inner_path_by_osmdata(path):
            return True

        first = path[0]
        last = path[len(path) - 1]
        if rl.Reliability.is_weakly_in_crossroad(self.G, first) and rl.Reliability.is_weakly_in_crossroad(self.G, last):
            d =  u.Util.distance(self.G, first, last) # TODO: use path length
            highway = self.get_highway_classification(path)
            if d < self.max_distance_inner_polyline[highway]:
                return True
            else:
                return False

    def is_correct_inner_path(self, path):
        if len(path) < 2:
            return False
        
        return self.is_correct_inner_path_with_boundary(path) or self.is_correct_inner_path_without_boundary(path)

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
                or rl.Reliability.is_weakly_in_crossroad(self.G, node))

    def get_next_node_along_polyline(self, current, pred):
        for n in self.G.neighbors(current):
            if n != pred:
                return n
        # cannot append
        return None

