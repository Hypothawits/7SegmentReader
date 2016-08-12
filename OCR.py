#!/usr/bin/env python
import tesseract
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

        #Set Min Size
        if self.size <10:
            self.size = 10

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
    try:
        print display_int1
    except:
        print "could print display inter"
    print "Data Saved (Not Really)"

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
    if display_int1[y,x].any(): #if any value not zero, white pixel
        return 0
    else:
        return 1

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
   

    start_x, start_y   = 100, 100,
    start_x2, start_y2 = 100, 100,
    start_x3, start_y3 = 100, 100,
    
    drawing = False  # true if mouse is pressed
    draw2   = False  
    draw3   = False

    # flag to stop opencv
    stopOpenCv = False
    ############################################################################
    
    # Video capture
    cap = cv2.VideoCapture(0)

    def nothing(x):
        pass

    # mouse callback function
    def draw_rectangle(event, x, y, flags, param):
        global start_x, start_y, drawing      
        global start_x2, start_y2, draw2, start_x3, start_y3, draw3

        if event == cv2.EVENT_LBUTTONDOWN:
            # menu position
            if y < 40:
                # menu map
                if x > 153 and x < 190:
                    OnClose(event)
                if x > 195 and x < 252:
                    print "Write a description"
                if x > 258 and x < 355:
                    SaveData()
                if x > 380 and x < 420:
                    # print 'first Int'
                    draw2 = False
                    draw3 = False                
                if x > 426 and x < 462:
                    # print "second Int"
                    draw2 = True
                    draw3 = False
                if x > 490 and x < 530:
                    # print "first decimal"
                    draw2 = False
                    draw3 = True

            else:
                drawing = True

                if (draw2 == False)and(draw3 == False):
                    start_x, start_y = x, y
                elif (draw2 == True)and(draw3 == False):
                    start_x2, start_y2 = x, y
                else:
                    start_x3, start_y3 = x, y

        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False                  

        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            if (draw2 == False)and(draw3 == False):
                start_x, start_y = x, y
            elif (draw2 == True)and(draw3 == False):
                start_x2, start_y2 = x, y
            else:
                start_x3, start_y3 = x, y


    # show main window
    cv2.namedWindow('frame')

    # Show blank image at first
    cv2.namedWindow('Int1 selection')
    display_int1   = np.zeros((200, 200, 3), np.uint8)
    cv2.imshow('frame', display_int1)

    cv2.namedWindow('Int2 selection')
    display_int2   = np.zeros((200, 200, 3), np.uint8)
    cv2.imshow('frame', display_int2)

    cv2.namedWindow('Decimal selection')
    display_decimal   = np.zeros((200, 200, 3), np.uint8)
    cv2.imshow('frame', display_decimal)

    # GUI
    cv2.createTrackbar('Threshold', 'Int1 selection',    int(thresh),  255, nothing)
    cv2.createTrackbar('Threshold', 'Int2 selection',    int(threshB), 255, nothing)
    cv2.createTrackbar('Threshold', 'Decimal selection', int(threshC), 255, nothing)

    cv2.createTrackbar('Size',   'frame', int(box_size),           100,  nothing)
    cv2.createTrackbar('Size B', 'frame', int(box_sizeB),          100,  nothing)
    cv2.createTrackbar('Erode',  'frame', int(erosion_iters),      4,    nothing)
    cv2.createTrackbar('Filter', 'frame', int(most_common_filter), 10,   nothing)
    
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
      #IntBox1
        IntBox1.size     = cv2.getTrackbarPos('Size',   'frame')
        IntBox1.location = [start_x,start_y]

        #get and process the selection
        IntBox1.selection = getSelection(IntBox1.location[0], IntBox1.location[1], IntBox1.size)
        IntBox1.selection = preprocessImage(IntBox1.selection, 'Threshold', 'Int1 selection')
        cv2.imshow('Int1 selection', IntBox1.selection)
        cv2.resizeWindow('Int1 selection', 300, 200)

        #convert image to number
        Int1ValueList = getValueList(IntBox1.segCoordinates,IntBox1.selection)
        Int1Value     = float(convertToNumber(Int1ValueList))
      
      #IntBox1
        IntBox2.size = cv2.getTrackbarPos('Size',   'frame')
        IntBox2.location = [start_x2,start_y2]

        IntBox2.selection = getSelection(IntBox2.location[0], IntBox2.location[1], IntBox2.size)
        IntBox2.selection = preprocessImage(IntBox2.selection, 'Threshold', 'Int2 selection')
        cv2.imshow('Int2 selection', IntBox2.selection)
        cv2.resizeWindow('Int2 selection', 300, 200)

        Int2ValueList = getValueList(IntBox2.segCoordinates,IntBox2.selection)
        Int2Value     = float(convertToNumber(Int2ValueList))

      #Decimal Box
        DecimalBox.size     = cv2.getTrackbarPos('Size B', 'frame')
        DecimalBox.location = [start_x3, start_y3]
        
        DecimalBox.selection = getSelection(DecimalBox.location[0], DecimalBox.location[1], DecimalBox.size)
        DecimalBox.selection = preprocessImage(DecimalBox.selection, 'Threshold', 'Decimal selection')
        cv2.imshow('Decimal selection', DecimalBox.selection)
        cv2.resizeWindow('Decimal selection', 300, 200)
        
        DecValueList = getValueList(DecimalBox.segCoordinates,DecimalBox.selection)
        DecValue     = float(convertToNumber(DecValueList))

       #Draw Rectangle and Location Points
        #must be done after the selections are made, 
        #or the box and points will appear in the image!
        IntBox1.drawBoxRectangle()
        IntBox2.drawBoxRectangle()
        DecimalBox.drawBoxRectangle()

        #Combine integer components and Decimal
        temperatureInt = 10*Int1Value + Int2Value + 0.1*DecValue
        
        print "Temperature = %0.1f"%temperatureInt
        cv2.imshow('frame', frame)


        c = cv.WaitKey(20)

        if c == "q":
            break
        if stopOpenCv:
            break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()