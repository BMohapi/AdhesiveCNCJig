import serial
import labjack
import time
import numpy as np
import sys
from csv import writer
from assemblyjigClasses import *


init_vert_location = np.int(input("Please enter the number of pouches the stack is starting from (Should be integer from 0 to 400): "))
pouchThickness = 0.27 # structure 2
#pouchThickness = 0.21 #structure 1
spacerThickness = 0.62
verticalLA.moveTo(285-(init_vert_location*(pouchThickness+spacerThickness)))
start_location = verticalLA.readLocation()
cycle_number = 0
dispense_height_right = 93.0
dispense_height_left = 99.0
fisnar.idle()

#move to fisnar comands, HLAmove,  are blocking
while(1):
    horizontalLA.moveLeft()
    state = cycleSwitch.read_state()
    loc = verticalLA.readLocation()
    print("Number of pouches assembled: ",cycle_number+init_vert_location)
    with open('0516_stepping1_2.1VDownDefinedStart285AUp1StartUpcorr.csv','a',newline='') as logfile:
        data = [np.int(cycle_number),np.float(loc)]
        logWriter = writer(logfile,delimiter=",")
        logWriter.writerow(data)
    while(state == "Starting new dispense cycle"):
        horizontalLA.moveLeft()
        fisnar.makeCircle("right",dispense_height_right)
        fisnar.idle()
        horizontalLA.moveRightFast()
        time.sleep(7) # Amount of time for HLA to move full speed
        horizontalLA.moveRight()
        fisnar.makeCircle("left",dispense_height_left)
        fisnar.idle()
        verticalLA.moveDown() ## Moving down from rest is a problem!
        time.sleep(4)
        verticalLA.moveStepdown((cycle_number+1)*(pouchThickness+spacerThickness),start_location)
        horizontalLA.moveLeftFast()
        time.sleep(12) # Amount of time for HLA to move full speed
        horizontalLA.moveLeft()
        cycle_number+=1
        state = "off!"

    time.sleep(0.5)