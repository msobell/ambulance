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

    def find_closest_patient(self):
        closest_patient = patients[0]
        mini = 10000
        for p in patients:
            if not p.in_ambulance:
                d = abs(p.x - self.x) + abs(p.y - self.y)
                t = p.ttl - self.time # time left to live
                if d < mini and t > 0:
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
        return ("%s (%s,%s)" % (repr(self.num),repr(self.x),repr(self.y)))
        #return ("Hospital %s at %s, %s with %s ambulances and %s patients.") %\
        #    (repr(self.num+1), repr(self.x), repr(self.y),\
        #repr(self.ambulances), repr(self.patients))

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

    while len(patients) > 0:
        for a in ambulances:
            while a.time < max_ttl:
                first = True
                # estimate the maximum time remaining
                hosp_dist = a.find_closest_hospital()[1]
                still_ok = True
                while len(a.cargo) < 4 and still_ok and len(patients) > 0:
                    # determine which patient to pick up
                    low_patient,d = a.find_closest_patient()
                    # 0 = patient, 1 = distance

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
                        a.move(low_patient.x,low_patient.y) # move the ambulance to the person
                        patients.remove(low_patient) # remove the patient from the street
                        low_patient.in_ambulance = True # dibbs!
                        a.cargo.append(low_patient) # add him/her to the ambulance
                        if first:
                            print "Ambulance",a.n, # Ambulance X
                            first = False
                        print low_patient,
                        a.time += 1 # takes 1 minute to load the patient

                # drop patients off
                h = a.find_closest_hospital()[0]
                a.move(h.x,h.y)
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
        
#    print "Total saved: ",total_saved
#    print "Time : ", round(time.time() - start_time,2)
#    print "Total lost: ",total_lost
