#!/usr/bin/env python3
# coding: utf-8

import argparse


import networkx as nx
import osmnx as ox

import crseg.segmentation as cs


parser = argparse.ArgumentParser(description="Build a basic description of the crossroad located at the requested coordinate.")

group_coords = parser.add_argument_group('Coordinates', "Describe a request region by coordinates")
group_coords.add_argument('--lat', help='Requested latitude', type=float)
group_coords.add_argument('--lng', help='Requested longitude', type=float)


group_byname = parser.add_argument_group('Name', "Describe a request region by internal name")
group_byname.add_argument('--by-name', help='Requested crossroad, selection by name', choices=["Manon", "Nicolas", "Jérémy-master", "Jérémy-thèse1", "obélisque", "lafayette", "Gauthier"])


parser.add_argument('-r', '--radius', help='Radius (in meter) where the crossroads will be reconstructed', type=float, default=150)
parser.add_argument('-d', '--display', help='Display crossroads in the reconstructed region', action='store_true')
parser.add_argument('-v', '--verbose', help='Verbose messages', action='store_true')
args = parser.parse_args()


latitude = args.lat
longitude = args.lng
byname = args.by_name

if byname == "Nicolas":
    latitude = 45.77204
    longitude = 3.08085
elif byname == "Manon":
    latitude = 45.77722
    longitude = 3.07295
elif byname == "Jérémy-master":
    latitude = 45.77631
    longitude = 3.09015
elif byname == "Jérémy-thèse1":
    latitude = 45.77351
    longitude = 3.09015
elif byname == "obélisque":
    latitude = 45.77373
    longitude  = 3.08685
elif byname == "lafayette":
    latitude = 45.77338
    longitude = 3.09226
elif byname == "Gauthier":
    latitude = 45.77712
    longitude = 3.09622

radius = args.radius

verbose = args.verbose
display = args.display


if verbose:
    print("=== DOWNLOADING DATA ===")

G = ox.graph_from_point((latitude, longitude), dist=radius, network_type="all", retain_all=False, truncate_by_edge=True, simplify=False)



if verbose:
    print("=== PREPROCESSING (1) ===")

# remove sidewalks, cycleways
keep_all_components = False
G = cs.Segmentation.remove_footways_and_parkings(G, keep_all_components)

if verbose:
    print("=== PREPROCESSING (2) ===")
G = ox.utils_graph.get_undirected(G)

if verbose:
    print("=== SEGMENTATION ===")
seg = cs.Segmentation(G)

seg.process()


if display:
    print("=== RENDERING ===")

    #ec = seg.get_regions_colors()
    ec = seg.get_regions_class_colors()
    #ec = seg.get_edges_reliability_colors()

    #nc = seg.get_nodes_reliability_colors()
    nc = seg.get_nodes_reliability_on_regions_colors()
    #nc = seg.get_boundary_node_colors()

    ox.plot.plot_graph(G, edge_color=ec, node_color=nc)


