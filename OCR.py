#!/usr/bin/env python
# import tesseract
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

#add time stamp to send data
#look for memory leak

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

def SaveData():
    #Does not do anything yet
    print "Doesn't Save Yet" 

def imageIdentify(Box, Selection):
    #Gets and processes the given box selection 

    #Get box size from slider
    Box.size = cv2.getTrackbarPos('Size',   Selection) 
    
    #Set the min box size
    if Box.size <10:
        Box.size = 10

    #gets and process the selection
    Box.selection = getSelection(Box.location[0], Box.location[1], Box.size)
    Box.selection = preprocessImage(Box.selection, 'Threshold', Selection)
    
    cv2.imshow(Selection, Box.selection)    #show proccesed image in selection window
    cv2.resizeWindow(Selection, 300, 300)   #keeps the windows a set size

    #convert image to number
    ValueList = getValueList(Box.segCoordinates,Box.selection)
    Value     = convertToNumber(ValueList)
    return Value

def getthresholdedimg(hsv):
    yellow = cv2.inRange(hsv, np.array((20, 100, 100)), np.array((30, 255, 255)))
    blue = cv2.inRange(hsv, np.array((100, 100, 100)), np.array((120, 255, 255)))
    both = cv2.add(yellow, blue)
    return both

def preprocessImage(imageSelection, X, frame):
    #preprocesses the selection by removing things 

    imageSelection  = cv2.cvtColor(imageSelection, cv2.COLOR_BGR2GRAY)  #Make GreyScale
    thresh          = cv2.getTrackbarPos(X, frame)                      #Get threshold from slider
    imageSelection  = cv2.threshold(imageSelection, thresh, 255, cv2.THRESH_BINARY)[1]
    
    kernel          = np.ones((5, 5), np.uint8)
    erosion_iters   = cv2.getTrackbarPos('Erode', 'frame')
    imageSelection  = cv2.erode(imageSelection, kernel, iterations = erosion_iters)
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
        return None

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
    location = [200, 200]
    
    

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
    global Config
    Config = ConfigParser.ConfigParser()
    Config.read("./config.ini")

    thresh   = ConfigSectionMap("PREPROCESS")['threshold']
    box_size = ConfigSectionMap("PREPROCESS")['size']

    def __init__(self, name):
        self.name = name
        cv2.namedWindow(name)
        self.display   = np.zeros((200, 200, 3), np.uint8)
        cv2.createTrackbar('Threshold', name,    int(self.thresh),   255, nothing)
        cv2.createTrackbar('Size',      name,    int(self.box_size), 150,  nothing)
        cv2.imshow('frame', self.display)

# class MappingError(Exception):
#     def __init__(self, value):
#         self.value = value
#     def __str__(self):
#         return repr(self.value)


print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
print "Start Programe"

if __name__ == '__main__':
    Config = ConfigParser.ConfigParser()
    Config.read("./config.ini")
    ############################################################################
    # Pre process params
    erosion_iters       = ConfigSectionMap("PREPROCESS")['erode']
    most_common_filter  = ConfigSectionMap("POSPROCESS")['filter']

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
    UDP_IP = "10.1.18.236"
    # UDP_IP = "127.0.0.1" #my ip
    UDP_PORT = 8100
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    # sock.sendto("Temperature Recording Started", (UDP_IP, UDP_PORT))
    ############################################################################
    #Logginf Set Up
    logging.basicConfig(filename = 'Consol.log', format = '%(levelname)s %(message)s', level = logging.DEBUG)
    logging.info('~~~~~~ Start Log ~~~~~~   ' + datetime.datetime.now().strftime('%y/%m/%d  %H:%M:%S.%f'))

    #############################################################################
    # Video capture
    cap = cv2.VideoCapture(0)
    cap.set(cv.CV_CAP_PROP_CONTRAST, 150.0)
    cap.set(cv.CV_CAP_PROP_EXPOSURE, 6.0)
    cap.set(cv.CV_CAP_PROP_BRIGHTNESS, 200)

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
                    print "Select which digit you would like to set up from the menu."
                    print "Move the box and adjust the size so that is covers the digit,"
                    print "each on the red dots should fall within each of the 7 segments."
                    print "Adjust the threshold slider for each selection so that the number is clearly"
                    print "visible with as little noise as possible."
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
                    # print "first Int Room"
                    Draw_FIntR = True
                    Draw_SIntR, Draw_FDecR = False,False
                if x > 276 and x < 312:
                    # print "second Int Room"
                    Draw_SIntR = True
                    Draw_FIntR, Draw_FDecR = False,False

                if x > 340 and x < 380:
                    # print "first decimal Room"
                    Draw_FDecR = True
                    Draw_FIntR, Draw_SIntR = False,False

            elif (y > 80)and(y < 120):
                #menu map, Third row Humidity
                Row3 = True
                Row1, Row2 = False,False
                if x > 230 and x < 270:
                    # print "first Int Humidity"
                    Draw_FIntH = True
                    Draw_SIntH, Draw_FDecH = False,False
                if x > 276 and x < 312:
                    # print "second Int Humidity"
                    Draw_SIntH = True
                    Draw_FIntH, Draw_FDecH = False,False

                if x > 340 and x < 380:
                    # print "first decimal Humidity"
                    Draw_FDecH = True
                    Draw_FIntH, Draw_SIntH = False,False

            else:
                drawing = True
                if Row1:    #Motor Temp
                    if (Draw_FIntM):
                        Motor_IntBox1.location = [x, y]
                    if (Draw_SIntM):
                        Motor_IntBox2.location = [x, y]
                    if (Draw_FDecM):
                        Motor_DecimalBox.location = [x, y]
                if Row2:    #Room Temp
                    if (Draw_FIntR):
                        Room_IntBox1.location = [x, y]
                    if (Draw_SIntR):
                        Room_IntBox2.location = [x, y]
                    if (Draw_FDecR):
                        Room_DecimalBox.location = [x, y]
                if Row3:    #Room umidity
                    if (Draw_FIntH):
                        Humidity_IntBox1.location = [x, y]
                    if (Draw_SIntH):
                        Humidity_IntBox2.location = [x, y]
                    if (Draw_FDecH):
                        Humidity_DecimalBox.location = [x, y]

        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False                  

        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            if Row1:    #Motor Temp
                if (Draw_FIntM):
                    Motor_IntBox1.location = [x, y]
                if (Draw_SIntM):
                    Motor_IntBox2.location = [x, y]
                if (Draw_FDecM):
                    Motor_DecimalBox.location = [x, y]
            if Row2:    #Room Temp
                if (Draw_FIntR):
                    Room_IntBox1.location = [x, y]
                if (Draw_SIntR):
                    Room_IntBox2.location = [x, y]
                if (Draw_FDecR):
                    Room_DecimalBox.location = [x, y]
            if Row3:    #Room umidity
                if (Draw_FIntH):
                    Humidity_IntBox1.location = [x, y]
                if (Draw_SIntH):
                    Humidity_IntBox2.location = [x, y]
                if (Draw_FDecH):
                    Humidity_DecimalBox.location = [x, y]

    # GUI and windows
    # show main window
    cv2.namedWindow('frame')
    cv2.createTrackbar('Erode', 'frame', int(erosion_iters),       4,   nothing)
    cv2.createTrackbar('Filter','frame', int(most_common_filter), 10,   nothing)

    # Create selection frames
    Int_selection_1_motor = SelectionFrame('Motor_Int1')
    Int_selection_2_motor = SelectionFrame('Motor_Int2')
    Dec_selection_motor   = SelectionFrame('Motor_Decimal')

    # Int_selection_1_room = SelectionFrame('Room_Int1')
    # Int_selection_2_room = SelectionFrame('Room_Int2')
    # Dec_selection_room   = SelectionFrame('Room_Decimal')

    # Int_selection_1_Humidity = SelectionFrame('Humidity_Int1')
    # Int_selection_2_Humidity = SelectionFrame('Humidity_Int2')
    # Dec_selection_Humidity   = SelectionFrame('Humidity_Decimal')

    
    # menu image
    menu = cv2.imread("menu.png")
    cv2.setMouseCallback('frame', draw_rectangle)

    meas_stack   = []
    integer_List = []
    decimal_List = []

    #create Boxes
    Motor_IntBox1       = segBox((0,255,0))
    Motor_IntBox2       = segBox((0,245,0))
    Motor_DecimalBox    = segBox((0,235,0))

    Room_IntBox1        = segBox((0,185,255))
    Room_IntBox2        = segBox((0,175,245))
    Room_DecimalBox     = segBox((0,165,235))

    Humidity_IntBox1    = segBox((255,185,0))
    Humidity_IntBox2    = segBox((245,175,0))
    Humidity_DecimalBox = segBox((235,165,0))
 
#Main Loop
    while True:
        # Capture frame-by-frame, Frame is the whole image captured
        ret, frame = cap.read()
        if frame is None:
            print 'ERROR: Frame is None, Camera not Found'
            logging.critical('Frame is None, Camera not Found')
            break
        
        # add menu
        frame_h, frame_w = frame.shape[:2]
        frame[0:menu.shape[0], 0:menu.shape[1]] = menu
    ########################################################################
    # ROI Regions of Interest
    ########################################################################
        Int1MotorList, Int1RoomList, Int1HumidityList = [],[],[]
        Int2MotorList, Int2RoomList, Int2HumidityList = [],[],[]
        DecMotorList,  DecRoomList,  DecHumidityList    = [],[],[]
        sendData = True
        #get 10 values to
        for i in range(0,10,+1):
          #Temperature Motor
            tempx = imageIdentify(Motor_IntBox1,    'Motor_Int1')
            tempy = imageIdentify(Motor_IntBox2,    'Motor_Int2')
            tempz = imageIdentify(Motor_DecimalBox, 'Motor_Decimal')
            if tempx != None:
                Int1MotorList.append(tempx)          
            if tempy != None:
                Int2MotorList.append(tempy)
            if tempz != None:
                DecMotorList.append(tempz)

          #Temperature Room
          #   Int1Room = imageIdentify(Room_IntBox1,    'Room_Int1')
          #   Int2Room = imageIdentify(Room_IntBox2,    'Room_Int2')
          #   DecRoom  = imageIdentify(Room_DecimalBox, 'Room_Decimal')
            # tempx = imageIdentify(Room_IntBox1,    'Room_Int1')
            # tempy = imageIdentify(Room_IntBox2,    'Room_Int2')
            # tempz = imageIdentify(Room_DecimalBox, 'Room_Decimal')
            # if tempx != None:
            #     Int1RoomList.append(tempx)          
            # if tempy != None:
            #     Int2RoomList.append(tempy)
            # if tempz != None:
            #     DecRoomList.append(tempz)

          #Humidity
          #   Int1Humidity = imageIdentify(Humidity_IntBox1,    'Humidity_Int1')
          #   Int2Humidity = imageIdentify(Humidity_IntBox2,    'Humidity_Int2')
          #   DecHumidity  = imageIdentify(Humidity_DecimalBox, 'Humidity_Decimal')
            # tempx = imageIdentify(Humidity_IntBox1,    'Humidity_Int1')
            # tempy = imageIdentify(Humidity_IntBox2,    'Humidity_Int2')
            # tempz = imageIdentify(Humidity_DecimalBox, 'Humidity_Decimal')
            # if tempx != None:
            #     Int1HumidityList.append(tempx)          
            # if tempy != None:
            #     Int2HumidityList.append(tempy)
            # if tempz != None:
            #     DecHumidityList.append(tempz)

        #finds the mode of the Lists, if any are empty (ie Failed to convert to Number)
            #then an error is thrown and no data is sent. The program then trys again.
        try:
            Int1Motor = Counter(Int1MotorList).most_common(1)[0][0]
            Int2Motor = Counter(Int2MotorList).most_common(1)[0][0]
            DecMotor  = Counter(DecMotorList ).most_common(1)[0][0]

            # Int1Room = Counter(Int1RoomList).most_common(1)[0][0]
            # Int2Room = Counter(Int2RoomList).most_common(1)[0][0]
            # DecRoom  = Counter(DecRoomList ).most_common(1)[0][0]

            # Int1Humidity = Counter(Int1HumidityList).most_common(1)[0][0]
            # Int2Humidity = Counter(Int2HumidityList).most_common(1)[0][0]
            # DecHumidity  = Counter(DecHumidityList ).most_common(1)[0][0]
        except:
            log_String = "List Empty! --- " + datetime.datetime.now().strftime('%H:%M:%S.%f')
            logging.warning(log_String)
            print log_String
            
            sendData = False

       #Draw Rectangle and Location Points
        #must be done after the selections are made, 
        #or the box and points will appear in the image!
        Motor_IntBox1.drawBoxRectangle()
        Motor_IntBox2.drawBoxRectangle()
        Motor_DecimalBox.drawBoxRectangle()
        
        # Room_IntBox1.drawBoxRectangle()
        # Room_IntBox2.drawBoxRectangle()
        # Room_DecimalBox.drawBoxRectangle()
        
        # Humidity_IntBox1.drawBoxRectangle()
        # Humidity_IntBox2.drawBoxRectangle()
        # Humidity_DecimalBox.drawBoxRectangle()

        if sendData:
            #Combine integer components and Decimal
            temperatureMotor = float(10*Int1Motor + Int2Motor) + 0.1*float(DecMotor)
            # temperatureRoom  = 10*Int1Room  + Int2Room  + 0.1*DecRoom
            # humidityRoom     = 10*Int1Humidity + Int2Humidity + 0.1*DecHumidity
            
            # print "Motor Temp: %0.1f,  Room Temp: %0.1f,  Humidity: %0.1f"%(temperatureMotor, temperatureRoom, humidityRoom)
            log_String = "Motor Temp: %0.1f --- "%(temperatureMotor) + datetime.datetime.now().strftime('%H:%M:%S.%f')
            
            print log_String
            logging.info(log_String)

            #Send Data over network
            SendArray = [temperatureMotor]
            sock.sendto('{"temperatures": %r}'%SendArray, (UDP_IP, UDP_PORT))


            cv2.imshow('frame', frame)
            c = cv.WaitKey(1000)
            if c == "q":
                break
            if stopOpenCv:
                break
        else:
            cv2.imshow('frame', frame)
            c = cv.WaitKey(1)

        if stopOpenCv:
                break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
    logging.info('~~~~~~ End Log ~~~~~~' + datetime.datetime.now().strftime('%y/%m/%d  %H:%M:%S.%f'))
