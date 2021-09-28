#!/usr/bin/env python3
# coding: utf-8

import argparse


import networkx as nx
import osmnx as ox

import crseg.segmentation as cs

parser = argparse.ArgumentParser(description="Download OpenStreetMap data within Paris city, only preserving streets. Result will be saved in data/graph.gpkg")

# load and validate parameters
args = parser.parse_args()

G = ox.graph_from_place("Paris, France", network_type="all", retain_all=False, truncate_by_edge=True, simplify=False)


# remove sidewalks, cycleways
keep_all_components = False
G = cs.Segmentation.remove_footways_and_parkings(G, keep_all_components)

# save data
ox.io.save_graph_geopackage(G)