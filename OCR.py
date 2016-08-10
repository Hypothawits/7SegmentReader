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

def Recognize(iplimage):
    global meas_stack
    tesseract.SetCvImage(iplimage, api)

    try:
        full_text = api.GetUTF8Text()
    except AttributeError:
        full_text = api.GetUNLVText().replace("^", "")

    conf = api.MeanTextConf()
    # Get the first line found by tesseract
    for index, text in enumerate(full_text.split('\n')):
        # Some char filter
        text = text.replace(" ", "")
        for char in ConfigSectionMap("POSPROCESS")['strip']:
            text = text.replace(char, "")
        try:
            text_val = float(text)
            # handle OCRed value if exists an expected value prvided by user
            if expected_value != "":
                up_limit = (float(expected_value)) * (1 + (float(expected_value_desv) / 100))
                dn_limit = (float(expected_value)) * (1 - (float(expected_value_desv) / 100))
                if (
                    len(text) > 0 and
                    text_val > dn_limit and
                    text_val < up_limit
                ):
                    pass
                else:
                    return '0'
            # most common filter valur

            most_common_filter_pos = cv2.getTrackbarPos('Filter', 'frame')
            # add last text
            meas_stack.append(text)
            if len(meas_stack) > most_common_filter_pos:
                # remove old
                meas_stack = meas_stack[-(most_common_filter_pos + 1):]
                # count most frequent value
                count = Counter(meas_stack)
                out = count.most_common()[0][0]
                ## show if the last is the most common
                # if out == meas_stack[-1]:
     #           print "Timestamp: " + datetime.datetime.now().strftime('%y%m%d%H%M%S_%f')
                # print "Line " + str(index)
                if conf >= 50:
                    return out
                else:
                    return 'no value'
        except:
            return 'no value'

def SaveData():

    print "Data Saved (Not Really)"

def getthresholdedimg(hsv):
    yellow = cv2.inRange(hsv, np.array((20, 100, 100)), np.array((30, 255, 255)))
    blue = cv2.inRange(hsv, np.array((100, 100, 100)), np.array((120, 255, 255)))
    both = cv2.add(yellow, blue)
    return both

def preprocessImage(imageSelection, X):
    imageSelection = cv2.cvtColor(imageSelection, cv2.COLOR_BGR2GRAY) #GreyScale
    thresh = cv2.getTrackbarPos(X, 'frame')
    imageSelection = cv2.threshold(imageSelection, thresh, 255, cv2.THRESH_BINARY)[1]
    kernel = np.ones((5, 5), np.uint8)
    erosion_iters = cv2.getTrackbarPos('Erode', 'frame')
    imageSelection = cv2.erode(imageSelection, kernel, iterations = erosion_iters)
    return imageSelection

def getSelection(startX, endX, startY, endY, R, G, B):
    min_x = min(startX, endX)
    max_x = max(startX, endX)
    min_y = min(startY, endY)
    max_y = max(startY, endY)
    selection = frame[min_y:max_y, min_x:max_x]
    
    return selection

def getText(display, select):
    if select == "int":
        threshold = 'Threshold I' 
        selection = 'Integer selection'
    elif select == "decimal":
        threshold = 'Threshold D'
        selection = 'Decimal selection'
    else:
        return "Error"

    height, width, channel = display.shape
    channel = 1
    
    display   = preprocessImage(display, threshold)
    cv2.imshow(selection, display)


    iplimage = cv.CreateImageHeader((width, height), cv.IPL_DEPTH_8U, channel)
    cv.SetData(iplimage, display.tostring(), display.dtype.itemsize * channel * (width))
    Text = Recognize(iplimage)
    return Text

print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
print "Start Programe"

if __name__ == '__main__':
    Config = ConfigParser.ConfigParser()
    Config.read("./config.ini")
    ############################################################################
    # Pre process params
    thresh              = ConfigSectionMap("PREPROCESS")['threshold']
    thresh_decimal      = ConfigSectionMap("PREPROCESS")['threshold']
    erosion_iters       = ConfigSectionMap("PREPROCESS")['erode']
    most_common_filter  = ConfigSectionMap("POSPROCESS")['filter']
    
    start_x, start_y,start_x2, start_y2 = -1, -1, -1, -1
    end_x, end_y, end_x2, end_y2        = 1, 1, 1, 1
    
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

    # Tesseract config
    api = tesseract.TessBaseAPI()
    api.Init(".", ConfigSectionMap("OCR")['fonttype'], tesseract.OEM_DEFAULT)
    api.SetVariable("tessedit_char_whitelist", ConfigSectionMap("OCR")['whitelist'])
    api.SetPageSegMode(tesseract.PSM_AUTO)
    api.SetVariable("debug_file", "/dev/null")

    def nothing(x):
        pass

    # mouse callback function
    def draw_rectangle(event, x, y, flags, param):
        global start_x, start_y, end_x, end_y, drawing, expected_value,\
        start_x2, start_y2, end_x2, end_y2, draw_second

        if event == cv2.EVENT_LBUTTONDOWN:
            # menu position
            if y < 40:
                # menu map
                if x > 8 and x < 148:
                    SaveImage(event)
                if x > 153 and x < 190:
                    OnClose(event)
                if x > 195 and x < 252:
                    print "OpenSource Development: https://github.com/arturaugusto/display_inter_ocr.\nBased on examples availables at https://code.google.com/p/python-tesseract/.\nGPLv2 License"
                if x > 258 and x < 355:
                    SaveData()
                if x > 400 and x < 510:
                     draw_second = False
                if x > 520 and x < 630: 
                    draw_second = True
            else:
                drawing = True
                if draw_second: #get decimal selection
                    start_x2, start_y2 = x, y
                    end_x2, end_y2 = x, y
                else: #get integer selection
                    start_x, start_y = x, y
                    end_x, end_y = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            #toggle between selecting Integer / Decimal
                  

        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            if draw_second:
                if y < 40:      #get Decimal selection
                    end_x2, end_y2 = x, 41
                else:
                    end_x2, end_y2 = x, y
            else:               #get integer selection
                if y < 40:
                    end_x, end_y = x, 41
                else:
                    end_x, end_y = x, y



    # show main window
    cv2.namedWindow('frame')

    # Show blank image at first
    cv2.namedWindow('Integer selection')
    cv2.namedWindow('Decimal selection')
    display_inter   = np.zeros((200, 200, 3), np.uint8)
    display_decimal = np.zeros((200, 200, 3), np.uint8)
    cv2.imshow('frame', display_inter)
    cv2.imshow('frame', display_decimal)

    # GUI
    cv2.createTrackbar('Threshold I', 'frame', int(thresh),            255,    nothing)
    cv2.createTrackbar('Erode',       'frame', int(erosion_iters),     4,      nothing)
    cv2.createTrackbar('Threshold D', 'frame', int(thresh_decimal),    255,    nothing)
    cv2.createTrackbar('Filter',      'frame', int(most_common_filter),10,     nothing)

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
        display_inter   = getSelection(start_x, end_x, start_y, end_y,     0,   255, 0)
        display_decimal = getSelection(start_x2, end_x2, start_y2, end_y2, 255, 0  , 0)

        #Draw Rectangle around selections
        cv2.rectangle(frame, (start_x, start_y),   (end_x, end_y),   (0, 255, 0), 1)    #draw Green box
        cv2.rectangle(frame, (start_x2, start_y2), (end_x2, end_y2), (0, 0, 225), 1)    #draw Red box
        cv2.imshow('frame', frame)

        #find size of selctions
        height,  width,  channel_1 = display_inter.shape
        height2, width2, channel_2 = display_decimal.shape

        ########################################################################
        # OCR work
        ########################################################################
        #Integer Selection Processing
        if (height > 10) and (width > 10) and (height2 > 10) and (width2 > 10):
            
            integer_Text = getText(display_inter,   "int")
            decimal_Text = getText(display_decimal, "decimal")

            if integer_Text != 'no value':
               print integer_Text + "    " + "int"
            if decimal_Text != 'no value':
                print decimal_Text + "    " + "dec"

        c = cv.WaitKey(20)

        if c == "q":
            break
        if stopOpenCv:
            break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

