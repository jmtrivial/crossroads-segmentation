

from . import reliability as rl
from . import region as r
from . import utils as u


class Crossroad(r.Region):

    def __init__(self, G, node):
        r.Region.__init__(self, G)

        self.max_distance_boundary_polyline = { "motorway": 50, 
                                                "trunk": 50,
                                                "primary": 40, 
                                                "secondary": 30, 
                                                "tertiary": 25, 
                                                "unclassified": 20, 
                                                "residential": 20,
                                                "living_street": 15,
                                                "service": 15,
                                                "default": 15
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

    def get_max_highway_classification(self):
        if len(self.nodes) == 0:
            return None
        result = "default"
        value = self.max_distance_boundary_polyline[result]
        center = self.nodes[0]
        for nb in self.G.neighbors(center):
            c = self.get_highway_classification((center, nb))
            v = self.max_distance_boundary_polyline[c]
            if v > value:
                result = c
                value = v
        return result
            

    def get_highway_classification(self, edge):
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

    def is_correct_inner_path(self, path):
        if len(path) < 2:
            return False
        # loops are not correct inner path in a crossing
        if path[0] == path[len(path) - 1]:
            return False

        # use "junction" OSM tag as a good clue
        if self.is_inner_path_by_osmdata(path):
            return True

        first = path[0]
        last = path[len(path) - 1]
        if rl.Reliability.is_weakly_in_crossroad(self.G, first) and rl.Reliability.is_weakly_boundary(self.G, last):
            d =  u.Util.length(self.G, path)
            highway = self.get_max_highway_classification()
            if d < self.max_distance_boundary_polyline[highway]:
                return True
            else:
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
                or rl.Reliability.is_weakly_in_crossroad(self.G, node))

    def get_next_node_along_polyline(self, current, pred):
        for n in self.G.neighbors(current):
            if n != pred:
                return n
        # cannot append
        return None

