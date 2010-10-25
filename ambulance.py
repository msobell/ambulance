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
total_saved = 0

def usage():
    sys.stdout.write( __doc__ % os.path.basename(sys.argv[0]))

class Ambulance:
    def __init__(self,n,x,y):
        self.n = n
        self.x = x
        self.y = y
        self.time = 0
        self.cargo = []
        self.timeleft = float('Inf')

    def __repr__(self):
        return ("Ambulance %s at %s, %s. Time = %s") % (repr(self.n),repr(self.x),repr(self.y),repr(self.time))

    def move(self,destx,desty):
        # print "time before: ",self.time
        # print "x: %s, y: %s || destx: %s, desty: %s" % (self.x,self.y,destx,desty)
        self.time += abs(destx - self.x) + abs(desty - self.y)
        # print "time after: ",self.time
        self.x = destx
        self.y = desty

    def find_closest_hospital(self):
        closest_hospital = hospitals[0]
        mini = 10000
        for h in hospitals:
            d = abs(h.x - self.x) + abs(h.y - self.y)
            if d < mini:
                mini = d
                closest_hospital = h
        return closest_hospital, mini

    def find_closest_patient(self):
        closest_patient = patients[0]
        mini = 10000
        for p in patients:
            if not p.in_ambulance:
                d = abs(p.x - self.x) + abs(p.y - self.y)
                if d < mini:
                    mini = d
                    closest_patient = p
        return closest_patient, mini


class Patient:
    def __init__(self,num,x,y,ttl):
        self.num = num
        self.x = x
        self.y = y
        self.ttl = ttl
        self.hospital = None
        self.scored = 10000
        self.in_ambulance = False

    def __repr__(self):
        return (("%s (%s,%s,%s)") %\
            (repr(self.num),repr(self.x),repr(self.y),\
                 repr(self.ttl)))

    def __cmp__(self, p):
        return (abs(self.x - p.x) + abs(self.y - p.y))

    def score(self,x,y,thres,time,timeleft):
        d = abs(x - self.x) + abs(y - self.y)
        # too far away or already dead or going to die in ambulance
        if d > thres or time > ttl or timeleft < (ttl-time):
            self.scored = 10000
        else:
            self.scored = (ttl-time) + d
            print "Person's %s score is %s" % (repr(self.num),repr(self.scored))
        return self.scored

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
    amb_counter = 0
    # get all the ambulances started
    for h in hospitals:
        print h.ambulances
        for i in range(0,h.ambulances):
            ambulances.append(Ambulance(amb_counter,h.x,h.y))
            amb_counter += 1

    print "Total ambulances: ",len(ambulances)

    thres = 20 # maximum manhattan distance to search for patients

    for p in patients:
        closest_hospital = hospitals[0]
        mini = 10000
        for h in hospitals:
            d = abs(h.x - p.x) + abs(h.y - p.y)
            if d < mini:
                mini = d
                closest_hospital = h
        d = abs(closest_hospital.x - p.x) + abs(closest_hospital.y - p.y)
        if p.ttl < (d + 2): # load and unload = 2 mins
            patients.remove(p)
            print "%s is unsaveable." % (repr(p))

    avg_ttl = 0
    for p in patients:
        avg_ttl += p.ttl
    avg_ttl /= len(patients)
    print "Average time to live: ",avg_ttl

    while len(patients) > 0:
        for a in ambulances:
            first = True
            # estimate the maximum time remaining
            hosp_dist = a.find_closest_hospital()[1]
            while len(patients) > 0 and len(a.cargo) < 4 and (min([p.ttl for p in patients]) + 1) > hosp_dist:
                a.timeleft = min([p.ttl for p in patients]) + 1
                hosp_dist = a.find_closest_hospital()[1]
                # distance to closest hospital (also time to get there)
                # h = a.find_closest_hospital()[1]
                # if h > a.timeleft + 50: # 20 is arbitrary
                low_patient = a.find_closest_patient()
                # print "Distance to closest patient: ",low_patient[1]
                low_patient = low_patient[0]
                # else:
                #     mini = 10000
                #     low_patient = patients[0]
                #     for p in patients:
                #         p.score(a.x,a.y,thres,a.time,a.timeleft) 
                #         if p.scored < mini:
                #             mini = p.scored
                #             low_patient = p
                a.move(low_patient.x,low_patient.y) # move the ambulance to the person
                patients.remove(low_patient) # remove the patient from the street
                # print "%s patients left" % (repr(len(patients)))
                low_patient.in_ambulance = True # dibbs!
                a.cargo.append(low_patient) # add him/her to the ambulance
                if first:
                    print "Ambulance",a.n, # Ambulance X 
                    first = False
                print low_patient,
                a.time += 1 # takes 1 minute to load the patient
                # print a,a.time
            h = a.find_closest_hospital()[0]
            a.move(h.x,h.y)
            a.time += 1 # unload all patients
            if len(a.cargo) > 0:
                print "\nAmbulance %s (%s,%s)" % (repr(a.n),repr(a.x),repr(a.y)) # Ambulance X 
            for r in a.cargo:
                if r.ttl > a.time:
                    total_saved += 1
            a.cargo = []
#                    print "Saved %s at %s. %s saved." % (repr(r.num),repr(a.time),repr(total_saved))
#                else:
#                    print "Lost %s at %s." % (repr(r.num),repr(a.time))

        # find dead patients
        for p in patients:
            alive = False # assume dead :'(
            for a in ambulances:
                rescue_time = a.time + abs(p.x - a.x) + abs(p.y - a.y)
                if rescue_time < p.ttl:
                    alive = True
                    break
            if not alive:
                patients.remove(p)
                print "%s is unsaveable." % (repr(p))
        
    
    print "Time : ", round(time.time() - start_time,2)
    print "Total saved: ",total_saved
    print "Patients remaining: ",len(patients)
