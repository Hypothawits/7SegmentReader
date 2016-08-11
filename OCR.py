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

def SaveImage(event):
    global display_inter
    params = list()
    params.append(cv.CV_IMWRITE_PNG_COMPRESSION)
    params.append(8)
    filename = datetime.datetime.now().strftime('%y%m%d%H%M%S_%f') + ".png"
    cv2.imwrite(filename, display_inter, params)

def OnClose(event):
    global stopOpenCv
    stopOpenCv = True

def SaveData():
    try:
        print display_inter
    except:
        print "could print display inter"
    print "Data Saved (Not Really)"

def getthresholdedimg(hsv):
    yellow = cv2.inRange(hsv, np.array((20, 100, 100)), np.array((30, 255, 255)))
    blue = cv2.inRange(hsv, np.array((100, 100, 100)), np.array((120, 255, 255)))
    both = cv2.add(yellow, blue)
    return both

def preprocessImage(imageSelection, X):
    #preprocesses the selection
    imageSelection = cv2.cvtColor(imageSelection, cv2.COLOR_BGR2GRAY) #GreyScale
    thresh = cv2.getTrackbarPos(X, 'frame')
    imageSelection = cv2.threshold(imageSelection, thresh, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((5, 5), np.uint8)
    erosion_iters = cv2.getTrackbarPos('Erode', 'frame')
    imageSelection = cv2.erode(imageSelection, kernel, iterations = erosion_iters)
    return imageSelection

def getSelection(startX, startY, size):
    #gets the selection from the main image
    selection = frame[startY - size:(startY + size), startX - size:(startX + size)]
    return selection

def drawPoint(origin, size, offset):

    cv2.circle(frame, (origin[0] + offset[0], origin[1] + offset[1]), 1 , (0, 0, 255), -1)   

def SevenSegCo(size, ax,ay,bx,by,cx,cy,dx,dy,ex,ey,fx,fy,gx,gy):
    #takes the 'relative' float position and converts to pixel positions
    #on the selection square

    size = size*2   #length of the Square selection

    #convert to pixel position on selection (x, y)
    A = [int(size*float(ax)),int(size*float(ay))]
    B = [int(size*float(bx)),int(size*float(by))]
    C = [int(size*float(cx)),int(size*float(cy))]
    D = [int(size*float(dx)),int(size*float(dy))]
    E = [int(size*float(ex)),int(size*float(ey))]
    F = [int(size*float(fx)),int(size*float(fy))]
    G = [int(size*float(gx)),int(size*float(gy))]

    #return list of cooridantes
    SevenSeg = [A,B,C,D,E,F,G]
    return SevenSeg

def drawSevenSegPoints(origin, size, SevenSeg):
    A = SevenSeg[0]
    B = SevenSeg[1]
    C = SevenSeg[2]
    D = SevenSeg[3]
    E = SevenSeg[4]
    F = SevenSeg[5]
    G = SevenSeg[6]

    drawPoint(origin, size, A)
    drawPoint(origin, size, B)
    drawPoint(origin, size, C)
    drawPoint(origin, size, D)
    drawPoint(origin, size, E)
    drawPoint(origin, size, F)
    drawPoint(origin, size, G)

def getValueList(SevenSeg, display_inter):
    #get the value (1/0) for each of the 7 segments
    valueList = []
    #Get A value
    for Seg in SevenSeg:
        valueList.append(SegValue(Seg, display_inter))
    return valueList

def SegValue(Seg, display_inter):
    x,y = Seg[0],Seg[1]
    if display_inter[y,x].any(): #if any value not zero, white pixel
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
    erosion_iters       = ConfigSectionMap("PREPROCESS")['erode']
    most_common_filter  = ConfigSectionMap("POSPROCESS")['filter']
    box_size            = ConfigSectionMap("PREPROCESS")['size']
    box_sizeB           = ConfigSectionMap("PREPROCESS")['size']
    threshB             = ConfigSectionMap("PREPROCESS")['threshold']

    start_x, start_y   = 100, 100,
    start_x2, start_y2 = 100, 100,
    
    drawing     = False  # true if mouse is pressed
    draw_second = False  #toggles selection drawing 

    # flag to stop opencv
    stopOpenCv = False

    # user assist vars
    expected_value = ""
    expected_value_desv = 20
    ############################################################################
    
    # Video capture
    cap = cv2.VideoCapture(1)

    def nothing(x):
        pass

    # mouse callback function
    def draw_rectangle(event, x, y, flags, param):
        global start_x, start_y, drawing, expected_value        
        global start_x2, start_y2, draw_second

        if event == cv2.EVENT_LBUTTONDOWN:
            # menu position
            if y < 40:
                # menu map
                if x > 8 and x < 148:
                    SaveImage(event)
                if x > 153 and x < 190:
                    OnClose(event)
                if x > 195 and x < 252:
                    print "Try read the Screen!"
                if x > 258 and x < 355:
                    SaveData()
                if x > 375 and x < 460:
                    draw_second = False                
                if x > 480 and x < 580:
                    draw_second = True
            else:
                drawing = True
                if draw_second == False:
                    start_x, start_y = x, y
                else:
                    start_x2, start_y2 = x, y

        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False                  

        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            if draw_second == False:
                start_x, start_y = x, y
            else:
                start_x2, start_y2 = x, y


    # show main window
    cv2.namedWindow('frame')

    # Show blank image at first
    cv2.namedWindow('Integer selection')
    display_inter   = np.zeros((200, 200, 3), np.uint8)
    cv2.imshow('frame', display_inter)

    cv2.namedWindow('Decimal selection')
    display_decimal   = np.zeros((200, 200, 3), np.uint8)
    cv2.imshow('frame', display_decimal)

    # GUI
    cv2.createTrackbar('Threshold',   'frame', int(thresh),             255,    nothing)
    cv2.createTrackbar('Threshold B', 'frame', int(threshB),            255,    nothing)
    cv2.createTrackbar('Size',        'frame', int(box_size),           100,    nothing)
    cv2.createTrackbar('Size B',      'frame', int(box_sizeB),          100,    nothing)
    cv2.createTrackbar('Erode',       'frame', int(erosion_iters),      4,      nothing)
    cv2.createTrackbar('Filter',      'frame', int(most_common_filter), 10,     nothing)
    
    # menu image
    menu = cv2.imread("menu.png")
    cv2.setMouseCallback('frame', draw_rectangle)

    meas_stack   = []
    integer_List = []
    decimal_List = []
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
        #get selections from main image
        size =  cv2.getTrackbarPos('Size',   'frame')
        sizeB = cv2.getTrackbarPos('Size B', 'frame')
        
        display_inter   = getSelection(start_x, start_y, size)
        display_decimal = getSelection(start_x2, start_y2, sizeB)

        #preprocess Selection
        display_inter   = preprocessImage(display_inter, 'Threshold')
        cv2.imshow('Integer selection', display_inter)

        display_decimal = preprocessImage(display_decimal,'Threshold B')
        cv2.imshow('Decimal selection', display_decimal)

        #Draw Rectangle around selections
        cv2.rectangle(frame, (start_x -size, start_y -size),   (start_x +size, start_y +size),   (0, 255, 0), 1)    #draw Green box
        cv2.rectangle(frame, (int(start_x2 -sizeB*float(0.3)), int(start_y2 -sizeB*float(0.4))),\
                             (int(start_x2 +sizeB*float(0.3)), int(start_y2 +sizeB*float(0.4))), (255, 0, 0), 1)    #draw Green box

        origin = [(start_x -size),\
                  (start_y -size)]      #(x,y) Top Left is Origin 
        originB = [int(start_x2 -sizeB*float(0.3)),\
                   int(start_y2 -sizeB*float(0.4))]   #(x,y) Top Left is Origin 
        
        #Set up Integer Segment read Points
        SevenSegInt1 = SevenSegCo(size, 0.30,0.15, 0.43,0.32, 0.43,0.70,\
                                        0.30,0.83, 0.17,0.70, 0.21,0.32, 0.30,0.50 )
        drawSevenSegPoints(origin, size, SevenSegInt1)

        SevenSegInt2 = SevenSegCo(size, 0.70,0.15, 0.83,0.32, 0.83,0.70,\
                                        0.70,0.83, 0.55,0.70, 0.59,0.32, 0.73,0.50)
        drawSevenSegPoints(origin, size, SevenSegInt2)


        #Read Integer Values
        Int1ValueList = getValueList(SevenSegInt1,display_inter)
        Int2ValueList = getValueList(SevenSegInt2,display_inter)

        #Convert to Number
        Int1Value = convertToNumber(Int1ValueList)
        Int2Value = convertToNumber(Int2ValueList)  

        #Combine integer components and Decimal
        temperatureInt = 10*Int1Value + Int2Value 

        print "Temperature = %d"%temperatureInt
        cv2.imshow('frame', frame)

        

        


        c = cv.WaitKey(20)

        if c == "q":
            break
        if stopOpenCv:
            break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

#find size of selctions
# height,  width,  channel_1 = display_inter.shape