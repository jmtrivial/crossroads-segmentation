#!/usr/bin/env python3
# coding: utf-8

import argparse


import networkx as nx
import osmnx as ox

import crseg.segmentation as cs
import crseg.reliability as r
import crseg.region as rg

# set parser
parser = argparse.ArgumentParser(description="Build a basic description of the crossroad located at the requested coordinate.")

group_input = parser.add_argument_group('Input region', "Define the input region from OSM (by coordinates or by name) or from a local file")
input_params = group_input.add_mutually_exclusive_group(required=True)
input_params.add_argument('--by-coordinates', nargs=2, help='Load input from OSM using the given latitude', type=float)

input_params.add_argument('--by-name', help='Load input from OSM using a predefined region', choices=["Manon", "Nicolas", "Jérémy-master", "Jérémy-thèse1", "obélisque", "lafayette", "Gauthier", "Pasteur-Duclaux"])
input_params.add_argument('--from-graphml', help='Load road graph from a GraphML file', type=argparse.FileType('r'))


parser.add_argument('-r', '--radius', help='Radius (in meter) where the crossroads will be reconstructed. Default: 150m', type=float, default=150)
parser.add_argument('-v', '--verbose', help='Verbose messages', action='store_true')

parser.add_argument('--skip-processing', help="Do not compute segmentation (can be useful to store OSM data without modification, or to use result of a previous run by loading a GraphML.", action='store_true')

group_display = parser.add_argument_group("Display", "Activate a display")
group_display.add_argument('--display-reliability', help='Display reliability computed before any segmentation', action='store_true')
group_display.add_argument('-d', '--display', help='Display crossroads in the reconstructed region', action='store_true')
group_display.add_argument('--display-segmentation', help='Display segmentation (crossroads and branches) in the reconstructed region', action='store_true')

group_output = parser.add_argument_group("Output", "Export intermediate properties or final data in a dedicated format")
group_output.add_argument('--to-text-all', help='Generate a text description of all reconstructed crossings', action='store_true')
group_output.add_argument('--to-text', help='Generate a text description of crossing in the middle of the map', action='store_true')
group_output.add_argument('--to-gexf', help='Generate a GEXF file with the computed graph (contains reliability scores for edges and nodes). Some metadata will not be exported.', type=argparse.FileType('w'))
group_output.add_argument('--to-graphml', help='Generate a GraphML file with the computed graph (contains reliability scores for edges and nodes)', type=argparse.FileType('w'))
group_output.add_argument('--to-json-all', help='Generate a json description of the crossings', type=argparse.FileType('w'))
group_output.add_argument('--to-json', help='Generate a json description of the crossing in the middle of the map', type=argparse.FileType('w'))

# load and validate parameters
args = parser.parse_args()

# get parameters
if args.by_coordinates:
    latitude = args.by_coordinates[0]
    longitude = args.by_coordinates[1]
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
elif byname == "Pasteur-Duclaux":
    latitude = 45.77364
    longitude = 3.07525

from_graphml = args.from_graphml

# set input parameters
radius = args.radius
verbose = args.verbose

display = args.display
display_reliability = args.display_reliability
display_segmentation = args.display_segmentation
to_text_all = args.to_text_all
to_text = args.to_text
to_gexf = args.to_gexf
to_graphml = args.to_graphml
to_json = args.to_json
to_json_all = args.to_json_all
skip_processing = args.skip_processing


# load data

if verbose:
    print("=== DOWNLOADING DATA ===")

if from_graphml:
    G = ox.io.load_graphml(from_graphml.name, 
                                node_dtypes={r.Reliability.boundary_reliability: float, 
                                        r.Reliability.crossroad_reliability: float,
                                        rg.Region.label_region: int},
                                edge_dtypes={r.Reliability.crossroad_reliability: float,
                                            rg.Region.label_region: int})
    # load parameters
    latitude = G.graph["cr.latitude"]
    longitude = G.graph["cr.longitude"]
    radius = G.graph["cr.radius"]

    print(type(G))    
else:
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
    print("Coordinates:", latitude, longitude)
    print("Radius:", radius)


if skip_processing:
    print("=== SKIP INITIALISATION ===")
    seg = cs.Segmentation(G, False)
else:
    if verbose:
        print("=== INITIALISATION ===")

    # segment it using topology and semantic
    seg = cs.Segmentation(G)

if display_reliability:
    print("=== RENDERING RELIABILITY ===")

    ec = seg.get_edges_reliability_colors()

    nc = seg.get_nodes_reliability_colors()

    ox.plot.plot_graph(G, edge_color=ec, node_color=nc)


if skip_processing:
    print("=== SKIP SEGMENTATION ===")
else:
    if display or display_segmentation or to_text or to_text_all or to_gexf or to_json or to_json_all or to_graphml: # or any other next step
        if verbose:
            print("=== SEGMENTATION ===")
        seg.process()


if to_text_all:
    if verbose:
            print("=== TEXT OUTPUT ===")
    print(seg.to_text_all())

if to_text:
    if verbose:
            print("=== TEXT OUTPUT ===")
    print(seg.to_text(longitude, latitude))

if to_json:
    if verbose:
            print("=== EXPORT IN JSON ===")
    seg.to_json(to_json.name, longitude, latitude)

if to_json_all:
    if verbose:
            print("=== EXPORT IN JSON ===")
    seg.to_json_all(to_json_all.name)

if display:
    if verbose:
        print("=== RENDERING ===")

    ec = seg.get_regions_class_colors()

    nc = seg.get_nodes_reliability_on_regions_colors()

    ox.plot.plot_graph(G, edge_color=ec, node_color=nc)

if display_segmentation:
    if verbose:
        print("=== RENDERING SEGMENTATION ===")

    ec = seg.get_regions_colors()

    nc = seg.get_nodes_regions_colors()

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

if to_graphml:
    if verbose:
        print("=== EXPORT IN GraphML ===")
        # Store parameters
        G.graph["cr.latitude"] = latitude
        G.graph["cr.longitude"] = longitude
        G.graph["cr.radius"] = radius
        for r in seg.regions:
            G.graph[rg.Region.regiontag_prefix + str(r)] = "crossroad" if seg.regions[r].is_crossroad() else "branch"
        # TODO: store for each region id its kind (crossing or branch)
        ox.io.save_graphml(G, to_graphml.name)
