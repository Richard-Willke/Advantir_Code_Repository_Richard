# -*- coding: utf-8 -*-
"""
Created on Sat May 23 21:26:58 2020

@author: asoro
"""
import time
import os
import sys
sys.path.insert(1, "GUIraspberrypi/src")

import io_param as io
import RPi.GPIO as GPIO
import numpy as np

import errno
from datetime import datetime

piping=True

def pipe_write(filename_FIFO,input):
    if piping:
        OpenWrite = os.open(filename_FIFO, os.O_WRONLY)
        if input!="":
            os.write(OpenWrite, input)
        os.close(OpenWrite)


def stringtime():
    now = datetime.now()
    timestamp = now.strftime('%m/%d %H:%M:%S.%f')[:-5]
    return timestamp


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(io.DoorLockpin, GPIO.OUT)
GPIO.setup(io.buzzerpin, GPIO.OUT)
GPIO.setup(io.VtclmotorUpPin, GPIO.OUT)
GPIO.setup(io.VtclmotorDownPin, GPIO.OUT)
GPIO.setup(io.QRscannerTrigerpin, GPIO.OUT)

GPIO.setup(io.CapsuleInPin, GPIO.IN)
GPIO.setup(io.IRcapdetectPin, GPIO.IN)
GPIO.setup(io.DoorClosepin, GPIO.IN)
GPIO.setup(io.AugerUpLimitPin, GPIO.IN)
GPIO.setup(io.AugerDownLimitPin, GPIO.IN)
GPIO.setup(io.Auger2ndLimitPin, GPIO.IN)

io_number_array=[io.DoorLockpin,        #0
                 io.VtclmotorUpPin,     #1
                 io.VtclmotorDownPin,   #2
                 io.QRscannerTrigerpin, #3
     #           io.buzzerpin,          #4
                 io.CapsuleInPin,       #5
                 io.IRcapdetectPin,     #6
                 io.DoorClosepin,       #7
                 io.AugerUpLimitPin,    #8
                 io.AugerDownLimitPin,  #9
                 io.Auger2ndLimitPin    #10
                 ]
                 
io_state_array=np.array([[-1]*len(io_number_array)])
io_state_mean_array=np.array([-1]*len(io_number_array))
io_state_array_list=np.empty((0,len(io_number_array)),int)
pass_io_state_array=np.array([-1]*len(io_number_array))

ioMonitor2uploader_FIFO = 'pipe_ioMonitor2uploader'

if piping :
    try:
        os.mkfifo(ioMonitor2uploader_FIFO)
    except OSError as oe:
        if oe.errno != errno.EEXIST:
            raise
    pipe_write(ioMonitor2uploader_FIFO,"")
    print( "ioMonitor2uploader_pipeopened_write")


while True:
    for i in range(len(io_number_array)):
        io_state_array[0][i]=GPIO.input(io_number_array[i])
    io_state_array_list=np.append(io_state_array_list, io_state_array, axis=0)
    
    if io_state_array_list.shape[0]>10:
        io_sum_array=np.sum(io_state_array_list,axis=0)
        io_state_array_list=np.delete(io_state_array_list,0,0)
        io_state_mean_array[io_sum_array>7]=1
        io_state_mean_array[io_sum_array<3]=0
        
        
        
        
    if not (pass_io_state_array==io_state_mean_array).all():
                    pass_io_state_array=np.copy(io_state_mean_array)
                    print (stringtime()+ "\a"+ str(io_state_mean_array))
                    pipe_write(ioMonitor2uploader_FIFO,stringtime()+ "\a"+ str(io_state_mean_array)+"\n")




