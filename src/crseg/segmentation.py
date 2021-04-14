


import networkx as nx
import osmnx as ox
import pandas as pd
import random
import math

class Segmentation:
    label_region = "region"
    label_boundary = "boundary"


    label_boundary_inside_region = 0
    label_boundary_crossing = 5
    label_boundary_traffic_signals = 10
    label_boundary_deadend = 1


    def __init__(self):
        random.seed()

    def process(self, G):
        # first set region flags
        i = 0
        lr = Segmentation.label_region
        nx.set_edge_attributes(G, values=None, name=lr)
        for u, v, a in G.edges(data=True):
            if a[lr] == None:
                self.dfs_region(G, [u, v], Segmentation.no_highway_nodes, lr, i)
                i += 1

        # then set boundary flags
        lb = Segmentation.label_boundary
        nx.set_node_attributes(G, values=Segmentation.label_boundary_inside_region, name=lb)
        for e in G.nodes:
            if "highway" in G.nodes[e]:
                if G.nodes[e]["highway"] == "crossing":
                    G.nodes[e][lb] = Segmentation.label_boundary_crossing
                else:
                    G.nodes[e][lb] = Segmentation.label_boundary_traffic_signals
            elif len(list(G.neighbors(e))) == 1:
                G.nodes[e][lb] = Segmentation.label_boundary_deadend
        

    # return edge colors according to the region label
    def get_regions_attr(self, G):
        return Segmentation.get_edge_random_colors_by_attr(G, Segmentation.label_region)


    def random_color():
        r1 = math.pi * random.random()
        r2 = math.pi * random.random()
        coef = 0.5
        return (coef * abs(math.sin(r1)) * abs(math.sin(r2)), \
                coef * abs(math.cos(r1)) * abs(math.sin(r2)), \
                coef * abs(math.sin(r1)) * abs(math.cos(r2)), 
                1)

    # return edge colors using one random color per label
    def get_edge_random_colors_by_attr(G, label):
        values = {}
        result = {}
        for e in G.edges:
            tag = G[e[0]][e[1]][e[2]][label]
            if not tag in values:
                values[tag] = Segmentation.random_color()
            result[e] = values[tag]
        return pd.Series(result)
        


    # return edge colors according to the boundary class
    def get_boundaries_attr(self, G):
        values = { Segmentation.label_boundary_inside_region: (0, 0, 0, 0), \
                Segmentation.label_boundary_crossing: (1, 1, 0, 1), \
                Segmentation.label_boundary_traffic_signals: (1, 0, 0, 1), \
                Segmentation.label_boundary_deadend: (0, 0, 1, 1)}
        result = {}
        for e in G.nodes:
            tag = G.nodes[e][Segmentation.label_boundary]
            result[e] = values[tag]
        return pd.Series(result)

    # a function to distinguish between boundary and no boundary edges
    def no_highway_nodes(G, node):
        if not "highway" in G.nodes[node]:
            return G.neighbors(node)
        else:
            return iter([])

    # a generic depth-first-search algorithm driven by a function that distinguish between
    # boundary and no boundary edges. Regions are flaggued using label=value
    def dfs_region(self, G, source_edge, iter_neighbors_func, label, value):
        nodes = [source_edge[0], source_edge[1]]
        if G[source_edge[0]][source_edge[1]][0][label] != None:
            return
        G[source_edge[0]][source_edge[1]][0][label]= value
        for start in nodes:
            stack = [(start, iter_neighbors_func(G, start))]
            while stack:
                parent, children = stack[-1]
                try:
                    child = next(children)
                    if G[parent][child][0][label] == None:
                        G[parent][child][0][label] = value
                        stack.append((child, iter_neighbors_func(G, child)))
                except StopIteration:
                    stack.pop()

