

from . import reliability as rl
from . import region as r
from . import utils as u


class Crossroad(r.Region):

    def __init__(self, G, node):
        r.Region.__init__(self, G)

        self.max_distance_boundary_polyline = { "motorway": 100, 
                                                "trunk": 100,
                                                "primary": 80, 
                                                "secondary": 80, 
                                                "tertiary": 50, 
                                                "unclassified": 40, 
                                                "residential": 40,
                                                "living_street": 40,
                                                "service": 40,
                                                "default": 40
                                                }

        self.min_distance_boundary_polyline = { "motorway": 100, 
                                                "trunk": 100,
                                                "primary": 50, 
                                                "secondary": 30, 
                                                "tertiary": 25, 
                                                "unclassified": 16, 
                                                "residential": 16,
                                                "living_street": 16,
                                                "service": 12,
                                                "default": 12
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



        for nb in self.G.neighbors(n):
            if self.unknown_region_edge((n, nb)):
                paths = self.get_possible_paths(n, nb)
                for path in paths[::-1]:
                    if path != None and self.is_correct_inner_path(path):
                        self.add_path(path)
                        break


    def add_path(self, path):
        for p in path:
            self.add_node(p)
        for p1, p2 in zip(path, path[1:]):
            self.add_edge((p1, p2))

    def is_correct_inner_node(self, node):
        return not rl.Reliability.is_weakly_boundary(self.G, node)

    def get_max_highway_classification_other(self, path):
        if len(self.nodes) == 0:
            return None
        result = "default"
        value = self.max_distance_boundary_polyline[result]
        center = self.nodes[0]
        for nb in self.G.neighbors(center):
            if nb != path[1]:
                c = self.get_highway_classification((center, nb))
                v = self.max_distance_boundary_polyline[c]
                if v > value:
                    result = c
                    value = v
        return result
            

    def get_closest_possible_biffurcation(self, point):
        result = -1
        length = -1
        for nb in self.G.neighbors(point):
            path = u.Util.get_path_to_biffurcation(self.G, point, nb)
            l = u.Util.length(self.G, path)
            if length < 0 or l < length:
                length = l
                result = path[len(path) - 1]

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
            highway = self.get_max_highway_classification_other(path)
            if d < self.min_distance_boundary_polyline[highway] or \
                (d < self.max_distance_boundary_polyline[highway] and \
                self.get_closest_possible_biffurcation(last) == first):
                return True
            else:
                return False


    def get_possible_paths(self, n1, n2):
        results = []

        path = [n1, n2]

        # check first for a boundary
        while self.is_middle_path_node(path[len(path) - 1]):
            next = self.get_next_node_along_polyline(path[len(path) - 1], path[len(path) - 2])                

            if next == None:
                print("ERROR: cannot follow a path")
                return results
            path.append(next)

            # if we reach a known region, we stop the expension process
            if not self.unknown_region_node(next):
                break

        results.append(path)

        if not self.is_middle_path_node(path[len(path) - 1], True):
            return results
        path = path.copy()

        # if it's a weak border, we continue until we reach a strong one
        while self.is_middle_path_node(path[len(path) - 1], True):
            next = self.get_next_node_along_polyline(path[len(path) - 1], path[len(path) - 2])                

            if next == None:
                print("ERROR: cannot follow a path")
                return results
            path.append(next)

            # if we reach a known region, we stop the expension process
            if not self.unknown_region_node(next):
                break

        results.append(path)

        return results
    
    def is_middle_path_node(self, node, strong = False):
        if len(list(self.G.neighbors(node))) != 2:
            return False

        if strong:
            return not (rl.Reliability.is_strong_boundary(self.G, node) \
                    or rl.Reliability.is_strong_in_crossroad(self.G, node))
        else:
            return not (rl.Reliability.is_weakly_boundary(self.G, node) \
                    or rl.Reliability.is_weakly_in_crossroad(self.G, node))

    def get_next_node_along_polyline(self, current, pred):
        for n in self.G.neighbors(current):
            if n != pred:
                return n
        # cannot append
        return None

