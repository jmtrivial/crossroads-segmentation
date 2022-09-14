
import networkx as nx
import osmnx as ox
import pandas as pd
import random
import math
import json


from . import crossroad as cr
from . import region as rg
from . import regionfactory as rf
from . import reliability as rel
from . import crossroad_connections as cc

class Segmentation:

    def __init__(self, G, init=True, C0 = 2, C1 = 2.5, C2 = 4, max_cycle_elements = 10):
        self.G = G
        self.regions = {}
        self.C0 = C0
        self.C1 = C1
        self.C2 = C2
        self.max_cycle_elements = max_cycle_elements
        random.seed()
        if init:
            rel.Reliability.init_attr(self.G)
        else:
            self.regions = rf.RegionFactory.rebuild_regions_from_tags(self.G)


    def set_tags_only_regions(self):
        # clear tags
        for n in self.G.nodes:
            self.G.nodes[n][rg.Region.label_region] = -1
        for u, v, a in self.G.edges(data = True):
            self.G[u][v][0][rg.Region.label_region] = -1

        # set tags wrt crossroad regions
        for rid in self.regions:
            region = self.regions[rid]
            if region.is_crossroad():
                for n in region.nodes:
                    self.G.nodes[n][rg.Region.label_region] = rid
                for e in region.edges:
                    self.G[e[0]][e[1]][0][rg.Region.label_region] = rid
                


    def process(self):

        # init flags
        rg.Region.init_attr(self.G)

        self.regions = {}

        # first build crossroads
        crossroads = cr.Crossroad.build_crossroads(self.G, self.C0)
        for c in crossroads:
            self.regions[c.id] = c

        # group subparts of crossroads together if they are part of the same crossing (using street names)
        clusters = cr.Crossroad.get_clusters(crossroads, self.C1)

        # for each cluster
        for cluster in clusters:
            # merge them
            if len(cluster) > 1:
                cluster[0].merge(cluster[1:])
            for o in cluster[1:]:
                del self.regions[o.id]

        # maximum length for missing maths
        scale_missing = self.C0
        # add inner paths and missing boundaries
        self.add_missing_paths(scale = scale_missing)
        
        # build links between regions
        links = rf.RegionFactory.build_links_between_crossings(self.G, self.regions)
        self.regions.update(links)
        self.set_tags_only_regions()

        # merge crossings
        self.merge_linked_crossroads()

        # add inner paths and missing boundaries (again)
        self.add_missing_paths(scale = scale_missing, boundaries = False)

        # create branch regions
        for rid in self.regions:
            if self.regions[rid].is_crossroad():
                self.regions[rid].compute_branches()
        
        for rid in self.inner_regions:
            self.inner_regions[rid].compute_branches()
            

    def merge_linked_crossroads(self):
        self.inner_regions = {}
        newIDs = {}

        cconnections = cc.CrossroadConnections(self.regions, self.C2)

        # merge multi crossings (triangles, rings, etc)
        for cycle in cconnections.get_cycles(self.max_cycle_elements):
            cWithIDs = [cr if cr[0] in self.regions else (newIDs[cr[0]], cr[1]) for cr in cycle][:-1]
            ids = [x[0] for x in cWithIDs]
            
            if len(set(ids)) > 1:
                firstID = ids[0]
                # add all regions as inner regions (of a bigger one)
                for id in ids:
                    self.add_inner_region(self.regions[id])

                for cr1, cr2 in zip(cWithIDs, cWithIDs[1:]):
                    id2 = newIDs[cr2[0]] if cr2[0] in newIDs else cr2[0]

                    # add paths that connects cr1 and cr2
                    self.regions[firstID].add_paths([x[0] for x in cr2[1]])
                    if id2 != firstID:
                        self.regions[firstID].merge([self.regions[id2]])
                        del self.regions[id2]
                        newIDs[id2] = firstID
                        for nid in newIDs:
                            if newIDs[nid] == id2:
                                newIDs[nid] = firstID

        # merge bi-connected crossings
        for pairs in cconnections.get_pairs():
            id1 = pairs[0] if pairs[0] in self.regions else newIDs[pairs[0]]
            id2 = pairs[1] if pairs[1] in self.regions else newIDs[pairs[1]]
            if id1 != id2:
                # add the two regions to the inner regions (of a bigger one)
                self.add_inner_region(self.regions[id1])
                self.add_inner_region(self.regions[id2])
                # add paths that are connecting these two regions
                self.regions[id1].add_paths([x[0] for x in pairs[2]])
                # merge the two regions
                self.regions[id1].merge([self.regions[id2]])
                # remove the old one
                del self.regions[id2]
                # update IDs
                newIDs[id2] = id1
                for nid in newIDs:
                    if newIDs[nid] == id2:
                        newIDs[nid] = id1


    def add_inner_region(self, region):
        # clone the given region and add it to the inner_regions structure
        newRegion = rf.RegionFactory.clone(region)
        self.inner_regions[newRegion.id] = newRegion

    def add_missing_paths(self, boundaries = True, scale = 2):
        for rid in self.regions:
            region = self.regions[rid]
            if region.is_crossroad():
                region.add_missing_paths(boundaries = boundaries, scale = scale)


    def in_crossroad_region(self, e):
        tag = self.G[e[0]][e[1]][0][rg.Region.label_region]
        if tag == -1:
            False
        else: 
            return self.regions[tag].is_crossroad()


    def get_adjacent_crossroad_regions(self, n):
        result = []
        for nb in self.G.neighbors(n):
            e = (n, nb)
            tag = self.G[e[0]][e[1]][0][rg.Region.label_region]
            if tag != -1 and self.regions[tag].is_crossroad():
                result.append(self.regions[tag].id)
            else:
                result.append(-1)
        return result

    def is_crossroad_node(self, n):
        tag = self.G.nodes[n][rg.Region.label_region]
        if tag == -1:
            False
        else: 
            return self.regions[tag].is_crossroad()

    ######################### Functions used to prepare the graph ########################

    def prepare_network_remove_non_highway(G):
        to_remove = []
        for u, v, k, a in G.edges(data=True, keys=True):
            if not "highway" in a:
                # remove a specific edge. If k==0, it will remove the first edge, and it might remain supplementary edge with a key != 0.
                # To solve this issue, at the end of this function, we use a trick by transforming data to a DiGraph, then to a MutliDiGraph (the original
                # data structure used by the program)
                to_remove.append((u, v, k))
        G.remove_edges_from(to_remove)

    def prepare_network_remove_small_ways(G, remove_parking_aisle=True, remove_footways=True, remove_cycleways=True):
        to_remove = []
        # remove footways and parkings
        for u, v, a in G.edges(data=True):
            if remove_footways:
                if "footway" in a or ("highway" in a and a["highway"] in ["footway"]):
                    if not ("psv" in a and a["psv"] in ["yes"]):
                        to_remove.append((u, v))
                    # add missing crossings
                    if not "highway" in G.nodes[u]:
                        G.nodes[u]["highway"] = "crossing"
                    if not "highway" in G.nodes[v]:
                        G.nodes[v]["highway"] = "crossing"
                if ("highway" in a and a["highway"] in ["path", "pedestrian", "steps"]) and not ("psv" in a and a["psv"] in ["yes"]):
                    to_remove.append((u, v))
            if remove_cycleways and "highway" in a and a["highway"] in ["cycleway"]:
                to_remove.append((u, v))
            if remove_parking_aisle:
                if "service" in a and a["service"] in ["parking_aisle"]:
                    to_remove.append((u, v))
        G.remove_edges_from(to_remove)


    def get_score_from_tags(tags):
        score = len(tags)
        if "name" in tags:
            score += 10
        return score

    def identify_best_way(G, u, v, ways):
        best = -1
        score = -1
        for w in ways:
            s = Segmentation.get_score_from_tags(w[2])
            if s > score:
                score = s
                best = w
        return best


    def prepare_network_remove_supplementary_highways(G):
        to_remove = []

        for u in G:
            for v in G[u]:
                ways = [(w, 0, G[u][v][w]) for w in G[u][v] if "highway" in G[u][v][w]]
                osmids = [w[2]["osmid"] for w in ways]

                if u in G[v]:
                    ways += [(w, 1, G[v][u][w]) for w in G[v][u] if "highway" in G[v][u][w] and G[v][u][w]["osmid"] not in osmids]
                if len(ways) > 1:
                    best_way_id = Segmentation.identify_best_way(G, u, v, ways)
                    to_remove += [(u, v, wid[0]) if wid[1] == 0 else (v, u, wid[0]) for wid in ways if not (wid[0] == best_way_id[0] and wid[1] == best_way_id[1])]
        G.remove_edges_from(to_remove)
                    

    def prepare_network(G, keep_all_components=False, remove_non_highway=True,
                        remove_parking_aisle=True,
                        remove_footways=True, remove_cycleways=True):

        if remove_non_highway:
            Segmentation.prepare_network_remove_non_highway(G)

        if remove_footways or remove_cycleways or remove_parking_aisle:
            Segmentation.prepare_network_remove_small_ways(G, remove_parking_aisle, remove_footways, remove_cycleways)

        Segmentation.prepare_network_remove_supplementary_highways(G)

        G = ox.utils_graph.remove_isolated_nodes(G)
        if not keep_all_components and len(G.nodes) != 0:
            G = ox.utils_graph.get_largest_component(G)
        # double transformation to fix keys != 0
        return nx.MultiDiGraph(nx.DiGraph(G))

        
    ######################### Functions related to graph rendering (colors) ########################

    # return edge colors according to the region label
    def get_regions_colors(self):
        result = {}
        color = {}
        for e in self.G.edges:
            tag = self.G[e[0]][e[1]][e[2]][rg.Region.label_region]
            if tag == -1:
                result[e] = (0.5, 0.5, 0.5, 0.5)
            else:
                if not tag in color:
                    color[tag] = Segmentation.predefined_color(len(color))
                result[e] = color[tag]
        return pd.Series(result)

    # return edge colors according to the region class label
    def get_regions_class_colors(self):
        result = {}
        for e in self.G.edges:
            tag = self.G[e[0]][e[1]][e[2]][rg.Region.label_region]
            if tag == -1:
                result[e] = (0.5, 0.5, 0.5, 0.5)
            elif self.regions[tag].is_crossroad():
                result[e] = (0.8, 0, 0, 1)
            elif self.regions[tag].is_branch():
                result[e] = (0.6, 0.6, 0, 1)
            else:
                result[e] = (0.3, 0.3, 0.3, 1)

        return pd.Series(result)


    def predefined_color(id):
        # source: https://colorbrewer2.org/#type=qualitative&scheme=Paired&n=12 (removing red)
        colors = [ (166/255, 206/255, 227/255),
                   (31/255, 120/255, 180/255),
                   (178/255, 223/255, 138/255),
                   (51/255, 160/255, 44/255),
                   (251/255, 154/255, 153/255),
                   (253/255, 191/255, 111/255),
                   (255/255, 127/255, 0/255),
                   (202/255, 178/255, 214/255),
                   (106/255, 61/255, 154/255),
                   (255/255, 255/255, 153/255),
                   (177/255, 89/255, 40/255)]
        if id < len(colors):
            return colors[id]
        else:
            return Segmentation.random_color()

    def random_color(only_bg = False):
        r1 = math.pi * random.random()
        r2 = math.pi * random.random()
        start = 0.2
        coef = 0.8
        return (0 if only_bg else (start + coef * abs(math.sin(r1)) * abs(math.sin(r2))), \
                start + coef * abs(math.cos(r1)) * abs(math.sin(r2)), \
                start + coef * abs(math.sin(r1)) * abs(math.cos(r2)), 
                1)

    # return edge colors using one random color per label
    def get_edge_random_colors_by_attr(G, label, values = {}):
        result = {}
        i = 0
        for e in G.edges:
            tag = G[e[0]][e[1]][e[2]][label]
            if not tag in values:
                if tag == -1:
                    values[tag] = (0.5, 0.5, 0.5, 0.5)
                else:
                    values[tag] = Segmentation.predefined_color(i)
                    i += 1
            result[e] = values[tag]
        return pd.Series(result)
        
    def get_nodes_reliability_on_regions_colors(self):

        result = {}
        for n in self.G.nodes:
            r_class = rel.Reliability.get_best_reliability_node(self.G, n)
            r_value = self.G.nodes[n][r_class]
            coef = (r_value - rel.Reliability.strongly_no) / (rel.Reliability.strongly_yes - rel.Reliability.strongly_no)
            coef = math.pow(coef, 2)
            if r_class == rel.Reliability.crossroad_reliability:
                result[n] = (0.8, 0, 0, coef)
            elif r_class == rel.Reliability.boundary_reliability:
                adj = self.get_adjacent_crossroad_regions(n)
                # in the middle of a branch
                if len([n for n in adj if n != -1]) == 0:
                    result[n] = (0, 0, 0.6, coef)
                # inside a region
                elif len(list(set([n for n in adj if n != -1]))) == 1 and len([n for n in adj if n != -1]) != 1:
                    result[n] = (1, 0.6, 0.6, coef)
                # in a boundary
                else:
                    result[n] = (0.6, 0.6, 0, coef)

            else: # branch
                result[n] = (0, 0, 0, 0)


        return pd.Series(result)


    def get_edges_reliability_colors(self):
        result = {}
        for e in self.G.edges:
            r_value = self.G[e[0]][e[1]][e[2]][rel.Reliability.crossroad_reliability]
            coef = (r_value - rel.Reliability.strongly_no) / (rel.Reliability.strongly_yes - rel.Reliability.strongly_no)
            coef = math.pow(coef, 2)
            result[e] = (1, 1, 1, coef)
        return pd.Series(result)

    def get_nodes_reliability_colors(self):

        result = {}
        for n in self.G.nodes:
            r_class = rel.Reliability.get_best_reliability_node(self.G, n)
            r_value = self.G.nodes[n][r_class]
            coef = (r_value - rel.Reliability.strongly_no) / (rel.Reliability.strongly_yes - rel.Reliability.strongly_no)
            coef = math.pow(coef, 2)
            if r_class == rel.Reliability.boundary_reliability:
                result[n] = (0.1, 0, 0.8, coef)
            else:
                result[n] = (0.8, 0, 0, coef)


        return pd.Series(result)

    def get_boundary_node_colors(self):

        result = {}
        for n in self.G.nodes:
            nb_adj_crossings = len(list(set([r for r in self.get_adjacent_crossroad_regions(n) if r != -1])))
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

    def get_nodes_regions_colors(self):
        result = {}
        i = 0
        for n in self.G.nodes:
            if len(list(self.G.neighbors(n))) <= 2:
                result[n] = (0, 0, 0, 0)
            else:
                label = self.G.nodes[n][rg.Region.label_region]
                if label < 0:
                    result[n] = (0, 0, 0, 0)
                else:
                    nb_edge_in_region = len([nb for nb in self.G[n] if self.G[n][nb][0][rg.Region.label_region] == label])
                    if nb_edge_in_region == 0:
                        result[n] = Segmentation.predefined_color(i)
                    else:
                        result[n] = (0, 0, 0, 0)

        return pd.Series(result)

    # input: a list of crossroads (main crossroad and possibly contained crossroads)
    def get_regions_colors_from_crossroad(self, cr):
        crids = [ c.id for c in cr ]
        mainCR = max(cr, key=lambda x: len(x.nodes))
        maxID = max(crids)
        result = {}
        color = {}
        for e in self.G.edges:
            tag = self.G[e[0]][e[1]][e[2]][rg.Region.label_region]
            if not tag in crids:
                # check if it's a branch of the main crossroad
                bid = mainCR.get_branch_id(e)
                if bid == -1:
                    result[e] = (0.5, 0.5, 0.5, 0.1)
                else:
                    tag = maxID + bid + 1
                    if not tag in color:
                        color[tag] = Segmentation.predefined_color(len(color))
                    result[e] = color[tag]
            else:
                ncrs = len([ c for c in cr if c.has_edge(e) ])
                result[e] = (math.sqrt(ncrs / len(crids)), 0, 0, 1)
        return pd.Series(result)

    # input: a list of crossroads (main crossroad and possibly contained crossroads)
    def get_nodes_regions_colors_from_crossroad(self, cr):
        crids = [ c.id for c in cr ]
        mainCR = max(cr, key=lambda x: len(x.nodes))
        result = {}
        for n in self.G.nodes:
            if len(list(self.G.neighbors(n))) <= 2:
                result[n] = (0, 0, 0, 0)
            else:
                label = self.G.nodes[n][rg.Region.label_region]
                if not label in crids:
                    result[n] = (0, 0, 0, 0)
                else:
                    # get regions that contains this node with no adjacent edge
                    ncrn = len([ r for r in cr if r.has_node(n) and len(r.edges_with_node(n)) == 0])
                    if ncrn == 0:
                        result[n] = (0, 0, 0, 0)
                    else:
                        result[n] = (math.sqrt(ncrn / len(crids)), 0, 0, 1)

        return pd.Series(result)

    ######################### text descriptions ########################

    # return a list of crossroads (main crossroad and possibly contained crossroads)
    def get_crossroad(self, longitude, latitude, multiscale = False):
        distance = -1
        middle = -1
        for rid in self.regions:
            if self.regions[rid].is_crossroad():
                region = self.regions[rid]
                x1 = self.G.nodes[region.get_center()]["x"]
                y1 = self.G.nodes[region.get_center()]["y"]
                d = ox.distance.great_circle_vec(lat1=y1, lng1=x1, lat2=latitude, lng2=longitude)
                if distance < 0 or d < distance:
                    distance = d
                    middle = rid

        if multiscale:
            result = []
            result.append(self.regions[middle])
            for rid in self.inner_regions:
                if self.regions[middle].contains(self.inner_regions[rid]):
                    result.append(self.inner_regions[rid])
            return result
        else:
            return [self.regions[middle]]

    def to_text(self, longitude, latitude, multiscale = False):
        cs = self.get_crossroad(longitude, latitude, multiscale)
        result = ""
        for i, c in enumerate(cs):
            if i != 0:
                result += "\n\n"
            result += c.to_text()
        return result

    def to_text_all(self, multiscale = False):
        result = ""
        for rid in self.regions:
            if self.regions[rid].is_crossroad():
                result += self.regions[rid].to_text()
                result += "\n"
                result += "\n"

        if multiscale:
            result = "Inner crossroads:"
            result += "\n"
            for rid in self.inner_regions:
                result += self.inner_regions[rid].to_text()
                result += "\n"
                result += "\n"
        return result

    ######################### json descriptions ########################

    def to_json(self, filename, longitude, latitude, multiscale = False):
        data = [x.to_json_data() for x in self.get_crossroad(longitude, latitude, multiscale)]

        with open(filename, 'w') as outfile:
            json.dump(data, outfile)


    def to_json_all(self, filename, multiscale = False):
        data = []
        for rid in self.regions:
            if self.regions[rid].is_crossroad():
                entry = self.regions[rid].to_json_data()
                data.append(entry)
        
        if multiscale:
            for rid in self.inner_regions:
                entry = self.inner_regions[rid].to_json_data()
                data.append(entry)

        with open(filename, 'w') as outfile:
            json.dump(data, outfile)

    
    ######################### geopackage description ########################

    def to_geopackage(self, filename):
        # add new attributes
        nx.set_node_attributes(self.G, values = "", name = "crossroad")
        nx.set_node_attributes(self.G, values = "", name = "sub_crossroad")
        nx.set_edge_attributes(self.G, values = "", name = "crossroad")
        nx.set_edge_attributes(self.G, values = "", name = "sub_crossroad")
        nx.set_edge_attributes(self.G, values = "", name = "branch")

        # fill attributes according to the computed regions
        for rid in self.regions:
            if self.regions[rid].is_crossroad():
                self.regions[rid].set_graph_attributes("crossroad", "branch")

        for rid in self.inner_regions:
            self.inner_regions[rid].set_graph_attributes("sub_crossroad")

        # save graph
        ox.io.save_graph_geopackage(self.G, filename)


