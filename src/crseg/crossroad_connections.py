

class CrossroadConnections:

    typology_crossroad = 1
    typology_link = 2
    typology_unknown = 0

    def __init__(self, regions):
        self.regions = regions

        self.init_structure()

    def init_structure(self):

        # build the list of crossroad and links
        self.crossroads = []
        self.links = []

        for rid in self.regions:
            if self.regions[rid].is_crossroad():
                self.crossroads.append(rid)
            elif self.regions[rid].is_link():
                self.links.append(rid)

        # for each node, build the list of intersecting regions
        self.nodes = {}
        for rid in self.regions:
            for n in self.regions[rid].nodes:
                self.add_node_region(rid, n)

        # for each region, the list of its adjacent regions (only links for crossroads, and only crossroads for links)
        self.adjacencies = {}
        for n in self.nodes:
            for r1 in self.nodes[n]:
                self.add_adjacencies(r1, self.nodes[n])
        

    def add_adjacencies(self, r1, connected)
        if not r1 in self.adjacencies:
            self.adjacencies[r1] = []
        for r2 in connected:
            if r2 != r1 and self.get_typology(r1) != self.get_typology(r2):
                self.adjacencies[r1].append(r2)

    def get_typology(self, rid):
        if rid in self.crossroads:
            return CrossroadConnections.typology_crossroad
        elif rid in self.links:
            return CrossroadConnections.typology_link
        else:
            return CrossroadConnections.typology_unknown
            

    def add_node_region(self, rid, nid):
        if not nid in self.nodes:
            self.nodes[nid] = []
        self.nodes[nid].append(rid)

    def get_pairs(self):
        result = []
        # TODO

        return result