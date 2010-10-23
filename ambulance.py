#! /usr/bin/env python
"""
Solves the ambulance problem
"""

import sys
import os
from numpy import array
from scipy.cluster.vq import vq, kmeans, whiten
import time

start_time = time.time()

def usage():
    sys.stdout.write( __doc__ % os.path.basename(sys.argv[0]))

class Ambulance:
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.time = 0

    def move(self,destx,desty):
        self.time += abs(x - destx) + abs(y - desty)
        self.x = destx
        self.y = desty

class Patient:
    def __init__(self,num,x,y,ttl):
        self.num = num
        self.x = x
        self.y = y
        self.ttl = ttl
        self.hospital = None

    def __repr__(self):
        return (("Patient %s at %s, %s. %s to live") %\
            (repr(self.num),repr(self.x),repr(self.y),\
                 repr(self.ttl)))

    def __cmp__(self, p):
        return (abs(self.x - p.x) + abs(self.y - p.y))

    def score(self,x,y,thres):
        d = abs(x - self.x) + abs(y - self.y)
        if d > thres:
            return -1
        else:
            return ttl*d

class Hospital:
    def __init__(self,num,x,y):
        self.x = x
        self.y = y
        self.ambulances = 0
        self.num = num
        self.patients = 0

    def __repr__(self):
        return ("Hospital %s at %s, %s with %s ambulances and %s patients.") %\
            (repr(self.num+1), repr(self.x), repr(self.y),\
                 repr(self.ambulances), repr(self.patients))

if __name__ == "__main__":

    if len(sys.argv) != 1:
        usage()
        sys.exit(1)

    patients = []
    hospitals = []
    qq = []
    i = 0

    for line in sys.stdin:
        a = line.split(',')
        x = int(a[0])
        y = int(a[1])
        ttl = int(a[2].split('\n')[0])
        patients.append(Patient(i,x,y,ttl))
        qq.append([x,y])
        i += 1

    p = array(qq, dtype='i')
    clusts = kmeans(p,5)
    # print "Clusters:\n" + repr(clusts[0].tolist()) + "\n"
    i = 0
    for c in clusts[0].tolist():
        hospitals.append(Hospital(i,c[0],c[1]))
        i += 1

    for p in patients:
        mini = 10000
        for h in hospitals:
            # manhattan distance
            t = abs(h.x - p.x) + abs(h.y - p.y)
            # print "T is " + repr(t) + " and min is " + repr(mini)
            if t < mini:
                mini = t
                p.hospital = h
        p.hospital.patients += 1

    # TODO - read in these values
    ambulance_numbers = [5,9,6,11,10]
    ambulance_numbers.sort()
    
    sorted_hospitals = sorted(hospitals, key=lambda Hospital: Hospital.patients)
    for h in sorted_hospitals:
        h.ambulances = ambulance_numbers[0]
        ambulance_numbers.remove(ambulance_numbers[0])

    ambulances = []

    # get all the ambulances started
    for h in hospitals:
        print h
        for i in range(0,h.ambulances):
            ambulances.append(Ambulance(h.x,h.y))

    for a in ambulances:
        count = 0
        for p in patient:
            p.score(a.x,a.y,5) # threshold of 5 blocks
        while count < 4:
            
            
    print "Time : ", round(time.time() - start_time,2)

