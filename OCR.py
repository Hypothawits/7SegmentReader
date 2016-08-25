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
    print "Using the config.ini enable the number of numbers you want to read."
    print "Within the config.ini set the ip address you wish to send data to."
    print "Select which digit you would like to set up from the menu."
    print "Move the box and adjust the size so that each of the red dots"
    print "fall within each of the 7 segments."
    print "Adjust the threshold slider for each selection so that the number is clearly"
    print "visible with as little noise as possible."

def imageIdentify(Box):
    global config
    try: 
        #Gets and processes the given box selection 
        #Get box size from  it's slider
        Selection_Frame = Box.name    #Selection Frame and Box share Name
        Box.size  = cv2.getTrackbarPos('Size',   Selection_Frame) 
        Box.threshold = cv2.getTrackbarPos('Threshold', Selection_Frame)  

        #Set the min box size
        if Box.size <10:
            Box.size = 10

        #gets and process the selection
        Box.selection = getSelection(Box.location[0], Box.location[1], Box.size)
        Box.selection = preprocessImage(Box.selection, Selection_Frame, Box.threshold)
        
        cv2.imshow(Selection_Frame, Box.selection)    #show proccesed image in selection window
        cv2.resizeWindow(Selection_Frame, 300, 300)   #keeps the windows a set size

        #convert image to number
        ValueList = getValueList(Box.segCoordinates, Box.selection)
        Value     = convertToInt(ValueList)

        return Value
    except:
        print "Selection Error: Out of Bounds"
        return None

def preprocessImage(imageSelection, frame, thresh):
    #preprocesses the selection by removing values below threshold 
    imageSelection  = cv2.cvtColor(imageSelection, cv2.COLOR_BGR2GRAY)  #Make GreyScale
    imageSelection  = cv2.threshold(imageSelection, thresh, 255, cv2.THRESH_BINARY)[1]
    kernel          = np.ones((5, 5), np.uint8)
    erosion_iters   = cv2.getTrackbarPos('Erode', 'frame')
    imageSelection  = cv2.erode(imageSelection, kernel, iterations = erosion_iters)
    return imageSelection

def getSelection(startX, startY, size):
    #gets the selection from the main image
    selection = frame[startY - size:(startY + size), startX - size:(startX + size)]
    return selection

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
        #for debuging, should never happen
        return 5

def convertToInt(X):
    #Uncomment for values less than 10
    # if X == [0,0,0,0,0,0,0]:
    #     return 0
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

def getDate(formate_string):
    return datetime.datetime.now().strftime(formate_string)

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

        #Set Nox variables to Config.ini
        Config.set('SIZES',     self.name,       self.size)
        Config.set('THRESHOLD', self.name,       self.threshold)
        Config.set('LOCATIONS', self.name + 'x', self.location[0])
        Config.set('LOCATIONS', self.name + 'y', self.location[1])

        #Update Window
        cv2.imshow('frame', frame)

class SelectionFrame:
    #Creates a window with threshold and selection size sliders
    def __init__(self, name):
        self.name = name
        cv2.namedWindow(name)
        self.display   = np.zeros((200, 200, 3), np.uint8)
        
        self.thresh   = ConfigSectionMap("THRESHOLD")[self.name]
        self.box_size = ConfigSectionMap("SIZES")[self.name]

        cv2.createTrackbar('Threshold', name,    int(self.thresh),   255, nothing)
        cv2.createTrackbar('Size',      name,    int(self.box_size), 150,  nothing)
        cv2.imshow('frame', self.display)

print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
print "Start Programe"

if __name__ == '__main__':
    ############################################################################
    # Config Set Up and Values loaded 
    Config = ConfigParser.ConfigParser()
    Config.read("./config.ini")
    erosion_iters = ConfigSectionMap("PREPROCESS")['erode']
    
    enable_orange = True if ConfigSectionMap("OCR")['orange'] == "True" else False #convert string to boolean
    enable_blue   = True if ConfigSectionMap("OCR")['blue']   == "True" else False #convert string to boolean

    ############################################################################
    # Variable Set Up
    drawing     = False         # true if mouse is pressed
    Draw_G1     = True          # Must be initialized 
    Draw_G2     = False         #
    Draw_G3     = False         # 
    Row1        = True          #
    Row2, Row3  = False, False  #
    stopOpenCv  = False         # flag to stop opencv

    #initialize to None
    greenValue  = None
    orangeValue = None
    blueValue   = None
    ############################################################################
    # UDP Set Up
    # UDP_IP = "10.1.18.236","127.0.0.1"
    UDP_IP   = ConfigSectionMap("OCR")['ip'] 
    UDP_PORT = 8100
    sock     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    ############################################################################
    # Logging Set Up
    logging.basicConfig(filename = 'Consol.log', format = '%(levelname)s %(message)s', level = logging.DEBUG)
    logging.info('~~~~~~ Start Log ~~~~~~   ' + getDate('%y/%m/%d  %H:%M:%S.%f'))
    #############################################################################
    # Video capture and Settings (Note: May not be avilible on all Cameras)
    cap = cv2.VideoCapture(0)
    cap.set(cv.CV_CAP_PROP_CONTRAST,   150)
    cap.set(cv.CV_CAP_PROP_EXPOSURE,   6.0)
    cap.set(cv.CV_CAP_PROP_BRIGHTNESS, 200)
    #############################################################################

    def nothing(x):
        pass

    # mouse callback function
    def mouseEvent(event, x, y, flags, param):
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
        G1List, O1List, B1List = [],[],[]
        G2List, O2List, B2List = [],[],[]
        G3List, O2List, B3List = [],[],[]
        sendData = True     #Make false to stop UDP data sending

        #Create a list of 10 values and find the mode. 
        #If no value is found, dont add to the list
        for i in range(0, 10, +1):
            #tempery values used incase imageIdentify was called twice
            #Temperature Motor
            tempx = imageIdentify(G_Box1)
            tempy = imageIdentify(G_Box2)
            tempz = imageIdentify(G_Box3)
            if tempx != None: G1List.append(tempx)          
            if tempy != None: G2List.append(tempy)
            if tempz != None: G3List.append(tempz)

            if enable_orange:
                #Temperature Room
                tempx = imageIdentify(O_Box1)
                tempy = imageIdentify(O_Box2)
                tempz = imageIdentify(O_Box3)
                if tempx != None: O1List.append(tempx)          
                if tempy != None: O2List.append(tempy)
                if tempz != None: O2List.append(tempz)

            if enable_blue:
                #Humidity
                tempx = imageIdentify(B_Box1)
                tempy = imageIdentify(B_Box2)
                tempz = imageIdentify(B_Box3)
                if tempx != None: B1List.append(tempx)          
                if tempy != None: B2List.append(tempy)
                if tempz != None: B3List.append(tempz)

        #finds the mode of the Lists, if list is empty throws an ERROR and 
        #sendData is set to false. The program then trys bypassing the 1 second wait. 
        try: #convert Motor Temperature
            G1 = Counter(G1List).most_common(1)[0][0]
            G2 = Counter(G2List).most_common(1)[0][0]
            G3 = Counter(G3List).most_common(1)[0][0]
        except:
            G1, G2, G3 = None,None,None
            log_String = "No Geen Temp Found ---" + getDate('%H:%M:%S.%f')
            logging.warning(log_String)
            # print log_String
            # sendData = False

        if enable_orange: # Find Mode if Enabled 
            try: #convert Room Temperature
                O1 = Counter(O1List).most_common(1)[0][0]
                O2 = Counter(O2List).most_common(1)[0][0]
                O3 = Counter(O2List).most_common(1)[0][0]
            except:
                #Set Values to None
                O1, O2, O3 = None,None,None
                log_String = "No Orange Temp Found --- " + getDate('%H:%M:%S.%f')
                logging.warning(log_String)
                # print log_String
        if enable_blue: # Find Mode if Enabled 
            try: #convert Room Humidity
                B1 = Counter(B1List).most_common(1)[0][0]
                B2 = Counter(B2List).most_common(1)[0][0]
                B3 = Counter(B3List).most_common(1)[0][0]
            except:
                #Set Values to None
                B1, B2, B3 = None,None,None
                log_String = "No Blue Temp Found --- " + Getdate('%H:%M:%S.%f')
                logging.warning(log_String)
                # print log_String

        draw()  #draw all the rectangels 

        ##############################################################################################
        # Send data over UDP
        

        #Combine integer components and Decimal
        greenValue = convertToFloat(G1,G2,G3)
        if enable_orange: orangeValue = convertToFloat(O1,O2,O3)
        if enable_blue:   blueValue   = convertToFloat(B1,B2,B3)
           
        #Create Send data array and log String
        SendArray = [greenValue, orangeValue, blueValue]
        log_String = "Motor Temp: %r :  Room Temp: %r :  Humidity: %r --- "%(greenValue, orangeValue, blueValue) + getDate('%H:%M:%S.%f')
        
        #Print and log outputed Data
        print log_String
        logging.info(log_String)

        #Check if there are Values to Send, and if there are any values, send them.
        if (greenValue != None) or (orangeValue != None) or (blueValue != None):
            #Send Data over network
            sock.sendto('{"temperatures": %r}'%SendArray, (UDP_IP, UDP_PORT))

            c = cv.WaitKey(1000)
            if c == "q":   break
            if stopOpenCv: break

        else: # if none values to send do nothing and restart loop.
            c = cv.WaitKey(1)
            if c == "q":   break
            if stopOpenCv: break

    # When everything done, release the capture, close windows, save config values
    cap.release()
    cv2.destroyAllWindows()

    #Save the Changes to the Config File
    with open("./config.ini",'w') as Configfile:
        Config.write(Configfile)

    logging.info('~~~~~~ End Log ~~~~~~' + getDate('%y/%m/%d  %H:%M:%S.%f'))
