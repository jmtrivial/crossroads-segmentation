


import networkx as nx
import osmnx as ox
import pandas as pd
import random
import math


from . import region as r
from . import utils as u



class Reliability:

    # minimum distance for a path to be considered as a branch in the first pass
    distance_inner_branch = 50
    
    # maximum distance for a path to be considered as not part of a crossroad in the first pass
    distance_inner_crossroad = 15

    # almost equivalent to the maximum distance for a crossing to be considered 
    # as the boundary of a crossroad
    max_distance_boundary_crossing = 20 

    # maximum distance for an inner region of a crossroad to be considered as a crossroad section
    max_distance_between_crossroads = 15

    boundary_reliability = "reliability boundary"
    branch_reliability = "reliability branch"
    crossroad_reliability = "reliability.crossroad"


    moderate_boundary = [ "stop", "traffic_signals", "motorway_junction" ]
    possible_boundary = [ "crossing"]
    strongly_no_boundary_attr = [ "bus_stop", "milestone", "steps", "elevator" ]


    strongly_yes = 1000
    strongly_no = 0

    uncertain = (strongly_yes + strongly_no) / 2

    weakly_yes = (strongly_yes + uncertain) / 2
    weakly_no = (strongly_no + uncertain) / 2

    moderate_yes = (weakly_yes + strongly_yes) / 2
    moderate_no = (weakly_no + strongly_no) / 2


    def init_attr(G):
        nx.set_node_attributes(G, values=Reliability.uncertain, name=Reliability.boundary_reliability)
        nx.set_node_attributes(G, values=Reliability.uncertain, name=Reliability.branch_reliability)
        nx.set_node_attributes(G, values=Reliability.uncertain, name=Reliability.crossroad_reliability)
        Reliability.compute_nodes_reliability(G)

        nx.set_edge_attributes(G, values=Reliability.uncertain, name=Reliability.branch_reliability)
        nx.set_edge_attributes(G, values=Reliability.uncertain, name=Reliability.crossroad_reliability)
        Reliability.compute_edges_reliability(G)

    def compute_edges_reliability(G):

        for e in G.edges():
            length = u.Util.distance(G, e[0], e[1])
            if "junction" in G[e[0]][e[1]][0]:
                G[e[0]][e[1]][0][Reliability.crossroad_reliability] = Reliability.strongly_yes
            elif length > Reliability.distance_inner_branch:
                G[e[0]][e[1]][0][Reliability.branch_reliability] = Reliability.strongly_yes

    def compute_nodes_reliability(G):

        # TODO: consider distances relative to the kind of way (primary, etc.)
        for n in G.nodes:
            nb_neighbors = len(list(G.neighbors(n)))
            if nb_neighbors == 1:
                G.nodes[n][Reliability.boundary_reliability] = Reliability.strongly_yes
            else:
                if "highway" in G.nodes[n]:
                    if G.nodes[n]["highway"] in Reliability.strongly_no_boundary_attr:
                        G.nodes[n][Reliability.boundary_reliability] = Reliability.moderate_no
                    elif G.nodes[n]["highway"] in Reliability.possible_boundary and nb_neighbors <= 3:
                        G.nodes[n][Reliability.boundary_reliability] = Reliability.strongly_yes
                    elif G.nodes[n]["highway"] in Reliability.moderate_boundary and nb_neighbors <= 3:
                        G.nodes[n][Reliability.boundary_reliability] = Reliability.moderate_yes
                        G.nodes[n][Reliability.crossroad_reliability] = Reliability.moderate_yes
                    elif nb_neighbors >= 3:
                        G.nodes[n][Reliability.crossroad_reliability] = Reliability.strongly_yes
                else:
                    if nb_neighbors == 2:
                        all = True
                        for nb in G.neighbors(n):
                            if u.Util.distance(G, n, nb) < Reliability.distance_inner_branch:
                                all = False
                                break
                        if all:
                            G.nodes[n][Reliability.boundary_reliability] = Reliability.strongly_no
                            G.nodes[n][Reliability.branch_reliability] = Reliability.strongly_yes
                    elif nb_neighbors >= 4:
                            G.nodes[n][Reliability.crossroad_reliability] = Reliability.strongly_yes
                    elif nb_neighbors >= 3:
                            adj_streetnames = u.Util.get_adjacent_streetnames(G, n)
                            # if all branches has same street name, not rely on a crossroad
                            if len(adj_streetnames) == 1 and not adj_streetnames[0] == None:
                                G.nodes[n][Reliability.crossroad_reliability] = Reliability.moderate_no
                            elif len(adj_streetnames) > 1:
                                # more than one street name, it is probably part of a crossroad
                                G.nodes[n][Reliability.crossroad_reliability] = Reliability.moderate_yes

    def get_best_reliability_edge(G, e):
        if G[e[0]][e[1]][e[2]][Reliability.branch_reliability] > G[e[0]][e[1]][e[2]][Reliability.crossroad_reliability]:
            return Reliability.branch_reliability
        else:
            return Reliability.crossroad_reliability


    def get_best_reliability_node(G, n):
        if G.nodes[n][Reliability.branch_reliability] > G.nodes[n][Reliability.crossroad_reliability] and \
            G.nodes[n][Reliability.branch_reliability] > G.nodes[n][Reliability.boundary_reliability]:
            return Reliability.branch_reliability
        elif G.nodes[n][Reliability.crossroad_reliability] > G.nodes[n][Reliability.branch_reliability] and \
            G.nodes[n][Reliability.crossroad_reliability] > G.nodes[n][Reliability.boundary_reliability]:
            return Reliability.crossroad_reliability
        else:
            return Reliability.boundary_reliability

    def is_strong_boundary(G, n):
        return G.nodes[n][Reliability.boundary_reliability] == Reliability.strongly_yes

    def is_weakly_boundary(G, n):
        return G.nodes[n][Reliability.boundary_reliability] >= Reliability.weakly_yes

    def is_weakly_no_boundary(G, n):
        return G.nodes[n][Reliability.boundary_reliability] <= Reliability.weakly_no

    def is_strong_no_boundary(G, n):
        return G.nodes[n][Reliability.boundary_reliability] == Reliability.strongly_no


    def is_strong_in_branch(G, n):
        return G.nodes[n][Reliability.branch_reliability] == Reliability.strongly_yes

    def is_weakly_in_branch(G, n):
        return G.nodes[n][Reliability.branch_reliability] >= Reliability.weakly_yes

    def is_weakly_not_in_branch(G, n):
        return G.nodes[n][Reliability.branch_reliability] <= Reliability.weakly_no

    def is_strong_not_in_branch(G, n):
        return G.nodes[n][Reliability.branch_reliability] == Reliability.strongly_no


    def is_strong_in_crossroad(G, n):
        return G.nodes[n][Reliability.crossroad_reliability] == Reliability.strongly_yes

    def is_weakly_in_crossroad(G, n):
        return G.nodes[n][Reliability.crossroad_reliability] >= Reliability.weakly_yes

    def is_weakly_not_in_crossroad(G, n):
        return G.nodes[n][Reliability.crossroad_reliability] <= Reliability.weakly_no

    def is_strong_not_in_crossroad(G, n):
        return G.nodes[n][Reliability.crossroad_reliability] == Reliability.strongly_no


    def is_strong_in_crossroad_edge(G, e):
        return G[e[0]][e[1]][0][Reliability.crossroad_reliability] == Reliability.strongly_yes

    def is_strong_in_branch_edge(G, e):
        return G[e[0]][e[1]][0][Reliability.branch_reliability] == Reliability.strongly_yes

    def is_final_branch_region(region):
        if Reliability.is_strong_branch_region(region):
            return True

        # TODO

        return False
    
    def is_final_crossroad_region(region):
        if Reliability.is_strong_crossroad_region(region):
            return True

        # TODO

        return False

    def is_strong_branch_region(region):
        # if one edge or inner node has a strong_crossroad flag, return False
        for e in region.edges:
            if Reliability.is_strong_in_crossroad_edge(region.G, e):
                return False
        for n in region.inner_nodes:
            if Reliability.is_weakly_in_crossroad(region.G, n):
                return False

        for n in region.inner_nodes:
            if Reliability.is_strong_in_branch(region.G, n):
                return True

        for e in region.edges:
            if Reliability.is_strong_in_branch_edge(region.G, e):
                return True
        return False

    def is_strong_crossroad_region(region):
        # if one edge or inner node has a strong_branch flag, return False
        for e in region.edges:
            if Reliability.is_strong_in_branch_edge(region.G, e):
                return False
        for n in region.inner_nodes:
            if Reliability.is_weakly_in_branch(region.G, n):
                return False

        # if it is a long path
        if region.is_path() and region.get_length() > Reliability.distance_inner_crossroad:
            return False

        for e in region.edges:
            if Reliability.is_strong_in_crossroad_edge(region.G, e):
                return True

        for n in region.inner_nodes + region.boundaries_nodes:
            if Reliability.is_strong_in_crossroad(region.G, n):
                return True

        return False

    def is_boundary_region(r):
        if not r.is_path():
            return False
        if Reliability.is_strong_branch_region(r):
            return False
        if r.get_length() >= Reliability.max_distance_boundary_crossing:
            return False

        for n in r.boundaries_nodes:
            if Reliability.is_weakly_boundary(r.G, n):
                return True
        return False
        
    def is_inner_crossing_region(r):
        if r.is_path() and r.get_length() > Reliability.max_distance_between_crossroads:
            return False

        found = False
        for n in r.boundaries_nodes:
            if Reliability.is_weakly_in_crossroad(r.G, n):
                found = True
            else:
                return False
        

        return found
