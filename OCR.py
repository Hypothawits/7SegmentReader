#Seven Segment Reader
import socket
import logging
import numpy as np
import cv2
import cv2.cv as cv
import time
import datetime
from   time import strftime
from   collections import Counter
import ConfigParser

def ConfigSectionMap(section):
    #Gets the Config values from the config.ini file
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
    #Sets the program to stop camera capture and close 
    global stopOpenCv
    stopOpenCv = True

def Instructions():
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print "Using the config.ini enable the number of numbers you want to read."
    print "Within the config.ini set the ip address you wish to send data to."
    print "Select which digit you would like to set up from the menu."
    print "Move the box and adjust the size so that each of the red dots"
    print "fall within each of the 7 segments."
    print "Adjust the threshold slider for each selection so that the number is clearly"
    print "visible with as little noise as possible."
    print "box locations and threshold values are only saved when the programme is closed via"
    print "the exit button, or the escape key 'q' is pressed."
    print "Press any key to continue!"
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    cv.WaitKey()

def imageIdentify(Box):
    global config
    try: 
        #Gets and processes the given box selection 
        #Get box size from  it's slider
        Selection_Frame = Box.name    #Selection Frame and Box share Name
        Box.size        = cv2.getTrackbarPos('Size',   Selection_Frame) 
        Box.threshold   = cv2.getTrackbarPos('Threshold', Selection_Frame)  

        #Set the min box size
        if Box.size <10: Box.size = 10

        #gets and process the selection
        Box.selection = getSelection(Box.location[0], Box.location[1], Box.size)
        Box.selection = preprocessImage(Box.selection, Selection_Frame, Box.threshold)
        
        cv2.imshow(Selection_Frame, Box.selection)    #show proccesed image in selection window
        cv2.resizeWindow(Selection_Frame, 300, 300)   #keeps the windows a set size so you cant see trackbars

        #convert image to number
        ValueList = getValueList(Box.segCoordinates, Box.selection)
        Value     = convertToInt(ValueList)

        return Value
    except:
        print "Selection Error: Out of Bounds"
        return None

def getSelection(startX, startY, size):
    #gets the selection from the main image
    selection = frame[startY - size:(startY + size), startX - size:(startX + size)]
    return selection

def preprocessImage(imageSelection, frame, thresh):
    #preprocesses the selection by removing values below threshold 
    imageSelection  = cv2.cvtColor(imageSelection, cv2.COLOR_BGR2GRAY)  #Make GreyScale
    imageSelection  = cv2.threshold(imageSelection, thresh, 255, cv2.THRESH_BINARY)[1]
    kernel          = np.ones((5, 5), np.uint8)
    erosion_iters   = cv2.getTrackbarPos('Erode', 'frame')
    imageSelection  = cv2.erode(imageSelection, kernel, iterations = erosion_iters)
    return imageSelection

def getValueList(SevenSeg, selection):
    #get the value (1/0) for each of the 7 segments
    valueList = []
    #Get A value
    for Seg in SevenSeg:
        valueList.append(SegValue(Seg, selection))
    return valueList

def SegValue(Seg, selection):
    x,y = Seg[0],Seg[1]
    try:
        if selection[y,x].any(): #if any value not zero, white pixel
            return 0
        else:
            return 1
    except:
        #for debuging, in case pixel out size of selection range
        return None

def convertToInt(X):
    #Uncomment for values less than 10
    if X == [0,0,0,0,0,0,0]: return 0
    if X == [1,1,1,1,1,1,0]: return 0
    if X == [0,1,1,0,0,0,0]: return 1
    if X == [1,1,0,1,1,0,1]: return 2
    if X == [1,1,1,1,0,0,1]: return 3
    if X == [0,1,1,0,0,1,1]: return 4
    if X == [1,0,1,1,0,1,1]: return 5
    if X == [1,0,1,1,1,1,1]: return 6
    if X == [1,1,1,0,0,0,0]: return 7
    if X == [1,1,1,1,1,1,1]: return 8    
    if X == [1,1,1,1,0,1,1]: return 9
    else: return None

def convertToFloat(a,b,c):
    try:
        return float(10*a + b) + 0.1*float(c)
    except:
        return None

def draw():
    #Draw Rectangle and Location Points
    #must be done after the selections are made, 
    #or the boxs and points will appear in the processed image!
    G_Box1.drawBoxRectangle()
    G_Box2.drawBoxRectangle()
    G_Box3.drawBoxRectangle()
    
    if enable_orange: #draw boxes if enabled
        O_Box1.drawBoxRectangle()
        O_Box2.drawBoxRectangle()
        O_Box3.drawBoxRectangle()
    if enable_blue:  #draw boxes if enabled  
        B_Box1.drawBoxRectangle()
        B_Box2.drawBoxRectangle()
        B_Box3.drawBoxRectangle()

    cv2.imshow('frame', frame)

def getDate(formate_string):
    
    return datetime.datetime.now().strftime(formate_string)

def nothing(x):
        #on trackbar change, do nothing
        pass

def mouseEvent(event, x, y, flags, param):
    # mouse callback function
    global Row1,    Row2,    Row3,   drawing      
    global Draw_G1, Draw_G2, Draw_G3
    global Draw_O1, Draw_O2, Draw_O3
    global Draw_B1, Draw_B2, Draw_B3

    if event == cv2.EVENT_LBUTTONDOWN:
        # menu position
        if y < 40:
            # menu map, First row Motor Temp
            Row1 = True
            Row2,Row3 = False,False

            if x > 3 and x < 40:
                OnClose(event)
            elif x > 45 and x < 105:
                Instructions()
                                    
            # Selection Control buttons
            elif x > 230 and x < 270:
                # print "first Int Motor"
                Draw_G1 = True
                Draw_G2, Draw_G3 = False,False                
            elif x > 276 and x < 312:
                # print "second Int Motor"
                Draw_G2 = True
                Draw_G1, Draw_G3 = False,False
            elif x > 340 and x < 380:
                # print "first decimal Motor"
                Draw_G3 = True
                Draw_G1, Draw_G2 = False,False

        elif (y > 40)and(y < 80):
            if enable_orange:
                #menu map, Second row Room Temp
                Row2 = True
                Row1, Row3 = False, False
                if x > 230 and x < 270:
                    # print "first Int Room"
                    Draw_O1 = True
                    Draw_O2, Draw_O3 = False,False
                elif x > 276 and x < 312:
                    # print "second Int Room"
                    Draw_O2 = True
                    Draw_O1, Draw_O3 = False,False

                elif x > 340 and x < 380:
                    # print "first decimal Room"
                    Draw_O3 = True
                    Draw_O1, Draw_O2 = False,False

        elif (y > 80)and(y < 120):
            if enable_blue:
                #menu map, Third row Humidity
                Row3 = True
                Row1, Row2 = False,False
                if x > 230 and x < 270:
                    # print "first Int Humidity"
                    Draw_B1 = True
                    Draw_B2, Draw_B3 = False,False
                elif x > 276 and x < 312:
                    # print "second Int Humidity"
                    Draw_B2 = True
                    Draw_B1, Draw_B3 = False,False

                elif x > 340 and x < 380:
                    # print "first decimal Humidity"
                    Draw_B3 = True
                    Draw_B1, Draw_B2 = False,False

        #Get mouse location for Drawing Selecion Boxes
        else:
            drawing = True
            if Row1:    #Geen Temperature
                if   Draw_G1: G_Box1.location = [x, y] 
                elif Draw_G2: G_Box2.location = [x, y] 
                elif Draw_G3: G_Box3.location = [x, y] 
                
            elif Row2:    #Room Temp
                if   Draw_O1: O_Box1.location = [x, y]
                elif Draw_O2: O_Box2.location = [x, y]
                elif Draw_O3: O_Box3.location = [x, y]
                
            elif Row3:    #Room umidity
                if   Draw_B1: Box1.location   = [x, y]
                elif Draw_B2: B_Box2.location = [x, y]
                elif Draw_B3: B_Box3.location = [x, y]

    #Move selection with mouse (while clicked)
    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        if Row1:    #Motor Temp
            if   Draw_G1: G_Box1.location = [x, y]
            elif Draw_G2: G_Box2.location = [x, y]
            elif Draw_G3: G_Box3.location = [x, y]
            
        elif Row2:    #Room Temp
            if   Draw_O1: O_Box1.location = [x, y]
            elif Draw_O2: O_Box2.location = [x, y]
            elif Draw_O3: O_Box3.location = [x, y]
            
        elif Row3:    #Room umidity
            if   Draw_B1: B_Box1.location = [x, y]
            elif Draw_B2: B_Box2.location = [x, y]
            elif Draw_B3: B_Box3.location = [x, y]

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False 

class segBox:
    #creates the frame and 7 seg point overlay for each selection 

    #Segment relative locations, adjust if displays are tilted differently.
    ax,ay = 0.50, 0.15
    bx,by = 0.65, 0.25
    cx,cy = 0.63, 0.65
    dx,dy = 0.46, 0.85
    ex,ey = 0.35, 0.65
    fx,fy = 0.36, 0.25
    gx,gy = 0.50, 0.50
    segmentLocations = [[ax,ay],[bx,by],[cx,cy],[dx,dy],[ex,ey],[fx,fy],[gx,gy]]

    #For storing image selection
    selection      = []

    #Point location coordinates
    segCoordinates = []

    #Set default location and size
    size      = 10
    threshold = 80
    location  = [200, 200]
    
    def __init__(self, name, colour):
        self.colour = colour
        self.name = name
        self.locationx = int(ConfigSectionMap("LOCATIONS")[self.name + 'x'])
        self.locationy = int(ConfigSectionMap("LOCATIONS")[self.name + 'y'])
        self.location = [self.locationx, self.locationy]

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

        #draw indicator for each segment location 
        for point in self.segCoordinates:
            cv2.circle(frame, (origin[0] + point[0], origin[1] + point[1]), 1, (0, 0, 255), -1)

        #Set values variables to Config.ini
        Config.set('SIZES',     self.name,       self.size)
        Config.set('THRESHOLD', self.name,       self.threshold)
        Config.set('LOCATIONS', self.name + 'x', self.location[0])
        Config.set('LOCATIONS', self.name + 'y', self.location[1])

        #Update Window
        cv2.imshow('frame', frame)

class SelectionFrame:
    #Creates a named window with threshold and selection size sliders
    def __init__(self, name):
        self.name = name
        cv2.namedWindow(name)

        self.display  = np.zeros((200, 200, 3), np.uint8)
        self.thresh   = ConfigSectionMap("THRESHOLD")[self.name]
        self.box_size = ConfigSectionMap("SIZES")[self.name]

        cv2.createTrackbar('Threshold', name,    int(self.thresh),   255,  nothing)
        cv2.createTrackbar('Size',      name,    int(self.box_size), 150,  nothing)
        cv2.imshow('frame', self.display)

print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
print "                   Start Programe                   "

if __name__ == '__main__':
    ############################################################################
    # Config Set Up and Values loaded 
    Config = ConfigParser.ConfigParser()
    Config.read("./config.ini")
    erosion_iters = ConfigSectionMap("PREPROCESS")['erode'] #Default is 1, seems to work best
    
    enable_orange = True if ConfigSectionMap("OCR")['orange'] == "True" else False #convert string to boolean
    enable_blue   = True if ConfigSectionMap("OCR")['blue']   == "True" else False #convert string to boolean

    ############################################################################
    # Variable Set Up
    drawing     = False         # true if mouse is pressed
    stopOpenCv  = False         # flag to stop opencv
    # Must be initialized 
    Row1,Row2,Row3          = True,False,False
    Draw_G1,Draw_G2,Draw_G3 = True,False,False
    Draw_O1,Draw_O2,Draw_O3 = False,False,False
    Draw_B1,Draw_B2,Draw_B3 = False,False,False

    #initialize to None
    greenValue, orangeValue, blueValue = None,None,None
    ############################################################################
    # UDP Set Up
    # UDP_IP = "10.1.18.236","127.0.0.1"
    UDP_IP   = ConfigSectionMap("OCR")['ip'] 
    UDP_PORT = 8100
    sock     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    ############################################################################
    # Logging Set Up
    logging.basicConfig(filename = 'Console.log', format = '%(levelname)s %(message)s', level = logging.DEBUG)
    logging.info('~~~~~~ Start Log ~~~~~~   ' + getDate('%y/%m/%d  %H:%M:%S.%f'))
    #############################################################################
    # Video capture and Settings (Note: May not be avilible on all Cameras)
    cap = cv2.VideoCapture(            int(ConfigSectionMap("CAMERA")['camera']))
    cap.set(cv.CV_CAP_PROP_CONTRAST,   int(ConfigSectionMap("CAMERA")['contrast']))
    cap.set(cv.CV_CAP_PROP_EXPOSURE,   int(ConfigSectionMap("CAMERA")['exposure']))
    cap.set(cv.CV_CAP_PROP_BRIGHTNESS, int(ConfigSectionMap("CAMERA")['brightness']))
    #############################################################################
    # GUI and Window Set Up
    # show main window and add it's trackbar
    cv2.namedWindow('frame')
    cv2.createTrackbar('Erode', 'frame', int(erosion_iters), 4, nothing)

    #create Boxes
    G_Box1 = segBox("g_box1" ,(0,255,0))
    G_Box2 = segBox("g_box2" ,(0,255,0))
    G_Box3 = segBox("g_box3" ,(0,255,0))

    O_Box1 = segBox("o_box1" ,(0,185,255))
    O_Box2 = segBox("o_box2" ,(0,185,255))
    O_Box3 = segBox("o_box3" ,(0,185,255))

    B_Box1 = segBox("b_box1" ,(255,185,0))
    B_Box2 = segBox("b_box2" ,(255,185,0))
    B_Box3 = segBox("b_box3" ,(255,185,0))


    # Create selection frames. Each set is for a 2 digit number with 1 decimal
    SelectionFrame(G_Box1.name)
    SelectionFrame(G_Box2.name)
    SelectionFrame(G_Box3.name)

    if enable_orange: #only create frames if option enabled
        SelectionFrame(O_Box1.name)
        SelectionFrame(O_Box2.name)
        SelectionFrame(O_Box3.name)

    if enable_blue:
        SelectionFrame(B_Box1.name)
        SelectionFrame(B_Box2.name)
        SelectionFrame(B_Box3.name)

    # Load Menu Image and Set up mouse callback
    menu = cv2.imread("menu.png")
    cv2.setMouseCallback('frame', mouseEvent)

#Main Loop
    while True:
        # Capture frame-by-frame, Frame is the whole image captured
        ret, frame = cap.read()
        #Check that Image was captured
        if frame is None:
            print 'ERROR: Frame is None, Camera not Found'
            logging.critical('Frame is None, Camera not Found')
            break
        
        # Draw menu over Frame
        frame[0:menu.shape[0], 0:menu.shape[1]] = menu
        ########################################################################
        # ROI Regions of Interest
        G1, O1, B1 = None,None,None
        G2, O2, B2 = None,None,None
        G3, O3, B3 = None,None,None

        #Temperature Motor
        G1 = imageIdentify(G_Box1)
        G2 = imageIdentify(G_Box2)
        G3 = imageIdentify(G_Box3)

        if enable_orange:
            #Temperature Room
            O1 = imageIdentify(O_Box1)
            O2 = imageIdentify(O_Box2)
            O3 = imageIdentify(O_Box3)

        if enable_blue:
            #Humidity
            B1 = imageIdentify(B_Box1)
            B2 = imageIdentify(B_Box2)
            B3 = imageIdentify(B_Box3)

        draw()  #draw all the rectangels 

        ##############################################################################################
        # Send data over UDP
        #Combine integer components and Decimal
        greenValue = convertToFloat(G1,G2,G3) #Try convert to Float, else set to None
        if enable_orange: orangeValue = convertToFloat(O1,O2,O3)
        if enable_blue:   blueValue   = convertToFloat(B1,B2,B3)
           
        #Create Send data array and log String
        SendArray = [greenValue, orangeValue, blueValue]
        log_String = "Motor Temp: %r :  Room Temp: %r :  Humidity: %r --- "%(greenValue, orangeValue, blueValue) + getDate('%H:%M:%S.%f')
        
        #Print and log outputed Data
        print log_String
        logging.info(log_String)

        #Check if there are Values to Send, and if there are any values, send them.
        if (greenValue is not None) or (orangeValue is not None) or (blueValue is not None):
            #Send Data over network
            sock.sendto('{"temperatures": %r}'%SendArray, (UDP_IP, UDP_PORT))

            c = cv.WaitKey(1000)
            if c == ord("q"):   break
            if stopOpenCv: break

        else: # if none values to send do nothing and restart loop.
            c = cv.WaitKey(1)
            if c == ord("q"):   break
            if stopOpenCv: break

    # When everything done, release the capture, close windows, save config values
    cap.release()
    cv2.destroyAllWindows()

    #Save the Changes to the Config File
    with open("./config.ini",'w') as Configfile:
        Config.write(Configfile)

    logging.info('~~~~~~ End Log ~~~~~~' + getDate('%y/%m/%d  %H:%M:%S.%f'))
