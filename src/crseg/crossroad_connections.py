
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
        self.regionsByNode = {}
        for rid in self.regions:
            for n in self.regions[rid].nodes:
                self.add_node_region(rid, n)

        # for each region, the list of its adjacent regions (only links for crossroads, and only crossroads for links)
        self.adjacencies = {}
        # for each junction node
        for n in self.regionsByNode:
            # for reach region associated to this node
            for r1 in self.regionsByNode[n]:
                # add an adjacency between this region and all regions connected via the current node
                self.add_adjacencies(r1, n, self.regionsByNode[n])

        # compute a list of connections between crossroads
        self.connected_crossroads = []
        # for each crossroad region
        for cr in self.crossroads:
            # for each adjacent links
            for l in self.adjacencies[cr]:
                # then find the reachable crossings from this link
                for cr2 in self.adjacencies[l]:
                    # only considering the ones with an ID higher to the ID of the initial crossroad region
                    if self.regions[cr].id < self.regions[cr2].id:
                        #add them as a pair
                        self.connected_crossroads.append((cr, cr2))


    def add_adjacencies(self, r1, node, regions):
        if not r1 in self.adjacencies:
            self.adjacencies[r1] = {}
        for r2 in regions:
            if r2 != r1 and self.get_typology(r1) != self.get_typology(r2):
                if not r2 in self.adjacencies[r1]:
                    self.adjacencies[r1][r2] = []
                self.adjacencies[r1][r2].append(node)

    def get_typology(self, rid):
        if rid in self.crossroads:
            return CrossroadConnections.typology_crossroad
        elif rid in self.links:
            return CrossroadConnections.typology_link
        else:
            return CrossroadConnections.typology_unknown
            

    def add_node_region(self, rid, nid):
        if not nid in self.regionsByNode:
            self.regionsByNode[nid] = []
        self.regionsByNode[nid].append(rid)

    def get_pairs(self):
        seen = {}
        dupes = []

        for x in self.connected_crossroads:
            if x not in seen:
                seen[x] = 1
            else:
                if seen[x] == 1:
                    dupes.append(x)
                seen[x] += 1

        return dupes