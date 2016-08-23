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