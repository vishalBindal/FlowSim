import sys
sys.path.append("..")

from Src.Topology import *
from Src.Node import *
from Src.Link import *

SERVER = 0
TOR = 1
AGGR = 2
CORE = 3

num_servers = 320 
num_tor = 20
num_aggr = 20
num_core = 16
num_pods = 5
val_K = 8

server_to_tor_link = 400.0 * Gb
general_link = 100.0 * Gb

class CustomFatTree(Topology):
    def __init__(self):
        # initialize nodes and links
        Topology.__init__(self)
        # The topology used for HPCC experiments is an adaption of K=8
        self.K = val_K
        # calculate servers number
        self.CalServerNums()
        # calculate tor switch number
        self.CalToRNums()
        # calculate aggregate switch number
        self.CalAggrNums()
        # calculate core switch number
        self.CalCoreNums()

    def CreateTopology(self):
        # create nodes
        self.CreateNodes()
        # create links
        self.CreateLinks()

    def CreateLinks(self):
        """
        We build this topology as a directed graph.
        It indicates n1 --- n2 will translate into to edges: (1, 2) and (2, 1)
        """
        for serverId in range(self.numOfServers):
            numServersPerRack = self.numOfServers // self.numOfToRs
            torNodeId = self.numOfServers + serverId // numServersPerRack
            self.links[serverId, torNodeId] = Link((serverId, torNodeId))
            self.links[torNodeId, serverId] = Link((torNodeId, serverId))

            self.links[serverId, torNodeId].linkCap = server_to_tor_link
            self.links[torNodeId, serverId].linkCap = server_to_tor_link
            # print(serverId, torNodeId)

        for torId in range(self.numOfToRs):
            numTorsPerPod = self.numOfToRs // num_pods
            podId = torId // numTorsPerPod
            torNodeId = self.ConvertToNodeId(torId, TOR)
            for i in range(numTorsPerPod):
                t2aggrId = podId * numTorsPerPod + i
                aggrNodeId = self.ConvertToNodeId(t2aggrId, AGGR)
                self.links[torNodeId, aggrNodeId] = Link((torNodeId, aggrNodeId))
                self.links[aggrNodeId, torNodeId] = Link((aggrNodeId, torNodeId))

                self.links[torNodeId, aggrNodeId].linkCap = general_link
                self.links[aggrNodeId, torNodeId].linkCap = general_link
                # print(torNodeId, aggrNodeId)

        for aggrId in range(self.numOfAggrs):
            aggrNodeId = self.ConvertToNodeId(aggrId, AGGR)
            for j in range(self.K // 2):
                a2coreId = (aggrId % (self.K // 2)) * (self.K // 2) + j
                coreNodeId = self.ConvertToNodeId(a2coreId, CORE)
                self.links[aggrNodeId, coreNodeId] = Link((aggrNodeId, coreNodeId))
                self.links[coreNodeId, aggrNodeId] = Link((coreNodeId, aggrNodeId))

                self.links[aggrNodeId, coreNodeId].linkCap = general_link
                self.links[coreNodeId, aggrNodeId].linkCap = general_link
                # print(aggrNodeId, coreNodeId)

    def CreateNodes(self):
        # node id starts from 0
        # append server node
        self.AddNodes(self.numOfServers)
        # append tor switch node
        self.AddNodes(self.numOfToRs)
        # append aggregate switch node
        self.AddNodes(self.numOfAggrs)
        # append core switch nodes
        self.AddNodes(self.numOfCores)

    # calculate related metrics
    def CalServerNums(self):
        self.numOfServers = num_servers

    def CalToRNums(self):
        self.numOfToRs = num_tor

    def CalAggrNums(self):
        self.numOfAggrs = num_aggr

    def CalCoreNums(self):
        self.numOfCores = num_core

    def GetRackId(self, serverId):
        numServersPerRack = self.numOfServers // self.numOfToRs
        return serverId // numServersPerRack

    # def GetSameRack(self, serverId):
    #     # return the server in the same rack next to self
    #     neighborId = serverId + 1
    #     numServersPerRack = self.numOfServers // self.numOfToRs
    #     # we say, if the neighborId divides by numServersPerRack, it must be the first server in the next rack
    #     if neighborId % numServersPerRack == 0:
    #         neighborId -= numServersPerRack
    #     return neighborId

    # def GetOtherRack(self, serverId, n):
    #     """
    #     This will return a serverId in another rack.
    #     """
    #     # return the server in the next rack with the same location, an offset of K/2
    #     neighborId = (serverId + self.K / 2) % n
    #     # neighborId is 0 means, this is the n'th server
    #     if neighborId == 0:
    #         neighborId = n
    #     return neighborId


    # def GetPodId(self, rackId):
    #     return (rackId - 1) / (self.K / 2) + 1

    def ConvertToNodeId(self, id, role):
        """
        Convert regular device id into node id.
        Four roles are defined: 0:server, 1:tor switch, 2:aggregate switch, 3:core switch
        """
        if role == 0:
            return id
        elif role == 1:
            return id + self.numOfServers
        elif role == 2:
            return id + self.numOfServers + self.numOfToRs
        elif role == 3:
            return id + self.numOfServers + self.numOfToRs + self.numOfAggrs
        else:
            return 0

    # add n nodes to topology instance
    def AddNodes(self, n):
        for id in range(n):
            node = Node()
            node.nodeId = len(self.nodes)
            self.nodes.append(node)

    # return corresponding role
    def GetServerNode(self, serverId):
        nodeId = self.ConvertToNodeId(serverId, SERVER)
        return self.nodes[nodeId]
    def GetToRNode(self, torId):
        nodeId = self.ConvertToNodeId(torId, TOR)
        return self.nodes[nodeId]
    def GetAggrNode(self, aggrId):
        nodeId = self.ConvertToNodeId(aggrId, AGGR)
        return self.nodes[nodeId]
    def GetCoreNode(self, coreId):
        nodeId = self.ConvertToNodeId(coreId, CORE)
        return self.nodes[nodeId]


    def __del__(self):
        pass
