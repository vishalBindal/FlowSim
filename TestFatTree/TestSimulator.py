__author__ = 'lich'

import sys
sys.path.append("..")

from Src.Simulator import *
from TestFlowScheduler import *
from Routing.ECMP_CustomFatTree import *
from Topology.CustomFatTree import * 

def main():
    sim = Simulator()
    testTopo = CustomFatTree()
    testTopo.CreateTopology()
    sim.AssignTopology(topo=testTopo)
    sim.AssignRoutingEngine(Routing=ECMP)
    sim.AssignScheduler(FlowScheduler=TestFlowScheduler, args=('Input/Fbtraffic_modif.txt'))
    sim.Run()

if __name__ == "__main__":
    main()
