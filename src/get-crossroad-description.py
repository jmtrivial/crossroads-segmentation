#!/usr/bin/env python3
# coding: utf-8

import argparse


import networkx as nx
import osmnx as ox

import crseg.segmentation as cs

# set parser
parser = argparse.ArgumentParser(description="Build a basic description of the crossroad located at the requested coordinate.")

group_coords = parser.add_argument_group('selection by coordinates', "Describe a request region by coordinates")
group_coords.add_argument('--lat', help='Requested latitude', type=float)
group_coords.add_argument('--lng', help='Requested longitude', type=float)


group_byname = parser.add_argument_group('selection by name', "Describe a request region by internal name")
group_byname.add_argument('--by-name', help='Requested crossroad, selection by name', choices=["Manon", "Nicolas", "Jérémy-master", "Jérémy-thèse1", "obélisque", "lafayette", "Gauthier"])

parser.add_argument('-r', '--radius', help='Radius (in meter) where the crossroads will be reconstructed. Default: 150m', type=float, default=150)
parser.add_argument('-v', '--verbose', help='Verbose messages', action='store_true')


group_display = parser.add_argument_group("Display", "Activate a display")
group_display.add_argument('--display-reliability', help='Display reliability computed before any segmentation', action='store_true')
group_display.add_argument('-d', '--display', help='Display crossroads in the reconstructed region', action='store_true')

group_output = parser.add_argument_group("Output", "Export intermediate properties or final data in a dedicated format")
group_output.add_argument('--to-text-all', help='Generate a text description of all reconstructed crossings', action='store_true')
group_output.add_argument('--to-text', help='Generate a text description of crossing in the middle of the map', action='store_true')
group_output.add_argument('--to-gexf', help='Generate a GEXF file with the computed graph (contains reliability scores for edges and nodes)', type=argparse.FileType('w'))
group_output.add_argument('--to-json-all', help='Generate a json description of the crossings', type=argparse.FileType('w'))
group_output.add_argument('--to-json', help='Generate a json description of the crossing in the middle of the map', type=argparse.FileType('w'))

# load and validate parameters
args = parser.parse_args()

# get parameters
latitude = args.lat
longitude = args.lng
byname = args.by_name

if byname == "Nicolas":
    latitude = 45.77204
    longitude = 3.08085
elif byname == "Manon":
    latitude = 45.77725
    longitude = 3.07279
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

# set input parameters
radius = args.radius
verbose = args.verbose

display = args.display
display_reliability = args.display_reliability
to_text_all = args.to_text_all
to_text = args.to_text
to_gexf = args.to_gexf
to_json = args.to_json
to_json_all = args.to_json_all

if verbose:
    print("Coordinates:", latitude, longitude)
    print("Radius:", radius)


# load data

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

# build an undirected version of the graph
G = ox.utils_graph.get_undirected(G)



if verbose:
    print("=== INITIALISATION ===")

# segment it using topology and semantic
seg = cs.Segmentation(G)

if display_reliability:
    print("=== RENDERING RELIABILITY ===")

    ec = seg.get_edges_reliability_colors()

    nc = seg.get_nodes_reliability_colors()

    ox.plot.plot_graph(G, edge_color=ec, node_color=nc)


if display or to_text or to_text_all or to_gexf or to_json or to_json_all: # or any other next step
    if verbose:
        print("=== SEGMENTATION ===")
    seg.process()


if to_text_all:
    print(seg.to_text_all())

if to_text:
    print(seg.to_text(longitude, latitude))

if to_json:
    seg.to_json(to_json.name)

if to_json_all:
    seg.to_json(to_json_all.name)

if display:
    if verbose:
        print("=== RENDERING ===")

    ec = seg.get_regions_class_colors()

    nc = seg.get_nodes_reliability_on_regions_colors()

    ox.plot.plot_graph(G, edge_color=ec, node_color=nc)


if to_gexf:
    if verbose:
        print("=== EXPORT IN GEXF ===")

    att_list = ['geometry']
    for n1, n2, d in G.edges(data=True):
        for att in att_list:
            d.pop(att, None)

    # Simplify after removing attribute
    nx.write_gexf(G, to_gexf.name)
