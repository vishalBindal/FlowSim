__author__ = 'li'

import random
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from Src import Flow, Link
from TUnits import *

# looking for examples supporting MCP
# run simulator step by step, running for 100 milliseconds
# simulating multiple flows over one link
PROTO = ['d2tcp', 'mcp', 'tcp', 'dctcp']
# PROTO = ['d2tcp']

class StepByStepSimulator:
    # setting up environment
    def __init__(self,
                 RTT=0.000001*100,
                 SIMTIME=0.1,
                 CONCURRENCY=5,
                 FLOWSIZEMEAN=0.5,
                 FLOWDDLMEAN=0.001*50,
                 ECN=64,
                 MAXBUFFER=12,
                 LINKCAP=10,
                 output='results.txt'):
        self.RTT = RTT
        self.SIMTIME = SIMTIME
        self.Steps = int(round(SIMTIME / RTT))
        self.MAXNUMFLOW = CONCURRENCY * self.Steps  # This is concurrency of flows
        self.FLOWSIZEMEAN = FLOWSIZEMEAN * MB
        self.FLOWDDLMEAN = FLOWDDLMEAN

        # ECN Threshold
        self.ECN = ECN * PKTSIZE
        self.MAXBUFFER = MAXBUFFER * MB
        self.LINKCAP = LINKCAP * KB
        self.LINK = Link.Link(1)
        self.LINK.linkCap = LINKCAP  # 1Gbps link

        self.fname = output

    def geninput(self):
        # Return a list of flows
        flowlist = []
        # flow format
        print 'Generating input'
        for fid in range(self.MAXNUMFLOW):
            flow = Flow.Flow()
            flow.flowId = fid
            flow.SetFlowSize(random.expovariate(1/self.FLOWSIZEMEAN))
            # deadline is in number of RTTs
            ddlinsteps = int(round(random.expovariate(1/self.FLOWDDLMEAN) / self.RTT))
            while ddlinsteps >= self.Steps - 1:
                ddlinsteps = int(round(random.expovariate(1/self.FLOWDDLMEAN) / self.RTT))
            flow.SetFlowDeadline(ddlinsteps)
            # print 'flow {} time for choice: {}'.format(fid, (Steps - flow.deadline))
            flow.startTime = random.choice(range(self.Steps - flow.deadline))
            # initial window
            flow.bw = 10*PKTSIZE/self.RTT
            flow.residualRate = 0
            flowlist.append(flow)
        return flowlist

    def Rate(self, flow, CongestionPercentage, LinkQueue):

        if flow.transport == 'dctcp':
            if CongestionPercentage > 0.002:
                cWin = flow.bw * self.RTT
                cWin *= (1 - CongestionPercentage/2.0)
                flow.bw = cWin/self.RTT
            else:
                flow.bw += 1*(PKTSIZE/self.RTT)
        elif flow.transport == 'tcp':
            if CongestionPercentage > 0.002:
                cWin = flow.bw * self.RTT
                cWin /= 2.0
                flow.bw = cWin/self.RTT
            else:
                flow.bw += 1*(PKTSIZE/self.RTT)
        elif flow.transport == 'd2tcp':
            if CongestionPercentage > 0.002:
                cWin = flow.bw * self.RTT
                Urgency = max(0, min(5.0, flow.remainSize/flow.remainTime))
                try:
                    cWin *= (1 - (CongestionPercentage**Urgency)/2.0)
                except:
                    print 'alpha = {}, urgency = {}'.format(CongestionPercentage, Urgency)
                    sys.exit("errors!")
                flow.bw = cWin/self.RTT
            else:
                flow.bw += (PKTSIZE/self.RTT)
        elif flow.transport == 'mcp':
            cWin = flow.bw * self.RTT
            ExpectedRate = flow.remainSize/flow.remainTime
            SourceTerm = flow.residualRate * ExpectedRate / flow.bw
            V = 1
            NetworkTerm = V * LinkQueue / self.LINK.linkCap
            delta = self.RTT * (SourceTerm - NetworkTerm)
            cWin += delta
            flow.bw = cWin/self.RTT
        return flow.bw

    def run(self):
        # create inputs
        Flows = self.geninput()
        # clear outputs
        open(self.fname, 'w').close()

        for proto in PROTO:
            for f in Flows:
                f.transport = proto
                if proto == 'dctcp' or proto == 'tcp':
                    f.bw = 2*PKTSIZE/self.RTT

            Flows.sort(key=lambda fs: fs.startTime)
            ReadyFlow = Flows
            ActiveFlow = []
            DeadFlow = []
            MissFlow = []
            for t in range(self.Steps):
                print 'Step {}'.format(t)
                newflows = [f for f in ReadyFlow if f.startTime == t]
                if newflows:
                    # print 'These flows, {}, are starting at {}'.format([f.flowId for f in newflows], t)
                    ActiveFlow += newflows

                InputLoad = sum([f.bw for f in ActiveFlow])
                # print 'Input load is {}'.format(InputLoad)
                self.LINK.queue += (InputLoad * self.RTT - self.LINK.linkCap)
                csize = 0.001
                dropsize = 0.001
                if self.LINK.queue <= self.ECN:
                    pass
                elif self.LINK.queue <= self.MAXBUFFER:
                    csize = self.LINK.queue - self.ECN
                else:
                    csize = self.LINK.queue - self.ECN
                    dropsize = self.LINK.queue - self.MAXBUFFER
                print 'Queue is {}'.format(self.LINK.queue)

                for f in ActiveFlow:
                    cpercent = max(0.000001, min(1, abs(f.bw*self.RTT/csize)))
                    if f.remainTime > 0:
                        f.bw = self.Rate(f, cpercent, self.LINK.queue)
                        f.residualRate += f.remainSize/f.remainTime - f.bw
                        f.residualRate = max(0.001, f.residualRate)
                    # print 'flow {} rate {}'.format(f.flowId, f.bw)
                    f.bw = max(0.001, f.bw)
                    droprate = 0.5
                    f.remainSize = min(f.remainSize, f.remainSize - f.bw * self.RTT\
                                       + droprate * cpercent * dropsize)
                    f.remainTime -= 1

                for f in ActiveFlow:
                    if f.remainSize <= 0.0 and f.remainTime >= 0:
                        print 'flow {} is finished at {}'.format(f.flowId, t)
                        f.finishTime = t
                        DeadFlow.append(f)
                        ActiveFlow.remove(f)
                    elif f.remainSize > 0 and f.remainTime <= 0:
                        print 'flow {} missed deadline at {}'.format(f.flowId, t)
                        f.finishTime = t
                        MissFlow.append(f)
                        ActiveFlow.remove(f)

            with open(self.fname, "a") as f:
                f.write('{}: Total number of flows: {}\n'.format(proto, len(Flows)))
                f.write('{}: Completed flows: {}\n'.format(proto, len(DeadFlow)))
                f.write('{}: Missed flows: {}\n'.format(proto, len(MissFlow)))
                f.write('{}: Miss Rate: {}\n'.format(proto, 1.0*len(MissFlow)/len(Flows)))
                f.write('\n')
                f.close()

if __name__=="__main__":
    sim = StepByStepSimulator()
    sim.run()