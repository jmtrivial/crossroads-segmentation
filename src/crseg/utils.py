import osmnx as ox


class Util:

    def distance(G, node1, node2):
        x1 = G.nodes[node1]["x"]
        y1 = G.nodes[node1]["y"]
        x2 = G.nodes[node2]["x"]
        y2 = G.nodes[node2]["y"]
        return ox.distance.great_circle_vec(lat1=y1, lng1=x1, lat2=y2, lng2=x2)

    def get_adjacent_streetnames(G, node):
        streetnames = set()
        for nb in G.neighbors(node):
            if "name" in G[node][nb][0]:
                streetnames.add(G[node][nb][0]["name"])
            else:
                streetnames.add(None)
        return list(streetnames)
