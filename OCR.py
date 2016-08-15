#!/usr/bin/env python
import tesseract
import socket
import numpy as np
import cv2
import cv2.cv as cv
import time
import datetime
from   time import strftime
from   collections import Counter
import ConfigParser

class segBox:
    #Segment relative locations. Class Variables
    ax,ay = 0.50, 0.15
    bx,by = 0.65, 0.25
    cx,cy = 0.63, 0.65
    dx,dy = 0.46, 0.85
    ex,ey = 0.35, 0.65
    fx,fy = 0.36, 0.25
    gx,gy = 0.50, 0.50

    selection      = []
    segCoordinates = []
    size     = 10
    location = []
    
    

    def __init__(self, colour):
        self.colour = colour

    def drawBoxRectangle(self):
        origin   = [self.location[0] - self.size, self.location[1] - self.size]

        #convert to pixel location within box (top left being origin)
        self.A = [int(self.size*2*float(self.ax)),int(self.size*2*float(self.ay))]
        self.B = [int(self.size*2*float(self.bx)),int(self.size*2*float(self.by))]
        self.C = [int(self.size*2*float(self.cx)),int(self.size*2*float(self.cy))]
        self.D = [int(self.size*2*float(self.dx)),int(self.size*2*float(self.dy))]
        self.E = [int(self.size*2*float(self.ex)),int(self.size*2*float(self.ey))]
        self.F = [int(self.size*2*float(self.fx)),int(self.size*2*float(self.fy))]
        self.G = [int(self.size*2*float(self.gx)),int(self.size*2*float(self.gy))]

        self.segCoordinates = [self.A,self.B,self.C,self.D,self.E,self.F,self.G]
        
        #draw rectangle arround selection
        cv2.rectangle(frame, (self.location[0] -self.size, self.location[1] -self.size),\
                             (self.location[0] +self.size, self.location[1] +self.size),\
                              self.colour, 1) 

        #draw segment indicator points
        cv2.circle(frame, (origin[0] + self.A[0], origin[1] + self.A[1]), 1 , (0, 0, 255), -1)
        cv2.circle(frame, (origin[0] + self.B[0], origin[1] + self.B[1]), 1 , (0, 0, 255), -1)
        cv2.circle(frame, (origin[0] + self.C[0], origin[1] + self.C[1]), 1 , (0, 0, 255), -1)
        cv2.circle(frame, (origin[0] + self.D[0], origin[1] + self.D[1]), 1 , (0, 0, 255), -1)
        cv2.circle(frame, (origin[0] + self.E[0], origin[1] + self.E[1]), 1 , (0, 0, 255), -1)
        cv2.circle(frame, (origin[0] + self.F[0], origin[1] + self.F[1]), 1 , (0, 0, 255), -1)
        cv2.circle(frame, (origin[0] + self.G[0], origin[1] + self.G[1]), 1 , (0, 0, 255), -1)
        
        cv2.imshow('frame', frame)

class SelectionFrame:
    def __init__(self, name, thresh_variable, box_size_variable ):
        self.name = name
        cv2.namedWindow(name)
        self.display   = np.zeros((200, 200, 3), np.uint8)
        cv2.createTrackbar('Threshold', name,    int(thresh_variable),   255, nothing)
        cv2.createTrackbar('Size',      name,    int(box_size_variable), 100,  nothing)
        cv2.imshow('frame', self.display)

def ConfigSectionMap(section):
    global Config
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def OnClose(event):
    global stopOpenCv
    stopOpenCv = True

def SaveData():

    print "Doesn't Save Yet" 

def imageIdentify(Box, Selection, x,y):
    Box.size     = cv2.getTrackbarPos('Size',   Selection)
    Box.location = [x,y]

    if Box.size <10:
        Box.size = 10

    #get and process the selection
    Box.selection = getSelection(Box.location[0], Box.location[1], Box.size)
    Box.selection = preprocessImage(Box.selection, 'Threshold', Selection)
    cv2.imshow(Selection, Box.selection)
    cv2.resizeWindow(Selection, 300, 200)

    #convert image to number
    ValueList = getValueList(Box.segCoordinates,Box.selection)
    Value     = float(convertToNumber(ValueList))
    return Value

def getthresholdedimg(hsv):
    yellow = cv2.inRange(hsv, np.array((20, 100, 100)), np.array((30, 255, 255)))
    blue = cv2.inRange(hsv, np.array((100, 100, 100)), np.array((120, 255, 255)))
    both = cv2.add(yellow, blue)
    return both

def preprocessImage(imageSelection, X, frame):
    #preprocesses the selection
    imageSelection = cv2.cvtColor(imageSelection, cv2.COLOR_BGR2GRAY) #GreyScale
    thresh = cv2.getTrackbarPos(X, frame)
    imageSelection = cv2.threshold(imageSelection, thresh, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((5, 5), np.uint8)
    erosion_iters = cv2.getTrackbarPos('Erode', 'frame')
    imageSelection = cv2.erode(imageSelection, kernel, iterations = erosion_iters)
    return imageSelection

def getSelection(startX, startY, size):
    #gets the selection from the main image
    selection = frame[startY - size:(startY + size), startX - size:(startX + size)]
    return selection

def getValueList(SevenSeg, display_int1):
    #get the value (1/0) for each of the 7 segments
    valueList = []
    #Get A value
    for Seg in SevenSeg:
        valueList.append(SegValue(Seg, display_int1))
    return valueList

def SegValue(Seg, display_int1):
    x,y = Seg[0],Seg[1]
    try:
        if display_int1[y,x].any(): #if any value not zero, white pixel
            return 0
        else:
            return 1
    except:
        return 0

def convertToNumber(X):
    if X == [1,1,1,1,1,1,0]:
        return 0
    if X == [0,1,1,0,0,0,0]:
        return 1
    if X == [1,1,0,1,1,0,1]:
        return 2
    if X == [1,1,1,1,0,0,1]:
        return 3
    if X == [0,1,1,0,0,1,1]:
        return 4
    if X == [1,0,1,1,0,1,1]:
        return 5
    if X == [1,0,1,1,1,1,1]:
        return 6
    if X == [1,1,1,0,0,0,0]:
        return 7
    if X == [1,1,1,1,1,1,1]:
        return 8    
    if X == [1,1,1,1,0,1,1]:
        return 9
    else:
        return 0

print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
print "Start Programe"

if __name__ == '__main__':
    Config = ConfigParser.ConfigParser()
    Config.read("./config.ini")
    ############################################################################
    # Pre process params
    thresh              = ConfigSectionMap("PREPROCESS")['threshold']
    threshB             = ConfigSectionMap("PREPROCESS")['threshold']
    threshC             = ConfigSectionMap("PREPROCESS")['threshold']
    erosion_iters       = ConfigSectionMap("PREPROCESS")['erode']
    most_common_filter  = ConfigSectionMap("POSPROCESS")['filter']
    box_size            = ConfigSectionMap("PREPROCESS")['size']
    box_sizeB           = ConfigSectionMap("PREPROCESS")['sizeb']
    box_sizeC           = ConfigSectionMap("PREPROCESS")['sizec']

   

    motor_x, motor_y   = 100, 100,
    motor_x2, motor_y2 = 100, 100,
    motor_x3, motor_y3 = 100, 100,
    
    drawing = False  # true if mouse is pressed
    Draw_FIntM   = True
    Draw_SIntM   = False  
    Draw_FDecM   = False
    Row1 = True
    Row2, Row3 = False, False

    # flag to stop opencv
    stopOpenCv = False
    ############################################################################
    #UDP Set Up
    UDP_IP = "172.17.2.216"
    # UDP_IP = "127.0.0.1" #my ip
    UDP_PORT = 8100
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    # sock.sendto("Temperature Recording Started", (UDP_IP, UDP_PORT))

    #############################################################################
    # Video capture
    cap = cv2.VideoCapture(0)

    def nothing(x):
        pass

    # mouse callback function
    def draw_rectangle(event, x, y, flags, param):
        global motor_x, motor_y, drawing      
        global motor_x2, motor_y2, motor_x3, motor_y3 
        global Draw_FIntM, Draw_SIntM, Draw_FDecM
        global Draw_FIntR, Draw_SIntR, Draw_FDecR
        global Draw_FIntH, Draw_SIntH, Draw_FDecH
        global Row1, Row2, Row3 

        if event == cv2.EVENT_LBUTTONDOWN:
            # menu position
            if y < 40:
                # menu map, First row Motor Temp
                Row1 = True
                Row2,Row3 = False,False

                if x > 3 and x < 40:
                    OnClose(event)
                if x > 45 and x < 105:
                    print "Write a description"
                if x > 110 and x < 205:
                    SaveData()
                if x > 230 and x < 270:
                    # print "first Int Motor"
                    Draw_FIntM = True
                    Draw_SIntM, Draw_FDecM = False,False                
                if x > 276 and x < 312:
                    # print "second Int Motor"
                    Draw_SIntM = True
                    Draw_FIntM, Draw_FDecM = False,False
                if x > 340 and x < 380:
                    # print "first decimal Motor"
                    Draw_FDecM = True
                    Draw_FIntM, Draw_SIntM = False,False

            elif (y > 40)and(y < 80):
                #menu map, Second row Room Temp
                Row2 = True
                Row1, Row3 = False, False
                if x > 230 and x < 270:
                    print "first Int Room"
                    Draw_FIntR = True
                    Draw_SIntR, Draw_FDecR = False,False
                if x > 276 and x < 312:
                    print "second Int Room"
                    Draw_SIntR = True
                    Draw_FIntR, Draw_FDecR = False,False

                if x > 340 and x < 380:
                    print "first decimal Room"
                    Draw_FDecR = True
                    Draw_FIntR, Draw_SIntR = False,False

            elif (y > 80)and(y < 120):
                #menu map, Third row Humidity
                Row3 = True
                Row1, Row2 = False,False
                if x > 230 and x < 270:
                    print "first Int Humidity"
                    Draw_FIntH = True
                    Draw_SIntH, Draw_FDecH = False,False
                if x > 276 and x < 312:
                    print "second Int Humidity"
                    Draw_SIntH = True
                    Draw_FIntH, Draw_FDecH = False,False

                if x > 340 and x < 380:
                    print "first decimal Humidity"
                    Draw_FDecH = True
                    Draw_FIntH, Draw_SIntH = False,False

            else:
                drawing = True
                if Row1:
                    if (Draw_FIntM):
                        motor_x, motor_y = x, y
                    elif (Draw_SIntM):
                        motor_x2, motor_y2 = x, y
                    elif (Draw_FDecM):
                        motor_x3, motor_y3 = x, y
                else:
                    print "Button Selection Error"

        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False                  

        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            if Row1:
                if (Draw_FIntM):
                    motor_x, motor_y = x, y
                elif (Draw_SIntM):
                    motor_x2, motor_y2 = x, y
                elif (Draw_FDecM):
                    motor_x3, motor_y3 = x, y
            else:
                print "Button Selection Error"


    # show main window
    cv2.namedWindow('frame')
    cv2.createTrackbar('Erode', 'frame', int(erosion_iters),      4,    nothing)
    cv2.createTrackbar('Filter','frame', int(most_common_filter), 10,   nothing)

    # Create selection frames
    Int_selection_1 = SelectionFrame('Int1 selection', thresh, box_size)
    # cv2.namedWindow('Int1 selection')
    # display_int1   = np.zeros((200, 200, 3), np.uint8)
    # cv2.createTrackbar('Threshold', 'Int1 selection',    int(thresh),   255, nothing)
    # cv2.createTrackbar('Size',      'Int1 selection',    int(box_size), 100,  nothing)
    # cv2.imshow('frame', display_int1)

    cv2.namedWindow('Int2 selection')
    display_int2   = np.zeros((200, 200, 3), np.uint8)
    cv2.createTrackbar('Threshold', 'Int2 selection',    int(threshB),  255, nothing)
    cv2.createTrackbar('Size',      'Int2 selection',    int(box_sizeC),100,  nothing)
    cv2.imshow('frame', display_int2)

    cv2.namedWindow('Decimal selection')
    display_decimal   = np.zeros((200, 200, 3), np.uint8)
    cv2.createTrackbar('Threshold', 'Decimal selection', int(threshC),  255, nothing)
    cv2.createTrackbar('Size',      'Decimal selection', int(box_sizeC),100,  nothing)
    cv2.imshow('frame', display_decimal)

    # GUI
    
    
    
    
    
    
    # menu image
    menu = cv2.imread("menu.png")
    cv2.setMouseCallback('frame', draw_rectangle)

    meas_stack   = []
    integer_List = []
    decimal_List = []

    #create Boxes
    DecimalBox  = segBox((255,0,0))
    IntBox1     = segBox((0,255,0))
    IntBox2     = segBox((0,222,0))
    
#Main Loop
    while True:
        # Capture frame-by-frame, Frame is the whole image captured
        ret, frame = cap.read()
        if frame is None:
            print 'frame is None'
            break
        
        # add menu
        frame_h, frame_w = frame.shape[:2]
        frame[0:menu.shape[0], 0:menu.shape[1]] = menu
    ########################################################################
    # ROI Regions of Interest
    ########################################################################
      #Temperature Motor
        Int1Value = imageIdentify(IntBox1,    'Int1 selection',    motor_x,motor_y)
        Int2Value = imageIdentify(IntBox2,    'Int2 selection',    motor_x2,motor_y2)
        DecValue  = imageIdentify(DecimalBox, 'Decimal selection', motor_x3, motor_y3)

       #Draw Rectangle and Location Points
        #must be done after the selections are made, 
        #or the box and points will appear in the image!
        IntBox1.drawBoxRectangle()
        IntBox2.drawBoxRectangle()
        DecimalBox.drawBoxRectangle()

        #Combine integer components and Decimal

        temperatureInt = 10*Int1Value + Int2Value + 0.1*DecValue
        
        print "Temperature = %0.1f"%temperatureInt
        
        SendArray = [temperatureInt]

        sock.sendto('{"temperatures": %r}'%SendArray, (UDP_IP, UDP_PORT))

        cv2.imshow('frame', frame)


        c = cv.WaitKey(100)

        if c == "q":
            break
        if stopOpenCv:
            break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()