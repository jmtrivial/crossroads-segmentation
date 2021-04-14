


import networkx as nx
import osmnx as ox

class Segmentation:
    label_region = "region"
    label_boundary = "boundary"


    label_boundary_inside_region = 0
    label_boundary_crossing = 5
    label_boundary_traffic_signals = 10
    label_boundary_deadend = 1


    def __init__(self):
        pass

    def process(self, G):
        # first set region flags
        i = 0
        lr = Segmentation.label_region
        nx.set_edge_attributes(G, values=None, name=lr)
        for u, v, a in G.edges(data=True):
            if a[lr] == None:
                self.dfs_region(G, [u, v], Segmentation.no_highway_nodes, lr, i)
                i += 1

        # then set boundary flags
        lb = Segmentation.label_boundary
        nx.set_node_attributes(G, values=Segmentation.label_boundary_inside_region, name=lb)
        for e in G.nodes:
            if "highway" in G.nodes[e]:
                if G.nodes[e]["highway"] == "crossing":
                    G.nodes[e][lb] = Segmentation.label_boundary_crossing
                else:
                    G.nodes[e][lb] = Segmentation.label_boundary_traffic_signals
            elif len(list(G.neighbors(e))) == 1:
                G.nodes[e][lb] = Segmentation.label_boundary_deadend
        

    # return edge colors according to the region label
    def get_regions_attr(self, G):
        return ox.plot.get_edge_colors_by_attr(G, attr=Segmentation.label_region)

    # return edge colors according to the boundary class
    def get_boundaries_attr(self, G):
        return ox.plot.get_node_colors_by_attr(G, attr=Segmentation.label_boundary)

    # a function to distinguish between boundary and no boundary edges
    def no_highway_nodes(G, node):
        if not "highway" in G.nodes[node]:
            return G.neighbors(node)
        else:
            return iter([])

    # a generic depth-first-search algorithm driven by a function that distinguish between
    # boundary and no boundary edges. Regions are flaggued using label=value
    def dfs_region(self, G, source_edge, iter_neighbors_func, label, value):
        nodes = [source_edge[0], source_edge[1]]
        if G[source_edge[0]][source_edge[1]][0][label] != None:
            return
        G[source_edge[0]][source_edge[1]][0][label]= value
        for start in nodes:
            stack = [(start, iter_neighbors_func(G, start))]
            while stack:
                parent, children = stack[-1]
                try:
                    child = next(children)
                    if G[parent][child][0][label] == None:
                        G[parent][child][0][label] = value
                        stack.append((child, iter_neighbors_func(G, child)))
                except StopIteration:
                    stack.pop()

