__author__ = 'lich'

import sys
sys.path.append("..")

from Topology.SpineLeaf import *
from Src.Routing import *
from random import choice
import gc
from SmartLearning.smartlearn import LearnSDN

#Define number of hidden nodes per layer with a list. For instance, [20, 10] means 2 hidden layers: the first with 20 nodes and the second with 10 nodes.
number_hidden_nodes_per_layer = [20, 20]
#Define type of activation function. 0 for logistic, 1 for tanh, 2 for soft plus, 3 for rectified linear unit and 4 for identity.
activation_function_type = 0
#Define exploration type. 0 for fixed epsilon and 1 for varying epsilon.
exploration_type = 1
#Define learning method. 0 for Q-learning, and 1 for R-learning.
learning_method = 0
#Define exploration probability from 0 to 1.
epsilon = 0.05
#Define learning rate from 0 to 1.
alpha = 0.1
#Define discount factor from 0 to 1.
gamma = 0.9
#Define learning parameter for average reward in R-learning.
beta = 0.1
#Define learning rate of neural network.
learning_rate = 0.3

class Qlearning(Routing):
    """
    This routing approach is specific for spine-leaf topology
    """
    def __init__(self, topo):
        Routing.__init__(self, topo)
        #self.numOfServers = topo.numOfServers
        #self.serverPerRack = topo.serverPerRack
        #self.numOfToRs = topo.numOfToRs
        #self.numOfCores = topo.numOfCores
        self.topo = topo
        self.QLearner = LearnSDN(self.topo.numOfCores, self.topo.numOfToRs, self.topo.numOfToRs, 2*self.topo.numOfToRs * self.topo.numOfCores, number_hidden_nodes_per_layer, activation_function_type, exploration_type, epsilon, alpha, gamma, beta, learning_rate, learning_method)

    def BuildAllPath(self):
        self.CalculateAllPath()

    def BuildPath(self, srcId, dstId, flow, state):
        self.CalculatePath(srcId, dstId, flow, state)

    def CalculateAllPath(self):
        """
        This function calculate path between each pair of servers with ECMP
        For spine-leaf, choosing a path is essentially choosing a spine to traverse
        """
        for srcId in range(self.numOfServers):
            #gc.collect()
            for dstId in range(self.topo.numOfServers):
                self.CalculatePath(srcId=srcId, dstId=dstId)

    def select_action(self, state, source_id, destination_id):
        # randomly choose a core switch. Delete this after implementing Qlearning algorithm
        #coreId = choice(range(self.topo.numOfServers + self.topo.numOfToRs, self.topo.numOfServers + self.topo.numOfToRs + self.topo.numOfCores))
        #return coreId
        source = source_id - self.topo.numOfServers
        destination = destination_id - self.topo.numOfServers
        action = self.QLearner.select_action(state, source, destination)
        action_id = self.topo.numOfServers + self.topo.numOfToRs + action
        return action_id

    def update(self, previous_state, source_id, destination_id, previous_action_id, current_state, reward):
        source = source_id - self.topo.numOfServers
        destination = destination_id - self.topo.numOfServers
        previous_action = previous_action_id - self.topo.numOfServers - self.topo.numOfToRs
        return self.QLearner.update(previous_state, source, destination, previous_action, current_state, reward)

    def CalculatePath(self, srcId, dstId, flow, state):
        # only self id is contained, if destination is self
        if srcId == dstId:
            self.pathList[srcId, dstId] = [srcId]
            return
        srcToRId = self.topo.numOfServers + srcId / self.topo.serverPerRack
        dstToRId = self.topo.numOfServers + dstId / self.topo.serverPerRack
        # if src and dst are in the same tor switch
        if srcToRId == dstToRId:
            self.pathList[srcId, dstId] = [srcId, srcToRId, dstId]
            return
        # src-dst must traverse core
        else:
            self.pathList[srcId, dstId] = [srcId, srcToRId, self.select_action(state, srcToRId, dstToRId), dstToRId, dstId]
    def __del__(self):
        pass
