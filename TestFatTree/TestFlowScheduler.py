__author__ = 'lich'
import sys
sys.path.append("..")

from Src.FlowScheduler import *
from Src.Flow import *

inDir = "Input/"
outDir = "Output/"

class TestFlowScheduler(FlowScheduler):
    def AssignFlows(self, args):
        """
        Args is the file name listing all flows
        """
        f_name = args
        f = open(f_name, "r")
        for line in f.readlines():
            l = line.split()
            flow = Flow()
            flow.startId = int(l[0])
            flow.endId = int(l[1])
            flow.SetFlowSize(float(l[2]))
            flow.startTime = float(l[3]) - 2.0
            flow.flowId = len(self.flows) + 1
            self.flows.append(flow)
        FlowScheduler.AssignFlows(self)
        f.close()

    def PrintFlows(self):
        f_name = outDir + "flowInfo.txt"
        f = open(f_name, "w")
        # f_name = outDir + "flowPlot.dat"
        # f_plot = open(f_name, "w")
        for flow in self.finishedFlows:
            flowTransTime = flow.finishTime - flow.startTime + 1e-6 * len(flow.pathLinkIds)
        #     print >> f, "flow %d used %f\t%f\t%f" % (flow.flowId, flowTransTime, flow.startTime, flow.finishTime)
            flow.bw = (flow.flowSize / flowTransTime) / Gb
        # # print bandwidth (in Mbps) in each line with sorted format
        # bwList = [flow.bw for flow in self.finishedFlows]
        # bwList.sort()
        # num = len(bwList)
        # for i in range(num):
        #     print >> f_plot, "%f\t%f" % (bwList[i] / Mb, float(i + 1) / num)
            print >> f, "%d->%d %f %d" % (flow.startId, flow.endId, flow.bw, flow.flowSize / 8)
        f.close()
        # f_plot.close()
