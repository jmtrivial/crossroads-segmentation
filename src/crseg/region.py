import networkx as nx
import osmnx as ox
import pandas as pd
import random
import math


from . import utils as u
from . import reliability as r



class Region:

    id_region = 0

    label_region = "region"

    def __init__(self, G):
        self.id = Region.id_region
        self.G = G
        self.edges = []
        self.nodes = []
        Region.id_region += 1

    def is_crossroad(self):
        return False

    def is_branch(self):
        return False

    def init_attr(G):
        nx.set_edge_attributes(G, values=None, name=Region.label_region)
        nx.set_node_attributes(G, values=None, name=Region.label_region)

    def unknown_region_node_in_graph(G, n):
        return G.nodes[n][Region.label_region] == None

    def unknown_region_edge_in_graph(G, e):
        return G[e[0]][e[1]][0][Region.label_region] == None

    def unknown_region_node(self, n):
        return Region.unknown_region_node_in_graph(self.G, n)

    def unknown_region_edge(self, e):
        return Region.unknown_region_edge_in_graph(self.G, e)

    def clear_node_region_in_grah(G, n):
        G.nodes[n][Region.label_region] = None

    def add_node(self, n):
        self.nodes.append(n)
        self.G.nodes[n][Region.label_region] = self.id

    def add_edge(self, e):
        self.nodes.append(e)
        self.G[e[0]][e[1]][0][Region.label_region] = self.id