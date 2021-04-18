
import networkx as nx
import osmnx as ox
import pandas as pd
import random
import math


from . import region as rg
from . import reliability as rel

class Segmentation:

    def __init__(self, G):
        self.G = G
        self.regions = []
        random.seed()

    def process(self):

        # init flags
        rg.Region.init_attr(self.G)
        rel.Reliability.init_attr(self.G)

        # build basic regions using strong boundary nodes
        for u, v in self.G.edges():
            if rg.Region.unknown_region((u, v, 0), self.G):
                self.build_basic_region([u, v])


        # TODO: ça semble pas marcher des masses

        # split the regions using a clustering approach 
        # new_regions = []
        # for r in self.regions:
        #     if r.is_unknown():
        #         nr = r.split_by_clusters()
        #         new_regions += nr
        # self.regions += new_regions


        # merge regions where a boundary is classified as a reliable inner node and has adjacent regions that are 
        # not too long paths to a reliable boundary
        # TODO: if a crossing is close to two crossroads, it should be the boundary of the clostest
        # for n in self.G.nodes:
        #     if rel.Reliability.is_weakly_in_crossroad(self.G, n) and rg.Region.is_boundary_node(self.G, n):
        #         regions = [ r for r in self.regions if n in r.boundaries_nodes and (rel.Reliability.is_boundary_region(r) or rel.Reliability.is_inner_crossing_region(r))]
        #         if len(regions) > 1:
        #             self.mergeRegions(regions)

        # then detect strong regions. It remains unknown regions we'll handle just after
        # for r in self.regions:
        #     r.set_strong_region_class()
        # return

        # # # then split all unknown regions at crossings
        # new_regions = []
        # for r in self.regions:
        #     if r.is_unknown():
        #         nr = r.split_by_clusters(maximal = True)
        #         new_regions += nr
        # self.regions += new_regions


        # # # then detect regions
        # for r in self.regions:
        #     r.set_final_region_class()


        # after this process, consolidate crossroads:
        # for r in self.regions:
        #     # - if a no-labelled region is a short path and adjacent to crossroad region, it's (part of) a crossroad
        #     if r.is_unknown() and r.is_small_path() and (r.has_adjacent_crossoroad(self.regions) or r.has_traffic_signals_boundary()):
        #         r.set_is_crossroad()
        #     # - if a branch region is adjacent to a crossroad region and has a traffic_signals boundary node with only 2 neighbors at the opposite extremity, it is (part of) a crossroad
        #     if r.is_branch() and r.is_small_path_between_crossroad_and_traffic_signals(self.regions): 
        #         r.set_is_crossroad()
        #     if r.is_branch() and r.has_junction_edge_attr():
        #         r.set_is_crossroad()

        # finally, merge connected branches in a 2-neighbors boundary
        # TODO

        # merge adjacent crossings if one of them is a simple path
        # TODO

        # merge two crossings if they are not adjacent, but connected by more than one (small) way
        # TODO

        # consider weak (nodes without semantic) and strong boundaries (crossing, traffic_signal on a 2-edges node, ..., adjacent to a long branch)
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
        return Segmentation.get_edge_random_colors_by_attr(self.G, rg.Region.label_region)

    # return edge colors according to the region class label
    def get_regions_class_colors(self):
        colors = { rg.Region.label_region_unknown: (0.3, 0.3, 0.3, 1), \
                rg.Region.label_region_crossroad: (0.8, 0, 0, 1), \
                rg.Region.label_region_branch: (0.6, 0.6, 0, 1)}
        return Segmentation.get_edge_random_colors_by_attr(self.G, rg.Region.label_region_class, colors)


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
            tag = self.G.nodes[e][rg.Region.label_boundary]
            if full_details:
                result[e] = values[tag]
            else:
                if tag == rg.Region.boundary_classes["inside"]:
                    result[e] = (0, 0, 0, 0)
                else:
                    result[e] = (0.7, 0.5, 1, 1)

        return pd.Series(result)

    def get_edges_reliability_colors(self):
        result = {}
        for e in self.G.edges:
            r_class = Reliability.get_best_reliability_edge(self.G, e)
            r_value = self.G[e[0]][e[1]][e[2]][r_class]
            coef = (r_value - Reliability.strongly_no) / (Reliability.strongly_yes - Reliability.strongly_no)
            coef = math.pow(coef, 2)
            if r_class == Reliability.branch_reliability:
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

    ######################### Functions related to region segmentation ########################

    # a function to distinguish between boundary and no boundary edges
    def no_strong_boundaries(G, node):
        if not rel.Reliability.is_strong_boundary(G, node):
            return G.neighbors(node)
        else:
            return iter([])

    # a generic depth-first-search algorithm driven by a function that distinguish between
    # boundary and no boundary edges. 
    def build_basic_region(self, source_edge):
        region = rg.Region(self.G)

        region.add_node(source_edge[0])
        region.add_node(source_edge[1])

        nodes = [source_edge[0], source_edge[1]]
        if not rg.Region.unknown_region((source_edge[0], source_edge[1], 0), self.G):
            return
        region.add_edge((source_edge[0], source_edge[1], 0))
        for start in nodes:
            stack = [(start, Segmentation.no_strong_boundaries(self.G, start))]
            while stack:
                parent, children = stack[-1]
                try:
                    child = next(children)
                    if rg.Region.unknown_region((parent, child, 0), self.G):
                        region.add_node(child)
                        region.add_edge((parent, child, 0))
                        stack.append((child, Segmentation.no_strong_boundaries(self.G, child)))
                except StopIteration:
                    stack.pop()
        self.regions.append(region)

    def mergeRegions(self, regions):
        for region in regions[1:]:
            regions[0].merge(region)
        self.regions = [r for r in self.regions if r not in regions[1:]]
            

