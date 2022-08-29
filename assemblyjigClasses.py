from asyncio import queues
from inspect import currentframe
from types import NoneType
import serial
import labjack
from labjack import ljm
import time
import numpy as np
import sys
from csv import writer
from datetime import datetime

## Initialize the labajack T7
handle = ljm.openS("ANY","ANY","ANY")

## Set up communication with the Fisnar Robot through COM3
SP = serial.Serial("COM3",115200,8,"N",1)
SP.isOpen()


class helperFunctions:
    def isFloat(input):
        try:
            float(input)
            return True
        except ValueError:
            return False



class cycleSwitch:
    
    def read_state(): 
        try:
            avg_state = ljm.eReadName(handle,"FIO1")
            if avg_state == 0:
                state = "Starting new dispense cycle"
            
            else:
                state = "Waiting for new cycle button press!"
        
            return state
        
        except Exception as e:
            print("Error readimg cycle switch state: ",e)
            print("Trying to read cycle switch state again!")
            cycleSwitch.read_state()


class horizontalLA:
    def __init__():
        pass
    
    def readLocation():
        try:
            right_read = ljm.eReadName(handle,"FIO2")
            left_read = ljm.eReadName(handle,"FIO3")
            if right_read == 0.0:
                location = "right"

            elif left_read == 0.0:
                location = "left"

            else:
                location = "middle"
        
            return location
        
        except Exception as e:
            print("Error reading HLA location: ",e)
            print("Trying to read HLA location again!")
            horizontalLA.readLocation()

    def moveRight(): ## Thinking of adding speed as an input variable 
        location = horizontalLA.readLocation()
        if (location!="right"):
            ljm.eWriteName(handle,"DAC1",1.0)
        while(location != "right"):
            #ljm.eWriteName(handle,"DAC1",1.0) #OV to driver moves right 
            location = horizontalLA.readLocation()
            #time.sleep(0.01) 
        ljm.eWriteName(handle,"DAC1",2.5) #2.5V to driver stops motion


    def moveRightFast():
        location = horizontalLA.readLocation()
        if (location!="right"):
            ljm.eWriteName(handle,"DAC1",0)
                
    
        
        
    def moveLeft():
        location = horizontalLA.readLocation()
        if (location!="left"):
            ljm.eWriteName(handle,"DAC1",4.0)
        while(location != "left"):
            #ljm.eWriteName(handle,"DAC1",4.0) #5V to driver moves left
            location = horizontalLA.readLocation()
            #time.sleep(0.01)
        ljm.eWriteName(handle,"DAC1",2.5) #2.5V to driver stops motion 
    
    def moveLeftFast():
        location = horizontalLA.readLocation()
        if (location!="left"):
            ljm.eWriteName(handle,"DAC1",6.0)
        
        
    def stop():
        ljm.eWriteName(handle,"DAC1",2.5)


class verticalLA:
    def readLocation():
        try:
            numberReadings = 20
            counter = 0
            voltage = np.zeros(numberReadings)
            while(counter<numberReadings-1):
                for i in range(numberReadings):
                    voltage[i] = ljm.eReadName(handle,"AIN0")
                    #time.sleep(0.01)
                    counter+=1
            
        
            avg_voltage = np.mean(voltage)
            location = 304.8-(125.1686883*(2.683738506-avg_voltage))
            return location
        
        except Exception as e:
            print("Error reading VLA location: ",e)
            print("Trying to read VLA location again!")
            verticalLA.readLocation()
    
    def moveUp():
        ljm.eWriteName(handle,"DAC0",3.5) #5V on driver drives up, keep voltage on to stay fully extended
    
    def moveDown():
        ljm.eWriteName(handle,"DAC0",2.0) #0V drives down until fully retracted
    
    def stop():
        ljm.eWriteName(handle,"DAC0",2.5) #2.5V stops motion
    
    def moveTo(target_location:float):
        cur_location  = verticalLA.readLocation()
        while(cur_location>target_location):
            verticalLA.moveDown()
            cur_location = verticalLA.readLocation() #keep updating cur_location
            
            if cur_location>target_location:  #Do not want to over specify when to stop - Alow some  overshoot
                continue
            else:
                verticalLA.stop()
        while(cur_location<target_location):
            verticalLA.moveUp()
            cur_location = verticalLA.readLocation() # keep updating curr_location
            print(cur_location)
            if cur_location<target_location: #Do not want to over specify when to stop - Alow some overshoot
                continue
            else:
                verticalLA.stop()


    def movetoStart():
        verticalLA.moveUp()
        time.sleep(1)
        verticalLA.moveTo(285)

    
    def moveStepdown(step_size:float,start_location:float):
        target_location = -1*(np.abs(step_size)) + start_location
        current_location = verticalLA.readLocation()
        print("step size: ",step_size)
        print("target location :",target_location)
        print("start location :",start_location)
        if (target_location<current_location):

            while (target_location<current_location):
                verticalLA.moveDown()
                current_location = verticalLA.readLocation()       
            verticalLA.stop()
        elif (target_location>current_location):
                while (target_location>current_location):
                    verticalLA.moveUp()
                    current_location = verticalLA.readLocation()       
                verticalLA.stop()
        print("current location :",current_location) 



class fisnarCircle: ##This is a computation heavy class, strongly open to simplifying it.
    def __init__(self,radius:float,x_center:float,y_center:float):
        self.radius = radius
        self.x_center = x_center
        self.y_center = y_center
    
    def circlePoints(self,min_dist:float): ## Would be smarter to define a minumum distance between start and end point and use that to cap the amount of computation 
        start_points = [self.x_center,self.y_center-self.radius] 
        theta_rad = min_dist/self.radius
        theta_deg = theta_rad*(180/np.pi)
        delta_x = np.abs(self.radius*np.sin(theta_deg))
        delta_y = np.abs(self.radius*np.cos(theta_deg))
        x_final = self.x_center - delta_x
        y_final = self.y_center - delta_y
        end_points = [x_final,y_final]
        circle_points = start_points + end_points
        return circle_points

 
class fisnar:

    def dispenseOn():
        ljm.eWriteName(handle,"FIO0",1)

    def dispenseOff():
        ljm.eWriteName(handle,"FIO0",0)

    def serialWrite(fisnar_command:str):
        SP.write(f"{fisnar_command}\r\n".encode(encoding="ascii"))
    
    def serialRead():
        read = SP.readline().decode("ascii")
        return read

    def home():
        fisnar.serialWrite("HM")
         
    def readLocation():
        fisnar.serialWrite("PA")
        location = fisnar.serialRead().split(",")
        if len(location) == 3 and helperFunctions.isFloat(location[0]) == True and helperFunctions.isFloat(location[1]) == True and helperFunctions.isFloat(location[2]) == True:
            return location
        
        else:
            location = fisnar.serialRead().split(",")  


    def moveTo(target_location:str):
        fisnar.serialWrite(f"MA +{target_location}")
        current_location = fisnar.readLocation()
        
        while current_location == None or len(current_location) != 3:
            current_location = fisnar.readLocation()
        split_target_location = target_location.split(",")
        
        if current_location != None and split_target_location[0] == current_location[0] and split_target_location[1] == current_location[1] and split_target_location[2] == current_location[2].strip("\r\n"):
            return_statement = print("Taget location reached!")
            return return_statement

        else:
            current_location = fisnar.readLocation()

    def idle():
        fisnar.moveTo("100,0,50")

    def makeCircle(side:str,dispense_height:float):## Takes and input of the side the circle is to be traced in 
        circle_radius = 10
        min_dist = 0.02
        if side == "left":
            x_center = 180
            y_center = 153.5
            circle_points  = fisnarCircle(circle_radius,x_center,y_center).circlePoints(min_dist)
            start_points = f"{circle_points[0]},{circle_points[1]},{dispense_height}"
            end_points = f"{circle_points[2]},{circle_points[3]}"
            fisnar.moveTo(start_points)
            time.sleep(6.9) #7.18
            fisnar.dispenseOn()
            time.sleep(0.5)
            if 1 == 1: ##Need to define some function that checks () when I have reached my target location
            
                fisnar.serialWrite(f"CW +{x_center},{y_center},{end_points}")
                time.sleep(3.5)
                fisnar.dispenseOff()
                
            
        elif side == "right":
            x_center = 96.5#85.5
            y_center = 142.5#144.5
            circle_points  = fisnarCircle(circle_radius,x_center,y_center).circlePoints(min_dist)
            start_points = f"{circle_points[0]},{circle_points[1]},{dispense_height}"
            end_points = f"{circle_points[2]},{circle_points[3]}"
            fisnar.moveTo(start_points)
            time.sleep(6.5)
            fisnar.dispenseOn()
            time.sleep(0.5)

            if 1 == 1: ##Need to define some function that checks () when I have reached my target location
                fisnar.serialWrite(f"CW +{x_center},{y_center},{end_points}")
                time.sleep(3.2)
                fisnar.dispenseOff()
            

        else:
            raise Exception("Enter a side to trace circle as string: left or right")

#fisnar.home()
fisnar.idle()
horizontalLA.moveLeft()
#horizontalLA.moveRight()
verticalLA.moveUp()
#verticalLA.moveDown()
#verticalLA.stop()


#verticalLA.readLocation()
#fisnar.home()

#fisnar.makeCircle("left",80)
