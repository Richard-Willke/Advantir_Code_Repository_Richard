#main interface buildup
#from signal import _SIGNUM
from contextlib import AbstractAsyncContextManager
from json.encoder import INFINITY
import tkinter as tk
from tkinter import *
from tkinter import ttk
import cv2
from tkinter import filedialog

#storage functions
import pickle
import os
os.system('cls')

#functions to find the intersections
import numpy as np
import math
import matplotlib.pyplot as plt

#functions to plot the desired graphs
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib

from tkinter import filedialog

def update_canny_params():
    global lowerBorder 
    global upperBorder

    borders = np.zeros(2)
    lowerBorder = max(0,int(slider.get()) - 25)
    upperBorder = max(int(slider.get()) + 25, 50)
    borders[0] = lowerBorder
    borders[1] = upperBorder
    output.insert(END, "Set Canny Detector parameters." + '\n')
    output.insert(END, "lower border = " + str(lowerBorder) + '\n')
    output.insert(END, "upper border = " + str(upperBorder) + '\n')
    pickle.dump(borders, open("borders.dat", "wb")) 

def _rect_inter_inner(x1,x2):
    n1=x1.shape[0]-1
    n2=x2.shape[0]-1
    X1=np.c_[x1[:-1],x1[1:]]
    X2=np.c_[x2[:-1],x2[1:]]    
    S1=np.tile(X1.min(axis=1),(n2,1)).T
    S2=np.tile(X2.max(axis=1),(n1,1))
    S3=np.tile(X1.max(axis=1),(n2,1)).T
    S4=np.tile(X2.min(axis=1),(n1,1))
    return S1,S2,S3,S4

def _rectangle_intersection_(x1,y1,x2,y2):
    S1,S2,S3,S4=_rect_inter_inner(x1,x2)
    S5,S6,S7,S8=_rect_inter_inner(y1,y2)

    C1=np.less_equal(S1,S2)
    C2=np.greater_equal(S3,S4)
    C3=np.less_equal(S5,S6)
    C4=np.greater_equal(S7,S8)

    ii,jj=np.nonzero(C1 & C2 & C3 & C4)
    return ii,jj

def intersection(x1,y1,x2,y2):
    """
    INTERSECTIONS Intersections of curves.
    Computes the (x,y) locations where two curves intersect.  
    The curves can be broken with NaNs or have vertical segments.
    """
    ii,jj=_rectangle_intersection_(x1,y1,x2,y2)
    n=len(ii)

    dxy1=np.diff(np.c_[x1,y1],axis=0)
    dxy2=np.diff(np.c_[x2,y2],axis=0)

    T=np.zeros((4,n))
    AA=np.zeros((4,4,n))
    AA[0:2,2,:]=-1
    AA[2:4,3,:]=-1
    AA[0::2,0,:]=dxy1[ii,:].T
    AA[1::2,1,:]=dxy2[jj,:].T

    BB=np.zeros((4,n))
    BB[0,:]=-x1[ii].ravel()
    BB[1,:]=-x2[jj].ravel()
    BB[2,:]=-y1[ii].ravel()
    BB[3,:]=-y2[jj].ravel()

    for i in range(n):
        try:
            T[:,i]=np.linalg.solve(AA[:,:,i],BB[:,i])
        except:
            T[:,i]=np.NaN


    in_range= (T[0,:] >=0) & (T[1,:] >=0) & (T[0,:] <=1) & (T[1,:] <=1)

    xy0=T[2:,in_range]
    xy0=xy0.T
    return xy0[:,0],xy0[:,1]

def scaling_programm_part():
    #find all convex hulls within the image via canny edge detection
    try:
        img = image
        img = cv2.imread(img) 
    except:
        img = cv2.imread("test.jpeg") 

    try:
        scalings = pickle.load(open("scalings.dat", "rb"))
        width_in_mm = scalings[0]
        height_in_mm = scalings[1]
    except:
        output.insert(END, "Please update the reference object parameters!" + '\n')
        pass

    t_lower = 50
    t_upper = 100
    try:
        borders = pickle.load(open("borders.dat", "wb"))
        t_lower = borders[0]
        t_upper = borders[1]
    except:
        t_lower = lowerBorder
        t_upper = upperBorder
    else:
        output.insert(END, "Please update the canny detector parameter!" + '\n')
        pass

    edge = cv2.Canny(img, t_lower, t_upper)
    kernel = np.ones((5, 5), np.uint8)  

    #remove the first instance of minor white noise within the edges. then use the edges to find all convex hulls in the image
    dilation = cv2.dilate(edge,kernel,iterations = 1)
    erosion = cv2.erode(dilation,kernel,iterations = 1)
    contours, hierarchy = cv2.findContours(erosion, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    #frame desired hulls out of all hulls
    x = hierarchy[0].shape
    for i in range(len(contours)):    
        if hierarchy[0][i][3] == -1:
            hull = cv2.convexHull(contours[i])
            cv2.drawContours(img, [hull], -1, (0, 255, 0), 2)  

    cv2.imshow('ConvexHull', img)
    cv2.waitKey(0) 

    #find line and normal line that approximate the two main axis of the object
    #then calculate the width and height via the intersections between the object and the lines
    intersection_coord_x = []
    intersection_coord_y = []
    intersection_coord_normal_x = []
    intersection_coord_normal_y = []
    width = []
    height = []
    #object_counter = -1

    #analize all detected objects. len(contours) is equal to the number of found objects 
    for i in range(len(contours)):
        x_coord = []
        y_coord = []   
        x_center = 0
        y_center = 0

        x_min = INFINITY
        x_max = -INFINITY
        y_min = INFINITY
        y_max = -INFINITY
        width_max = 0
        height_max = 0
        index_max = -1
    
        #find the shapes that do not have a parent (or also: find each hull that is not surrounded by any other hull)
        if hierarchy[0][i][3] == -1:
            a = contours[i].shape
            #copy all coordinate data of the chosen object hull 
            for j in range(a[0]): 
                x_center += contours[i][j][0][0]/a[0]
                y_center += contours[i][j][0][1]/a[0]
                x_coord.append(contours[i][j][0][0])
                y_coord.append(contours[i][j][0][1])

                #suche nach min_x , max_x, min_y und max_y
                if contours[i][j][0][0] < x_min:
                    x_min = contours[i][j][0][0]
                if contours[i][j][0][0] > x_max:
                    x_max = contours[i][j][0][0]
                if contours[i][j][0][1] < y_min:
                    y_min = contours[i][j][0][1]
                if contours[i][j][0][1] > y_max:
                    y_max = contours[i][j][0][1]
       
            #find the line that approximates the object the best. This line will later be used to calculate the width of the object
            m, b = np.polyfit(x_coord, y_coord, 1)        
            x_lin = np.linspace(0, 1000, 10000)
            x1 = x_lin
            y1 = m*x_lin + b
            if abs(m)<0.01:
                if m > 0:
                    m = 0.01
                else:
                    m = -0.01
            x2 = np.array(x_coord)
            y2 = np.array(y_coord)
            x_int,y_int=intersection(x1,y1,x2,y2)
            intersection_coord_x.append(x_int)
            intersection_coord_y.append(y_int)

            #if there are more than one intersections (usually just 2 because of convex hull),
            #then calculate the middle of the object, the normal line to the polyfit line and also the intersections with the normal line
            if intersection_coord_x != []:
                if len(intersection_coord_x[0]) > 1:
                    middle_x = (intersection_coord_x[0][0] + intersection_coord_x[0][1])/2
                    middle_y = (intersection_coord_y[0][0] + intersection_coord_y[0][1])/2        
                    m_normal = -(1/m)
                    b_normal = middle_y - middle_x*m_normal
                    x_n = np.linspace(0, 1000, 10000)
                    x_normal = x_n
                    y_normal = x_normal*m_normal + b_normal
                    x_new,y_new=intersection(x_normal,y_normal,x2,y2)
                    intersection_coord_normal_x.append(x_new)
                    intersection_coord_normal_y.append(y_new)
        
            #if there is more than one intersection with the normal line (goal is again 2 because of convex hull),
            #then calculate the width and height of the object
            if intersection_coord_normal_x != []:
                if len(intersection_coord_normal_x[0]) > 1:
                    width.append(np.sqrt((intersection_coord_x[0][0]-intersection_coord_x[0][1])**2 + (intersection_coord_y[0][0]-intersection_coord_y[0][1])**2))
                    height.append(np.sqrt((intersection_coord_normal_x[0][0]-intersection_coord_normal_x[0][1])**2 + (intersection_coord_normal_y[0][0]-intersection_coord_normal_y[0][1])**2))
                else:
                    alpha = np.arctan(m)
                    width.append(abs((x_max-x_min)*np.cos(alpha)))
                    height.append(abs((y_max-y_min)*np.sin(alpha)))
                    #width.append(0)
                    #height.append(0)
            else:
                alpha = np.arctan(m)
                width.append(abs((x_max-x_min)*np.cos(alpha)))
                height.append(abs((y_max-y_min)*np.sin(alpha)))
                #width.append(0)
                #height.append(0)

            if width_max < width[-1] and height_max < height[-1]:
                width_max = width[-1]
                height_max = height[-1]
                index_max = i

            if width[-1] != 0 and height[-1] != 0:
                hull = cv2.convexHull(contours[i])
                cv2.drawContours(img, [hull], -1, (0, 0, 255), 2) 

            #reset the coordinates for the next object that has to be analyzed
            intersection_coord_x.clear()
            intersection_coord_y.clear()
            intersection_coord_normal_x.clear()
            intersection_coord_normal_y.clear()
        
            #clear object information for the next object that has to be analyzed 
            x_coord.clear()
            y_coord.clear()

    hull = cv2.convexHull(contours[index_max])
    cv2.drawContours(img, [hull], -1, (255, 0, 255), 2)  

    cv2.imshow('ConvexHull', img)
    cv2.waitKey(0) 
    
    #plot the values and give useful information of the scanned objects
    #average_width = np.sum(width)/object_counter
    #average_height = np.sum(height)/object_counter
    
    area = []
    for i in range(len(width)):
        area.append(width[i]*height[i])
    
    reference_object = 0
    reference_object = np.argmax(area)
    output.insert(END, "Received object number " + str(reference_object) + " as reference object." + '\n')
    
    #parameters of reference 
    #reference_obj_number = 0
    #reference_obj_number = reference_object
    output.insert(END, "Confirmed reference object number: " + str(reference_object) + '\n')
    pixel_per_mm_width = width[reference_object]/width_in_mm
    pixel_per_mm_height = height[reference_object]/height_in_mm
    
    #array of rescaled size values
    width_in_mm_rescaled = []
    height_in_mm_rescaled = []

    #store all valuable and usable data
    for i in range(len(width)):
        if i != reference_object and (width[i] != 0 or height[i] != 0):
            width_in_mm_rescaled.append(width[i]/pixel_per_mm_width)
            height_in_mm_rescaled.append(height[i]/pixel_per_mm_height)

    width_in_mm_rescaled.sort()
    height_in_mm_rescaled.sort()

    #plot relevant values in bar charts. Needs to be changed dependent on the user's intent
    child = Toplevel(window, bg = "black")
    
    fig5 = Figure(figsize=(5, 4), dpi=100)
    figure_canvas = FigureCanvasTkAgg(fig5, child)
    axes = fig5.add_subplot()
    axes.bar(range(len(width_in_mm_rescaled)), width_in_mm_rescaled)
    axes.set_title('number of analyzed objects')
    axes.set_ylabel('object width in mm')
    axes.set_yticks(np.arange(max(width_in_mm_rescaled)+1))
    figure_canvas.get_tk_widget().grid(row = 21, column = 4, sticky = W)   
    
    fig6 = Figure(figsize=(5, 4), dpi=100)
    figure_canvas2 = FigureCanvasTkAgg(fig6, child)
    axes2 = fig6.add_subplot()
    axes2.bar(range(len(height_in_mm_rescaled)), height_in_mm_rescaled)
    axes2.set_title('number of analyzed objects')
    axes2.set_ylabel('object height in mm')
    axes2.set_yticks(np.arange(max(height_in_mm_rescaled)+1))
    figure_canvas2.get_tk_widget().grid(row = 21, column = 5, sticky = W)  
    
    #useful information that will be printed out
    average_width_mm = np.sum(width_in_mm_rescaled)/len(width_in_mm_rescaled)
    average_height_mm = np.sum(height_in_mm_rescaled)/len(height_in_mm_rescaled)
    greatest_width_mm = '%.2f' % max(width_in_mm_rescaled)
    smallest_width_mm =  '%.2f' % min(width_in_mm_rescaled)
    greatest_height_mm = '%.2f' % max(height_in_mm_rescaled)
    smallest_height_mm = '%.2f' % min(height_in_mm_rescaled)
    
    output_information.insert(END, "Greatest width:" + '\t' + '\t' +  str(greatest_width_mm ) + "mm" + '\n')
    output_information.insert(END, "Smallest width:" + '\t' + '\t' + str(smallest_width_mm ) + "mm" + '\n')
    output_information.insert(END, "Greatest height:" + '\t' + str(greatest_height_mm ) + "mm" + '\n')
    output_information.insert(END, "Smallest height:" + '\t' + str(smallest_height_mm ) + "mm" + '\n')
    output_information.insert(END, "Average width:" + " " + '\t' + '\t' + str('%.2f' % average_width_mm) + "mm" + '\n')
    output_information.insert(END, "Average height:" + '\t' + '\t' + str('%.2f' % average_height_mm) + "mm" + '\n')
    
    output.insert(END, "Calculated values, scaled in mm." + '\n')

def update_reference_dimensions():
    global width_in_mm
    global height_in_mm
    global scalings
    width_in_mm = 24
    height_in_mm = 18.6
    scalings = np.zeros(2)
    
    if textentry_reference_dimensions_x.get() != "" and textentry_reference_dimensions_y.get() != "":
        try: 
            width_in_mm = float(textentry_reference_dimensions_x.get())
            height_in_mm = float(textentry_reference_dimensions_y.get())
            scalings[0] = width_in_mm
            scalings[1] = height_in_mm
            output.insert(END, "Adjusted reference object dimensions." + '\n')
            output.insert(END, "x = " + str(width_in_mm) + '\n')
            output.insert(END, "y = " + str(height_in_mm) + '\n')
            pickle.dump(scalings, open("scalings.dat", "wb")) 
        except: 
            scalings = pickle.load(open("scalings.dat", "rb"))
            width_in_mm = scalings[0]
            height_in_mm = scalings[1]
            output.insert(END, "Rolling with stored values." + '\n')
            output.insert(END, "x = " + str(width_in_mm) + '\n')
            output.insert(END, "y = " + str(height_in_mm) + '\n')
       
def click_upload():
    #entered_text = textentry_picture.get()
    output.delete(0.0,END)
    global image

    tempdir = filedialog.askopenfilename(parent=window, initialdir="/",title='Select a .mp4 video file')
    if len(tempdir) > 0:
        image = tempdir
        #cv2.imshow('Pre processed picture', image)
        output.insert(END, "UPLOADED IMAGE:" + '\n')
        output.insert(END, image + '\n')
    '''
    try:
        image = cv2.imread(entered_text + ".jpg")
        cv2.imshow('Pre processed picture', image)
        output.insert(END, entered_text + ".jpg picture uploaded." + '\n')
    except:
        image = cv2.imread(entered_text + ".jpeg")
        cv2.imshow('Pre processed picture', image)
        output.insert(END, entered_text + ".jpeg picture uploaded." + '\n')
    '''
              
def find_object_dimensions():
    scaling_programm_part()
    output.insert(END, "Processed all object hulls." + '\n')
  
def close_window():
    pickle.dump(scalings, open("scalings.dat", "wb"))
    window.destroy()
    exit()
   
if __name__ == "__main__":   
    window = Tk()
    window.title("Height and width analysis programm")
    window.configure(background = "grey")

    Label(window, text = "Reference Object Dimensions im mm:", bg = "grey", fg = "white", font = "none 10 bold").grid(row = 2, column = 0, sticky = W)
    Label(window, text = "x", bg = "grey", fg = "white", font = "none 10 bold").grid(row = 2, column = 2, sticky = W)
    textentry_reference_dimensions_x = Entry(window, width = 17, bg = "white")
    textentry_reference_dimensions_y = Entry(window, width = 17, bg = "white")
    textentry_reference_dimensions_x.grid(row = 2, column = 1, sticky = W)
    textentry_reference_dimensions_y.grid(row = 2, column = 3, sticky = W)
    Button(window, text= "SUBMIT", width = 14, command = update_reference_dimensions).grid(row = 3, column = 1, sticky = W)

    Label(window, text = "\t \t Intensity value:", bg = "grey", fg = "white", font = "none 10 bold").grid(row = 4, column = 0, sticky = W)
    current_value = tk.DoubleVar()
    slider = Scale(window,from_=0,to=400,orient=HORIZONTAL)
    slider.grid(row = 4, column = 1, columnspan = 3, sticky = W)
    Button(window, text= "SUBMIT", width = 14, command = update_canny_params).grid(row = 5, column = 1, sticky = W)

    Label(window, text = "\t \t Give picture path:", bg = "grey", fg = "white", font = "none 10 bold").grid(row = 9, column = 0, sticky = W)
    Button(window, text = "UPLOAD", width = 14, command = click_upload).grid(row = 9, column = 1, sticky = W)

    Label(window, text = "\t \t Start Analysis:", bg = "grey", fg = "white", font = "none 10 bold").grid(row = 11, column = 0, sticky = W)
    Button(window, text = "START", width = 14, command = find_object_dimensions).grid(row = 11, column = 1, sticky = W)

    Label(window, text = "Logbook output:", bg = "grey", fg = "white", font = "none 10 bold").grid(row = 14, column = 0, sticky = W)
    output = Text(window, width = 40, height = 6, wrap = WORD, background = "white")
    output.grid(row = 15, column = 0, columnspan = 4, sticky = W)

    Label(window, text = " ", bg = "grey", fg = "white", font = "none 10").grid(row = 16, column = 0, sticky = W)
    Label(window, text = "Information output:", bg = "grey", fg = "white", font = "none 10 bold").grid(row = 14, column = 5, sticky = W)
    output_information = Text(window, width = 40, height = 6, wrap = WORD, background = "white")
    output_information.grid(row = 15, column = 5, columnspan = 4, sticky = W)

    Button(window, text= "EXIT", width = 8, command = close_window).grid(row = 20, column = 0, sticky = W)

    window.mainloop()

'''
#print(cv2.__file__) 
#pyinstaller mainInterfaceBuildup.py -F --paths="D:\Studium\WS20\Python\lib\site-packages\cv2" 
#will need to compile the .exe with this command since cv2 makes problems there

#20220608_120434
#width_in_mm = 24
#height_in_mm = 18.6
#SizeDetectorFinishedInterface.py
'''