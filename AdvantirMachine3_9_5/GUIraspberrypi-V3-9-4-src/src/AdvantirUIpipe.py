
# import tkinter as tk                # python 3
# from tkinter import font  as tkfont # python 3
import sys
sys.path.insert(1, "GUIraspberrypi/src")
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
from common  import *

import errno
import subprocess as sp
import WpaUpdater as wp
from printwtime import printtime
import json
import configparser
import urllib2
import SharedArray as sa

config = configparser.ConfigParser()
config.read('/home/pi/swirlgo_machine.conf')
machine_profile=config["machine-config"]

# screen 480x800 ui
screensize=(800,1280)
TEST_UI=False

framenow = ""
circleimagecentre = [screensize[0]/2, int(276*screensize[1]/800.00)]
selectedmainmenu=0
mainmenu_foldername=[]
menuBRAND=""
menuFLAVOR=""
menuTYPE=""
menuSOFT=""
dictFromMA={}

pathtoDir="/home/pi/GUIraspberrypi"
if TEST_UI:
    pathtoDir="."

#pathtoDir="."
animationfolder="/AnimationsforUI16Oct"
iconfolder="/icons"
selectedsubmenu=""
selectedcatagory=""
versiontext="[empty]"
screenpress=False
spinnerSpeed=15

try:
    shm_ma2ui = sa.attach("shm://sgo-ma-ui")
    print "previous sgo-ma-ui share memory exit,attaching it"
except:
    print "sgo-ma-ui share memory not exit"   
    shm_ma2ui = sa.create('shm://sgo-ma-ui',1,dtype=bool) 


try:
    shm_a = sa.attach("shm://sgo_internetstatus")
    print "previous sgo_internetstatus share memory exit,attaching it"
except:
    print "sgo_internetstatus share memory not exit"   
    shm_a = sa.create('shm://sgo_internetstatus',1) 
         
listofscreen=["loadingScn","insertScn","doorcloseRemoveScn","doorcloseInsertScn" ,"pushInTrayScn","identifyScn", "recognizedScn", "errorScn2","errorScn3","errorScn4",
              "blendingScn","opencapScn","readyScn", "dispensingScn","extraDispensingScn", "removeScn"]#, "scantemp"]  , "smileyScn","thankyouScn"            

# --------------PIPE setup---------------------------
MA2UI_FIFO="pipe_from_MA_to_UI"
UI2MA_FIFO = 'pipe_from_UI_to_MA'

time.sleep(1)

def scnCvt(x):
    return int(x*screensize[1]/800.00)


if not TEST_UI:
    UI2MA_FIFOOpenWrite = os.open(UI2MA_FIFO, os.O_WRONLY)
    print "UI2MA_pipeopened_to_write"
    os.close(UI2MA_FIFOOpenWrite)
    
    MA2UI_FIFOOpenRead= open(MA2UI_FIFO, 'r', buffering= 1)
    MA2UI_FIFOOpenRead.read()
    print "MA2UI_pipeopened_read"

#----------------------------------------------------
def showframe(controller, scn):
    global framenow
    framenow = scn
    print("showing frame:"+framenow)

    return SampleApp().show_frame(scn)


def UI2MA_pipe_write(input):
    if not TEST_UI:
        UI2MA_FIFOOpenWrite = os.open(UI2MA_FIFO, os.O_WRONLY)
        os.write(UI2MA_FIFOOpenWrite, input)
        os.close(UI2MA_FIFOOpenWrite)


def jsonOrganizeLoad(txt):
    txtsplit=txt.replace("}{", "},{")
    txtsplit=txtsplit.replace("} {", "},{")
    txtsplit="["+txtsplit+"]"
    arraylistfile=json.loads(txtsplit)
    singlelist={}
    for listi in arraylistfile:
        singlelist.update(listi)
    return singlelist


def checkInternetConnection():
    try:
        urllib2.urlopen('https://www.google.com', timeout=0.3)
        return True
    except : 
        return False


def checkVersionFile():
    global versiontext
    try:
        with open('/home/pi/Desktop/version.txt', 'r') as f:
            text=""
            for line in f:
                text+=line
            versiontext=text
    except:
        pass
        

class SampleApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(family='Helvetica', size=scnCvt(18), weight="bold", slant="italic")
        checkVersionFile()

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others

        self.attributes("-fullscreen", True) # for full screenpathtoDir="/home/pi/GUIraspberrypi"
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (loadingScn,insertScn,doorcloseRemoveScn,doorcloseInsertScn ,pushInTrayScn,identifyScn, recognizedScn, errorScn2,errorScn3,errorScn4,
              blendingScn,opencapScn, readyScn, dispensingScn,extraDispensingScn, smileyScn,thankyouScn, removeScn,loopingmain):#, scantemp):
            page_name = F.__name__
            frame = F(parent=container, controller=self, )
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")


        #self.show_frame("readyScn")
        self.show_frame("loadingScn")

    def show_frame(self, page_name):
        global framenow
        '''Show a frame for the given page name'''
        if framenow==page_name: # fix the blackout bugs! due to will replicate same screen in a time 
            return
        frame = self.frames[page_name]
        frame.tkraise()
        framenow = page_name
        print("updating frame:" + framenow)
        frame.updatescreen()
        print("animating frame:" + framenow)
        frame.animation()
    def updatemenu(self, page_name):
        global framenow
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.updatescreen()
    

class insertScn(tk.Frame):
    def __init__(self, parent, controller):
        # touch event to send signal to main code ,-->identifyingScn,
        # send signal as insertScn to main code
        # rotate ring
        # display image and font text

        tk.Frame.__init__(self, parent)

        self.controller = controller
        self.configure(bg="black")

        ########### text and graphic
        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.bind("<ButtonRelease-1>", self.click_release)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
  
        #wifi icon 
        image10 = Image.open(pathtoDir+iconfolder+'/wifiicon.png').resize((scnCvt(25),scnCvt(20)),Image.ANTIALIAS)
        self.image11 = Image.open(pathtoDir+iconfolder + '/qumark.png').resize((scnCvt(15), scnCvt(20)), Image.ANTIALIAS)
        self.tkimage10 = tkimage10 = ImageTk.PhotoImage(image10)
        canvas_obj10 = self.canvas.create_image(scnCvt(445), scnCvt(70), image=tkimage10) # position for wifiicon

        # wifi question mark icon update
        self.img_a = copy.deepcopy(self.image11)
        w, h = self.img_a.size
        self.draw = ImageDraw.Draw(self.img_a)
        self.draw.rectangle([0, 0, w, h], fill=(0, 0, 0, 0), outline=(0, 0, 0, 0))

        self.tkimage_a = tkimage_a = ImageTk.PhotoImage(self.img_a)

        self.canvas_obj_a = self.canvas.create_image(scnCvt(445), scnCvt(70), image=tkimage_a) # position for quatation mark for wifiicon

        imgtext=text_to_image_aranger(scnCvt(400),scnCvt(25),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         "Pull out tray   to begin" )
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(imgtext)
        canvas_obj4 = self.canvas.create_image(scnCvt(240), scnCvt(600), image=tkimage4) #position for text

        self.angle = 0
      
        #top hidden Menu button setup
        imageMenu = Image.new("RGB",(scnCvt(30),scnCvt(30)), (0,0,0))
        self.tkimageMenu=tkimageMenu=ImageTk.PhotoImage(imageMenu)
        sidemenu=tk.Menubutton(self, image=tkimageMenu, relief=tk.RAISED, bg='black', bd=0)
        sidemenu.grid()
        sidemenu.menu=tk.Menu(sidemenu,tearoff=0,font=("Verdana", scnCvt(16)),foreground="white", background="black")
   
        sidemenu["menu"]=sidemenu.menu
        sidemenu.menu.add_checkbutton(label="developer mode", command = self.starttodeveloperMenu)
        sidemenu.menu.add_checkbutton(label="shut down",  command=self.shutdownMenu)
        
        canvas_obj14 = self.canvas.create_window(75, 135, window=sidemenu) #position for Hidden Menu

        #bottom Menu button
        imageMenu2 = Image.open(pathtoDir +iconfolder+ '/ic_cone_swirl.png').resize((scnCvt(17), scnCvt(39)), Image.ANTIALIAS)
        self.tkimageMenubottom=tkimageMenubottom=ImageTk.PhotoImage(imageMenu2)
        sidemenubottom=tk.Button(self, image=tkimageMenubottom,relief=tk.RAISED, activebackground='black',activeforeground='black',
                                    bg='black', fg='black',  bd=0 ,highlightthickness=0,command=self.softnessSetting)

        canvas_obj15 = self.canvas.create_window(scnCvt(410), scnCvt(70), window=sidemenubottom) #position of softness Menu botton
        ######################
        label_version= tk.Label(self, text=versiontext, fg='white', bg='black')
        label_version.config(font= ('times', scnCvt(5)))
        canvas_obj16 = self.canvas.create_window(scnCvt(240), scnCvt(750), window=label_version) #position of softness Menu botton
        #####
        self.imagelist =glob(pathtoDir+animationfolder+"/Tray_Pull_20fps/*")
        self.imagelist.sort()

        self.animationArrayImg=[]
 
    def shutdownMenu(self):

        shutdowncanvas = tk.Canvas(self, width=scnCvt(200), height=scnCvt(100), bg="red", bd=scnCvt(10))
        shutdowncanvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        button_shutdown = tk.Button(self, text=' Shut Down', bg="#3c4987", fg="#ffffff",
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, command=lambda: os.system("sudo shutdown -h now"))
        button_cancel = tk.Button(self, text='  Cancel  ', bg="#3c4987", fg="#ffffff",
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, command=lambda: shutdowncanvas.destroy() )
        label_shutdownconfirm = tk.Label(self, text='Are you sure you want\n shut down?', fg='white', bg='red')
        label_shutdownconfirm.config(font= ('times', scnCvt(15), 'bold'))

        shutdowncanvas.create_window(scnCvt(60),scnCvt(80), window=button_shutdown)
        shutdowncanvas.create_window(scnCvt(160), scnCvt(80), window=button_cancel)
        shutdowncanvas.create_window(scnCvt(110), scnCvt(30), window=label_shutdownconfirm)
    
    def softnessSetting(self):
        try:
            self.softnesscanvas.destroy()
        except:
            pass
        self.softnesscanvas = tk.Canvas(self, width=scnCvt(400), height=scnCvt(150), bg="black", bd=scnCvt(10))
        self.softnesscanvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        if "Softness" in  machine_profile:
            menuSOFT=int(machine_profile["Softness"])
        else:
            menuSOFT=3
        colourlist=["black"]*5
        colourlist[menuSOFT-1]="white"
        fntcolourlist=["white"]*5
        fntcolourlist[menuSOFT-1]="black"
        button_Softest = tk.Button(self, text='Softest', bg=colourlist[0], fg=fntcolourlist[0], width=7,compound=tk.CENTER,
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, font= ('times', scnCvt(14)), command=lambda: self.sendSoftnessParam(1))
        button_Soft = tk.Button(self, text='Soft', bg=colourlist[1], fg=fntcolourlist[1],width=7,compound=tk.CENTER,
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, font= ('times', scnCvt(14)), command=lambda: self.sendSoftnessParam(2))                                   
        button_Regular = tk.Button(self, text='Regular', bg=colourlist[2], fg=fntcolourlist[2],width=7,compound=tk.CENTER,
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, font= ('times', scnCvt(14)), command=lambda: self.sendSoftnessParam(3))
        button_Firm = tk.Button(self, text='Firm', bg=colourlist[3], fg=fntcolourlist[3],width=7,compound=tk.CENTER,
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, font= ('times', scnCvt(14)), command=lambda: self.sendSoftnessParam(4) )
        button_Firmest = tk.Button(self, text='Firmest', bg=colourlist[4], fg=fntcolourlist[4],width=7,compound=tk.CENTER,
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, font= ('times', scnCvt(14)), command=lambda: self.sendSoftnessParam(5))

        button_cancel = tk.Button(self, text='Cancel', bg="black", fg="white",width=scnCvt(7),compound=tk.CENTER,
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, font= ('times', scnCvt(14)),command=lambda: self.softnesscanvas.destroy() )
        label_shutdownconfirm = tk.Label(self, text='Please Select Softness.',fg='white', bg='black')
        label_shutdownconfirm.config(font= ('times', scnCvt(15), 'bold'))

        self.softnesscanvas.create_window(scnCvt(50),scnCvt(80), window=button_Softest)
        self.softnesscanvas.create_window(scnCvt(130), scnCvt(80), window=button_Soft)
        self.softnesscanvas.create_window(scnCvt(210),scnCvt(80), window=button_Regular)
        self.softnesscanvas.create_window(scnCvt(290), scnCvt(80), window=button_Firm)
        self.softnesscanvas.create_window(scnCvt(370),scnCvt(80), window=button_Firmest)
        self.softnesscanvas.create_window(scnCvt(210), scnCvt(130), window=button_cancel)
        self.softnesscanvas.create_window(scnCvt(110), scnCvt(30), window=label_shutdownconfirm)

    def sendSoftnessParam(self,softness):
        machine_profile['Softness']=str(softness)
        with open('/home/pi/swirlgo_machine.conf', 'w') as configfile:
            config.write(configfile)
        self.softnesscanvas.destroy()

    def starttodeveloperMenu(self):

        shutdowncanvas = tk.Canvas(self, width=scnCvt(250), height=scnCvt(100), bg="red", bd=scnCvt(10))
        shutdowncanvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        button_shutdown = tk.Button(self, text=' Restart ', bg="#3c4987", fg="#ffffff",
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, command= self.developmentprocess)
        button_cancel = tk.Button(self, text='  Cancel  ', bg="#3c4987", fg="#ffffff",
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, command=lambda: shutdowncanvas.destroy() )
        label_shutdownconfirm = tk.Label(self, text='Are you sure you want\n restart to developer mode?', fg='white', bg='red')
        label_shutdownconfirm.config(font= ('times', scnCvt(15), 'bold'))

        shutdowncanvas.create_window(scnCvt(60),scnCvt(80), window=button_shutdown)
        shutdowncanvas.create_window(scnCvt(210), scnCvt(80), window=button_cancel)
        shutdowncanvas.create_window(scnCvt(135), scnCvt(30), window=label_shutdownconfirm)
    
    def developmentprocess(self):
        os.system("python ~/GUIraspberrypi/tools/starttodeveloper.py")
        os.system("sudo reboot")

    ########### animation- rotation
    def updatescreen(self):
        print
        "Displaying insertScn"

        w, h = self.img_a.size
        if shm_a[0]:
                quIconCover = h
        else:
            quIconCover = 0
        self.draw = ImageDraw.Draw(self.img_a)
        self.draw.rectangle([0, 0, w, quIconCover], fill=(0, 0, 0, 0), outline=(0, 0, 0, 0))
        self.tkimage_a = tkimage_a = ImageTk.PhotoImage(self.img_a)
        self.canvas.itemconfig(self.canvas_obj_a, image=tkimage_a)
        
        self.frame=0
        self.animationArrayImg.append(Image.open(self.imagelist[self.frame]))
        self.tkimage = tkimage = ImageTk.PhotoImage(self.animationArrayImg[self.frame])        
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)

    ########### animation- rotation
    def animation(self):
        self.timestart=time.time() #frame start decoding
        #video display---------------
        self.frame+=1
        self.frame %= len(self.imagelist)
        if self.frame>=len(self.animationArrayImg):
            self.animationArrayImg.append(Image.open(self.imagelist[self.frame]))
            # self.animationArrayImg.append(Image.fromarray(self.imagelist.get_data(self.frame)))
        self.tkimage = tkimage = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        # time2=time.time()
        # self.tkimage = tkimage = ImageTk.PhotoImage(Image.fromarray(self.imagelist.get_data(self.frame)))
      #  self.tkimage = tkimage = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        
        
        #----------------------------
        # self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        # time3=time.time()
        # wifi question mark icon update

        self.img_a = copy.deepcopy(self.image11)
        w, h = self.img_a.size
        # update wifi connection status
        if self.frame==0:
            
            if shm_a[0] :
                quIconCover = h
            else:
                quIconCover = 0
            self.draw = ImageDraw.Draw(self.img_a)
            self.draw.rectangle([0, 0, w, quIconCover], fill=(0, 0, 0, 0), outline=(0, 0, 0, 0))
            self.tkimage_a = tkimage_a = ImageTk.PhotoImage(self.img_a)
            self.canvas.itemconfig(self.canvas_obj_a, image=tkimage_a)

        # time4=time.time()


        # frame rate re-adjuster 
        framerate=time.time()-self.timestart
        # print "frame time:" , framerate,time2-self.timestart,time3-time2,time4-time3
        if framerate>0.04:
            settimedelay=1
        else:
            settimedelay=int(1000.00*(0.04-framerate))
        #----------------------
        
        if (framenow == "insertScn"):
            self.after(settimedelay, self.animation)
        else :
            del self.animationArrayImg[:]

    def click_release(self, event):
        global screenpress
        screenpress=True


class doorcloseRemoveScn(tk.Frame):
    def __init__(self, parent, controller):
        # received signal from main code ,
        # send signal as identifyScn to main code
        # rotate ring
        # display image and font text
        # dot ... animation
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")

        ########### text and graphic
        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black', highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image2 = Image.open(pathtoDir +iconfolder+ '/ic_pod_inactive.png')
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir +iconfolder+ '/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        imgtext=text_to_image_aranger(scnCvt(400),scnCvt(25),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         "Please push to close the tray" )
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(imgtext)
        canvas_obj4 = self.canvas.create_image(scnCvt(240), scnCvt(600), image=tkimage4) #position for text


        spinnerimage_animated = Image.open(pathtoDir +iconfolder+ '/ic_spinner.png').resize((scnCvt(79),scnCvt(35)))
        self.image_animated = Image.new('RGBA', (scnCvt(79),scnCvt(79)), (0, 0, 0, 0))
        self.image_animated.paste(spinnerimage_animated, 
                ((self.image_animated.size[0]-spinnerimage_animated.size[0])/2,(self.image_animated.size[1]-spinnerimage_animated.size[1])/2))
        self.angle = 0
        self.radianoff=0.300
        self.radiusspinner=101.53
        self.pastx=0
        self.pasty=0
        
    def updatescreen(self):
        print
        "Displaying DoorcloseRemoveScn"
        #initial spinner at 
        x=math.sin(math.radians(self.angle)+self.radianoff)*self.radiusspinner
        y=math.cos(math.radians(self.angle)+self.radianoff)*self.radiusspinner

        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0]+scnCvt(x), circleimagecentre[1]+scnCvt(y), image=tkimage)
        self.pastx=circleimagecentre[0]+scnCvt(x)
        self.pasty=circleimagecentre[1]+scnCvt(y)
        self.angle -= spinnerSpeed
        self.angle %= 360

    ########### animation- rotation
    def animation(self):
        x=math.sin(math.radians(self.angle)+self.radianoff)*self.radiusspinner
        y=math.cos(math.radians(self.angle)+self.radianoff)*self.radiusspinner
        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        self.canvas.move(self.canvas_obj,(circleimagecentre[0]+scnCvt(x))-self.pastx,(circleimagecentre[1]+scnCvt(y)-self.pasty))
        self.pastx=circleimagecentre[0]+scnCvt(x)
        self.pasty=circleimagecentre[1]+scnCvt(y)
        self.angle -= spinnerSpeed
        self.angle %= 360

        if (framenow == "doorcloseRemoveScn"):
    
            self.after(20, self.animation)


class doorcloseInsertScn(tk.Frame):

    def __init__(self, parent, controller):
        # received signal from main code ,
        # send signal as identifyScn to main code
        # rotate ring
        # display image and font text
        # dot ... animation
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")

        ########### text and graphic
        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black', highlightthickness=0)
        self.canvas.bind("<ButtonRelease-1>", self.click_release)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image2 = Image.open(pathtoDir +iconfolder+ '/ic_pod.png')
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir +iconfolder+ '/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        imgtext=text_to_image_aranger(scnCvt(400),scnCvt(25),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(48),1,
                         "Remove central sticker" )
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(imgtext)
        canvas_obj4 = self.canvas.create_image(scnCvt(240), scnCvt(600), image=tkimage4) #position for text

        #"NEXT" text on below screen    
        text1 = "NEXT"        
        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", scnCvt(40))
        w,h=font1.getsize(text1)
        #white background black text
        image2 = Image.new("RGB", (scnCvt(480), scnCvt(120)),(255,255,255))
        drawtextbelowvideo = ImageDraw.Draw(image2)
        drawtextbelowvideo.text(((scnCvt(480)-w)/2, (scnCvt(120)-h)/2), text1, font=font1, fill=(0,0,0)) 
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        #black background white text
        image21 = Image.new("RGB", (scnCvt(480), scnCvt(120)),(0,0,0))
        drawtextbelowvideo1 = ImageDraw.Draw(image21)
        drawtextbelowvideo1.text(((scnCvt(480)-w)/2, (scnCvt(120)-h)/2), text1, font=font1, fill=(255,255,255)) 
        self.tkimage21 = tkimage21 = ImageTk.PhotoImage(image21)

        self.canvas_obj2 = self.canvas.create_image(circleimagecentre[0], scnCvt(740), image=tkimage2)

        self.imagelist =glob(pathtoDir+animationfolder+"/Remove_Sticker_20fps/*")
        self.imagelist.sort()

        self.animationArrayImg=[]

    def updatescreen(self):
        print
        "Displaying DoorcloseInsertScn"
        # animation setup
        self.frame=0
        self.animationArrayImg.append(Image.open(self.imagelist[self.frame]))
        self.tkimage = tkimage = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)
        self.canvas.itemconfig(self.canvas_obj2, image=self.tkimage2)
        shm_ma2ui[0]=False

    ########### animation- rotation
    def animation(self):
        self.timestart=time.time() #frame start decoding
        #video display---------------
        self.frame+=1
        self.frame %= len(self.imagelist)
        if self.frame>=len(self.animationArrayImg):
            self.animationArrayImg.append(Image.open(self.imagelist[self.frame]))
        self.tkimage = tkimage = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)

        if shm_ma2ui[0]==True:
            if self.frame%20>14:
                self.canvas.itemconfig(self.canvas_obj2, image=self.tkimage21)
            else:
                self.canvas.itemconfig(self.canvas_obj2, image=self.tkimage2)
    
        # frame rate re-adjuster 
        framerate=time.time()-self.timestart
        if framerate>0.04:
            settimedelay=1
        else:
            settimedelay=int(1000.00*(0.04-framerate))

        #----------------------
        if (framenow == "doorcloseInsertScn"):
            self.after(settimedelay, self.animation)
        else :
            del self.animationArrayImg[:]

    def click_release(self, event):
        pairlist = {"TOUCH": "1"}
        UI2MA_pipe_write(json.dumps(pairlist))
        self.controller.show_frame("pushInTrayScn")

        
class pushInTrayScn(tk.Frame):

    def __init__(self, parent, controller):
        # received signal from main code ,
        # send signal as identifyScn to main code
        # rotate ring
        # display image and font text
        # dot ... animation
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")
        ########### text and graphic
        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black', highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image2 = Image.open(pathtoDir +iconfolder+ '/ic_pod.png')
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir +iconfolder+ '/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        imgtext=text_to_image_aranger(scnCvt(400),scnCvt(25),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         "Insert pod and push in tray" )
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(imgtext)
        canvas_obj4 = self.canvas.create_image(scnCvt(240), scnCvt(600), image=tkimage4) #position for text

        self.imagelist =glob(pathtoDir+animationfolder+"/insert_push_in_tray/*")
        self.imagelist.sort()

        self.animationArrayImg=[]

    def updatescreen(self):
        print
        "Displaying pushInTrayScn"       
        # animation setup
        self.frame=0
        self.animationArrayImg.append(Image.open(self.imagelist[self.frame]))
        self.tkimage = tkimage = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)

    ########### animation- rotation
    def animation(self):
        self.timestart=time.time() #frame start decoding
        #video display---------------
        self.frame+=1
        self.frame %= len(self.imagelist)
        if self.frame>=len(self.animationArrayImg):
            self.animationArrayImg.append(Image.open(self.imagelist[self.frame]))
        self.tkimage = tkimage = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        # frame rate re-adjuster 
        framerate=time.time()-self.timestart
        if framerate>0.04:
            settimedelay=1
        else:
            settimedelay=int(1000.00*(0.04-framerate))
        #----------------------
        if (framenow == "pushInTrayScn"):
            self.after(settimedelay, self.animation)
        else :
            del self.animationArrayImg[:]


class identifyScn(tk.Frame):
    def __init__(self, parent, controller):
	
        # received signal from main code ,
        # send signal as identifyScn to main code
        # rotate ring
        # display image and font text
        # dot ... animation
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")
        ########### text and graphic
        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black', highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image2 = Image.open(pathtoDir+iconfolder+'/ic_pod.png')
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        imgtext=text_to_image_aranger(scnCvt(400),scnCvt(25),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         "Identifying Swirl Pod..." )
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(imgtext)
        canvas_obj4 = self.canvas.create_image(scnCvt(240), scnCvt(600), image=tkimage4) #position for text

        spinnerimage_animated = Image.open(pathtoDir +iconfolder+ '/ic_spinner.png').resize((scnCvt(79),scnCvt(35)))
        self.image_animated = Image.new('RGBA', (scnCvt(79),scnCvt(79)), (0, 0, 0, 0))
        self.image_animated.paste(spinnerimage_animated, 
                ((self.image_animated.size[0]-spinnerimage_animated.size[0])/2,(self.image_animated.size[1]-spinnerimage_animated.size[1])/2))
        self.angle = 0
        self.radianoff=0.300
        self.radiusspinner=101.53
        self.pastx=0
        self.pasty=0

        
    def updatescreen(self):
        global menuBRAND,menuFLAVOR,menuTYPE

        menuBRAND = ""
        menuFLAVOR = ""
        menuTYPE = ""
        print "Displaying identifyScn"
        x=math.sin(math.radians(self.angle)+self.radianoff)*self.radiusspinner
        y=math.cos(math.radians(self.angle)+self.radianoff)*self.radiusspinner

        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0]+scnCvt(x), circleimagecentre[1]+scnCvt(y), image=tkimage)
        self.pastx=circleimagecentre[0]+scnCvt(x)
        self.pasty=circleimagecentre[1]+scnCvt(y)        
        self.angle -= spinnerSpeed
        self.angle %= 360

    ########### animation- rotation
    def animation(self):
        x=math.sin(math.radians(self.angle)+self.radianoff)*self.radiusspinner
        y=math.cos(math.radians(self.angle)+self.radianoff)*self.radiusspinner
        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        self.canvas.move(self.canvas_obj,(circleimagecentre[0]+scnCvt(x))-self.pastx,(circleimagecentre[1]+scnCvt(y)-self.pasty))
        self.pastx=circleimagecentre[0]+scnCvt(x)
        self.pasty=circleimagecentre[1]+scnCvt(y)
        self.angle -= spinnerSpeed
        self.angle %= 360

        if (framenow == "identifyScn"):
            self.after(20, self.animation)


class recognizedScn(tk.Frame):

    def __init__(self, parent, controller):
        # received signal from main code ,
        # send signal as recognizedScn to main code
        # display name of brand and flavour
        # tick animation
        # display image and font text

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")
        #label = tk.Label(self, text="recognizedScn", font=controller.title_font)
        #label.pack(side="top", fill="x", pady=10)
        #button = tk.Button(self, text="Go to the start page",
         #                  command=lambda: controller.show_frame("processScn"))
        #button.pack()

        ########### text and graphic

        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black', highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.canvas.bind("<ButtonRelease-1>", self.click_release)

        image2 = Image.open(pathtoDir+iconfolder+'/ic_tick_inactive.png')
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        self.angle = 0
        self.cover=0
        self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_tick.png')

    def updatescreen(self):
        print "Displaying recognizedScn"
        global selectedcatagory, selectedsubmenu
        # submenucp=copy.deepcopy(selectedsubmenu)
        #
        # while True:
        #     idxofchar = submenucp.find("/")
        #     if idxofchar >= 0:
        #         selectedcatagory = submenucp[:idxofchar]
        #         submenucp = submenucp[(idxofchar + 1):]
        #     else:
        #         break
        #
        # idxofbrand = submenucp.find("-")
        # if idxofbrand >= 0:
        #     text1 = submenucp[:idxofbrand]
        #     submenucp = submenucp[(idxofbrand + 1):]
        # else:
        #     text1 = selectedcatagory
        #
        # idxofflavour = submenucp.find(".")
        # if idxofflavour >= 0:
        #     text2 = submenucp[:idxofflavour]
        # else:
        #     text2 = "Australian Mango "

        text2 = ""

        text1 = menuFLAVOR

        text3 = ""
        
        imgtext1=text_to_image_aranger(scnCvt(400),scnCvt(12),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         text1 )
        imgtext2=text_to_image_aranger(scnCvt(400),scnCvt(6),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(25),1,
                         text2 )
        imgtext3=text_to_image_aranger(scnCvt(400),scnCvt(4),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(16),1,
                         text3 )
        self.img=merging_image_to_center_vertical(imgtext1,imgtext2,scnCvt(10))
        self.img=merging_image_to_center_vertical(self.img,imgtext3,scnCvt(10))

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.img)
        canvas_obj4 = self.canvas.create_image(scnCvt(240), scnCvt(600), image=tkimage4)


        self.img_a=copy.deepcopy(self.image_animated)
        w,h=self.img_a.size
        self.draw = ImageDraw.Draw(self.img_a)
        self.draw.rectangle([self.cover,0,w,h],fill=(0,0,0,0),outline=(0,0,0,0))
        self.tkimage = tkimage = ImageTk.PhotoImage(self.img_a)
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)
        self.cover +=3



        ########### animation- rotation

    def animation(self):
        self.img_a=copy.deepcopy(self.image_animated)
        w,h=self.img_a.size
        self.draw = ImageDraw.Draw(self.img_a)
        self.draw.rectangle([self.cover,0,w,h],fill=(0,0,0,0),outline=(0,0,0,0))
        self.tkimage = tkimage = ImageTk.PhotoImage(self.img_a)
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        self.cover +=3

	
        if (framenow == "recognizedScn" and self.cover<=w):
            self.after(20, self.animation)
        else:
            self.cover=0
    def click_release(self, event):
        global screenpress
        screenpress=True
        pairlist = {"TOUCH": "1"}
        UI2MA_pipe_write(json.dumps(pairlist))


class errorScn1(tk.Frame):  # Not Recognized Screen

    def __init__(self, parent, controller):
        # received signal from main code ,
        # send signal as errorScn to main code

        # warning animation
        # display image and font text

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")
        #label = tk.Label(self, text="errorScn", font=controller.title_font)
        #label.pack(side="top", fill="x", pady=10)
        #button = tk.Button(self, text="Go to the start page",
        #                   command=lambda: controller.show_frame("mainmenuScn"))
        #button.pack()

        ########### text and graphic

        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

       # image2 = Image.open('ic_recog.png')

       # self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
       # canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        text1 = "QR Not Recognised"
        text2 = "Please try again. Only insert official\nSwirl Pods or kindly seek assistance\nfrom staff.(Tel: 9798 2556)"

        # font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        # font2 = ImageFont.truetype(pathtoDir+"/font/OpenSans-SemiBold.ttf", 20)

        # img = Image.new("RGB", (500, 400))
        # draw = ImageDraw.Draw(img)
        # draw.text((30, 180), text1, font=font1)
        # draw.text((30, 235), text2, font=font2)


        imgtext1=text_to_image_aranger(scnCvt(400),scnCvt(6),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         text1 )
        imgtext2=text_to_image_aranger(scnCvt(400),scnCvt(4),
                        pathtoDir+"/font/OpenSans-SemiBold.ttf",scnCvt(20),1,
                         text2 )
        img=merging_image_to_center_vertical(imgtext1,imgtext2,scnCvt(25))

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(scnCvt(240), scnCvt(600), image=tkimage4)

      

        self.angle = 0
        self.scale=0.0


        self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_recog.png')
        self.imga_h,self.imga_w =self.image_animated.size

    def updatescreen(self):
        print "Displaying errorScn1"


        dampwave_scale = math.exp(-self.scale) * math.sin(2 * math.pi * self.scale) + 1  # decay wave
        img_a = self.image_animated.resize((int(self.imga_h * dampwave_scale), int(self.imga_w * dampwave_scale)),
                                           Image.ANTIALIAS)
        self.tkimage = tkimage = ImageTk.PhotoImage(img_a)
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)
        self.scale += 0.10
 
        ########### animation- rotation

    def animation(self):

        dampwave_scale=math.exp(-self.scale)*math.sin(2*math.pi*self.scale)+1 #decay wave
        img_a = self.image_animated.resize((int(self.imga_h*dampwave_scale),int(self.imga_w*dampwave_scale)), Image.ANTIALIAS)
        self.tkimage = tkimage = ImageTk.PhotoImage(img_a)
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        self.scale +=0.10
    
        if (framenow == "errorScn1" and self.scale<2.5):
            self.after(20, self.animation)
        else: self.scale=0.0


class errorScn2(tk.Frame):  ## temperature too high

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")

        ########### text and graphic

        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)


        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        text1 = "Motor is HoT!  "
        text2 = "Please wait for 5 min or kindly seek assistance from stuff."

        # font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        # font2 = ImageFont.truetype(pathtoDir+"/font/OpenSans-SemiBold.ttf", 20)

        # img = Image.new("RGB", (500, 400))
        # draw = ImageDraw.Draw(img)
        # draw.text((30, 180), text1, font=font1)
        # draw.text((30, 235), text2, font=font2)

        imgtext1=text_to_image_aranger(scnCvt(400),scnCvt(6),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         text1 )
        imgtext2=text_to_image_aranger(scnCvt(400),scnCvt(4),
                        pathtoDir+"/font/OpenSans-SemiBold.ttf",scnCvt(20),1,
                         text2 )
        img=merging_image_to_center_vertical(imgtext1,imgtext2,scnCvt(25))

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(scnCvt(240), scnCvt(600), image=tkimage4)

        self.angle = 0
        self.scale=0.0


        self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_recog.png')
        self.imga_h,self.imga_w =self.image_animated.size

    def updatescreen(self):
        print "Displaying errorScn2"


        dampwave_scale = math.exp(-self.scale) * math.sin(2 * math.pi * self.scale) + 1  # decay wave
        img_a = self.image_animated.resize((int(self.imga_h * dampwave_scale), int(self.imga_w * dampwave_scale)),
                                           Image.ANTIALIAS)
        self.tkimage = tkimage = ImageTk.PhotoImage(img_a)
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)
        self.scale += 0.10
   
        ########### animation- rotation

    def animation(self):

        dampwave_scale=math.exp(-self.scale)*math.sin(2*math.pi*self.scale)+1 #decay wave
        img_a = self.image_animated.resize((int(self.imga_h*dampwave_scale),int(self.imga_w*dampwave_scale)), Image.ANTIALIAS)
        self.tkimage = tkimage = ImageTk.PhotoImage(img_a)
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        self.scale +=0.10

        if (framenow == "errorScn2" and self.scale<2.5):
            self.after(20, self.animation)
        else: self.scale=0.0


class errorScn3(tk.Frame):  ## no selection and time out

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")

        ########### text and graphic

        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        text1 = "Main Cover is Open !!"
        text2 = "Please close the main cover"

        # font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        # font2 = ImageFont.truetype(pathtoDir+"/font/OpenSans-SemiBold.ttf", 20)

        # img = Image.new("RGB", (500, 400))
        # draw = ImageDraw.Draw(img)
        # draw.text((30, 180), text1, font=font1)
        # draw.text((30, 235), text2, font=font2)

        imgtext1=text_to_image_aranger(scnCvt(400),scnCvt(6),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         text1 )
        imgtext2=text_to_image_aranger(scnCvt(400),scnCvt(4),
                        pathtoDir+"/font/OpenSans-SemiBold.ttf",scnCvt(20),1,
                         text2 )
        img=merging_image_to_center_vertical(imgtext1,imgtext2,scnCvt(25))

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(scnCvt(240), scnCvt(600), image=tkimage4)

        self.angle = 0
        self.scale=0.0


        self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_recog.png')
        self.imga_h,self.imga_w =self.image_animated.size

    def updatescreen(self):
        print "Displaying errorScn3"


        dampwave_scale = math.exp(-self.scale) * math.sin(2 * math.pi * self.scale) + 1  # decay wave
        img_a = self.image_animated.resize((int(self.imga_h * dampwave_scale), int(self.imga_w * dampwave_scale)),
                                           Image.ANTIALIAS)
        self.tkimage = tkimage = ImageTk.PhotoImage(img_a)
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)
        self.scale += 0.10
        self.angle -= 5
        self.angle %= 360
        ########### animation- rotation

    def animation(self):

        dampwave_scale=math.exp(-self.scale)*math.sin(2*math.pi*self.scale)+1 #decay wave
        img_a = self.image_animated.resize((int(self.imga_h*dampwave_scale),int(self.imga_w*dampwave_scale)), Image.ANTIALIAS)
        self.tkimage = tkimage = ImageTk.PhotoImage(img_a)
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        self.scale +=0.10
        self.angle -= 5
        self.angle %= 360
        if (framenow == "errorScn3" and self.scale<2.5):
            self.after(20, self.animation)
        else: 
            self.scale=0.0


class errorScn4(tk.Frame):  # Capsule temperature too high

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")

        ########### text and graphic

        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)


        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
    
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        text1 = "Capsule is too warm!"
        text2 = "Please exchange capsule or kindly seek assistance from staff."

        # font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        # font2 = ImageFont.truetype(pathtoDir+"/font/OpenSans-SemiBold.ttf", 20)

        # img = Image.new("RGB", (500, 400))
        # draw = ImageDraw.Draw(img)
        # draw.text((30, 180), text1, font=font1)
        # draw.text((30, 235), text2, font=font2)

        imgtext1=text_to_image_aranger(scnCvt(400),scnCvt(6),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         text1 )
        imgtext2=text_to_image_aranger(scnCvt(400),scnCvt(4),
                        pathtoDir+"/font/OpenSans-SemiBold.ttf",scnCvt(20),1,
                         text2 )
        img=merging_image_to_center_vertical(imgtext1,imgtext2,scnCvt(25))

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(scnCvt(240), scnCvt(600), image=tkimage4)

        self.angle = 0
        self.scale=0.0


        self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_recog.png')
        self.imga_h,self.imga_w =self.image_animated.size

    def updatescreen(self):
        print "Displaying errorScn4"


        dampwave_scale = math.exp(-self.scale) * math.sin(2 * math.pi * self.scale) + 1  # decay wave
        img_a = self.image_animated.resize((int(self.imga_h * dampwave_scale), int(self.imga_w * dampwave_scale)),
                                           Image.ANTIALIAS)
        self.tkimage = tkimage = ImageTk.PhotoImage(img_a)
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)
      
        self.scale += 0.10
        self.angle -= 5
        self.angle %= 360
        ########### animation- rotation

    def animation(self):

        dampwave_scale=math.exp(-self.scale)*math.sin(2*math.pi*self.scale)+1 #decay wave
        img_a = self.image_animated.resize((int(self.imga_h*dampwave_scale),int(self.imga_w*dampwave_scale)), Image.ANTIALIAS)
        self.tkimage = tkimage = ImageTk.PhotoImage(img_a)
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        self.scale +=0.10
        self.angle -= 5
        self.angle %= 360
        if (framenow == "errorScn4" and self.scale<2.5):
            self.after(20, self.animation)
        else: 
            self.scale=0.0        


class blendingScn(tk.Frame):

    def __init__(self, parent, controller):
        # received signal from main code ,
        # send signal as processScn to main code
        # process animation
        # rotate ring
        # display image and font text
        # dot ... animation
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")
        #label = tk.Label(self, text="processScn", font=controller.title_font)
        #label.pack(side="top", fill="x", pady=10)
        #button = tk.Button(self, text="Go to the start page",
        #                   command=lambda: controller.show_frame("readyScn"))
        #button.pack()

        ########### text and graphic

        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)


        image2 = Image.open(pathtoDir+iconfolder+'/ic_tick_inactive.png')
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        # self.angle = 0

        # self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_spinner2.png').resize((scnCvt(228),scnCvt(228)))
        spinnerimage_animated = Image.open(pathtoDir +iconfolder+ '/ic_spinner.png').resize((scnCvt(79),scnCvt(35)))
        self.image_animated = Image.new('RGBA', (scnCvt(79),scnCvt(79)), (0, 0, 0, 0))
        self.image_animated.paste(spinnerimage_animated, 
                ((self.image_animated.size[0]-spinnerimage_animated.size[0])/2,(self.image_animated.size[1]-spinnerimage_animated.size[1])/2))
        self.angle = 0
        self.radianoff=0.300
        self.radiusspinner=101.53
        self.pastx=0
        self.pasty=0
    def updatescreen(self):
        print "Displaying blendingScn"
        global selectedcatagory, selectedsubmenu,dictFromMA
        dictFromMA["INFOP"]="" 

        print "showing :"+menuFLAVOR
        text1 = "Please Wait"
        text2 = "Processing ..."
        text3 = menuFLAVOR
        text4 = ""

        imgtext1=text_to_image_aranger(scnCvt(400),scnCvt(12),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         text1 )
        imgtext2=text_to_image_aranger(scnCvt(400),scnCvt(9),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(35),1,
                         text2 )
        imgtext3=text_to_image_aranger(scnCvt(400),scnCvt(6),
                        pathtoDir+"/font/OpenSans-SemiBold.ttf",scnCvt(25),1,
                         text3 )
        imgtext4=text_to_image_aranger(scnCvt(400),scnCvt(5),
                        pathtoDir+"/font/OpenSans-SemiBoldItalic.ttf",scnCvt(20),1,
                         text4 )

        self.img=merging_image_to_center_vertical(imgtext1,imgtext2,scnCvt(12))
        self.img=merging_image_to_center_vertical(self.img,imgtext3,scnCvt(9))
        self.img=merging_image_to_center_vertical(self.img,imgtext4,scnCvt(6))

     

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.img)
        canvas_obj4 = self.canvas.create_image(scnCvt(240), scnCvt(600), image=tkimage4)


        x=math.sin(math.radians(self.angle)+self.radianoff)*self.radiusspinner
        y=math.cos(math.radians(self.angle)+self.radianoff)*self.radiusspinner

        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0]+scnCvt(x), circleimagecentre[1]+scnCvt(y), image=tkimage)
        self.pastx=circleimagecentre[0]+scnCvt(x)
        self.pasty=circleimagecentre[1]+scnCvt(y)
        self.angle -= spinnerSpeed
        self.angle %= 360

        self.label_info = tk.Label(self, text='10', fg='white', bg='black')
        self.label_info.config(font= ('times', scnCvt(15), 'bold'))
        self.canvas.create_window(scnCvt(220), scnCvt(750), window=self.label_info)       
        
        ########### animation- rotation

    def animation(self):
        x=math.sin(math.radians(self.angle)+self.radianoff)*self.radiusspinner
        y=math.cos(math.radians(self.angle)+self.radianoff)*self.radiusspinner
        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        self.canvas.move(self.canvas_obj,(circleimagecentre[0]+scnCvt(x))-self.pastx,(circleimagecentre[1]+scnCvt(y)-self.pasty))
        self.pastx=circleimagecentre[0]+scnCvt(x)
        self.pasty=circleimagecentre[1]+scnCvt(y)
        if "INFOP" in dictFromMA:
            self.label_info.config(text=dictFromMA["INFOP"] )

        self.angle -= spinnerSpeed
        self.angle %= 360
        if (framenow == "blendingScn"):
            self.after(20, self.animation)


class opencapScn(tk.Frame):

    def __init__(self, parent, controller):
        # received signal from main code ,
        # send signal as readyScn to main code

        # rotate ring
        # display image and font text
        # dot ... animation

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")


        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.bind("<ButtonRelease-1>", self.click_release)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)




        # image2 = Image.open(pathtoDir+iconfolder+'/next_icon1.png')
        # self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        # self.canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

    #     text1 = "UNSCREW CAP"

    #     #
    #     font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 35)
    #     fonts1w, fonts1h=font1.getsize(text1)
    #     # font2 = ImageFont.truetype(pathtoDir+"/font/OpenSans-SemiBold.ttf", 20)

    #     #
    #     textbelowvideo = Image.new("RGB", (800, 100))
    #     drawtextbelowvideo = ImageDraw.Draw(textbelowvideo)
    #     drawtextbelowvideo.text((400-fonts1w/2, 20), text1, font=font1)
    #    # draw.text((30, 235), text2, font=font1)

    #     self.tkimage3 = tkimage3 = ImageTk.PhotoImage(textbelowvideo)
    #     canvas_obj3 = self.canvas.create_image(240, 600, image=tkimage3)
        image2 = Image.new("RGB", (scnCvt(480), scnCvt(120)),(255,255,255))
        text1 = "NEXT"        
        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", scnCvt(40))
        w,h=font1.getsize(text1)
        drawtextbelowvideo = ImageDraw.Draw(image2)
        drawtextbelowvideo.text(((scnCvt(480)-w)/2, (scnCvt(120)-h)/2), text1, font=font1, fill=(0,0,0)) 
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        self.canvas_obj2 = self.canvas.create_image(circleimagecentre[0], scnCvt(740), image=tkimage2)

        imgtext=text_to_image_aranger(scnCvt(400),scnCvt(25),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         "Pull to remove cap" )
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(imgtext)
        canvas_obj3 = self.canvas.create_image(scnCvt(240), scnCvt(570), image=tkimage3) #position for text


        self.frame=0
        self.cover=0

     #   self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_spin_complete.png')
        # video_name = pathtoDir+animationfolder+"/Opencap23072020.mp4"  # This is your video file path
        # self.imagelist = imageio.get_reader(video_name)

        self.imagelist =glob(pathtoDir+animationfolder+"/Opencap23072020/*")
        self.imagelist.sort()

        self.animationArrayImg=[]
        



        # del video_name



    def updatescreen(self):
        print
        "Displaying OpenCapScn"
        # loadtimestart=time.time()
        # for idx in range(len(self.imagelist)):
        #     self.animationArrayImg.append(Image.fromarray(self.imagelist.get_data(idx)))

        # print "time to load: ", time.time()-loadtimestart
        self.frame=0
        self.animationArrayImg.append(Image.open(self.imagelist[self.frame]))
        # self.animationArrayImg.append(Image.fromarray(self.imagelist.get_data(self.frame)))
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        #self.tkimage4 = tkimage4 =ImageTk.PhotoImage(Image.fromarray(self.imagelist.get_data(self.frame)))
        # self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        self.canvas_obj4 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage4)


        self.fadeflag=False
        self.cover+=1



        self.timing=int(time.time()*2)
        self.coverflag=False
        self.cbflag=False

    def animation(self):
        self.timestart=time.time() #frame start decoding
        #video display---------------
        self.frame+=1
        self.frame %= len(self.imagelist)
        if self.frame>=len(self.animationArrayImg):
            self.animationArrayImg.append(Image.open(self.imagelist[self.frame]))
            # self.animationArrayImg.append(Image.fromarray(self.imagelist.get_data(self.frame)))
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.animationArrayImg[self.frame])

        # self.tkimage4 = tkimage4 =ImageTk.PhotoImage(Image.fromarray(self.imagelist.get_data(self.frame)))
        # self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.animationArrayImg[self.frame])

        self.canvas.itemconfig(self.canvas_obj4, image=tkimage4)
        #----------------------------

     #   self.angle -= 5
     #   self.angle %= 360

        # frame rate re-adjuster 
        framerate=time.time()-self.timestart
        if framerate>0.04:
            settimedelay=1
        else:
            settimedelay=int(1000.00*(0.04-framerate))
            
        #----------------------
        

        if (framenow == "opencapScn"):
            if self.cbflag==False:
                print "loop opencapScn"
                self.cbflag=True
            self.after(settimedelay, self.animation)
        else :
            if self.cbflag==True:
                print "close opencapScn"
                self.cbflag=False
            del self.animationArrayImg[:]

    def click_release(self, event):
        self.controller.show_frame("readyScn")


class readyScn(tk.Frame):

    def __init__(self, parent, controller):
        # received signal from main code ,
        # send signal as readyScn to main code

        # rotate ring
        # display image and font text
        # dot ... animation

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")
        #label = tk.Label(self, text="readyScn", font=controller.title_font)
        #label.pack(side="top", fill="x", pady=10)
        #button = tk.Button(self, text="Go to the start page",
        #                   command=lambda: controller.show_frame("dispensingScn"))
        #button.pack()

        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.bind("<ButtonRelease-1>", self.click_release)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # image2 = Image.open(pathtoDir+iconfolder+'/ic_cone_w_words.png')
        image2 = Image.new("RGB", (scnCvt(480), scnCvt(120)),(255,255,255))
        text1 = "START DISPENSE"        
        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", scnCvt(40))
        w,h=font1.getsize(text1)
        drawtextbelowvideo = ImageDraw.Draw(image2)
        drawtextbelowvideo.text(((scnCvt(480)-w)/2, (scnCvt(120)-h)/2), text1, font=font1, fill=(0,0,0))        
        
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        self.canvas_obj2 = self.canvas.create_image(circleimagecentre[0], scnCvt(740), image=tkimage2)


        # image3 = Image.open(pathtoDir+'/blackring.png')
        # self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        # canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)
        #
        # text1 = "Ready "
        # text2 = "1. Pull to remove dispense cap. \n2. Position cup/cone below dispensing tip. \n3. Tap icon on the right to start dispense."




        # text2 = "POSITION YOUR CUP UNDER NOZZLE"

        # font2 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 35)
        # fonts2w, fonts2h = font2.getsize(text2)

        # textbelowvideo2 = Image.new("RGB", (fonts2w, fonts2h))
        # drawtextbelowvideo2 = ImageDraw.Draw(textbelowvideo2)
        # drawtextbelowvideo2.text((0, 0), text2, font=font2)

        # self.tkimage3 = tkimage3 = ImageTk.PhotoImage(textbelowvideo2)
        # canvas_obj3 = self.canvas.create_image(240, 600, image=tkimage3)


        imgtext=text_to_image_aranger(scnCvt(440),scnCvt(25),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         "Position cup under nozzle" )
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(imgtext)
        canvas_obj3 = self.canvas.create_image(scnCvt(240), scnCvt(570), image=tkimage3) #position for text

        #
        # font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        # font2 = ImageFont.truetype(pathtoDir+"/font/OpenSans-SemiBold.ttf", 20)
        #
        # img = Image.new("RGB", (500, 400))
        # draw = ImageDraw.Draw(img)
        # draw.text((30, 180), text1, font=font1)
        # draw.text((30, 235), text2, font=font2)

        # self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        # canvas_obj4 = self.canvas.create_image(250, 200, image=tkimage4)\
        self.frame=0
        self.cover=0
        self.angle = 0
        # self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_spin_complete.png')
        # video_name = pathtoDir+animationfolder+"/position_cup_tap_dispense_24fps.mp4"  # This is your video file path
        # self.imagelist = imageio.get_reader(video_name)
        self.imagelist =glob(pathtoDir+animationfolder+"/position_cup_tap_dispense_24fps/*")
        self.imagelist.sort()

        self.animationArrayImg=[]



        # del video_name



    def updatescreen(self):
        global dictFromMA
        print
        "Displaying ReadyScn"

        # loadtimestart=time.time()
        # for idx in range(len(self.imagelist)):
        #     self.animationArrayImg.append(Image.fromarray(self.imagelist.get_data(idx)))
        # print "time to load: ", time.time()-loadtimestart
        self.frame=0
        self.animationArrayImg.append(Image.open(self.imagelist[self.frame]))
        # self.animationArrayImg.append(Image.fromarray(self.imagelist.get_data(self.frame)))
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        # self.tkimage4 = tkimage4 =ImageTk.PhotoImage(Image.fromarray(self.imagelist.get_data(self.frame)))
        # self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        self.canvas_obj4 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage4)

        # self.imgcover = Image.new("RGB", (300, 300))
        # self.tkimageCover = tkimageCover = ImageTk.PhotoImage(self.imgcover)

        # self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        # self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1]-48, image=tkimage)
       
        self.fadeflag=False
        self.cover+=1
        self.cbflag=False
        


        # w,h= self.image_animated.size
        # imga=Image.new("RGBA", (w+6,h+6))
        # draw = ImageDraw.Draw(imga)
        # draw.rectangle([0,0,w+6,h+6], fill=(0,0,0,self.cover), outline=(0,0,0,0))
        # self.tkimage_a = tkimage_a = ImageTk.PhotoImage(imga)
        # self.canvas_obj_a = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1],image= tkimage_a)
        ########### animation- rotation
        self.timing=int(time.time()*2)
        self.coverflag=False
        self.looptime=time.time()


    def animation(self):
        self.timestart=time.time()
        self.frame+=1
        self.frame %= len(self.imagelist)
        if self.frame>=len(self.animationArrayImg):
            self.animationArrayImg.append(Image.open(self.imagelist[self.frame]))
            # self.animationArrayImg.append(Image.fromarray(self.imagelist.get_data(self.frame)))
        time5=time.time()    
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        time6=time.time()  

        # self.tkimage4 = tkimage4 =ImageTk.PhotoImage(Image.fromarray(self.imagelist.get_data(self.frame)))
        #self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        # self.frame+=1
        # self.frame %= len(self.imagelist)
        self.canvas.itemconfig(self.canvas_obj4, image=tkimage4)
        # print "load image: ",time.time()-time6 , " ",time6-time5

        #----------------------------

        # if self.frame%2==0:
        #     timestart1=time.time()
        #     self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        #     timestart2=time.time()
        #     self.canvas.itemconfig(self.canvas_obj, image=self.tkimage)
        #     timestart3=time.time()
        #     print "rotate time: ",timestart3-timestart2, timestart2-timestart1

        # if self.timing != int(time.time()*2):
        #     self.timing=int(time.time()*2)
        #     self.coverflag ^= True
        # if self.coverflag:
        #
        #     self.canvas.itemconfig(self.canvas_obj, image=self.tkimage)
        # else:
        #
        #     self.canvas.itemconfig(self.canvas_obj, image=self.tkimageCover)

        

        # if self.cover>=255:
        #     self.fadeflag=True
        # if self.cover<=0:
        #     self.fadeflag=False
        # if self.fadeflag:
        #     self.cover -=1
        # else:
        #     self.cover += 1
        #
        # w,h= self.image_animated.size
        # imga=Image.new("RGBA", (w+6,h+6))
        # draw = ImageDraw.Draw(imga)
        # draw.rectangle([0,0,w+6,h+6], fill=(0,0,0,self.cover), outline=(0,0,0,0))
        # self.tkimage_a = tkimage_a = ImageTk.PhotoImage(imga)
        # self.canvas.itemconfig(self.canvas_obj_a, image=tkimage_a)
      #  self.canvas_obj_a = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1],image= tkimage_a)
        # self.frame+=1
        # self.frame %= len(self.imagelist)
    

        # frame rate re-adjuster 
        framerate=time.time()-self.timestart
        # print "frame rate: ", time.time()-self.looptime
        self.looptime=time.time()
        if framerate>0.04:
            settimedelay=1
        else:
            settimedelay=int(1000.00*(0.04-framerate))
        #----------------------

        if (framenow == "readyScn"):
            if self.cbflag==False:
                print "loop readyScn"
                self.cbflag=True
            self.after(settimedelay, self.animation)
        else :
            if self.cbflag==True:
                print "close readyScn"
                self.cbflag=False
            del self.animationArrayImg[:]

    def click_release(self, event):
        global screenpress
        screenpress=True
        pairlist = {"TOUCH": "1"}

        UI2MA_pipe_write(json.dumps(pairlist))


class dispensingScn(tk.Frame):

    def __init__(self, parent, controller):
        # received signal from main code ,
        # send signal as processScn to main code
        # dispense animation
        # rotate ring
        # display image and font text
        # dot ... animation

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")
        #label = tk.Label(self, text="dispensingScn", font=controller.title_font)
        #label.pack(side="top", fill="x", pady=10)
        #button = tk.Button(self, text="Go to the start page",
        #                   command=lambda: controller.show_frame("enjoyScn"))
        #button.pack()

        ########### text and graphic
        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image2 = Image.open(pathtoDir+iconfolder+'/ic_cone_swirl_inactive.png')
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        # text1 = "Dispensing..."

        # font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        # img = Image.new("RGB", (500, 400))
        # draw = ImageDraw.Draw(img)
        # draw.text((30, 180), text1, font=font1)

        # self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        # canvas_obj4 = self.canvas.create_image(240, 600, image=tkimage4)


        imgtext=text_to_image_aranger(scnCvt(400),scnCvt(25),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         "Dispensing..." )
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(imgtext)
        canvas_obj4 = self.canvas.create_image(scnCvt(240), scnCvt(600), image=tkimage4) #position for text

        # self.angle = 0
        self.cover=0
        # self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_spinner2.png').resize((scnCvt(228),scnCvt(228)))
        self.image_animated2 = Image.open(pathtoDir+iconfolder+'/ic_cone_swirl.png')
        spinnerimage_animated = Image.open(pathtoDir +iconfolder+ '/ic_spinner.png').resize((scnCvt(79),scnCvt(35)))
        self.image_animated = Image.new('RGBA', (scnCvt(79),scnCvt(79)), (0, 0, 0, 0))
        self.image_animated.paste(spinnerimage_animated, 
                ((self.image_animated.size[0]-spinnerimage_animated.size[0])/2,(self.image_animated.size[1]-spinnerimage_animated.size[1])/2))
        self.angle = 0
        self.radianoff=0.300
        self.radiusspinner=101.53
        self.pastx=0
        self.pasty=0
        
    def updatescreen(self):
        print "Displaying dispensingScn"
        global dictFromMA
        dictFromMA["INFOP"]="" 
        x=math.sin(math.radians(self.angle)+self.radianoff)*self.radiusspinner
        y=math.cos(math.radians(self.angle)+self.radianoff)*self.radiusspinner

        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0]+scnCvt(x), circleimagecentre[1]+scnCvt(y), image=tkimage)
        self.pastx=circleimagecentre[0]+scnCvt(x)
        self.pasty=circleimagecentre[1]+scnCvt(y)
        self.img_a = copy.deepcopy(self.image_animated2)
        w, h = self.img_a.size
        self.draw = ImageDraw.Draw(self.img_a)
        self.draw.rectangle([0, 0, w, scnCvt(53) - self.cover], fill=(0, 0, 0, 0), outline=(0, 0, 0, 0))
        self.tkimage_a = tkimage_a = ImageTk.PhotoImage(self.img_a)
        self.canvas_obj_a = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage_a)

        self.cover += 0.10
        self.angle -= spinnerSpeed
        self.angle %= 360

        self.label_info = tk.Label(self, text='', fg='white', bg='black')
        self.label_info.config(font= ('times', scnCvt(15), 'bold'))
        self.canvas.create_window(scnCvt(220), scnCvt(750), window=self.label_info)           

        ########### animation- rotation

    def animation(self):
        x=math.sin(math.radians(self.angle)+self.radianoff)*self.radiusspinner
        y=math.cos(math.radians(self.angle)+self.radianoff)*self.radiusspinner
        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        self.canvas.move(self.canvas_obj,(circleimagecentre[0]+scnCvt(x))-self.pastx,(circleimagecentre[1]+scnCvt(y)-self.pasty))
        self.pastx=circleimagecentre[0]+scnCvt(x)
        self.pasty=circleimagecentre[1]+scnCvt(y)

        self.img_a=copy.deepcopy(self.image_animated2)
        w,h=self.img_a.size
        self.draw = ImageDraw.Draw(self.img_a)
        self.draw.rectangle([0,0,w,scnCvt(53)-self.cover],fill=(0,0,0,0),outline=(0,0,0,0))
        self.tkimage_a = tkimage_a = ImageTk.PhotoImage(self.img_a)
        self.canvas.itemconfig(self.canvas_obj_a, image=tkimage_a)
        if "INFOP" in dictFromMA:
            self.label_info.config(text=dictFromMA["INFOP"] )
            
        self.cover += 0.10
        self.angle -= spinnerSpeed
        self.angle %= 360
        if (framenow == "dispensingScn"):
            self.after(20, self.animation)
        else:
            self.cover=0


class extraDispensingScn(tk.Frame):

    def __init__(self, parent, controller):
        # received signal from main code ,
        # send signal as processScn to main code
        # dispense animation
        # rotate ring
        # display image and font text
        # dot ... animation

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")
        #label = tk.Label(self, text="dispensingScn", font=controller.title_font)
        #label.pack(side="top", fill="x", pady=10)
        #button = tk.Button(self, text="Go to the start page",
        #                   command=lambda: controller.show_frame("enjoyScn"))
        #button.pack()

        ########### text and graphic
        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image2 = Image.open(pathtoDir+iconfolder+'/ic_cone_swirl_inactive.png')
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        # text1 = "Dispensing..."

        # font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        # img = Image.new("RGB", (500, 400))
        # draw = ImageDraw.Draw(img)
        # draw.text((30, 180), text1, font=font1)

        # self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        # canvas_obj4 = self.canvas.create_image(240, 600, image=tkimage4)


        imgtext=text_to_image_aranger(scnCvt(400),scnCvt(25),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         "Dispense Finish!" )
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(imgtext)
        canvas_obj4 = self.canvas.create_image(scnCvt(240), scnCvt(600), image=tkimage4) #position for text

        # self.angle = 0
        self.cover=0
        # self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_spinner2.png').resize((scnCvt(228),scnCvt(228)))
        self.image_animated2 = Image.open(pathtoDir+iconfolder+'/ic_cone_swirl.png')
        # spinnerimage_animated = Image.open(pathtoDir +iconfolder+ '/ic_spinner.png').resize((scnCvt(79),scnCvt(35)))
        # self.image_animated = Image.new('RGBA', (scnCvt(79),scnCvt(79)), (0, 0, 0, 0))
        # self.image_animated.paste(spinnerimage_animated, 
        #         ((self.image_animated.size[0]-spinnerimage_animated.size[0])/2,(self.image_animated.size[1]-spinnerimage_animated.size[1])/2))
        self.img_a = copy.deepcopy(self.image_animated2)
        w, h = self.img_a.size
        self.draw = ImageDraw.Draw(self.img_a)
        # self.draw.rectangle([0, 0, w, scnCvt(53) - self.cover], fill=(0, 0, 0, 0), outline=(0, 0, 0, 0))
        self.tkimage_a = tkimage_a = ImageTk.PhotoImage(self.img_a)
        self.canvas_obj_a = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage_a)
        self.angle = 0
        self.radianoff=0.300
        self.radiusspinner=101.53
        self.pastx=0
        self.pasty=0
        
        self.timeleft=10.0

        # button_Soft = tk.Button(self, text='Soft', bg=colourlist[1], fg=fntcolourlist[1],width=scnCvt(7),compound=tk.CENTER,
        #                            activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
        #                            pady=1, bd=1, font= ('times', scnCvt(14)), command=lambda: self.sendSoftnessParam(2))  
                                   
        self.extradispcanvas = tk.Canvas(self, width=scnCvt(350), height=scnCvt(120), bg="black", bd=scnCvt(10))
        self.extradispcanvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        button_extdisp = tk.Button(self, text='Extra Dispense', bg="white", fg="black",width=14,
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1,font= ('times', scnCvt(14)), command=lambda: self.sendExtraDispence(True))
        button_cancel = tk.Button(self, text='No Thanks!', bg="white", fg="black",width=14,
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1,font= ('times', scnCvt(14)), command=lambda:self.sendExtraDispence(False) )
        label_extardispende = tk.Label(self, text='Do you need extra dispense?', fg='white', bg='black')
        label_extardispende.config(font= ('times', scnCvt(15), 'bold'))
        self.label_extardispendetime = tk.Label(self, text='10', fg='white', bg='black')
        self.label_extardispendetime.config(font= ('times', scnCvt(15), 'bold'))

        self.extradispcanvas.create_window(scnCvt(98),scnCvt(80), window=button_extdisp)
        self.extradispcanvas.create_window(scnCvt(273), scnCvt(80), window=button_cancel)
        self.extradispcanvas.create_window(scnCvt(350)/2, scnCvt(30), window=label_extardispende)
        self.extradispcanvas.create_window(scnCvt(60), scnCvt(120), window=self.label_extardispendetime)
        
    def updatescreen(self):
        print "Displaying extraDispensingScn"
        self.sendmsgonce=True
        self.timeleft=10.0
        self.label_extardispendetime.config( text=str(self.timeleft))


    def animation(self):
        self.timeleft-=0.1
        self.label_extardispendetime.config( text=str(int(self.timeleft))+"s")
        if (framenow == "extraDispensingScn"):
            self.after(100, self.animation)
        if self.timeleft<=0 and self.sendmsgonce:
            self.sendExtraDispence(False)
            

    def sendExtraDispence(self,pn):
        if self.sendmsgonce:
            pairlist = {"EXTDISP": pn}
            UI2MA_pipe_write(json.dumps(pairlist))
            self.sendmsgonce=False


class smileyScn(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")
        #label = tk.Label(self, text="enjoyScn", font=controller.title_font)
        #label.pack(side="top", fill="x", pady=10)
        #button = tk.Button(self, text="Go to the start page",
        #                   command=lambda: controller.show_frame("insertScn"))
        #button.pack()

        ########### text and graphic
        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.canvas.bind("<ButtonRelease-1>", self.click_release)

        self.canvas.bind("<B1-Motion>", self.click_press)

        self.canvas.bind("<Button-1>", self.click_press)
        # image2 = Image.open(pathtoDir+'/ic_cone_swirl.png')
        # self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        # canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)
        #
        # image3 = Image.open(pathtoDir+'/blackring.png')
        # self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        # canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        text1 = "Before you go..."
        text2 = "How likely are you to recommend us to your friend or colleague?"
        text3 = "Not Likely"
        text4 = "Very Likely"
        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Bold.ttf", scnCvt(40))
        font2 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", scnCvt(22))
        font3 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Bold.ttf", scnCvt(20))
        img = Image.new("RGB", (scnCvt(800), scnCvt(400)))
        draw = ImageDraw.Draw(img)
        f1w, f1h=font1.getsize(text1)
        f2w, f2h = font2.getsize(text2)
        f3w, f3h = font3.getsize(text3)
        f4w, f4h = font3.getsize(text4)
        draw.text((scnCvt(400)-f1w/2, scnCvt(100)), text1, font=font1)
        draw.text((scnCvt(400)-f2w/2, scnCvt(180)), text2, font=font2)
        draw.text((scnCvt(10), scnCvt(380)), text3, font=font3)
        draw.text((scnCvt(800)-scnCvt(10)-f4w, scnCvt(380)), text4, font=font3)

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(scnCvt(400), scnCvt(150), image=tkimage4)

        self.angle = 0
        self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_spin_complete.png')
        self.tkimage = range(10)
        self.canvas_obj = range(10)

    def updatescreen(self):
        print "Displaying smileyScn"

        self.image_animated = []
        self.moving = 0
        self.pitchsize = (800) / (10)
        self.difspeed=0.7
        self.movingspeed=0.2
        self.presskeylatch=[0]*10
        font1 = ImageFont.truetype(pathtoDir + "/font/Orbitron-Bold.ttf", 40)

        for ic_no in range(10):
            #img = Image.new("RGB", (70, 70),(int(255*self.colorRange[ic_no][0]),int(255*self.colorRange[ic_no][1]),int(255*self.colorRange[ic_no][2])))
            self.img = Image.new("RGB", (70, 70),(255,255,255))

            self.draw = ImageDraw.Draw(self.img)
            textnum=str(ic_no+1)
            f1w, f1h = font1.getsize(textnum)
            self.draw.rectangle([5,5,65,65],fill=(0,0,0,0),outline=(0,0,0,0) )
            self.draw.text((35 - f1w / 2, 35-f1h/2), textnum, font=font1)
            self.image_animated.append(self.img)
            self.tkimage[ic_no] = ImageTk.PhotoImage(self.img)

        for ic_no in range(10):
            dampwave_scale = 900 * math.exp(-self.moving + (ic_no * self.difspeed))
            self.canvas_obj[ic_no] = self.canvas.create_image(self.pitchsize * (ic_no + 0.5) + dampwave_scale,
                                                                  250, image=self.tkimage[ic_no])

 #       global menuBRAND,menuFLAVOR,menuTYPE
 #       menuBRAND = ""
 #       menuFLAVOR = ""
 #       menuTYPE = ""
        global selectedrating
        selectedrating=-1
        ########### animation- rotation

    def animation(self):

        self.moving += self.movingspeed
        for ic_no in range(10):
            dampwave_scale = 900*math.exp(-self.moving+(ic_no*self.difspeed))
            dampwave_scale2 = 900 * math.exp(-self.moving+self.movingspeed + (ic_no * self.difspeed))
            ans=dampwave_scale2-dampwave_scale

            self.canvas.move(self.canvas_obj[ic_no], -ans,0)
        # self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        # self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        #
        # self.angle -= 5
        # self.angle %= 360
        if (framenow == "smileyScn"  and dampwave_scale>0.1):
            self.after(10, self.animation)
        else:
            self.moving=0

    def click_release(self, event):
        global selectedrating,screenpress
        presspix=np.array([event.x, event.y])
        for selno in range(len(self.image_animated)):
            buttonpix=np.array([self.pitchsize*(selno+0.5), 250])
            if (np.linalg.norm(presspix-buttonpix)<35):

                selectedrating = selno+1
                screenpress = True
                pairlist = {"TOUCH": "1","RATE":str(selectedrating)}

                UI2MA_pipe_write(json.dumps(pairlist))
                self.controller.show_frame("thankyouScn")
                break


                #1280x800
                #1024*600
                #800x480

    def click_press(self, event):
        global selectedrating
        presspix=np.array([event.x, event.y])
        for selno in range(len(self.image_animated)):
            buttonpix=np.array([self.pitchsize*(selno+0.5), 250])
            if (np.linalg.norm(presspix-buttonpix)<35):
                self.presskeylatch[selno]=1

                img_a = self.image_animated[selno].resize((int(90), int(90)), Image.ANTIALIAS)
                self.tkimage[selno]  = ImageTk.PhotoImage(img_a)
                self.canvas.itemconfig(self.canvas_obj[selno], image=self.tkimage[selno])
                #self.canvas_obj[selno] = self.canvas.create_image(self.pitchsize * (selno + 0.5),
                #                                                  circleimagecentre[1], image=self.tkimage[selno])

                selectedrating = selno
               # menuTYPE=mainmenu_foldername[selectedmainmenu][5:]

            elif self.presskeylatch[selno]==1:
                self.tkimage[selno]  = ImageTk.PhotoImage(self.image_animated[selno])
                self.canvas.itemconfig(self.canvas_obj[selno], image=self.tkimage[selno])
                

class thankyouScn(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")



        ########### text and graphic
        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)



        text1 = "Thanks for your feedback!"

        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Bold.ttf", scnCvt(40))

        img = Image.new("RGB", (scnCvt(800), scnCvt(400)))
        draw = ImageDraw.Draw(img)
        f1w, f1h=font1.getsize(text1)

        draw.text((scnCvt(400)-f1w/2, scnCvt(200)), text1, font=font1)


        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(scnCvt(400), scnCvt(150), image=tkimage4)



    def updatescreen(self):
        print "Displaying Thankpage"

        ########### animation- rotation

    def animation(self):

        if (framenow == "thankyouScn" ):
            self.after(10, self.animation)
        else:
            self.moving=0


class loadingScn(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")



        ########### text and graphic
        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image1 = Image.open(pathtoDir+iconfolder+'/Swirl-Go-Logo-Innovfest-Unboardb.png').resize((scnCvt(480),scnCvt(480)), Image.ANTIALIAS)
        self.tkimage1 = tkimage1 = ImageTk.PhotoImage(image1)
        canvas_obj1 = self.canvas.create_image(circleimagecentre[0], scnCvt(400), image=tkimage1)

        text1 = "Loading ..."

        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Bold.ttf", scnCvt(40))


        f1w, f1h=font1.getsize(text1)
        img = Image.new("RGB", (f1w, f1h+scnCvt(10)))
        draw = ImageDraw.Draw(img)

        draw.text((0, 0), text1, font=font1)


        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(circleimagecentre[0], scnCvt(600), image=tkimage4)



    def updatescreen(self):
        print "Displaying Loading page"

        ########### animation- rotation

    def animation(self):

        if (framenow == "loadingScn" ):
            self.after(10, self.animation)
        else:
            self.moving=0


class removeScn(tk.Frame):

    def __init__(self, parent, controller):
        # touch event to send signal to main code ,-->identifyingScn,
        # send signal as insertScn to main code
        # rotate ring
        # display image and font text

        tk.Frame.__init__(self, parent)

        self.controller = controller
        self.configure(bg="black")
        #label = tk.Label(self, text="insertScn", font=controller.title_font)
        #label.pack(side="top", fill="x", pady=10)
        #button = tk.Button(self, text="Go to the identifyScn",
        #                   command=lambda: controller.show_frame("identifyScn"))
        #button.pack()

        ########### text and graphic
        self.canvas = tk.Canvas(self, width=scnCvt(480), height=scnCvt(800), bg='black',highlightthickness=0)
        self.canvas.bind("<ButtonRelease-1>", self.click_release)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # image2 = Image.open(pathtoDir+'/ic_pod.png')
        # self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        # canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)
        #
        # image3 = Image.open(pathtoDir+'/blackring.png')
        # self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        # canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        # text1 = "Pull open tray to"
        # text12= "remove Swirl Pod"

        # font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        # img = Image.new("RGB", (500, 400))
        # draw = ImageDraw.Draw(img)
        # draw.text((30, 180), text1, font=font1)
        # draw.text((30, 230), text12, font=font1)
        # self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        # canvas_obj4 = self.canvas.create_image(240, 600, image=tkimage4)


        imgtext=text_to_image_aranger(scnCvt(400),scnCvt(25),
                        pathtoDir+"/font/Orbitron-Medium.ttf",scnCvt(50),1,
                         "Pull open tray to remove Swirl Pod" )
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(imgtext)
        canvas_obj4 = self.canvas.create_image(scnCvt(240),scnCvt(600), image=tkimage4) #position for text

        self.angle = 0
        self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_spin_complete.png')
        # video_name = pathtoDir+animationfolder+"/Removepod23072020.mp4"  # This is your video file path
        
        
        # self.imagelist = imageio.get_reader(video_name)
        # frameicon = Image.open(pathtoDir + animationfolder + "/frame4.png").convert('L')

        # self.animationArrayImg=[]
        # for idx in range(len(self.imagelist)):
        #     image_frame = Image.fromarray(self.imagelist.get_data(idx))
        #     w, h = image_frame.size
        #     framecolor = Image.new("RGB", (w, h))
        #     image_frame = Image.composite(image_frame, framecolor, frameicon)
        #     self.animationArrayImg.append(image_frame)
        # del image_frame
        # del framecolor
        # del w,h
        # del frameicon
        # del video_name
        self.imagelist =glob(pathtoDir+animationfolder+"/Removepod23072020/*")
        self.imagelist.sort()
        self.animationArrayImg=[]

        ########### animation- rotation
    def updatescreen(self):
        print "Displaying removeScn"

        # video display --------
        self.frame=0
        self.animationArrayImg.append(Image.open(self.imagelist[self.frame]))
        
        self.tkimage = tkimage = ImageTk.PhotoImage(self.animationArrayImg[self.frame])

        #--------------------------

        #self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)

        self.angle -= 5
        self.angle %= 360
    
    ########### animation- rotation

    def animation(self):
        self.timestart=time.time() #frame start decoding
        #video display---------------
        if self.frame>=len(self.animationArrayImg):
            self.animationArrayImg.append(Image.open(self.imagelist[self.frame]))
        self.tkimage = tkimage = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        self.frame+=1
        self.frame %= len(self.imagelist)
        #----------------------------

        #self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        framerate=time.time()-self.timestart
        if framerate>0.04:
            settimedelay=1
        else:
            settimedelay=int(1000.00*(0.04-framerate))

        self.angle -= 5
        self.angle %= 360
        if (framenow == "removeScn"):
            self.after(settimedelay, self.animation)
        else :
            del self.animationArrayImg[:]

    def click_release(self, event):
        global screenpress
        screenpress=True


class loopingmain(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        global screenpress
        if not TEST_UI:
            try:
                os.mkfifo(MA2UI_FIFO)
            except OSError as oe:
                if oe.errno != errno.EEXIST:
                    raise
        print "loopingngng11"

        time.sleep(2)
        self.count=0
        self.looping()



    def looping(self):
        
        if not TEST_UI:
            global screenpress, menuBRAND, menuFLAVOR, menuTYPE,MA2UI_FIFOOpenRead,dictFromMA
            screenselect=""
            
            msgFromMA = MA2UI_FIFOOpenRead.read()

            if len(msgFromMA) != 0:
                print "MA2UI msg:",msgFromMA
                dictFromMA=jsonOrganizeLoad(msgFromMA)

                if "BRAND" in dictFromMA:
                    menuBRAND=dictFromMA["BRAND"]

                if "DESERT_TYPE" in dictFromMA:
                    menuTYPE=dictFromMA["DESERT_TYPE"]

                if "FLAVOUR" in dictFromMA:
                    menuFLAVOR=dictFromMA["FLAVOUR"]
                    print "menuFLAVOR:",menuFLAVOR

                if "SCN" in dictFromMA:
                    screenselect=dictFromMA["SCN"]

                    if (screenselect in listofscreen) and framenow != screenselect:
                        print "select", screenselect
                        self.controller.show_frame(screenselect)
                    pairlist = {"SCN": framenow}
                    UI2MA_pipe_write(json.dumps(pairlist))
            self.after(100, self.looping)        
        if TEST_UI:
            print "num=>",self.count
            self.count+=1
            self.count=self.count%len(listofscreen)
            self.controller.show_frame(listofscreen[self.count])
            self.after(10000, self.looping)  


if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()