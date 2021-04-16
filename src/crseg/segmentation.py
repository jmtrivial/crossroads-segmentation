


import networkx as nx
import osmnx as ox
import pandas as pd
import random
import math


class Region:

    # TODO: consider distances relative to the kind of way (primary, etc.)

    # during the first detection stage, a region with multiple branches is considered as a crossroad if its diameter is equal to this value
    maximum_basic_crossroad_diameter = 10
    
    # during the first detection stage, if a basic street has a length up to this value, it is automatically classified as a branch
    minimum_basic_street_length = 50

    # during the clustering process inside a not classifid region, significant nodes (boundaries and biffurcation) are clustered in a 
    # single region if their distance to the group is less than this value
    maximum_cluster_distance = 15

    label_region = "region"
    label_region_class = "region_class"
    label_boundary = "boundary"


    region_junction_classes = { "roundabout" }

    boundary_classes = { "inside": 0, 
                         
                         "deadend": 1,
                         "turning_loop": 2,

                         "crossing": 5, 
                         "give_way": 6, 
                         "stop": 7, 
                         "traffic_signals": 8,

                         "mini_roundabout": 20,
                         "turning_circle": 21,
                         "motorway_junction": 31,

                         "other": 100,

                         "computed_boundary": 1000
                        }

    highway_no_boundary = [ "bus_stop", "milestone", "steps", "elevator" ]

    label_region_unknown = 0
    label_region_crossroad = 1
    label_region_branch = 2

    nb_regions = 0

    def __init__(self, G):
        self.edge_label = Region.nb_regions
        self.G = G
        self.edges = []
        self.boundaries_nodes = []
        self.inner_nodes = []
        self.region_class = Region.label_region_unknown
        Region.nb_regions += 1
    
    def init_attr(G):
        nx.set_edge_attributes(G, values=None, name=Region.label_region)
        nx.set_edge_attributes(G, values=Region.label_region_unknown, name=Region.label_region_class)
        nx.set_node_attributes(G, values=Region.boundary_classes["inside"], name=Region.label_boundary)


    def has_traffic_signals_boundary(self):
        for n in self.boundaries_nodes:
            if self.G.nodes[n][Region.label_boundary] == Region.boundary_classes["traffic_signals"]:
                return True
        return False

    def has_biffurcation_boundary(self):
        for n in self.boundaries_nodes:
            if len(list(self.G.neighbors(n))) > 2:
                return True
        return False

    def is_small_path_between_crossroad_and_traffic_signals(self, other_regions):
        if not self.is_small_path():
            return False

        bn = self.get_adjacent_crossroad_boundary_nodes(other_regions)
        if len(bn) != 1:
            return False

        other_node = [ b for b in self.boundaries_nodes if not b in bn ]
        if len(other_node) != 1:
            return False

        return self.G.nodes[other_node[0]][Region.label_boundary] == Region.boundary_classes["traffic_signals"]

    def get_adjacent_crossroad_boundary_nodes(self, other_regions):
        result = []
        b_crossroads = sum([r.boundaries_nodes for r in other_regions if r.is_crossroad()], [])
        for b in self.boundaries_nodes:
            if b in b_crossroads:
                result.append(b)
        return result

    def has_adjacent_crossoroad(self, other_regions):
        return len(self.get_adjacent_crossroad_boundary_nodes(other_regions)) != 0

    def is_small_path(self, threshold = maximum_cluster_distance):
        if len(self.boundaries_nodes) != 2:
            return False
        length = 0
        for e in self.edges:
            x1 = self.G.nodes[e[0]]["x"]
            y1 = self.G.nodes[e[0]]["y"]
            x2 = self.G.nodes[e[1]]["x"]
            y2 = self.G.nodes[e[1]]["y"]
            length += ox.distance.great_circle_vec(lat1=y1, lng1=x1, lat2=y2, lng2=x2)
        return length < threshold

    # a basic boundary is a node with highway attribute or a deadend (due to cropping, or real deadend)
    def is_basic_boundary(node, G):
        nbnb = len(list(G.neighbors(node)))
        highway = "highway" in G.nodes[node] and not G.nodes[node]["highway"] in Region.highway_no_boundary
        return (highway and nbnb < 4) or nbnb == 1

    def unknown_region(edge, G):
        return G[edge[0]][edge[1]][edge[2]][Region.label_region] == None

    def add_edge(self, edge):
        if not edge in self.edges:
            # add edge
            self.edges.append(edge)

            # set label
            self.G[edge[0]][edge[1]][edge[2]][Region.label_region] = self.edge_label

    def remove_edge(self, edge):

        if edge in self.edges:
            self.edges.remove(edge)
            self.G[edge[0]][edge[1]][edge[2]][Region.label_region] = -1
        else:
            edge2 = (edge[1], edge[0], 0)
            if edge2 in self.edges:
                self.edges.remove(edge2)
                self.G[edge2[0]][edge2[1]][edge[2]][Region.label_region] = -1

    def remove_node(self, node):
        if node in self.inner_nodes:
            self.inner_nodes.remove(node)
        if node in self.boundaries_nodes:
            self.G.nodes[node][Region.label_boundary] = Region.boundary_classes["inside"]
            self.boundaries_nodes.remove(node)

    def add_node(self, n):
        if Region.is_basic_boundary(n, self.G):
            if not self.add_boundary_node(n):
                self.add_inner_node(n)
        else:
            self.add_inner_node(n)
    
    def add_inner_node(self, n):
        if not n in self.inner_nodes:
            self.inner_nodes.append(n)


    def add_boundary_node(self, b):
        if not b in self.boundaries_nodes:
            # add node
            self.boundaries_nodes.append(b)

            # set boundary label
            lb = Region.label_boundary
            if "highway" in self.G.nodes[b] and self.G.nodes[b]["highway"] != None:
                if self.G.nodes[b]["highway"] in Region.boundary_classes:
                    self.G.nodes[b][lb] = Region.boundary_classes[self.G.nodes[b]["highway"]]
                else:
                    self.G.nodes[b][lb] = Region.boundary_classes["other"]
                    print("Unknown tag:", self.G.nodes[b]["highway"])
                return True

            elif len(list(self.G.neighbors(b))) == 1:
                self.G.nodes[b][lb] = Region.boundary_classes["deadend"]
                return True
            else:
                return False
        else:
            return True

    def set_basic_region_class(self):
        if self.is_basic_branch():
            self.set_is_branch()
        if self.is_basic_crossroad():
            self.set_is_crossroad()

    def is_basic_branch(self):
        # a street with no name shorter than x meters is not a street
        return len(self.boundaries_nodes) == 2 and len(self.get_biffurcation_inner_nodes()) == 0 and self.max_distance_to_closest_boundary() > Region.minimum_basic_street_length


    def has_junction_edge_attr(self):
        return self.has_edge_attr("junction")

    def has_edge_attr(self, key):
        for e in self.edges:
            if not key in self.G[e[0]][e[1]][e[2]]:
                return False
        return True

    def is_basic_crossroad(self):
        return (len(self.boundaries_nodes) <= 2 and self.has_junction_edge_attr()) or \
             (len(self.boundaries_nodes) > 2 and self.max_distance_between_boundary() < Region.maximum_basic_crossroad_diameter)

    def get_biffurcation_inner_nodes(self):
        return [n for n in self.inner_nodes if len(list(self.G.neighbors(n))) > 2]
        

    def max_distance_to_closest_boundary(self):
        max_dist = 0
        for n1 in self.boundaries_nodes:
            x1 = self.G.nodes[n1]["x"]
            y1 = self.G.nodes[n1]["y"]
            dist = 0
            for n2 in self.boundaries_nodes:
                if n1 != n2:
                    x2 = self.G.nodes[n2]["x"]
                    y2 = self.G.nodes[n2]["y"]
                    # Consider that geometry is not projected
                    d = ox.distance.great_circle_vec(lat1=y1, lng1=x1, lat2=y2, lng2=x2)
                    if dist == 0 or (d != 0 and d < dist):
                        dist = d
            if dist > max_dist:
                max_dist = dist
        return max_dist


    def max_distance_between_boundary(self):
        max_dist = 0
        for n1 in self.boundaries_nodes:
            x1 = self.G.nodes[n1]["x"]
            y1 = self.G.nodes[n1]["y"]
            dist = 0
            for n2 in self.boundaries_nodes:
                if n1 != n2:
                    x2 = self.G.nodes[n2]["x"]
                    y2 = self.G.nodes[n2]["y"]
                    # Consider that geometry is not projected
                    d = ox.distance.great_circle_vec(lat1=y1, lng1=x1, lat2=y2, lng2=x2)
                    if d > max_dist:
                        max_dist = d
        return max_dist

    def has_edge(self, n1, n2):
        return (n1, n2, 0) in self.edges or (n2, n1, 0) in self.edges

    def has_street_name(self):
        for e in self.edges:
            if "street_name" in self.G[e[0]][e[1]][e[2]]:
                return True
        return False

    def set_region_class(self, r_class):
        self.region_class = r_class
        for e in self.edges:
            self.G[e[0]][e[1]][e[2]][Region.label_region_class] = r_class

    def is_unknown(self):
        return self.region_class == Region.label_region_unknown

    def is_branch(self):
        return self.region_class == Region.label_region_branch

    def is_crossroad(self):
        return self.region_class == Region.label_region_crossroad

    def set_is_branch(self):
        self.set_region_class(Region.label_region_branch)

    def set_is_crossroad(self):
        self.set_region_class(Region.label_region_crossroad)

    def distance_to_cluster(self, node, cluster):
        distance = -1
        x1 = self.G.nodes[node]["x"]
        y1 = self.G.nodes[node]["y"]
        for n in cluster:
            x2 = self.G.nodes[n]["x"]
            y2 = self.G.nodes[n]["y"]
            d = ox.distance.great_circle_vec(lat1=y1, lng1=x1, lat2=y2, lng2=x2)
            if distance < 0 or d < distance:
                distance = d
        return distance

    def cluster_by_distance(self, nodes):
        result = []

        for n in nodes:
            inside = []
            for i in range(len(result)):
                if self.distance_to_cluster(n, result[i]) < Region.maximum_cluster_distance:
                    inside.append(i)
                    
            if len(inside) == 0:
                result.append([n])
            else:
                ncluster = sum([ c for i, c in enumerate(result) if i in inside ], [])
                ncluster.append(n)
                result = [ c for i, c in enumerate(result) if not i in inside ]
                result.append(ncluster)
        return result

    def split_by_edge_groups(self, subregions):
        result = []
        # for each subregion except the
        for i, subregion in enumerate(subregions):
            if len(subregion) > 0:
                last = i == len(subregions) - 1
                # create a new region (or use the current one for the last subregion)
                if not last:
                    nregion = Region(self.G)
                
                # add all the edges of the subregion in the new region and remove them from the initial region
                inodes = {}
                for e in subregion:
                    if not last:
                        self.remove_edge((e[0], e[1], 0))
                        nregion.add_edge((e[0], e[1], 0))
                    inodes[e[0]] = inodes[e[0]] + 1 if e[0] in inodes else 1
                    inodes[e[1]] = inodes[e[1]] + 1 if e[1] in inodes else 1

                # add all the boundary nodes in the new region and remove them from the initial region
                for n in inodes:
                    if inodes[n] != len(list(self.G.neighbors(n))):
                        if not last:
                            self.remove_node(n)
                            nregion.add_boundary_node(n)
                        else:
                            self.add_boundary_node(n)
                        if self.G.nodes[n][Region.label_boundary] == Region.boundary_classes["inside"]:
                            self.G.nodes[n][Region.label_boundary] = Region.boundary_classes["computed_boundary"]                    
                    else:
                        if not last:
                            self.remove_node(n)
                            nregion.add_inner_node(n)
                        else:
                            self.add_inner_node(n)
                if not last:
                    result.append(nregion)

                curregion = self if last else nregion
                nbExtremities = len([n for n in inodes if inodes[n] != len(list(self.G.neighbors(n)))])
                if nbExtremities <= 2:
                    if curregion.is_small_path() and curregion.has_biffurcation_boundary():
                        curregion.set_is_crossroad()
                    else:
                        curregion.set_is_branch()
                else:
                    curregion.set_is_crossroad()
        
        return result

    #
    def continue_path_to_significant_node(self, path, nodes):
        node = path[len(path) - 1]
        if node in nodes:
            return path
        else:
            pred = path[len(path) - 2]
            next = None
            for nb in self.G.neighbors(node):
                if nb != pred:
                    next = nb
                    break
            if next == None:
                return []
            path.append(next)

            if len(list(self.G.neighbors(next))) != 2:
                if next in nodes:
                    return path
                else:
                    return []
            else:
                return self.continue_path_to_significant_node(path, nodes)


    # input nodes are crossing nodes or nodes of interest. 
    # it produces as output all the inner paths, ie paths where first and last nodes are input nodes, but no inner node is an input node
    def get_paths_between_significant_nodes(self, nodes):

        paths = []
        for i, node in enumerate(nodes):
            for nb in self.G.neighbors(node):
                # build path starting from i and going through nb
                if self.has_edge(node, nb):
                    path = self.continue_path_to_significant_node([node, nb], nodes)
                else:
                    path = []
                # only consider paths that reach nodes
                if len(path) > 0:
                    # avoid double paths
                    if path[len(path) - 1] > node:
                        paths.append(path)

        return paths

    # given a list of set clusters defined by a list of nodes in the region,
    # it returns a list where each element is a list of edges corresponding to a partition of the 
    # current region
    def get_edges_in_regions(self, clusters):
        # init the result list: one segment per cluster 
        result = [ [] for c in clusters ]
        paths = self.get_paths_between_significant_nodes(sum(clusters, []))
        for path in paths:
            start = [ i for i, c in enumerate(clusters) if path[0] in c][0]
            end = [ i for i, c in enumerate(clusters) if path[len(path) - 1] in c][0]
            if start == end:
                for p1, p2 in zip(path, path[1:]):
                    result[start].append((p1, p2))
            else:
                result.append([(p1, p2) for p1, p2 in zip(path, path[1:])])
        return result

    # split regions using a clustering of biffurcation and boundary nodes to detect crossroads.
    # if a cluster has a single biffurcation node, it corresponds to a multi-boundary node (that will be a crossroad)
    # otherwise, the cluster and the contained edges are a new region that corresponds to a crossroad
    # if nodes are in a single cluster, it means that the region is a crossroad region
    # This function updates the current region and return a list of supplementary regions
    def split_by_clusters(self):
        significant_nodes = self.boundaries_nodes + self.get_biffurcation_inner_nodes()
        clusters = self.cluster_by_distance(significant_nodes)
        if len(clusters) == 1:
            if len(significant_nodes) > 2:
                self.set_is_crossroad()
        else:
            subregions = self.get_edges_in_regions(clusters)
            supplementary_regions = self.split_by_edge_groups(subregions)
            return supplementary_regions
        return []

class Segmentation:

    def __init__(self, G):
        self.G = G
        self.regions = []
        random.seed()

    def process(self):

        # init flags
        Region.init_attr(self.G)

        # build basic regions using boundary nodes (crossings, )
        for u, v in self.G.edges():
            if Region.unknown_region((u, v, 0), self.G):
                self.build_basic_region([u, v])


        # finally decide for each region its class

        # first using basic detection
        for r in self.regions:
            r.set_basic_region_class()

        # split the current regions using a cluster approach. 
        new_regions = []
        for r in self.regions:
            if r.is_unknown():
                nr = r.split_by_clusters()
                new_regions += nr
        self.regions += new_regions

        # after this process, consolidate crossroads:
        for r in self.regions:
            # - if a no-labelled region is a short path and adjacent to crossroad region, it's (part of) a crossroad
            if r.is_unknown() and r.is_small_path() and (r.has_adjacent_crossoroad(self.regions) or r.has_traffic_signals_boundary()):
                r.set_is_crossroad()
            # - if a branch region is adjacent to a crossroad region and has a traffic_signals boundary node with only 2 neighbors at the opposite extremity, it is (part of) a crossroad
            if r.is_branch() and r.is_small_path_between_crossroad_and_traffic_signals(self.regions): 
                r.set_is_crossroad()
            if r.is_branch() and r.has_junction_edge_attr():
                r.set_is_crossroad()

        # finally, merge connected branches in a 2-neighbors boundary
        # TODO

        # merge adjacent crossings if one of them is a simple path
        # TODO

        # merge two crossings if they are not adjacent, but connected by more than one (small)
        # TODO

        # merge crossings if they are connecting branches with similar name (3 crossings as a triangle)
        # TODO

        # a split of streets (for a road island) is not a crossroad. Might be fixed by the branch detection
        # TODO

        # branch detection: parallel ways connected to a single crossroad are part of the same branch
        # TODO

        # crossroad detection
        # hierarchical structure:
        # - crossroad regions
        # - adjacent crossroad regions
        # - weakly connected crossroad regions (see below "merge crossings")



    ######################### Functions used to prepare the graph ########################

    def remove_footways(G, keep_all_components):
        to_remove = []
        for u, v, a in G.edges(data = True):
            if "footway" in a or "highway" in a and a["highway"] in ["footway", "cycleway"]:
                to_remove.append((u, v))
        G.remove_edges_from(to_remove)
        G = ox.utils_graph.remove_isolated_nodes(G)
        if not keep_all_components:
            G = ox.utils_graph.get_largest_component(G)
        return G

        
    ######################### Functions related to graph rendering (colors) ########################

    # return edge colors according to the region label
    def get_regions_colors(self):
        return Segmentation.get_edge_random_colors_by_attr(self.G, Region.label_region)

    # return edge colors according to the region class label
    def get_regions_class_colors(self):
        colors = { Region.label_region_unknown: (0.3, 0.3, 0.3, 1), \
                Region.label_region_crossroad: (0.8, 0, 0, 1), \
                Region.label_region_branch: (0.6, 0.6, 0, 1)}
        return Segmentation.get_edge_random_colors_by_attr(self.G, Region.label_region_class, colors)


    def random_color():
        r1 = math.pi * random.random()
        r2 = math.pi * random.random()
        coef = 0.5
        return (coef * abs(math.sin(r1)) * abs(math.sin(r2)), \
                coef * abs(math.cos(r1)) * abs(math.sin(r2)), \
                coef * abs(math.sin(r1)) * abs(math.cos(r2)), 
                1)

    # return edge colors using one random color per label
    def get_edge_random_colors_by_attr(G, label, values = {}):
        result = {}
        for e in G.edges:
            tag = G[e[0]][e[1]][e[2]][label]
            if not tag in values:
                values[tag] = Segmentation.random_color()
            result[e] = values[tag]
        return pd.Series(result)
        


    # return edge colors according to the boundary class
    def get_boundaries_colors(self, full_details=True):
        values = { "inside": (0, 0, 0, 0), \
                "crossing": (1, 1, 0, 1), \
                "give_way": (0.6, 0, 0, 1), \
                "stop": (0.7, 0, 0, 1), \
                "traffic_signals": (1, 0, 0, 1), \
                "deadend": (0, 0, 1, 1)}
        result = {}
        for e in self.G.nodes:
            tag = self.G.nodes[e][Region.label_boundary]
            if full_details:
                result[e] = values[tag]
            else:
                if tag == Region.boundary_classes["inside"]:
                    result[e] = (0, 0, 0, 0)
                else:
                    result[e] = (0.7, 0.5, 1, 1)

        return pd.Series(result)




    ######################### Functions related to region segmentation ########################

    # a function to distinguish between boundary and no boundary edges
    def no_highway_nodes(G, node):
        if not Region.is_basic_boundary(node, G):
            return G.neighbors(node)
        else:
            return iter([])

    # a generic depth-first-search algorithm driven by a function that distinguish between
    # boundary and no boundary edges. 
    def build_basic_region(self, source_edge):
        region = Region(self.G)

        region.add_node(source_edge[0])
        region.add_node(source_edge[1])

        nodes = [source_edge[0], source_edge[1]]
        if not Region.unknown_region((source_edge[0], source_edge[1], 0), self.G):
            return
        region.add_edge((source_edge[0], source_edge[1], 0))
        for start in nodes:
            stack = [(start, Segmentation.no_highway_nodes(self.G, start))]
            while stack:
                parent, children = stack[-1]
                try:
                    child = next(children)
                    if Region.unknown_region((parent, child, 0), self.G):
                        region.add_node(child)
                        region.add_edge((parent, child, 0))
                        stack.append((child, Segmentation.no_highway_nodes(self.G, child)))
                except StopIteration:
                    stack.pop()
        self.regions.append(region)

