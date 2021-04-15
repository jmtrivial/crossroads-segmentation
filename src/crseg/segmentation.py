


import networkx as nx
import osmnx as ox
import pandas as pd
import random
import math


class Region:

    maximum_basic_crossroad_diameter = 50
    minimum_basic_street_length = 50

    label_region = "region"
    label_region_class = "region_class"
    label_boundary = "boundary"

    label_boundary_inside_region = 0
    label_boundary_crossing = 5
    label_boundary_give_way = 6
    label_boundary_stop = 7
    label_boundary_traffic_signals = 10
    label_boundary_deadend = 1


    label_region_unknown = 0
    label_region_crossroad = 1
    label_region_branch = 2

    def __init__(self, G, edge_label):
        self.edge_label = edge_label
        self.G = G
        self.edges = []
        self.boundaries_nodes = []
    
    def init_attr(G):
        nx.set_edge_attributes(G, values=None, name=Region.label_region)
        nx.set_edge_attributes(G, values=Region.label_region_unknown, name=Region.label_region_class)
        nx.set_node_attributes(G, values=Region.label_boundary_inside_region, name=Region.label_boundary)


    # a basic boundary is a node with highway attribute or a deadend (due to cropping, or real deadend)
    def is_basic_boundary(node, G):
        nbnb = len(list(G.neighbors(node)))
        highway = "highway" in G.nodes[node]
        return highway or nbnb == 1

    def unknown_region(edge, G):
        return G[edge[0]][edge[1]][edge[2]][Region.label_region] == None

    def add_edge(self, edge):
        if not edge in self.edges:
            # add edge
            self.edges.append(edge)

            # set label
            self.G[edge[0]][edge[1]][edge[2]][Region.label_region] = self.edge_label


    def add_node(self, n):
        if Region.is_basic_boundary(n, self.G):
            self.add_boundary_node(n)


    def add_boundary_node(self, b):
        if not b in self.boundaries_nodes:
            # add node
            self.boundaries_nodes.append(b)

            # set boundary label
            lb = Region.label_boundary
            if "highway" in self.G.nodes[b] and self.G.nodes[b]["highway"] != None:
                if self.G.nodes[b]["highway"] == "crossing":
                    self.G.nodes[b][lb] = Region.label_boundary_crossing
                elif self.G.nodes[b]["highway"] == "stop":
                    self.G.nodes[b][lb] = Region.label_boundary_stop
                elif self.G.nodes[b]["highway"] == "give_way":
                    self.G.nodes[b][lb] = Region.label_boundary_give_way
                elif self.G.nodes[b]["highway"] == "traffic_signals":
                    self.G.nodes[b][lb] = Region.label_boundary_traffic_signals
                else:
                    print("Unknown tag:", self.G.nodes[b]["highway"])

            elif len(list(self.G.neighbors(b))) == 1:
                self.G.nodes[b][lb] = Region.label_boundary_deadend
            else:
                print("on est au niveau d'un sommet avec comme voisins", list(self.G.neighbors(b)))

    def set_region_class(self):
        if self.is_basic_branch():
            self.set_is_branch()
        if self.is_basic_crossroad():
            self.set_is_crossroad()

    def is_basic_branch(self):
        # a street with no name shorter than x meters is not a street
        return len(self.boundaries_nodes) == 2 and self.max_distance_to_closest_boundary() > Region.minimum_basic_street_length

    def is_basic_crossroad(self):
        return len(self.boundaries_nodes) > 2 and self.max_distance_between_boundary() < Region.maximum_basic_crossroad_diameter

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

    def has_street_name(self):
        for e in self.edges:
            if "street_name" in self.G[e[0]][e[1]][e[2]]:
                return True
        return False


    def set_is_branch(self):
        for e in self.edges:
            self.G[e[0]][e[1]][e[2]][Region.label_region_class] = Region.label_region_branch

    def set_is_crossroad(self):
        for e in self.edges:
            self.G[e[0]][e[1]][e[2]][Region.label_region_class] = Region.label_region_crossroad


class Segmentation:

    def __init__(self, G):
        self.G = G
        self.regions = []
        random.seed()

    def process(self):

        # init flags
        Region.init_attr(self.G)

        # build region flags
        i = 0
        for u, v in self.G.edges():
            if Region.unknown_region((u, v, 0), self.G):
                self.build_basic_region([u, v], i)
                i += 1


        # finally decide for each region its class
        for r in self.regions:
            r.set_region_class()


        
    ######################### Functions related to graph rendering (colors) ########################

    # return edge colors according to the region label
    def get_regions_colors(self):
        return Segmentation.get_edge_random_colors_by_attr(self.G, Region.label_region)

    # return edge colors according to the region class label
    def get_regions_class_colors(self):
        colors = { Region.label_region_unknown: (0.3, 0.3, 0.3, 1), \
                Region.label_region_crossroad: (0.8, 0, 0, 1), \
                Region.label_region_branch: (0.8, 0.8, 0, 1)}
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
        values = { Region.label_boundary_inside_region: (0, 0, 0, 0), \
                Region.label_boundary_crossing: (1, 1, 0, 1), \
                Region.label_boundary_give_way: (0.6, 0, 0, 1), \
                Region.label_boundary_stop: (0.7, 0, 0, 1), \
                Region.label_boundary_traffic_signals: (1, 0, 0, 1), \
                Region.label_boundary_deadend: (0, 0, 1, 1)}
        result = {}
        for e in self.G.nodes:
            tag = self.G.nodes[e][Region.label_boundary]
            if full_details:
                result[e] = values[tag]
            else:
                if tag == Region.label_boundary_inside_region:
                    result[e] = values[tag]
                else:
                    result[e] = values[Region.label_boundary_traffic_signals]
            
        return pd.Series(result)




    ######################### Functions related to region segmentation ########################

    # a function to distinguish between boundary and no boundary edges
    def no_highway_nodes(G, node):
        if not Region.is_basic_boundary(node, G):
            return G.neighbors(node)
        else:
            return iter([])

    # a generic depth-first-search algorithm driven by a function that distinguish between
    # boundary and no boundary edges. Regions are flaggued using label=value
    def build_basic_region(self, source_edge, value):
        region = Region(self.G, value)

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

