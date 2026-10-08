import sys
import Tkinter as tk  # python 2
import tkFont as tkfont  # python 2
from PIL import ImageTk
from PIL import Image
from PIL import ImageFont, ImageDraw
import imageio
import copy
import math
from glob import glob
import numpy as np
import time
import os

import errno
import subprocess as sp
import WpaUpdater as wp
from printwtime import printtime
import json
import configparser

#arangetype=0 text keep to left
#arangetype=1 text keep to centre
def text_to_image_aranger(maxWidth,space,texttypedir,textheight,arangetype,text):
        
        font1 = ImageFont.truetype(texttypedir, textheight)
        word=""
        wordline=""
        wordlinelist=[]
        h=0
        for i in range(len(text)):
            
            if text[i]==" ":
                tmpwordline=wordline+" "+word
                w,h = font1.getsize(tmpwordline[1:])

                if w>maxWidth:
                    wordlinelist.append(wordline[1:])
                    wordline=" "+word
                else:
                    wordline=tmpwordline

                word=""
                
            else:
                word+=(text[i])

        tmpwordline=wordline+" "+word
        w,h = font1.getsize(tmpwordline[1:])
        if w>maxWidth:
            wordlinelist.append(wordline[1:])
            wordlinelist.append(word)
        else:
            wordlinelist.append(tmpwordline[1:])

        
        img=Image.new("RGB", (maxWidth,(textheight)*len(wordlinelist)+space*(len(wordlinelist)-1)+textheight/3))   
        draw = ImageDraw.Draw(img)
        for k in range(len(wordlinelist)):
            if (arangetype==0):
                draw.text((0, k*(textheight+space)), wordlinelist[k], font=font1)
            elif (arangetype==1):
                w,h = font1.getsize(wordlinelist[k])
                draw.text(((maxWidth-w)/2, k*(textheight+space)), wordlinelist[k], font=font1)

        return img

def merging_image_to_center_vertical(img1, img2, space):
    w1,h1=img1.size
    w2,h2=img2.size
    maxW=max(w1,w2)
    maxH=h1+space+h2
    img=Image.new("RGB", (maxW,maxH))  
    img.paste(img1, ((maxW-w1)//2,0))
    img.paste(img2, ((maxW-w2)//2,h1+space))    
    return img
        # w,h = font1.getsize(text)
        # img = Image.new("RGB", (w,h))
        # draw = ImageDraw.Draw(img)
        # draw.text((0, 0), text, font=font1)

        # return img