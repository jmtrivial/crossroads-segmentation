import networkx as nx
import osmnx as ox
import pandas as pd
import random
import math


from . import utils as u
from . import reliability as r
from . import clustering as c



class Region:

    # during the clustering process inside a not classified region, significant nodes (boundaries and biffurcation) are clustered in a 
    # single region if their distance to the group is less than this value
    maximum_cluster_distance = 10

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
    
    def __eq__(self, other):
        return self.edge_label == other.edge_label

    def init_attr(G):
        nx.set_edge_attributes(G, values=None, name=Region.label_region)
        nx.set_edge_attributes(G, values=Region.label_region_unknown, name=Region.label_region_class)
        nx.set_node_attributes(G, values=Region.boundary_classes["inside"], name=Region.label_boundary)

    def get_adjacent_edge_labels(G, n):
        labels = set()
        for e in G.edges(n):
            labels.add(G[e[0]][e[1]][0][Region.label_region])

        return list(labels)

    def merge(self, otherRegion):

        # first add edges
        for e in otherRegion.edges:
            self.add_edge(e)

        # then add new inner nodes
        for n in otherRegion.inner_nodes:
            self.add_inner_node(n)

        #then add nodes from boundary nodes
        for b in otherRegion.boundaries_nodes:
            if b in self.boundaries_nodes:
                # if no other region is adjacent to this node, it is not a boundary
                if len(Region.get_adjacent_edge_labels(self.G, b)) == 1:
                    self.remove_node(b)
                    self.add_inner_node(b)
            else:
                self.add_boundary_node(b)
        
    def is_empty(self):
        return len(self.edges) == 0 and len(self.boundaries_nodes) == 0 and len(self.inner_nodes) == 0


    def has_biffurcation_inner_node(self):
        for n in self.inner_nodes:
            if len(list(self.G.neighbors(n))) > 2:
                return True
        return False

    def get_biffurcation_inner_node(self):
        result = []
        for n in self.inner_nodes:
            if len(list(self.G.neighbors(n))) > 2:
                result.append(n)
        return result

    def is_path(self):
        return len(self.boundaries_nodes) == 2 and not self.has_biffurcation_inner_node()

    def get_length(self):
        length = 0
        for e in self.edges:
            x1 = self.G.nodes[e[0]]["x"]
            y1 = self.G.nodes[e[0]]["y"]
            x2 = self.G.nodes[e[1]]["x"]
            y2 = self.G.nodes[e[1]]["y"]
            length += ox.distance.great_circle_vec(lat1=y1, lng1=x1, lat2=y2, lng2=x2)
        return length

    def is_small_path(self, threshold = maximum_cluster_distance):
        if len(self.boundaries_nodes) != 2:
            return False
        
        return self.get_length() < threshold



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
        if r.Reliability.is_strong_boundary(self.G, n):
            self.add_boundary_node(n)
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
                self.G.nodes[b][lb] = Region.boundary_classes["other"]
                return False
        else:
            return True

    def is_boundary_node(G, b):
        return G.nodes[b][Region.label_boundary] != Region.boundary_classes["inside"]

    def has_edge(self, n1, n2):
        return (n1, n2, 0) in self.edges or (n2, n1, 0) in self.edges

    def get_inner_nodes_by_reliability_upto(self, key, value):
        result = []
        for n in self.inner_nodes:
            if self.G.nodes[n][key] > value:
                result.append(n)
        return result

    def set_final_region_class(self):
        if self.region_class == Region.label_region_unknown:
            if r.Reliability.is_final_branch_region(self):
                self.set_region_class(Region.label_region_branch)
            elif r.Reliability.is_final_crossroad_region(self):
                self.set_region_class(Region.label_region_crossroad)


    def set_strong_region_class(self):
        branch = False
        crossroad = False
        if r.Reliability.is_strong_branch_region(self):
            self.set_region_class(Region.label_region_branch)
        elif r.Reliability.is_strong_crossroad_region(self):
            self.set_region_class(Region.label_region_crossroad)

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



    def recompute_nodes(self):
        nodes = {}
        for e in self.edges:
            for i in range(0, 2):
                if e[i] in nodes:
                    nodes[e[i]] += 1
                else:
                    nodes[e[i]] = 1

        self.inner_nodes = []
        self.boundaries_nodes = []

        for n in nodes:
            nbnb = len(list(self.G.neighbors(n)))
            if nodes[n] != nbnb or nbnb == 1:
                self.add_boundary_node(n)
            else:
                self.add_inner_node(n)
                self.G.nodes[n][Region.label_boundary] = Region.boundary_classes["inside"]



    # assuming that subregions is a partition of the edges in the current region,
    # it splits the region by creating new regions, and 
    def split_by_edge_partition(self, subregions):
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

                if not last:
                    result.append(nregion)

        # remove empty regions (should not append)
        result = [r for r in result if not r.is_empty()]        

        # then update nodes in each new region
        self.recompute_nodes()
        for r in result:
            r.recompute_nodes()

        return result


    # split regions using a clustering of stongly branch nodes, strongly crossroad nodes and boundary nodes.
    # if a cluster has a single biffurcation node, it corresponds to a multi-boundary node (that will be a crossroad)
    # otherwise, the cluster and the contained edges are a new region that corresponds to a crossroad
    # if nodes are in a single cluster, it means that the region is a crossroad region
    # This function updates the current region and return a list of supplementary regions
    def split_by_clusters(self, maximal = False):
        clustering = c.Clustering(self)

        if maximal:
            biffurcation_nodes = self.get_biffurcation_inner_node() + self.boundaries_nodes
            clustering.set_seeds([biffurcation_nodes])
            clustering.set_maximum_distances([Region.maximum_cluster_distance])
            subregions = clustering.process()
        else:
            possible_branch_nodes = self.get_inner_nodes_by_reliability_upto(r.Reliability.branch_reliability, r.Reliability.weakly_yes)
            possible_crossroad_nodes = self.get_inner_nodes_by_reliability_upto(r.Reliability.crossroad_reliability, r.Reliability.weakly_yes)

            clustering.set_seeds([self.boundaries_nodes + possible_branch_nodes, self.boundaries_nodes + possible_crossroad_nodes])
            clustering.set_maximum_distances([-1, Region.maximum_cluster_distance])
            subregions = clustering.process()
        
        if len(subregions) > 1:
            supplementary_regions = self.split_by_edge_partition(subregions)
            return supplementary_regions
        return []
