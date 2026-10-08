'''
Author: Richard Fabian Willke
Place: Advantir Innovations, SwirlGO, Singapore
Date: 2nd June, 2022

Purpose: 
This code analyses the width of the dispensed Ice Cream of the machine. 
The input is a camera video from the documentation stand. 
The programm uses the canny edge detector to find the edges of the ice cream inside the image.
The distance of the two outer edges is being used to calculate the width. 
The width is being corrected with the angle of the ice cream, since the width will look broader when the stream has a tilt.         
In the end, the value is being plotted in a graph for manual analysis. 
The data can also be used for further machine controlled analysis.
Ideally, the resulting function should look like a step function: 
time < 0 : x = 0
time >= 0: x = 1
'''

import numpy as np
import matplotlib.pyplot as plt
import math
import tkinter as tk
from tkinter import *
from tkinter import filedialog
import cv2
import pickle
import os
import pandas as pd
import datetime
os.system('cls')

def update_border_params():
    global lowerBorder 
    global upperBorder

    try:
        borders = pickle.load(open("borders.dat", "rb"))
    except:
        lowerBorder = 150
        upperBorder = 190
    borders = np.zeros(2)
    
    try:
        lowerBorder = max(0,int(slider.get()) - 25)
        upperBorder = max(int(slider.get()) + 25, 50)
        borders[0] = lowerBorder
        borders[1] = upperBorder
        output.delete(0.0,END)
        output.insert(END, "Set Canny Detector parameters." + '\n')
        output.insert(END, "lower border = " + str(lowerBorder) + '\n')
        output.insert(END, "upper border = " + str(upperBorder) + '\n')
        pickle.dump(borders, open("borders.dat", "wb")) 
    except: 
        borders = pickle.load(open("borders.dat", "rb"))
        lowerBorder = borders[0]
        upperBorder = borders[1]
        output.delete(0.0,END)
        output.insert(END, "Rolling with stored values." + '\n')
        output.insert(END, "lower border = " + str(lowerBorder) + '\n')
        output.insert(END, "upper border = " + str(upperBorder) + '\n')
    
    video = cv2.VideoCapture(chosen_video)

    while(video.isOpened()):
        ret, frame = video.read()
        if ret == True:                                                 #if you put in a different frame size, first look at the image size
            image =  frame
            borders[0] = lowerBorder
            borders[1] = upperBorder
            output.delete(0.0,END)
            output.insert(END, "Set canny parameters." + '\n')
            output.insert(END, "lower border = " + str(lowerBorder) + '\n')
            output.insert(END, "upper border = " + str(upperBorder) + '\n')
            pickle.dump(borders, open("ROI_borders.dat", "wb")) 
            video.release()

def setROIborders():
    global leftBorder 
    global rightBorder
    global topBorder 
    global bottomBorder 
    leftBorder = 120
    rightBorder = 170
    topBorder = 120    
    bottomBorder = 170
    ROI_borders = (0,0,0,0)

    try:
        ROI_borders = pickle.load(open("ROI_borders.dat", "rb"))
    except:
        leftBorder = 120
        rightBorder = 170
        topBorder = 120
        bottomBorder = 170
        ROI_borders = np.zeros(4)
    
    try:
        video = cv2.VideoCapture(chosen_video)
        ret, frame = video.read()
        if ret == True:                                                 #if you put in a different frame size, first look at the image size
            image =  frame
            region = cv2.selectROI(image)
            
            leftBorder = int(region[0])
            rightBorder = int(region[2]) + int(region[0])
            topBorder = int(region[1])
            bottomBorder = int(region[3]) + int(region[1])
            ROI_borders = np.zeros(4)
            ROI_borders[0] = leftBorder
            ROI_borders[1] = rightBorder
            ROI_borders[2] = topBorder
            ROI_borders[3] = bottomBorder
            output.delete(0.0,END)
            output.insert(END, "Set ROI borders." + '\n')
            output.insert(END, "left border = " + str(leftBorder) + '\n')
            output.insert(END, "right border = " + str(rightBorder) + '\n')
            output.insert(END, "top border = " + str(topBorder) + '\n')
            output.insert(END, "bottom border = " + str(bottomBorder) + '\n')
            pickle.dump(ROI_borders, open("ROI_borders.dat", "wb")) 
    except: 
        ROI_borders = pickle.load(open("ROI_borders.dat", "rb"))
        ROI_borders[0] = leftBorder
        ROI_borders[1] = rightBorder
        ROI_borders[2] = topBorder
        ROI_borders[3] = bottomBorder
        output.delete(0.0,END)
        output.insert(END, "Rolling with stored values." + '\n')
        output.insert(END, "left border = " + str(leftBorder) + '\n')
        output.insert(END, "right border = " + str(rightBorder) + '\n')
        output.insert(END, "top border = " + str(topBorder) + '\n')
        output.insert(END, "bottom border = " + str(bottomBorder) + '\n')

def uploadVideo():
    tempdir = filedialog.askopenfilename(parent=window, initialdir="/",title='Select a .mp4 video file')
    if len(tempdir) > 0:
        video_name = tempdir
        global chosen_video 
        chosen_video = video_name
        output.delete(0.0,END)
        output.insert(END, "VIDEO UPLOADED:" + '\n' + chosen_video + '\n')
        
def analysisProgramm():
    output.delete(0.0,END)
    average_width = 0
    global width_over_time
    global hue_variance_axis
    global intensity_variance_axis
    global saturation_variance_axis
    global time
    width_over_time = []
    frame_number = []
    counter = 0

    hue_average_list = []
    intensity_average_list = []
    saturation_average_list = []

    try:
        t_lower = lowerBorder
        t_upper = upperBorder
    except:
        borders = pickle.load(open("borders.dat", "rb"))
        t_lower = borders[0]
        t_upper = borders[1]

    try:
        lowest_point = bottomBorder
        highest_point = topBorder
        left_border_roi = leftBorder
        right_border_roi = rightBorder
    except:
        ROI_borders = pickle.load(open("ROI_borders.dat", "rb"))
        lowest_point = int(ROI_borders[0])
        highest_point = int(ROI_borders[1])
        left_border_roi = int(ROI_borders[2])
        right_border_roi = int(ROI_borders[3])

    hue_variance_axis = []
    intensity_variance_axis = []
    saturation_variance_axis = []
    cut_off_time = []
    stream_cut_off_heights = []
    video = cv2.VideoCapture(chosen_video)

    if(video.isOpened() == False):
        print("Error opening video file")

    while(video.isOpened()):
        ret, frame = video.read()
        try:
            frame = frame[max(0,(highest_point-50)):min(len(frame[0]),(lowest_point+50)), max(0,(left_border_roi-50)):min(len(frame[1]),(right_border_roi+50))]
        except:
            break

        edge_frame = cv2.Canny(frame, t_lower, t_upper)
        frame_HSV = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        stream_hue = []
        stream_intensity = []
        stream_saturation = []
        hue_average = 0
        hue_variance = 0
        intensity_average = 0
        intensity_variance = 0
        saturation_average = 0
        saturation_variance = 0

        if ret == True:                                                 #if you put in a different frame size, first look at the image size
            counter += 1                                                #increase counter after each frame
            minimum = 0                                                 #reset minimum and maximum after each analized frame
            maximum = 0
            normed_distance = []
            middle_pixel_x = []
            middle_pixel_y = []
            m = 0
            b = 0
            cut_off_point = frame.shape[0] 

            for i in range(50,lowest_point-highest_point+50):    
                listing = []
                edge_frame_list= np.asmatrix(edge_frame)
                for j in range(0,right_border_roi-left_border_roi+100): 
                    if edge_frame_list[i,j] > 0:
                        listing.append(j)  
                    if len(listing)>1:    
                        minimum = listing[0]
                        maximum = listing[-1]
                    else:
                        minimum = maximum 

                if i<=cut_off_point:
                    if minimum == maximum:
                        cut_off_point = i
                        break                                           # new break statement. exit width analysis for frame if break off point detected
                    else:  
                        cut_off_point = frame.shape[0]-50              
                        frame[i,minimum] = frame[i,maximum] = (0, 0, 255)
                        normed_distance.append((maximum - minimum))
                        middle_pixel_x.append(minimum)
                        middle_pixel_y.append(i)
                        average_width = np.sum(normed_distance)
                        #for j in range(minimum, maximum+1):
                        for j in range(minimum+1, maximum):
                            stream_hue.append((frame_HSV[i,j,0]*2))
                            stream_intensity.append((frame_HSV[i,j,2]*100/255))
                            stream_saturation.append((frame_HSV[i,j,1]*100/255))
                            #print(frame_HSV[i,j,1])

            stream_cut_off_heights.append(cut_off_point)
            if((len(normed_distance) == 0) or (cut_off_point == 50)):
                average_width = 0
            else:
                average_width = np.sum(normed_distance)/(cut_off_point-50)
            if len(stream_cut_off_heights)>=2:
                if stream_cut_off_heights[-1] < stream_cut_off_heights[-2]:
                    cut_off_time.append(counter/30)            

            m = 0
            b = 0
            alpha = 0
            if len(middle_pixel_y)>=2 and len(middle_pixel_x)>=2:
                m, b = np.polyfit(middle_pixel_y, middle_pixel_x, 1)        #make line fitting alongside the border of the stream, to calculate its angle
                alpha = np.arctan(m)
        
            if len(stream_hue)>0:
                hue_average = np.sum(stream_hue)/len(stream_hue)
                intensity_average = np.sum(stream_intensity)/len(stream_intensity)
                saturation_average = np.sum(stream_saturation)/len(stream_saturation)
                for k in range(len(stream_hue)):
                    stream_hue[k] = stream_hue[k]-hue_average
                    stream_intensity[k] = stream_intensity[k]-intensity_average
                    stream_saturation[k] = stream_saturation[k]-saturation_average
                hue_average_list.append(hue_average)
                intensity_average_list.append(intensity_average)
                saturation_average_list.append(saturation_average)
            hue_variance_axis.append(hue_average)  
            intensity_variance_axis.append(intensity_average) 
            saturation_variance_axis.append(saturation_average)  
            width_over_time.append(average_width*math.cos(alpha))           #correct the width by accounting the angle & attach new value to the list that is being plotted later
            frame_number.append(counter)
            average_width = 0
            cv2.imshow('frame', frame) 
            if cv2.waitKey(25) == ord('q'):                                 #stop the video by pressing q. This will immediately lead to the printout of the graph, however only up to the already displayed frame
                break
        else:
            break
        
    video.release()
    cv2.destroyAllWindows()

    time = []
    for i in range(len(frame_number)):
        time.append(frame_number[i]/30)

    plt.plot(time, width_over_time)
    plt.xlabel('time in seconds')
    plt.ylabel('width in pixel over time')
    plt.title('Width of flowing substance over course of dispense')
    if len(cut_off_time) > 0:
        for i in range(len(cut_off_time)):
            plt.axvline(x=cut_off_time[i],color="red", linestyle ="dotted")
    plt.show()
    
    hue_variance_axis_sorted = np.sort(hue_variance_axis)
    try:
        median = hue_variance_axis_sorted[len(hue_variance_axis_sorted)/2]
    except:
        median = hue_variance_axis_sorted[int(len(hue_variance_axis_sorted)/2)]

    maximum_variance = np.max(hue_variance_axis)
    minimum_variance = np.min(hue_variance_axis)
    maximum_variance_time = np.argmax(hue_variance_axis)/30

    hue_average = np.sum(hue_variance_axis)/len(hue_variance_axis)
    hue_average_of_average = np.sum(hue_average_list)/len(hue_average_list)
    for k in range(len(hue_average_list)):
        hue_average_list[k] = hue_average_list[k]-hue_average_of_average
    hue_variance = ((np.sum(hue_average_list))**2)/len(hue_average_list)

    output.delete(0.0, END)
    output.insert(END,"Hue average:" + '\t' + '\t' + str(f'{hue_average:.3E}') + '\n') 
    output.insert(END,"Hue max:" + '\t' + '\t' + str(f'{maximum_variance:.3E}') + '\n')
    output.insert(END,"Hue min:" + '\t' + '\t' + str(f'{minimum_variance:.3E}') + '\n')
    output.insert(END,"Hue variance:" + '\t' + '\t' + str(f'{hue_variance:.3E}') + '\n')

    plt.plot(time, hue_variance_axis)
    plt.xlabel('time in seconds')
    plt.ylabel('hue of flow over time')
    plt.ylim([0,360])
    plt.title('hue of flow color over course of dispense')
    if len(cut_off_time) > 0:
        for i in range(len(cut_off_time)):
            plt.axvline(x=cut_off_time[i],color="red", linestyle ="dotted")
    plt.axhline(y=maximum_variance, linestyle='dotted')
    plt.axhline(y=minimum_variance, linestyle='dotted')
    #plt.text(maximum_variance, maximum_variance_time, '({}, {})'.format(maximum_variance, maximum_variance_time))
    plt.show()

    intensity_variance_axis_sorted = np.sort(intensity_variance_axis)
    maximum_variance = np.max(intensity_variance_axis)
    minimum_variance = np.min(intensity_variance_axis)
    maximum_variance_time = np.argmax(intensity_variance_axis)/30

    intensity_average = np.sum(intensity_variance_axis)/len(intensity_variance_axis)
    intensity_average_of_average = np.sum(intensity_average_list)/len(intensity_average_list)
    for k in range(len(intensity_average_list)):
        intensity_average_list[k] = intensity_average_list[k]-intensity_average_of_average
    intensity_variance = ((np.sum(intensity_average_list))**2)/len(intensity_average_list)

    output.delete(0.0, END)
    output.insert(END,"Intensity average:" + '\t' + '\t' + '\t' + str(f'{intensity_average:.3E}') + '\n') 
    output.insert(END,"Intensity max:" + '\t' + '\t' + '\t' + str(f'{maximum_variance:.3E}') + '\n')
    output.insert(END,"Intensity min:" + '\t' + '\t' + '\t' + str(f'{minimum_variance:.3E}') + '\n')
    output.insert(END,"Intensity variance:" + '\t' + '\t' + '\t' + str(f'{intensity_variance:.3E}') + '\n')

    plt.plot(time, intensity_variance_axis)
    plt.xlabel('time in seconds')
    plt.ylabel('intensity of flow over time')
    plt.ylim([0,100])
    plt.title('intensity of flow color over course of dispense')
    if len(cut_off_time) > 0:
        for i in range(len(cut_off_time)):
            plt.axvline(x=cut_off_time[i],color="red", linestyle ="dotted")
    plt.axhline(y=maximum_variance, linestyle='dotted')
    plt.axhline(y=minimum_variance, linestyle='dotted')
    #plt.text(maximum_variance, maximum_variance_time, '({}, {})'.format(maximum_variance, maximum_variance_time))
    plt.show()

    saturation_variance_axis_sorted = np.sort(saturation_variance_axis)
    maximum_variance = np.max(saturation_variance_axis)
    minimum_variance = np.min(saturation_variance_axis)
    maximum_variance_time = np.argmax(saturation_variance_axis)/30

    saturation_average = np.sum(saturation_variance_axis)/len(saturation_variance_axis)
    saturation_average_of_average = np.sum(saturation_average_list)/len(saturation_average_list)
    for k in range(len(saturation_average_list)):
        saturation_average_list[k] = saturation_average_list[k]-saturation_average_of_average
    saturation_variance = ((np.sum(saturation_average_list))**2)/len(saturation_average_list)

    output.delete(0.0, END)
    output.insert(END,"Saturation average:" + '\t' + '\t' + '\t' + str(f'{saturation_average:.3E}') + '\n') 
    output.insert(END,"Saturation max:" + '\t' + '\t' + '\t' + str(f'{maximum_variance:.3E}') + '\n')
    output.insert(END,"Saturation min:" + '\t' + '\t' + '\t' + str(f'{minimum_variance:.3E}') + '\n')
    output.insert(END,"Saturation variance:" + '\t' + '\t' + '\t' + str(f'{saturation_variance:.3E}') + '\n')

    plt.plot(time, saturation_variance_axis)
    plt.xlabel('time in seconds')
    plt.ylabel('saturation of flow over time')
    plt.ylim([0,100])
    plt.title('saturation of flow color over course of dispense')
    if len(cut_off_time) > 0:
        for i in range(len(cut_off_time)):
            plt.axvline(x=cut_off_time[i],color="red", linestyle ="dotted")
    plt.axhline(y=maximum_variance, linestyle='dotted')
    plt.axhline(y=minimum_variance, linestyle='dotted')
    #plt.text(maximum_variance, maximum_variance_time, '({}, {})'.format(maximum_variance, maximum_variance_time))
    plt.show()

    df = pd.DataFrame({"Time":np.array(time),
                        "Width over time":np.array(width_over_time),
                        "hue over time":np.array(hue_variance_axis)
                        })
    now = datetime.datetime.now()
    dt_string = now.strftime("%d_%m_%Y_%H_%M_%S")
    df.to_csv('session_dataset_'+dt_string+'.csv')
    
def postAnalysis():
    length = int(slider2.get())
    filtered_width = []
    #filtered_hue = []
    #filtered_intensity = []
    filtered_hue_average = []
    filtered_intensity_average = []
    filtered_saturation_average = []

    for i in (range(0,int(len(width_over_time)+length-1))):
        if i >= length and i < len(width_over_time):
            filtered_width.append(filtered_width[-1]+(width_over_time[i]-width_over_time[i-length])/length)
            filtered_hue_average.append(filtered_hue_average[-1]+(hue_variance_axis[i]-hue_variance_axis[i-length])/length)
            filtered_intensity_average.append(filtered_intensity_average[-1]+(intensity_variance_axis[i]-intensity_variance_axis[i-length])/length)
            filtered_saturation_average.append(filtered_saturation_average[-1]+(saturation_variance_axis[i]-saturation_variance_axis[i-length])/length)
        elif i < length:
            try:
                filtered_width.append(filtered_width[-1]+width_over_time[i]/length)
                filtered_hue_average.append(filtered_hue_average[-1]+(hue_variance_axis[i]/length)-(hue_variance_axis[0]/length))
                filtered_intensity_average.append(filtered_intensity_average[-1]+(intensity_variance_axis[i]/length)-(intensity_variance_axis[0]/length))
                filtered_saturation_average.append(filtered_saturation_average[-1]+(saturation_variance_axis[i]/length)-(saturation_variance_axis[0]/length))
            except:
                filtered_width.append(width_over_time[i]/length)
                filtered_hue_average.append(hue_variance_axis[0])
                filtered_intensity_average.append(intensity_variance_axis[0])
                filtered_saturation_average.append(saturation_variance_axis[0])
        elif i >= len(width_over_time):
            filtered_width.append(filtered_width[-1]-width_over_time[i-length]/length)
            filtered_hue_average.append(filtered_hue_average[-1]-hue_variance_axis[i-length]/length)
            filtered_intensity_average.append(filtered_intensity_average[-1]-intensity_variance_axis[i-length]/length)
            filtered_saturation_average.append(filtered_saturation_average[-1]-saturation_variance_axis[i-length]/length)

    time2 = []
    filtered_width2 = []
    filtered_hue2 = []
    filtered_intensity2 = []
    filtered_saturation2 = []
    a = len(time)
    for i in range(a):
        time2.append(time[i])
        filtered_width2.append(filtered_width[i])
        filtered_hue2.append(filtered_hue_average[i])
        filtered_intensity2.append(filtered_intensity_average[i])
        filtered_saturation2.append(filtered_saturation_average[i])
    hue_sorted = np.sort(filtered_hue2)
    try:
        median_hue = hue_sorted[len(hue_sorted)/2]
    except:
        median_hue = hue_sorted[int(len(hue_sorted)/2)]
    hue_average = np.sum(filtered_hue2)/len(filtered_hue2)
    for i in range(len(hue_sorted)):
        hue_sorted[i] -= hue_average
    #hue_variance = ((np.sum(hue_sorted - hue_average))**2)/len(hue_sorted)
    hue_variance = ((np.sum(hue_sorted))**2)/len(hue_sorted)
    plt.plot(time2, filtered_width2)
    plt.xlabel('time in seconds')
    plt.ylabel('width in pixel over time')
    plt.title('Width of flowing substance over course of dispense')
    plt.show()


    n = 40
    hue_approx = []
    hue_approx = np.polyfit(time2, filtered_hue2, n)
    y = []
    for i in range(len(time2)):
        new = 0
        for k in range(len(hue_approx)):
            new += (hue_approx[n-k])*(time2[i]**(k))
        y.append(new)

    output.delete(0.0, END)
    output.insert(END,"Hue average:" + '\t' + '\t' + '\t' + str(f'{hue_average:.3E}') + '\n')
    output.insert(END,"Hue median:" + '\t' + '\t' + '\t' + str(f'{median_hue:.3E}') + '\n')
    output.insert(END,"Hue max:" + '\t' + '\t' + '\t' + str(f'{hue_sorted[-1]:.3E}') + '\t' + '\t' + "Hue max approx:" + '\t' + '\t' + '\t' + str(f'{np.max(y):.3E}') + '\n') 
    output.insert(END,"Hue min:" + '\t' + '\t' + '\t' + str(f'{hue_sorted[0]:.3E}') + '\t' + '\t' + "Hue min approx:" + '\t' + '\t' + '\t' + str(f'{np.min(y):.3E}') + '\n') 
    output.insert(END,"Hue range:" + '\t' + '\t' + '\t' + str(f'{(hue_sorted[-1]-hue_sorted[0]):.3E}') + '\t' + '\t' + "Hue range approx:" + '\t' + '\t' + '\t' + str(f'{(np.max(y)-np.min(y)):.3E}') + '\n')
    output.insert(END,"Hue variance:" + '\t' + '\t' + '\t' + str(f'{hue_variance:.3E}') + '\n')

    fig, ax = plt.subplots()
    ax.plot(time2, y, c="r")
    ax.axhline(y=max(y), linestyle='dotted', c="r")
    ax.axhline(y=min(y), linestyle='dotted', c="r")
    ax.plot(time2, filtered_hue2)
    plt.xlabel('time in seconds')
    plt.ylabel('hue of flow over time')
    maximum_variance = np.max(filtered_hue2)
    minimum_variance = np.min(filtered_hue2)
    ax.axhline(y=maximum_variance, linestyle='dotted')
    ax.axhline(y=minimum_variance, linestyle='dotted')
    plt.ylim([0,360])
    plt.title('hue of flow color over course of dispense')
    y_sort = np.sort(y)
    value_matrix = []
    cluster = []
    j = 1
    cluster.append(y[0])
    radius = float(slider3.get())/10
    borders = []
    while j < len(y):                                         #iterate through all values y to cluster
        if abs(y_sort[j-1]-y_sort[j])<radius:
            cluster.append(y_sort[j])
        else:
            value_matrix.append(cluster)
            borders.append(cluster[-1])
            cluster.clear()
            cluster.append(y_sort[j])
        j += 1
    value_matrix.append(cluster)
    if len(value_matrix)>1:
        borders_time = []
        for n in range(len(borders)):
            for k in range(len(y)):
                if y[k] == borders[n]:
                    borders_time.append(time2[k])
        borders_time_filtered = []
        for n in range(len(borders_time)):
            if abs(borders_time[n]-borders_time[n-1])>(1/10):
                borders_time_filtered.append(borders_time[n])
        borders_time_filtered.append(borders_time[n])
        for col in range(len(borders_time_filtered)):
            ax.axvline(x=borders_time_filtered[col], linestyle='dotted', c="g")
    plt.show()


    n = 40
    intensity_approx = []
    intensity_approx = np.polyfit(time2, filtered_intensity2, n)
    y = []
    for i in range(len(time2)):
        new = 0
        for k in range(len(intensity_approx)):
            new += (intensity_approx[n-k])*(time2[i]**(k))
        y.append(new)  

    intensity_average = np.sum(filtered_intensity2)/len(filtered_intensity2)
    intensity_sorted = np.sort(filtered_intensity2)
    median_intensity = intensity_sorted[int(len(intensity_sorted)/2)]

    output.delete(0.0, END)
    output.insert(END,"Intensity average:" + '\t' + '\t' + '\t' + str(f'{intensity_average:.3E}') + '\n')
    output.insert(END,"Intensity median:" + '\t' + '\t' + '\t' + str(f'{median_intensity:.3E}') + '\n')
    output.insert(END,"Intensity max:" + '\t' + '\t' + '\t' + str(f'{intensity_sorted[-1]:.3E}') + '\t' + '\t' + '\t' + "Intensity max approx:" + '\t' + '\t' + '\t' + '\t' + str(f'{np.max(y):.3E}') + '\n') 
    output.insert(END,"Intensity min:" + '\t' + '\t' + '\t' + str(f'{intensity_sorted[0]:.3E}') + '\t' + '\t' + '\t' + "Intensity min approx:" + '\t' + '\t' + '\t' + '\t' + str(f'{np.min(y):.3E}') + '\n') 
    output.insert(END,"Intensity range:" + '\t' + '\t' + '\t' + str(f'{(intensity_sorted[-1]-intensity_sorted[0]):.3E}') + '\t' + '\t' + '\t' + "Intensity range approx:" + '\t' + '\t' + '\t' + '\t' + str(f'{(np.max(y)-np.min(y)):.3E}') + '\n')
    #output.insert(END,"Intensity variance:" + str(f'{intensity_variance:.3E}') + '\n')

    fig, ax = plt.subplots()
    ax.plot(time2, y, c="r")
    ax.axhline(y=max(y), linestyle='dotted', c="r")
    ax.axhline(y=min(y), linestyle='dotted', c="r")
    ax.plot(time2, filtered_intensity2)
    plt.xlabel('time in seconds')
    plt.ylabel('intensity of flow over time')
    maximum_variance = np.max(filtered_intensity2)
    minimum_variance = np.min(filtered_intensity2)
    ax.axhline(y=maximum_variance, linestyle='dotted')
    ax.axhline(y=minimum_variance, linestyle='dotted')
    plt.ylim([0,100])
    plt.title('intensity of flow color over course of dispense')
    y_sort = np.sort(y)
    value_matrix = []
    cluster = []
    j = 1
    cluster.append(y[0])
    radius2 = float(slider4.get())/10
    borders = []
    while j < len(y):                                         #iterate through all values y to cluster
        if abs(y_sort[j-1]-y_sort[j])<radius2:
            cluster.append(y_sort[j])
        else:
            value_matrix.append(cluster)
            borders.append(cluster[-1])
            cluster.clear()
            cluster.append(y_sort[j])
        j += 1
    value_matrix.append(cluster)
    if len(value_matrix)>1:
        borders_time = []
        for n in range(len(borders)):
            for k in range(len(y)):
                if y[k] == borders[n]:
                    borders_time.append(time2[k])
        
        borders_time_filtered = []
        for n in range(len(borders_time)):
            if abs(borders_time[n]-borders_time[n-1])>(1/5):
                borders_time_filtered.append(borders_time[n])
        borders_time_filtered.append(borders_time[n])
        for col in range(len(borders_time_filtered)):
            ax.axvline(x=borders_time_filtered[col], linestyle='dotted', c="g")
    plt.show()
    

    n = 40
    saturation_approx = []
    saturation_approx = np.polyfit(time2, filtered_saturation2, n)
    y = []
    for i in range(len(time2)):
        new = 0
        for k in range(len(saturation_approx)):
            new += (saturation_approx[n-k])*(time2[i]**(k))
        y.append(new) 
    
    saturation_average = np.sum(filtered_saturation2)/len(filtered_saturation2)
    saturation_sorted = np.sort(filtered_saturation2)
    median_saturation = saturation_sorted[int(len(saturation_sorted)/2)]

    output.delete(0.0, END)
    output.insert(END,"Saturation average:" + '\t' + '\t' + '\t' + str(f'{saturation_average:.3E}') + '\n')
    output.insert(END,"Saturation median:" + '\t' + '\t' + '\t' + str(f'{median_saturation:.3E}') + '\n')
    output.insert(END,"Saturation max:" + '\t' + '\t' + '\t' + str(f'{saturation_sorted[-1]:.3E}') + '\t' + '\t' + '\t' + "Saturation max approx:" + '\t' + '\t' + '\t' + '\t' + str(f'{np.max(y):.3E}') + '\n') 
    output.insert(END,"Saturation min:" + '\t' + '\t' + '\t' + str(f'{saturation_sorted[0]:.3E}') + '\t' + '\t' + '\t' + "Saturation min approx:" + '\t' + '\t' + '\t' + '\t' + str(f'{np.min(y):.3E}') + '\n') 
    output.insert(END,"Saturation range:" + '\t' + '\t' + '\t' + str(f'{(saturation_sorted[-1]-saturation_sorted[0]):.3E}') + '\t' + '\t' + '\t' + "Saturation range approx:" + '\t' + '\t' + '\t' + '\t' + str(f'{(np.max(y)-np.min(y)):.3E}') + '\n')
    #output.insert(END,"Intensity variance:" + str(f'{intensity_variance:.3E}') + '\n')    

    fig, ax = plt.subplots()
    ax.plot(time2, y, c="r")
    ax.axhline(y=max(y), linestyle='dotted', c="r")
    ax.axhline(y=min(y), linestyle='dotted', c="r")
    ax.plot(time2, filtered_saturation2)
    plt.xlabel('time in seconds')
    plt.ylabel('saturation of flow over time')
    maximum_variance = np.max(filtered_saturation2)
    minimum_variance = np.min(filtered_saturation2)
    ax.axhline(y=maximum_variance, linestyle='dotted')
    ax.axhline(y=minimum_variance, linestyle='dotted')
    plt.ylim([0,100])
    plt.title('saturation of flow color over course of dispense')
    y_sort = np.sort(y)
    value_matrix = []
    cluster = []
    j = 1
    cluster.append(y[0])
    radius3 = float(slider5.get())/10
    borders = []
    while j < len(y):                                         #iterate through all values y to cluster
        if abs(y_sort[j-1]-y_sort[j])<radius3:
            cluster.append(y_sort[j])
        else:
            value_matrix.append(cluster)
            borders.append(cluster[-1])
            cluster.clear()
            cluster.append(y_sort[j])
        j += 1
    value_matrix.append(cluster)
    if len(value_matrix)>1:
        borders_time = []
        for n in range(len(borders)):
            for k in range(len(y)):
                if y[k] == borders[n]:
                    borders_time.append(time2[k])
        
        borders_time_filtered = []
        for n in range(len(borders_time)):
            if abs(borders_time[n]-borders_time[n-1])>(1/5):
                borders_time_filtered.append(borders_time[n])
        borders_time_filtered.append(borders_time[n])
        for col in range(len(borders_time_filtered)):
            ax.axvline(x=borders_time_filtered[col], linestyle='dotted', c="g")
    plt.show()

if __name__ == "__main__":
    window = Tk()
    window.title("Width over time flow analysis")
    window.configure(background = "grey")

    Label(window, text = "Processing:", bg = "grey", fg = "white", font = "none 12 bold").grid(row = 4, column = 0, sticky = W)
    Label(window, text = "\t \t Video name:", bg = "grey", fg = "white", font = "none 12 bold").grid(row = 5, column = 0, sticky = W)
    Button(window, text = "UPLOAD", width = 14, command = uploadVideo).grid(row = 5, column = 1, sticky = W)

    Label(window, text = "\t Enter ROI border parameters:", bg = "grey", fg = "white", font = "none 12 bold").grid(row = 6, column = 0, sticky = W)
    Button(window, text = "SUBMIT", width = 14, command = setROIborders).grid(row = 6, column = 1, sticky = W)

    Label(window, text = "\t \t Intensity value:", bg = "grey", fg = "white", font = "none 12 bold").grid(row = 7, column = 0, sticky = W)
    current_value = tk.DoubleVar()
    slider = Scale(window,from_=0,to=400,orient=HORIZONTAL)
    slider.grid(row = 7, column = 1, columnspan = 3, sticky = W)
    try:
        borders = pickle.load(open("borders.dat", "rb"))
        lowerBorder = borders[0]
        slider.set(lowerBorder +25)
    except:
        slider.set(201)
    Button(window, text= "SUBMIT", width = 14, command = update_border_params).grid(row = 8, column = 1, sticky = W)

    Label(window, text = " ", bg = "grey", fg = "white", font = "none 12 bold").grid(row = 9, column = 0, sticky = W)
    Button(window, text = "START", width = 14, command = analysisProgramm).grid(row = 9, column = 1, sticky = W)

    Label(window, text = "\t Post Processing:", bg = "grey", fg = "white", font = "none 12 bold").grid(row = 4, column = 2, sticky = W)
    Label(window, text = " \t \t Number of MA samples:", bg = "grey", fg = "white", font = "none 12 bold").grid(row = 5, column = 2, sticky = W)
    sample_value = tk.DoubleVar()
    slider2 = Scale(window,from_=1,to=200,orient=HORIZONTAL)
    slider2.grid(row = 5, column = 3, columnspan = 1, sticky = W)
    slider2.set(1)
    Button(window, text= "PROCESS", width = 14, command = postAnalysis).grid(row = 6, column = 3, sticky = W)

    Label(window, text = "\t \t Classifier Hue:", bg = "grey", fg = "white", font = "none 12 bold").grid(row = 7, column = 2, sticky = W)
    sample_value = tk.DoubleVar()
    slider3 = Scale(window,from_=0,to=20,orient=HORIZONTAL)
    slider3.grid(row = 7, column = 3, columnspan = 1, sticky = W)
    slider3.set(7)
    Button(window, text= "SET", width = 14, command = postAnalysis).grid(row = 8, column = 3, sticky = W)

    Label(window, text = "\t \t Classifier Intensity:", bg = "grey", fg = "white", font = "none 12 bold").grid(row = 9, column = 2, sticky = W)
    sample_value = tk.DoubleVar()
    slider4 = Scale(window,from_=0,to=20,orient=HORIZONTAL)
    slider4.grid(row = 9, column = 3, columnspan = 1, sticky = W)
    slider4.set(4)
    Button(window, text= "SET", width = 14, command = postAnalysis).grid(row = 10, column = 3, sticky = W)

    Label(window, text = "\t \t Classifier Saturation:", bg = "grey", fg = "white", font = "none 12 bold").grid(row = 11, column = 2, sticky = W)
    sample_value = tk.DoubleVar()
    slider5 = Scale(window,from_=0,to=20,orient=HORIZONTAL)
    slider5.grid(row = 11, column = 3, columnspan = 1, sticky = W)
    slider5.set(4)
    Button(window, text= "SET", width = 14, command = postAnalysis).grid(row = 12, column = 3, sticky = W)

    Label(window, text = " ", bg = "grey", fg = "white", font = "none 12 bold").grid(row = 17, column = 0, sticky = W)
    Label(window, text = "Logbook output:", bg = "grey", fg = "white", font = "none 12 bold").grid(row = 18, column = 0, sticky = W)
    output = Text(window, width = 108, height = 14, wrap = WORD, background = "white")
    output.grid(row = 19, column = 0, columnspan = 8, sticky = W)

    window.mainloop()

#pyinstaller mainInterfaceBuildup.py -F --paths="D:\Studium\WS20\Python\lib\site-packages\cv2" 