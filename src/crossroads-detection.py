#!/usr/bin/env python3
# coding: utf-8

import networkx as nx
import osmnx as ox

import crseg.segmentation as cs

print("=== DOWNLOADING DATA ===")

# Croisement de Manon
#G = ox.graph_from_bbox(north=45.77811, west=3.07116, south=45.77644, east=3.07537, network_type="drive", retain_all=False, truncate_by_edge=True, simplify=False)

# détail proche croisement Manon
#G = ox.graph_from_point((45.77704, 3.07491), dist=50, network_type="drive", retain_all=False, truncate_by_edge=True, simplify=False)

# voisinage large du croisement Manon
G = ox.graph_from_point((45.77722, 3.07295), dist=300, network_type="drive", retain_all=False, truncate_by_edge=True, simplify=False)

# croisement de Jérémy (master)
#G = ox.graph_from_point((45.77631, 3.09015), dist=200, network_type="drive", retain_all=False, truncate_by_edge=True, simplify=False)

# croisement en croix de Jérémy (thèse)
#G = ox.graph_from_point((45.77351, 3.09015), dist=200, network_type="drive", retain_all=False, truncate_by_edge=True, simplify=False)

# croisement en T près du CRDV
#G = ox.graph_from_point((45.78032, 3.08051), dist=100, network_type="all", retain_all=False, truncate_by_edge=True, simplify=False)

# croisement de Nicolas
#G = ox.graph_from_point((45.77204, 3.08085), dist=150, network_type="drive", retain_all=False, truncate_by_edge=True, simplify=False)

# croisement décalé près du CRDV
#G = ox.graph_from_point((45.78070, 3.07912), dist=70, network_type="drive", retain_all=False, truncate_by_edge=True, simplify=False)

# abords jardin Lecoq (sud)
#G = ox.graph_from_point((45.77162, 3.08946), dist=300, network_type="all", retain_all=False, truncate_by_edge=True, simplify=False)


# Clermont-Ferrand en entier
#G = ox.graph_from_place("Clermont-Ferrand, France", network_type="all", retain_all=False, truncate_by_edge=True, simplify=False)

# remove sidewalks, cycleways
G = cs.Segmentation.remove_footways(G)
G = ox.utils_graph.get_undirected(G)

print("=== SEGMENTATION ===")
seg = cs.Segmentation(G)

seg.process()


print("=== RENDERING ===")

ec = seg.get_regions_class_colors()
nc = seg.get_boundaries_colors(False)

ox.plot.plot_graph(G, edge_color=ec, node_color=nc)

