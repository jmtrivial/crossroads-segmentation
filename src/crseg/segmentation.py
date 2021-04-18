
import networkx as nx
import osmnx as ox
import pandas as pd
import random
import math


from . import crossroad as cr
from . import branch as b
from . import region as rg
from . import reliability as rel

class Segmentation:

    def __init__(self, G):
        self.G = G
        self.regions = []
        random.seed()

    def process(self):

        # init flags
        rel.Reliability.init_attr(self.G)
        rg.Region.init_attr(self.G)


        self.regions = {}

        # first build crossroads
        crossroads = cr.Crossroad.build_crossroads(self.G)
        for c in crossroads:
            self.regions[c.id] = c

        # then build straight sections
        # branches = b.Branch.build_branches(self.G)
        # for br in branches:
        #     self.regions[br.id] = br


    def in_crossroad_region(self, e):
        tag = self.G[e[0]][e[1]][0][rg.Region.label_region]
        if tag == None:
            False
        else: 
            return self.regions[tag].is_crossroad()

    def get_adjacent_crossing_regions(self, n):
        result = set()
        for nb in self.G.neighbors(n):
            e = (n, nb)
            tag = self.G[e[0]][e[1]][0][rg.Region.label_region]
            if tag != None and self.regions[tag].is_crossroad():
                result.add(self.regions[tag].id)
        return list(result)

    def is_crossroad_node(self, n):
        tag = self.G.nodes[n][rg.Region.label_region]
        if tag == None:
            False
        else: 
            return self.regions[tag].is_crossroad()

    ######################### Functions used to prepare the graph ########################

    def remove_footways_and_parkings(G, keep_all_components):
        to_remove = []
        for u, v, a in G.edges(data = True):
            if "footway" in a or ("highway" in a and a["highway"] in ["footway", "cycleway", "path"]):
                to_remove.append((u, v))
            elif "service" in a and a["service"] in ["parking_aisle"]:
                to_remove.append((u, v))                
        G.remove_edges_from(to_remove)
        G = ox.utils_graph.remove_isolated_nodes(G)
        if not keep_all_components:
            G = ox.utils_graph.get_largest_component(G)
        return G

        
    ######################### Functions related to graph rendering (colors) ########################

    # return edge colors according to the region label
    def get_regions_colors(self):
        result = {}
        color = {}
        for e in self.G.edges:
            tag = self.G[e[0]][e[1]][e[2]][rg.Region.label_region]
            if tag == None:
                result[e] = (0.5, 0.5, 0.5, 0.5)
            else:
                if not tag in color:
                    color[tag] = Segmentation.random_color()
                result[e] = color[tag]
        return pd.Series(result)

    # return edge colors according to the region class label
    def get_regions_class_colors(self):
        result = {}
        for e in self.G.edges:
            tag = self.G[e[0]][e[1]][e[2]][rg.Region.label_region]
            if tag == None:
                result[e] = (0.5, 0.5, 0.5, 0.5)
            elif self.regions[tag].is_crossroad():
                result[e] = (0.8, 0, 0, 1)
            elif self.regions[tag].is_branch():
                result[e] = (0.6, 0.6, 0, 1)
            else:
                result[e] = (0.3, 0.3, 0.3, 1)

        return pd.Series(result)


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
                if tag == None:
                    values[tag] = (0.5, 0.5, 0.5, 0.5)
                else:
                    values[tag] = Segmentation.random_color()
            result[e] = values[tag]
        return pd.Series(result)
        



    def get_edges_reliability_colors(self):
        result = {}
        for e in self.G.edges:
            r_class = rel.Reliability.get_best_reliability_edge(self.G, e)
            r_value = self.G[e[0]][e[1]][e[2]][r_class]
            coef = (r_value - rel.Reliability.strongly_no) / (rel.Reliability.strongly_yes - rel.Reliability.strongly_no)
            coef = math.pow(coef, 2)
            if r_class == rel.Reliability.branch_reliability:
                result[e] = (0.6, 0.6, 0, coef)
            else:
                result[e] = (0.8, 0, 0, coef)
        return pd.Series(result)

    def get_nodes_reliability_colors(self):

        result = {}
        for n in self.G.nodes:
            r_class = rel.Reliability.get_best_reliability_node(self.G, n)
            r_value = self.G.nodes[n][r_class]
            coef = (r_value - rel.Reliability.strongly_no) / (rel.Reliability.strongly_yes - rel.Reliability.strongly_no)
            coef = math.pow(coef, 2)
            if r_class == rel.Reliability.branch_reliability:
                result[n] = (0.6, 0.6, 0, coef)
            elif r_class == rel.Reliability.boundary_reliability:
                result[n] = (0.1, 0, 0.8, coef)
            else:
                result[n] = (0.8, 0, 0, coef)


        return pd.Series(result)

    def get_boundary_node_colors(self):

        result = {}
        for n in self.G.nodes:
            nb_adj_crossings = len(self.get_adjacent_crossing_regions(n))
            nbnb = len(list(self.G.neighbors(n)))
            nbAdj = len([ nb for nb in self.G.neighbors(n) if rg.Region.unknown_region_edge_in_graph(self.G, (n, nb))])
            if nbnb == nbAdj:
                if nbnb == 1: # dead end
                    result[n] = (0.5, 0.5, 0.5, 0.1)
                elif rg.Region.unknown_region_node_in_graph(self.G, n):
                    result[n] = (0, 0, 0.5, 1) # node not taggued, possibly a missing crossing
                else:
                    if nb_adj_crossings >= 2:
                        result[n] = (0.6, 0.6, 0, 1) # splitter in a crossroad
                    elif nb_adj_crossings == 0 and self.is_crossroad_node(n):
                        result[n] = (1, 0, 0, 1) # single-node crossroad
                    else:
                        result[n] = (0, 0, 0, 0)
            else:
                if nb_adj_crossings >= 2:
                    result[n] = (0.6, 0.6, 0, 1) # splitter in a crossroad
                elif nb_adj_crossings == 0 and self.is_crossroad_node(n):
                    result[n] = (1, 0, 0, 1) # single-node crossroad
                else:
                    result[n] = (0, 0, 0, 0)
        return pd.Series(result)
