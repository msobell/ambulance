#! /usr/bin/env python
"""
Solves the ambulance problem
"""

import sys
import os
from numpy import array
from scipy.cluster.vq import vq, kmeans, whiten
import time
import random

start_time = time.time()
total_saved = 0
total_lost = 0

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

    def score(self,p):
        d = abs(p.x - self.x) + abs(p.y - self.y)
        dth = p.find_closest_hospital()[1]
        t = p.ttl - self.time
        thres = 20
        if t > thres:
            p.score = d*5/(t-thres)
        else:
            p.score = float('Inf')
        if len(self.cargo) > 3:
             p.score += 4*dth
        return p.score

    # def find_closest_patient(self):
    #     closest_patient = patients[0]
    #     mini = 10000
    #     for p in patients:
    #         if not p.in_ambulance:
    #             d = abs(p.x - self.x) + abs(p.y - self.y)
    #             t = p.ttl - self.time # time left to live
    #             if d < mini and t > 0:
    #                 mini = d
    #                 closest_patient = p
    #     return closest_patient, mini

    def find_closest_patient(self):
        closest_patient = patients[0]
        mini = 10000
        for p in patients:
            if not p.in_ambulance:
                d = self.score(p)
                t = p.ttl - self.time # time left to live
                # dont pick up dead dudes
                if d < mini and t > 0:
                    mini = d
                    closest_patient = p
        return closest_patient,mini,sorted(patients, key=lambda Patient: Patient.score)

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

    def find_closest_hospital(self):
        closest_hospital = hospitals[0]
        mini = 10000
        for h in hospitals:
            d = abs(h.x - self.x) + abs(h.y - self.y)
            if d < mini:
                mini = d
                closest_hospital = h
        return closest_hospital, mini

class Hospital:
    def __init__(self,num,x,y):
        self.x = x
        self.y = y
        self.ambulances = 0
        self.num = num
        self.patients = 0

    def __repr__(self):
        return ("%s (%s,%s)" % (repr(self.num),repr(self.x),repr(self.y)))
        #return ("Hospital %s at %s, %s with %s ambulances and %s patients.") %\
        #    (repr(self.num+1), repr(self.x), repr(self.y),\
        #repr(self.ambulances), repr(self.patients))

    def find_closest_patient(self):
        closest_patient = patients[0]
        mini = 10000
        for p in patients:
            d = abs(self.x - p.x) + abs(self.y - p.y)
            if d < mini:
                mini = d
                closest_patient = p
        return closest_patient

def path_cost(l):
    dist = 0
    for i in range(0,len(l)):
        cx = int(l[i].split(',')[0])
        cy = int(l[i].split(',')[1])
        if i > 0:
            dist += abs(px-cx) + abs(py-py)
        px = cx
        py = cy
    return dist

if __name__ == "__main__":

    if len(sys.argv) != 1:
        usage()
        sys.exit(1)

    patients = []
    hospitals = []
    ambulance_numbers = []
    qq = []
    i = 0

    for line in sys.stdin:
        if "loc" in line or "num" in line or line == "\n":
            pass
        else:
            a = line.split(',')
            if len(a) == 3:
                x = int(a[0])
                y = int(a[1])
                ttl = int(a[2].split('\n')[0])
                patients.append(Patient(i,x,y,ttl))
                qq.append([x,y])
                i += 1
            else:
                ambulance_numbers.append(int(a[0]))
                
    a_save = ambulance_numbers + []
    ambulance_numbers.sort()

    p = array(qq, dtype='i')
    clusts = kmeans(p,5)
    # print "Clusters:\n" + repr(clusts[0].tolist()) + "\n"
    i = 0
    for c in clusts[0].tolist():
        hospitals.append(Hospital(i,c[0],c[1]))
        i += 1

    for h in hospitals:
        # move -- poor man's k-medoids
        c = h.find_closest_patient()
        h.x = c.x
        h.y = c.y

    # figure out how many patients in each cluster
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

    sorted_hospitals = sorted(hospitals, key=lambda Hospital: Hospital.patients)
    for h in sorted_hospitals:
        h.ambulances = ambulance_numbers[0]
        ambulance_numbers.remove(ambulance_numbers[0])

    # this is ugly please forgive me
    count = 0
    use_h = hospitals + []
    while count < 5:
        for h in use_h:
            if h.ambulances == a_save[count]:
                h.num = count
                count += 1
                use_h.remove(h)
                break

    hospitals = sorted(hospitals, key=lambda Hospital: Hospital.num)    
    print "Hospitals",
    for h in hospitals:
        print h,
    print ""

    ambulances = []
    amb_counter = 0
    # get all the ambulances started
    for h in hospitals:
        # print h.ambulances
        for i in range(0,h.ambulances):
            ambulances.append(Ambulance(amb_counter,h.x,h.y))
            amb_counter += 1

    # print "Total ambulances: ",len(ambulances)

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
            # print "%s is unsaveable." % (repr(p))

    avg_ttl = 0
    max_ttl = 0
    for p in patients:
        avg_ttl += p.ttl
        if max_ttl < p.ttl:
            max_ttl = p.ttl
    avg_ttl /= len(patients)
    # print "Average time to live: ",avg_ttl

    # find patients under hospitals
    for p in patients:
        for h in hospitals:
            if p.x == h.x and p.y == h.y:
                patients.remove(p)
                total_saved += 1

    path = []
    for i in range(len(ambulances)):
        path.append([])
        # fuck python. sometimes.

    scored_p = []
    while len(patients) > 0:
        for a in ambulances:
            path[a.n].append(repr(a.x) + "," + repr(a.y))
            while a.time < max_ttl:
                first = True
                finding = False
                # estimate the maximum time remaining
                hosp_dist = a.find_closest_hospital()[1]
                still_ok = True
                while len(a.cargo) < 4 and still_ok and len(patients) > 0:
                    if not finding:
                        # determine which patient to pick up
                        low_patient,d,scored_p = a.find_closest_patient()
                        # 0 = patient, 1 = distance, 2 = sorted array

                    # should we go back?
                    # if someone is going to die RIGHT NOW if we don't go back...
                    # LOGIC: lowest time to live is still greater than the time it takes to
                    # pick up the next patient and drive to the nearest hospital
                    # this logic is OK because the path from the patient to the hospital
                    # is always less than the ambulance to the hospital PLUS the ambulance to the
                    # patient. Phew.
                    if len(a.cargo) > 0:
                        still_ok = min([p.ttl for p in a.cargo]) > a.find_closest_hospital()[1] + d + 2 + a.time
                    else:
                        still_ok = low_patient.ttl > a.find_closest_hospital()[1] + d + 2 + a.time

                    # pick that patient up
                    if still_ok:
                        finding = False
                        a.move(low_patient.x,low_patient.y) # move the ambulance to the person
                        path[a.n].append(repr(a.x) + "," + repr(a.y))
                        patients.remove(low_patient) # remove the patient from the street
                        low_patient.in_ambulance = True # dibbs!
                        a.cargo.append(low_patient) # add him/her to the ambulance
                        if first:
                            print "Ambulance",a.n, # Ambulance X
                            first = False
                        print low_patient,
                        a.time += 1 # takes 1 minute to load the patient
                    else:
                        scored_p.remove(low_patient)
                        low_patient = scored_p[0]
                        finding = True
                        
                # drop patients off
                h = a.find_closest_hospital()[0]
                if len(a.cargo) > 0:
                    a.move(h.x,h.y)
                    path[a.n].append(repr(a.x) + "," + repr(a.y))
                a.time += 1 # unload all patients
                if len(a.cargo) > 0:
                    print "\nAmbulance %s (%s,%s)" % (repr(a.n),repr(a.x),repr(a.y)) # Ambulance X 
                for r in a.cargo:
                    if r.ttl > a.time:
                        total_saved += 1
                    else:
                        total_lost += 1
                a.cargo = []

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
                # print "%s is unsaveable." % (repr(p))
        
    # pseudocode for the simulated annealing algo:
    #     take an initial route r1
    #     loop until T is low enough or you have found an answer close to the optimal
    #         consider a randomly chosen possible change yielding a route r2
    #     if r2 is lower cost than r1
    #         replace r1 by r2
    #         else replace r1 by r2 with probbility
    #              e^((cost(r1)-cost(r2))/T)
    #     decrease the temperature T

    hosp_locs = []
    for h in hospitals:
        hosp_locs.append(repr(h.x) + "," + repr(h.y))

    # T = 60
    # while T > 50:
    #     for amb_path in path:
    #         c = path_cost(amb_path)
    #         t = 0
    #         for i in amb_path:
    #             while i not in hosp_locs
    #             t += 1
    #         a = random.randint(0,t)
    #         b = random.randint(0,t)
    #         t1 = amb_path[a]
    #         t2 = amb_path[b]
    #         temp_path = amb_path + []
    #         if a > b:
    #             temp_path.insert(t1,b)
    #             temp_path.remove(t1)
    #             temp_path.insert(t2,a)
    #             temp_path.remove(t2)
    #         elsif a < b:
    #             temp_path.insert(t1,b)
    #             temp_path.remove(t1)
    #             temp_path.insert(t2,a)
    #             temp_path.remove(t2)
    #         if path_cost(temp_path) < c:
    #             amb_path = temp_path
    #         elsif e^((cost(r1)-cost(r2))/T):
    #             amb_path = temp_path
    #     T-=10
        
print "Total saved: " + repr(total_saved)
