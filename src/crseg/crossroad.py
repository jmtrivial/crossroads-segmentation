
import osmnx as ox

from . import reliability as rl
from . import region as r
from . import utils as u
from . import branch_description as bd


class Crossroad(r.Region):

    def __init__(self, G, node = None, target_id = -1):
        r.Region.__init__(self, G, target_id)

        self.max_distance_boundary_polyline = { "motorway": 100, 
                                                "trunk": 100,
                                                "primary": 80, 
                                                "secondary": 80, 
                                                "tertiary": 50, 
                                                "unclassified": 40, 
                                                "residential": 40,
                                                "living_street": 30,
                                                "service": 20,
                                                "default": 25
                                                }

        self.min_distance_boundary_polyline = { "motorway": 100, 
                                                "trunk": 100,
                                                "primary": 50, 
                                                "secondary": 40, 
                                                "tertiary": 30, 
                                                "unclassified": 25, 
                                                "residential": 25,
                                                "living_street": 20,
                                                "service": 10,
                                                "default": 15
                                                }

        if node != None:
            self.propagate(node)
            self.build_branches_description()

    def __str__(self):
        return "id: %s, center: %s, branches: %s" % (self.id, self.center, self.branches)

    def __repr__(self):
        return "id: %s, center: %s" % (self.id, self.center)

    def get_center(self):
        return self.center

    def is_crossroad(self):
        return True

    def to_text(self):
        # TODO: improve by identifying similar branches
        return self.__str__()


    def get_branch_description_from_edge(self, edge):
        e = self.G[edge[0]][edge[1]][0]
        angle = u.Util.bearing(self.G, self.get_center(), edge[1])
        name = e["name"] if "name" in e else None
        return bd.BranchDescription(angle, name)

    def get_branches_description_from_node(self, border):
        edges = [(border, nb) for nb in self.G.neighbors(border) if not self.has_edge((nb, border))]
        return [self.get_branch_description_from_edge(e) for e in edges]

    def get_radius(self):
        borders = [n for n in self.nodes if self.is_boundary_node(n) and n != self.get_center()]
        center = self.get_center()
        if len(borders) == 0:
            radius = 0
            for nb in self.G.neighbors(center):
                c = self.get_highway_classification((center, nb))
                v = self.min_distance_boundary_polyline[c] / 2 # we reduce the impact of missing branches
                if v > radius:
                    radius = v
            return radius
        else:
            return sum([u.Util.distance(self.G, center, b) for b in borders]) / len(borders)
        

    def get_open_paths(self, point, radius):
        result = []

        for nb in self.G.neighbors(point):
            if not self.has_edge((nb, point)):    
                result.append(u.Util.get_path_to_biffurcation(self.G, point, nb, radius))

        return result

    def build_branches_description(self):
        self.branches = []

        center = self.get_center()
        radius = self.get_radius()

        borders = [n for n in self.nodes if self.is_boundary_node(n)]

        for b in borders:
            if b != center:
                self.branches = self.branches + self.get_branches_description_from_node(b)
            else:
                # go trough all possible paths starting from the center
                # and add the corresponding branches
                open_branches = self.get_open_paths(center, radius)
                for ob in open_branches:
                    self.branches.append(self.get_branch_description_from_edge((ob[len(ob) - 2], ob[len(ob) - 1])))
        

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
        self.center = n

        for nb in self.G.neighbors(n):
            if self.unknown_region_edge((n, nb)):
                paths = self.get_possible_paths(n, nb)
                for path in paths[::-1]:
                    if path != None and self.is_correct_inner_path(path):
                        self.add_path(path)
                        break


    def is_correct_inner_node(self, node):
        return not rl.Reliability.is_weakly_boundary(self.G, node)

    def get_max_highway_classification_other(self, path):
        if len(self.nodes) == 0:
            return None
        result = "default"
        value = self.max_distance_boundary_polyline[result]
        center = self.get_center()
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
            r = 1
            if len(list(self.G.neighbors(first))) > 4: # a crossroad with many lanes is larger, thus 
                r = 2
            highway = self.get_max_highway_classification_other(path)
            if d < self.min_distance_boundary_polyline[highway] * r or \
                (d < self.max_distance_boundary_polyline[highway] * r and \
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


    def get_crossroads_in_neighborhood(self, crossroads, scale = 3):
        result = []

        center = self.get_center()
        radius = self.get_radius() * scale

        for c in crossroads:
            if c.id != self.id and u.Util.distance(self.G, center, c.get_center()) < radius:
                result.append(c)

        return result


    def find_direct_path_to_possible_adjacent_biffurcation(self, point):
        center = self.get_center()
        for nb in self.G.neighbors(center):
            path = u.Util.get_path_to_biffurcation(self.G, center, nb)
            if path[len(path) - 1] == point:
                return path
        return None

    def in_same_cluster(self, crossroad):

        if self.id == crossroad.id:
            return False  

        angle = u.Util.bearing(self.G, self.get_center(), crossroad.get_center())


        # if their is no direct path between centers, or 
        # if it exists a strong border between the two crossings, they are not
        # in the same cluster
        path = self.find_direct_path_to_possible_adjacent_biffurcation(crossroad.get_center())
        if path == None or rl.Reliability.has_strong_boundary_in_path(self.G, path):
            return False



        # if no strong boundary has been identified, consider similar branches
        # orthogonal to the junction
        for b1 in self.branches:
            for b2 in crossroad.branches:
                if b1.is_similar(b2) and b1.is_orthogonal(angle):
                    return True

        # if their distance is less than their combinded radius
        if u.Util.distance(self.G, self.get_center(), crossroad.get_center()) < self.get_radius() + crossroad.get_radius():
            return True

        return False

    def get_clusters(crossroads, scale = 3):
        result = []

        visited = []

        for crossroad in crossroads:
            if not crossroad.id in visited:
                visited.append(crossroad.id)
                cluster = [crossroad]
            else:
                cluster = [c for c in result if crossroad in c]
                if len(cluster) != 1:
                    cluster = [crossroad]
                else:
                    cluster = cluster[0]
                    result = [c for c in result if not crossroad in c]

            cr_in_neigborhood = crossroad.get_crossroads_in_neighborhood(crossroads, scale)
            for cr in cr_in_neigborhood:
                if crossroad.in_same_cluster(cr):
                    if not cr.id in visited:
                        visited.append(cr.id)
                        cluster.append(cr)
                    else:
                        # merge clusters
                        other_cluster = [c for c in result if cr in c]
                        if len(other_cluster) != 1:
                            # we check if the merge wasn't processed before
                            if not cr in cluster:
                                print("Error while merging two clusters:", crossroad, cr)
                                print("Other cluster", other_cluster)
                                print("result", result)
                        else:
                            other_cluster = other_cluster[0]
                            cluster = cluster + other_cluster
                            result = [c for c in result if not cr in c]
                        
            if len(cluster) >= 1:
                result.append(cluster)

        # finally remove single clusters
        result = [r for r in result if len(r) > 1]
        return result

    def add_direct_paths_between_nodes(self, points):

        for p1 in points:
            for n in self.G.neighbors(p1):
                if not self.has_edge((p1, n)):
                    path = u.Util.get_path_to_biffurcation(self.G, p1, n)
                    if path[len(path) - 1] in points:
                        self.add_path(path)

    def merge(self, regions):
        # add nodes and edges from the other regions
        for region in regions:
            for n in region.nodes:
                self.add_node(n)
            for e in region.edges:
                self.add_edge(e)

        old_centers = [r.get_center() for r in regions]
        old_centers.append(self.get_center())

        # add missing paths between old centers
        self.add_direct_paths_between_nodes(old_centers)

        # set a new center
        center = u.Util.centroid(self.G, old_centers)
        distance = -1
        new_center = None
        for n in self.nodes:
            d = u.Util.distance_to(self.G, n, center)
            if distance < 0 or d < distance:
                distance = d
                new_center = n
        if new_center != None:
            self.center = new_center
        
        # finally rebuild the branch descriptions
        self.build_branches_description()
