
# import tkinter as tk                # python 3
# from tkinter import font  as tkfont # python 3
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
from multiprocessing import Process#
from Queue import Queue,Empty
import os
import errno
import subprocess as sp
import WpaUpdater as wp
from printwtime import printtime

# screen 800x480 ui
TEST_UI=False

framenow = ""
circleimagecentre = [640, 200]
selectedmainmenu=0
mainmenu_foldername=[]
menuBRAND=""
menuFLAVOR=""
menuTYPE=""
menuSOFT=""

pathtoDir="/home/pi/GUIraspberrypi"
#pathtoDir="."
animationfolder="/AnimationsforUI16Oct"
iconfolder="/icons"
selectedsubmenu=""
selectedcatagory=""
screenpress=False
listofscreen=["insertScn","doorcloseScn" ,"identifyScn", "recognizedScn", "errorScn1","errorScn2","errorScn3",
              "blendingScn","readyScn", "dispensingScn", "smileyScn","thankyouScn", "mainmenuScn",
              "submenuScn", "removeScn", "wifiScn"]

# --------------PIPE setup---------------------------
MA2UI_FIFO="pipe_from_MA_to_UI"
UI2MA_FIFO = 'pipe_from_UI_to_MA'

time.sleep(1)

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

def str2pair( st):
    pairlist = list()
    while True:
        startslash = st.find("/")
        center = st.find(":")
        if center < 0 or startslash < 0:
            break
        firststr = st[startslash + 1: center]
        duplcatedslash = firststr.find("/")
        if duplcatedslash > -1:
            firststr = firststr[duplcatedslash + 1:]
        st = st[center:]
        center = st.find(":")
        endslash = st.find("/")
        secondstr = st[center + 1: endslash]
        st = st[endslash:]
        pair = (firststr, secondstr)
        pairlist.append(pair)
    pairlist = dict(pairlist)
    return pairlist

def pair2str( pairlist):
    str = ""
    for p in pairlist:
        str = str + "/" + p + ":" + pairlist[p]
    str = str + "/"
    return str

class SampleApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others

        self.attributes("-fullscreen", True) # for full screen
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (insertScn,doorcloseScn ,identifyScn, recognizedScn, errorScn1,errorScn2,errorScn3,
              blendingScn,readyScn, dispensingScn, smileyScn,thankyouScn, mainmenuScn,
              submenuScn, removeScn, wifiScn,loopingmain):
            page_name = F.__name__
            frame = F(parent=container, controller=self, )
            self.frames[page_name] = frame

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")


        #self.show_frame("removeScn")
        self.show_frame("insertScn")

    def show_frame(self, page_name):
        global framenow
        '''Show a frame for the given page name'''
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


class wifiScn(tk.Frame):
    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")

        self.canvas = tk.Canvas(self, width=800, height=400, bg='black', highlightthickness=0)

        self.canvas.bind("<ButtonRelease-1>", self.click_release)
        self.canvas.bind("<B1-Motion>", self.click_press)
        self.canvas.bind("<Button-1>", self.click_press)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        text = "Wifi Setting"

        text1 = "SSID:"
        text2 = "Password:"

        font1 = ImageFont.truetype(pathtoDir+'/font/OpenSans-SemiBold.ttf', 25)
        font1w, font1h = font1.getsize(text)
        img = Image.new("RGB", (800, 40))
        draw = ImageDraw.Draw(img)
        draw.text((400 - font1w / 2, 0), text, font=font1)

        draw.line((30, 20, 260, 20), fill=(255, 255, 255, 255), width=1)
        draw.line((540, 20, 770, 20), fill=(255, 255, 255, 255), width=1)

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(400, 45, image=tkimage4)

        self.content_ssid = tk.StringVar()
        self.content_pwd = tk.StringVar()
        entry_ssid = tk.Entry(self, textvariable=self.content_ssid)
        entry_pwd = tk.Entry(self, textvariable=self.content_pwd)

        label_ssid = tk.Label(self, text=text1, bg='black', fg='white')
        label_pwd = tk.Label(self, text=text2, bg='black', fg='white')

        button_cancel = tk.Button(self, text='cancel', bg="#3c4987", fg="#ffffff",
                                  activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                  pady=1, bd=1, command=self.cancelbuttonpress)
        button_connect = tk.Button(self, text='connect', bg="#3c4987", fg="#ffffff",
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, command=self.connectbuttonpress)
        button_refresh = tk.Button(self, text='refresh', bg="#3c4987", fg="#ffffff",
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, command=self.refreshbuttonpress)
        button_left = tk.Button(self, text='  <  ', bg="#3c4987", fg="#ffffff",
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, command=self.leftbuttonpress)
        button_right = tk.Button(self, text='  >  ', bg="#3c4987", fg="#ffffff",
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, command=self.rightbuttonpress)

        canvas_obj5 = self.canvas.create_window(600, 100, window=entry_ssid)
        canvas_obj6 = self.canvas.create_window(600, 125, window=entry_pwd)

        canvas_obj7 = self.canvas.create_window(490, 100, window=label_ssid)
        canvas_obj8 = self.canvas.create_window(475, 125, window=label_pwd)

        canvas_obj9 = self.canvas.create_window(550, 160, window=button_cancel)
        canvas_obj11 = self.canvas.create_window(650, 160, window=button_connect)
        canvas_obj12 = self.canvas.create_window(80, 250, window=button_refresh)

        canvas_obj13 = self.canvas.create_window(140, 250, window=button_left)
        canvas_obj14 = self.canvas.create_window(180, 250, window=button_right)

        self.wpaFile_dir="/etc/wpa_supplicant/wpa_supplicant.conf"
        self.wifilistsave_dir = pathtoDir+"/wifilistsave.txt"



    def updatescreen(self):

        self.wifipagelist=0
        self.Shiftbutton = False
        self.runkb()
        self.scanwifissid()

    def leftbuttonpress(self):
        print ("previous page")
        if self.wifipagelist==0:
            self.wifipagelist=0
        else:
            self.wifipagelist=self.wifipagelist-1
        self.updatelistbox()

    def rightbuttonpress(self):
        print ("next page")
        if self.wifipagelist==(len(self.scanwifilist)/10):

            self.wifipagelist=(len(self.scanwifilist)/10)
        else:
            self.wifipagelist=self.wifipagelist+1
        self.updatelistbox()

    def refreshbuttonpress(self):
        print ("refresh")
        self.scanwifissid()

    def cancelbuttonpress(self):
        print ("cancel")
        self.controller.show_frame("insertScn")

    def connectbuttonpress(self):
        print ("connect ", self.content_pwd.get(), self.content_ssid.get())
        self.dictSaveWifi.update({self.content_ssid.get(): self.content_pwd.get()})
        wp.saveWifiFile(self.wifilistsave_dir, self.wpafirsttext,self.dictSaveWifi)
        wp.updateWpaFile(self.wpaFile_dir, self.wpafirsttext,self.content_ssid.get(),self.content_pwd.get() )
        #refresh network
        p4 = sp.Popen(['systemctl', 'daemon-reload'], stdout=sp.PIPE)
        p5 = sp.Popen(['systemctl', 'restart', 'dhcpcd'], stdout=sp.PIPE)
        self.controller.show_frame("insertScn")

    def select(self, value):
        if value == "BACK":
            textpwd = self.content_pwd.get()
            textpwd = textpwd[:-1]
            self.content_pwd.set(textpwd)
        elif value == "SPACE":
            textpwd = self.content_pwd.get()
            textpwd = textpwd + ' '
            self.content_pwd.set(textpwd)
        elif value == "SHIFT":
            self.Shiftbutton = not self.Shiftbutton
            self.runkb()
        else:
            textpwd = self.content_pwd.get()
            textpwd = textpwd + value
            self.content_pwd.set(textpwd)

    def scanwifissid(self):

        self.scanwifilist=wp.wifiscanlist()

       # self.scanwifilist = ['fdggrh', 'dhethrh', 'wsd', 'rtfgfgg', 'feq', 'wdgryet']
        self.wpafirsttext, self.dictSaveWifi=wp.convertWpaFile2Dict(self.wifilistsave_dir)
        self.scanVsSavedictbool=wp.compareScanAndSaveWifi(self.dictSaveWifi,self.scanwifilist)
        self.updatelistbox()

    def updatelistbox(self):
        print ("page number:" ,self.wifipagelist, " ",len(self.scanwifilist))
        self.wifilistbox = tk.Listbox(self, width=30, height=10)
        for no, kv in enumerate(self.scanwifilist):
            if no>(self.wifipagelist*10-1):
                if self.scanVsSavedictbool[kv]:
                    self.wifilistbox.insert(no-(self.wifipagelist*10), kv+"    -*")
                else:
                    self.wifilistbox.insert(no-(self.wifipagelist*10), kv)
        canvas_obj8 = self.canvas.create_window(160, 150, window=self.wifilistbox)

    def runkb(self):
        varRow = 2
        varColumn = 0
        buttonlist = [None] * len(wp.kbbuttons)
        canvas_object_buttonlist = [None] * len(wp.kbbuttons)

        if self.Shiftbutton:
            buttonkey = wp.kbbuttonsS
        else:
            buttonkey = wp.kbbuttons
        for idx, button in enumerate(buttonkey):

            command = lambda x=button: self.select(x)

            if button == "SPACE" or button == "SHIFT" or button == "BACK":
                buttonlist[idx] = tk.Button(self, text=button, width=6, bg="#3c4987", fg="#ffffff",
                                            activebackground="#ffffff", activeforeground="#3c4987", relief='raised',
                                            padx=1,
                                            pady=1, bd=1, command=command)
                canvas_object_buttonlist[idx] = self.canvas.create_window(65 + varColumn * 45.6, 250 + varRow * 25,
                                                                          window=buttonlist[idx])
            else:
                buttonlist[idx] = tk.Button(self, text=button, width=4, bg="#3c4987", fg="#ffffff",
                                            activebackground="#ffffff", activeforeground="#3c4987", relief='raised',
                                            padx=1,
                                            pady=1, bd=1, command=command)
                canvas_object_buttonlist[idx] = self.canvas.create_window(65 + varColumn * 45, 250 + varRow * 25,
                                                                          window=buttonlist[idx])

            varColumn += 1
            if varColumn > 14 and varRow == 2:
                varColumn = 0
                varRow += 1
            if varColumn > 14 and varRow == 3:
                varColumn = 0
                varRow += 1
            if varColumn > 14 and varRow == 4:
                varColumn = 0
                varRow += 1

    def animation(self):
        selectedssidno = self.wifilistbox.curselection()
        if selectedssidno:
            selectedssid = self.scanwifilist[selectedssidno[0]+(self.wifipagelist*10)]
            self.content_ssid.set(selectedssid)
            if self.scanVsSavedictbool[selectedssid]:
                self.content_pwd.set(self.dictSaveWifi[selectedssid])
            else:
                self.content_pwd.set("")
        # for icno in range(len(self.image_animated)):
        #   self.tkimage[icno]=ImageTk.PhotoImage(self.image_animated[icno])
        if (framenow == "wifiScn"):
            self.after(10, self.animation)

    def click_release(self, event):

        presspix = np.array([event.x, event.y])

    def click_press(self, event):

        presspix = np.array([event.x, event.y])


class insertScn(tk.Frame):

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
        self.canvas = tk.Canvas(self, width=800, height=400, bg='black',highlightthickness=0)
        self.canvas.bind("<ButtonRelease-1>", self.click_release)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        #
        # image2 = Image.open(pathtoDir+'/ic_pod.png')
        # self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        # canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)
        #
        # image3 = Image.open(pathtoDir+'/blackring.png')
        # self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        # canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        image10 = Image.open(pathtoDir+iconfolder+'/wifiicon.png').resize((25,20),Image.ANTIALIAS)
        self.image11 = Image.open(pathtoDir+iconfolder + '/qumark.png').resize((15, 20), Image.ANTIALIAS)
        self.tkimage10 = tkimage10 = ImageTk.PhotoImage(image10)
        canvas_obj10 = self.canvas.create_image(775, 10, image=tkimage10)



        text1 = "Insert Swirl Pod"

        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        w,h = font1.getsize(text1)
        img = Image.new("RGB", (w,h))
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), text1, font=font1)
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(400, 380, image=tkimage4)

        self.angle = 0
        self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_spin_complete.png')


        # Menu button setup
      #  imageMenu = Image.open(pathtoDir + '/Menu.png')
        imageMenu = Image.new("RGB",(20,20), (0,0,0))
        self.tkimageMenu=tkimageMenu=ImageTk.PhotoImage(imageMenu)
        sidemenu=tk.Menubutton(self, image=tkimageMenu, relief=tk.RAISED,bg='black', bd=0)
        sidemenu.grid()
        sidemenu.menu=tk.Menu(sidemenu,tearoff=0)
        sidemenu["menu"]=sidemenu.menu
        sidemenu.menu.add_checkbutton(label="wifi setting", command =lambda: controller.show_frame("wifiScn"))
        sidemenu.menu.add_checkbutton(label="shut down", command=self.shutdownMenu)
        canvas_obj14 = self.canvas.create_window(20, 20, window=sidemenu)

        video_name = pathtoDir+animationfolder+"/Insert02022020.mp4"  # This is your video file path
        self.imagelist = imageio.get_reader(video_name)

        self.animationArrayImg=[]
        for idx in range(len(self.imagelist)):
            self.animationArrayImg.append(Image.fromarray(self.imagelist.get_data(idx)))


        del video_name

    def shutdownMenu(self):

        shutdowncanvas = tk.Canvas(self, width=200, height=100, bg="red", bd=10)
        shutdowncanvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        button_shutdown = tk.Button(self, text=' Shut Down', bg="#3c4987", fg="#ffffff",
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, command=lambda: os.system("sudo shutdown -h now"))
        button_cancel = tk.Button(self, text='  Cancel  ', bg="#3c4987", fg="#ffffff",
                                   activebackground="#ffffff", activeforeground="#3c4987", relief='raised', padx=1,
                                   pady=1, bd=1, command=lambda: shutdowncanvas.destroy() )
        label_shutdownconfirm = tk.Label(self, text='Are you sure you want\n shut down?', fg='white', bg='red')
        label_shutdownconfirm.config(font= ('times', 15, 'bold'))

        shutdowncanvas.create_window(60,80, window=button_shutdown)
        shutdowncanvas.create_window(160, 80, window=button_cancel)
        shutdowncanvas.create_window(110, 30, window=label_shutdownconfirm)


        ########### animation- rotation
    def updatescreen(self):
        print
        "Displaying insertScn"

        self.frame=0



        self.tkimage = tkimage = ImageTk.PhotoImage(self.animationArrayImg[self.frame])

        self.canvas_obj = self.canvas.create_image(400, 150, image=tkimage)
        self.angle -= 5
        self.angle %= 360

        # wifi question mark icon update
        self.img_a = copy.deepcopy(self.image11)
        w, h = self.img_a.size
        self.draw = ImageDraw.Draw(self.img_a)
        self.draw.rectangle([0, 0, w, h], fill=(0, 0, 0, 0), outline=(0, 0, 0, 0))

        self.tkimage_a = tkimage_a = ImageTk.PhotoImage(self.img_a)

        self.canvas_obj_a = self.canvas.create_image(775, 10, image=tkimage_a)


    ########### animation- rotation

    def animation(self):

        #video display---------------

        self.tkimage = tkimage = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        self.frame+=1
        self.frame %= len(self.imagelist)
        #----------------------------
        # self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)

        # wifi question mark icon update

        self.img_a = copy.deepcopy(self.image11)
        w, h = self.img_a.size
        if wp.wificonnected():
            quIconCover = h
        else:
            quIconCover = 0
        self.draw = ImageDraw.Draw(self.img_a)
        self.draw.rectangle([0, 0, w, quIconCover], fill=(0, 0, 0, 0), outline=(0, 0, 0, 0))
        self.tkimage_a = tkimage_a = ImageTk.PhotoImage(self.img_a)
        self.canvas.itemconfig(self.canvas_obj_a, image=tkimage_a)

        self.angle -= 5
        self.angle %= 360
        if (framenow == "insertScn"):
            self.after(5, self.animation)

    def click_release(self, event):
        global screenpress
        screenpress=True
        # ====this is for wifi icon click to access to wifi menu
        # presspix = np.array([event.x, event.y])
        # buttonpix = np.array([775, 25])
        # if (np.linalg.norm(presspix - buttonpix) < 115):
        #     self.controller.show_frame("wifiScn")
        #================================


class doorcloseScn(tk.Frame):

    def __init__(self, parent, controller):
        # received signal from main code ,
        # send signal as identifyScn to main code
        # rotate ring
        # display image and font text
        # dot ... animation
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")
        # label = tk.Label(self, text="identifyScn", font=controller.title_font)
        # label.pack(side="top", fill="x", pady=10)
        # button = tk.Button(self, text="Go to the start page",
        #                   command=lambda: controller.show_frame("errorScn"))
        # button.pack()

        ########### text and graphic
        self.canvas = tk.Canvas(self, width=800, height=400, bg='black', highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image2 = Image.open(pathtoDir +iconfolder+ '/ic_pod_inactive.png')
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir +iconfolder+ '/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)


        text1 = "Please close the"
        text12 = "door..."
        font1 = ImageFont.truetype(pathtoDir + "/font/Orbitron-Medium.ttf", 40)
        img = Image.new("RGB", (500, 400))
        draw = ImageDraw.Draw(img)
        draw.text((30, 180), text1, font=font1)
        draw.text((30, 230), text12, font=font1)
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(250, 200, image=tkimage4)

        self.image_animated = Image.open(pathtoDir +iconfolder+ '/ic_spinner2.png')
        self.angle = 0

    def updatescreen(self):
        print
        "Displaying DoorcloseScn"
        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)
        self.angle -= 5
        self.angle %= 360

    ########### animation- rotation
    def animation(self):
        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        # canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)
        self.angle -= 5
        self.angle %= 360

        if (framenow == "doorcloseScn"):
            self.after(10, self.animation)


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
        #label = tk.Label(self, text="identifyScn", font=controller.title_font)
        #label.pack(side="top", fill="x", pady=10)
        #button = tk.Button(self, text="Go to the start page",
        #                   command=lambda: controller.show_frame("errorScn"))
        #button.pack()

        ########### text and graphic
        self.canvas = tk.Canvas(self, width=800, height=400, bg='black', highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image2 = Image.open(pathtoDir+iconfolder+'/ic_pod_inactive.png')
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        text1 = "Identifying Swirl"
        text12 = "Pod..."
        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        img = Image.new("RGB", (500, 400))
        draw = ImageDraw.Draw(img)
        draw.text((30, 180), text1, font=font1)
        draw.text((30, 230), text12, font=font1)
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(250, 200, image=tkimage4)

        self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_spinner2.png')
        self.angle = 0
        global menuBRAND,menuFLAVOR,menuTYPE
        menuBRAND = ""
        menuFLAVOR = ""
        menuTYPE = ""
        
    def updatescreen(self):
        print "Displaying identifyScn"
        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)
        self.angle -= 5
        self.angle %= 360
    ########### animation- rotation
    def animation(self):
        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        #canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)
        self.angle -= 5
        self.angle %= 360

        if (framenow == "identifyScn"):
            self.after(10, self.animation)


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

        self.canvas = tk.Canvas(self, width=800, height=400, bg='black', highlightthickness=0)
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

        font1 = ImageFont.truetype(pathtoDir + "/font/Orbitron-Medium.ttf", 40)
        font2 = ImageFont.truetype(pathtoDir + "/font/OpenSans-SemiBold.ttf", 25)
        font3 = ImageFont.truetype(pathtoDir + "/font/OpenSans-SemiBoldItalic.ttf", 16)

        self.img = Image.new("RGB", (500, 400))
        self.draw = ImageDraw.Draw(self.img)

        textline = ["", "", ""]
        font1w, font1h = font1.getsize(text1)
        print
        "TT: ", font1w
        if font1w > 480:
            wordlist = text1.split(" ")
            subtext = ""
            testsubtext = ""
            textlineNo = 0
            for subword in wordlist:
                if testsubtext == "":
                    testsubtext = subword
                else:
                    testsubtext = subtext + " " + subword
                fonts1w, fonts1h = font1.getsize(testsubtext)
                if fonts1w < 480:
                    textline[textlineNo] = testsubtext
                    subtext = testsubtext
                else:
                    textlineNo += 1
                    subtext = subword
                    textline[textlineNo] = subtext
                    if textlineNo >= 3:
                        textlineNo = -1
                        break

            # for i in range(textlineNo+1):
            #     print textline[i]
            #     if text1=="":
            #         text1=textline[i]
            #     else:
            #         text1=text1+"\n"+textline[i]
            # draw.text((30, (180-textlineNo*font1h)), text1, font=font1)
            for i in range(textlineNo + 1):
                print textline[i]
                self.draw.text((30, (180 - (textlineNo - i) * (font1h + 15))), textline[i], font=font1)


        else:
            self.draw.text((30, 180), text1, font=font1)

        self.draw.text((30, 235), text2, font=font2)
        self.draw.text((30, 350), text3, font=font3, fill=(226, 167, 151, 255))

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.img)
        canvas_obj4 = self.canvas.create_image(250, 200, image=tkimage4)


        self.img_a=copy.deepcopy(self.image_animated)
        w,h=self.img_a.size
        self.draw = ImageDraw.Draw(self.img_a)
        self.draw.rectangle([self.cover,0,w,h],fill=(0,0,0,0),outline=(0,0,0,0))
        self.tkimage = tkimage = ImageTk.PhotoImage(self.img_a)
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)
        self.cover +=2
        self.angle -= 5
        self.angle %= 360


        ########### animation- rotation

    def animation(self):
        self.img_a=copy.deepcopy(self.image_animated)
        w,h=self.img_a.size
        self.draw = ImageDraw.Draw(self.img_a)
        self.draw.rectangle([self.cover,0,w,h],fill=(0,0,0,0),outline=(0,0,0,0))
        self.tkimage = tkimage = ImageTk.PhotoImage(self.img_a)
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        self.cover +=2
        self.angle -= 5
        self.angle %= 360
	
        if (framenow == "recognizedScn" and self.cover<=w):
            self.after(10, self.animation)
        else:
            self.cover=0
    def click_release(self, event):
        global screenpress
        screenpress=True
        pairlist = {"TOUCH": "1"}
        UI2MA_pipe_write(pair2str(pairlist))
	
class mainmenuScn(tk.Frame):

    def __init__(self, parent, controller):
        # received signal from main code ,
        # send signal as recognizedScn to main code
        # display name of brand and flavour
        # tick animation
        # display image and font text

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")
        #label = tk.Label(self, text="mainmenuScn", font=controller.title_font)
        #label.pack(side="top", fill="x", pady=10)
        #button = tk.Button(self, text="Go to the start page",
        #                   command=lambda: controller.show_frame("submenuScn"))
        #button.pack()

        ########### text and graphic

        self.canvas = tk.Canvas(self, width=800, height=400, bg='black',highlightthickness=0)

        self.canvas.bind( "<ButtonRelease-1>", self.click_release)

        self.canvas.bind( "<B1-Motion>", self.click_press)

        self.canvas.bind( "<Button-1>", self.click_press)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        text = "Choose Your Swirl "

        font1 = ImageFont.truetype(pathtoDir+"/font/OpenSans-SemiBold.ttf", 25)
        font1w,font1h=font1.getsize(text)
        img = Image.new("RGB", (800, 40))
        draw = ImageDraw.Draw(img)
        draw.text((400-font1w/2, 0), text, font=font1)
        draw.line((30, 20,260, 20),fill=(255,255,255,255), width=1)
        draw.line((540, 20, 770,20), fill=(255,255,255,255), width=1)


        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(400, 45, image=tkimage4)

        self.moving=0
        global mainmenu_foldername
        mainmenu_foldername=glob(pathtoDir+"/menu/*")

        global selectedmainmenu
        self.image_animated=[]
        for img_idx in range(len(mainmenu_foldername)):

            self.image_animated.append(Image.open(mainmenu_foldername[img_idx]+"/MENU.png").resize((230, 230), Image.ANTIALIAS))


         ## will pick by event
        selectedmainmenu=1

        self.pitchsize=(800)/(len(self.image_animated))

        ########### animation- rotation
        self.canvas_obj=range(len(self.image_animated))
        self.tkimage=range(len(self.image_animated))

        self.difspeed=0.7
        self.movingspeed=0.2
        self.presskeylatch=[0]*len(self.image_animated)


    def updatescreen(self):
        print "Displaying mainmenuScn"
        for icno in range(len(self.image_animated)):
            self.tkimage[icno]=ImageTk.PhotoImage(self.image_animated[icno])

        for ic_no in range(len(self.image_animated)):
            dampwave_scale = 900*math.exp(-self.moving+(ic_no*self.difspeed))
            self.canvas_obj[ic_no] = self.canvas.create_image(self.pitchsize*(ic_no+0.5)+dampwave_scale, circleimagecentre[1], image=self.tkimage[ic_no])

    def click_release(self, event):
        global selectedmainmenu,menuTYPE
        presspix=np.array([event.x, event.y])
        for selno in range(len(self.image_animated)):
            buttonpix=np.array([self.pitchsize*(selno+0.5), circleimagecentre[1]])
            if (np.linalg.norm(presspix-buttonpix)<115):

                selectedmainmenu = selno

                submenucp=mainmenu_foldername[selectedmainmenu]
                while True:
                    idxofchar = submenucp.find("/")
                    if idxofchar >= 0:
                        menuTYPE = submenucp[idxofchar+1:]
                        submenucp = submenucp[(idxofchar + 1):]
                    else:
                        break

                #menuTYPE = mainmenu_foldername[selectedmainmenu][5:]
                #self.controller.updatemenu("submenuScn")
                self.controller.show_frame("submenuScn")
                break

                #1280x800
                #1024*600
                #800x480

    def click_press(self, event):
        global selectedmainmenu, menuTYPE
        presspix=np.array([event.x, event.y])
        for selno in range(len(self.image_animated)):
            buttonpix=np.array([self.pitchsize*(selno+0.5), circleimagecentre[1]])
            if (np.linalg.norm(presspix-buttonpix)<115):
                self.presskeylatch[selno]=1

                img_a = self.image_animated[selno].resize((int(200), int(200)), Image.ANTIALIAS)
                self.tkimage[selno]  = ImageTk.PhotoImage(img_a)
                self.canvas.itemconfig(self.canvas_obj[selno], image=self.tkimage[selno])
                #self.canvas_obj[selno] = self.canvas.create_image(self.pitchsize * (selno + 0.5),
                #                                                  circleimagecentre[1], image=self.tkimage[selno])

                selectedmainmenu = selno
               # menuTYPE=mainmenu_foldername[selectedmainmenu][5:]

            elif self.presskeylatch[selno]==1:
                self.tkimage[selno]  = ImageTk.PhotoImage(self.image_animated[selno])
                self.canvas.itemconfig(self.canvas_obj[selno], image=self.tkimage[selno])
                #self.canvas_obj[selno] = self.canvas.create_image(self.pitchsize * (selno + 0.5),
                #                                                  circleimagecentre[1], image=self.tkimage[selno])
                #self.controller.updatemenu("submenuScn")
                #self.controller.show_frame("submenuScn")
                #break




    def animation(self):

        #for icno in range(len(self.image_animated)):
         #   self.tkimage[icno]=ImageTk.PhotoImage(self.image_animated[icno])
        self.moving += self.movingspeed
        for ic_no in range(len(self.image_animated)):
            dampwave_scale = 900*math.exp(-self.moving+(ic_no*self.difspeed))
            dampwave_scale2 = 900 * math.exp(-self.moving+self.movingspeed + (ic_no * self.difspeed))
            ans=dampwave_scale2-dampwave_scale

            self.canvas.move(self.canvas_obj[ic_no], -ans,0)



	
        if (framenow == "mainmenuScn" and dampwave_scale>0.1):
            self.after(10, self.animation)
        else:
            self.moving=0

class submenuScn(tk.Frame):

    def __init__(self, parent, controller):
        # received signal from main code ,
        # send signal as recognizedScn to main code
        # display name of brand and flavour
        # tick animation
        # display image and font text

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")
        #label = tk.Label(self, text="submenuScn", font=controller.title_font)
        #label.pack(side="top", fill="x", pady=10)
        #button = tk.Button(self, text="Go to the start page",
        #                   command=lambda: controller.show_frame("errorScn"))
        #button.pack()

        ########### text and graphic

        self.canvas = tk.Canvas(self, width=800, height=400, bg='black',highlightthickness=0)

        self.canvas.bind( "<ButtonRelease-1>", self.click_release)

        self.canvas.bind( "<B1-Motion>", self.click_press)

        self.canvas.bind( "<Button-1>", self.click_press)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image2 = Image.open(pathtoDir+iconfolder+'/Home_Icon.png').resize((50, 50), Image.ANTIALIAS)
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        canvas_obj2 = self.canvas.create_image(50, 350, image=tkimage2)

        self.moving = 0
        self.difspeed = 0.7
        self.movingspeed = 0.2



    def updatescreen(self):
        print "Displaying submenuScn"
        #text = mainmenu_foldername[selectedmainmenu][5:]
        text = menuTYPE

        font1 = ImageFont.truetype(pathtoDir+"/font/OpenSans-SemiBold.ttf", 25)
        font1w, font1h = font1.getsize(text)
        img = Image.new("RGB", (800, 40))
        draw = ImageDraw.Draw(img)
        draw.text((400 - font1w / 2, 0), text, font=font1)
        draw.line((30, 20, 260, 20), fill=(255, 255, 255, 255), width=1)
        draw.line((540, 20, 770, 20), fill=(255, 255, 255, 255), width=1)

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(400, 45, image=tkimage4)

        self.image_animated = []
        self.submenu_img=submenu_img=glob(mainmenu_foldername[selectedmainmenu]+"/*.png")
        for img_idx in range(len(submenu_img)):
            if submenu_img[img_idx].find("MENU.png")>0:
                del submenu_img[img_idx]
                break

        for img_idx in range(len(submenu_img)):
            self.image_animated.append(Image.open(submenu_img[img_idx]).resize((230, 230), Image.ANTIALIAS))


        self.pitchsize = (800) / len(self.image_animated)

        ########### animation- rotation
        self.canvas_obj = range(len(self.image_animated))
        self.tkimage = range(len(self.image_animated))

        for icno in range(len(self.image_animated)):
            self.tkimage[icno] = ImageTk.PhotoImage(self.image_animated[icno])

        for ic_no in range(len(self.image_animated)):
            dampwave_scale = 900 * math.exp(-self.moving + (ic_no * self.difspeed))
            self.canvas_obj[ic_no] = self.canvas.create_image(self.pitchsize * (ic_no +0.5) + dampwave_scale,
                                                              circleimagecentre[1], image=self.tkimage[ic_no])
        self.presskeylatch = [0] * len(self.image_animated)



    def click_release(self,event):
        global selectedsubmenu,menuBRAND,menuFLAVOR
        presspix = np.array([event.x, event.y])
        for selno in range(len(self.image_animated)):
            buttonpix = np.array([self.pitchsize * (selno + 0.5), circleimagecentre[1]])
            if (np.linalg.norm(presspix - buttonpix) < 115):
                selectedsubmenu = self.submenu_img[selno]

                #self.controller.updatemenu("processScn")
                #self.controller.updatemenu("recognizedScn")

                submenucp = copy.deepcopy(selectedsubmenu)

                while True:
                    idxofchar = submenucp.find("/")
                    if idxofchar >= 0:
                        selectedcatagory = submenucp[:idxofchar]
                        submenucp = submenucp[(idxofchar + 1):]
                    else:
                        break

                idxofbrand = submenucp.find("-")
                if idxofbrand >= 0:
                    menuBRAND = submenucp[:idxofbrand]
                    submenucp = submenucp[(idxofbrand + 1):]
                else:
                    menuBRAND = menuTYPE

                idxofflavour = submenucp.find(".")
                if idxofflavour >= 0:
                    menuFLAVOR = submenucp[:idxofflavour]
                else:
                    menuFLAVOR = "---------------"

                pairlist={"BRAND":menuBRAND, "TYPE":menuTYPE,"FLAVOR":menuFLAVOR,"SOFT":menuSOFT}

                UI2MA_pipe_write(pair2str(pairlist))

                #self.controller.show_frame("recognizedScn")

                break

        homebuttonpix = np.array([50+50/2, 350+50/2])
        if (np.linalg.norm(presspix - homebuttonpix) < 80):
            #self.controller.updatemenu("mainmenuScn")
            print "home button press"
            self.controller.show_frame("mainmenuScn")

    def click_press(self, event):
        global selectedmainmenu
        presspix=np.array([event.x, event.y])
        for selno in range(len(self.image_animated)):
            buttonpix=np.array([self.pitchsize*(selno+0.5), circleimagecentre[1]])
            if (np.linalg.norm(presspix-buttonpix)<115):
                self.presskeylatch[selno]=1

                img_a = self.image_animated[selno].resize((int(200), int(200)), Image.ANTIALIAS)
                self.tkimage[selno]  = ImageTk.PhotoImage(img_a)
                self.canvas.itemconfig(self.canvas_obj[selno], image=self.tkimage[selno])


                #self.canvas_obj[selno] = self.canvas.create_image(self.pitchsize * (selno + 0.5),
                #                                                  circleimagecentre[1], image=self.tkimage[selno])

            elif self.presskeylatch[selno]==1:
                self.tkimage[selno]  = ImageTk.PhotoImage(self.image_animated[selno])
                self.canvas.itemconfig(self.canvas_obj[selno], image=self.tkimage[selno])
                #self.canvas_obj[selno] = self.canvas.create_image(self.pitchsize * (selno + 0.5),
                #                                                  circleimagecentre[1], image=self.tkimage[selno])


    def animation(self):



        self.moving += self.movingspeed
        for ic_no in range(len(self.image_animated)):
            dampwave_scale = 900 * math.exp(-self.moving + (ic_no * self.difspeed))
            dampwave_scale2 = 900 * math.exp(-self.moving + self.movingspeed + (ic_no * self.difspeed))
            ans = dampwave_scale2 - dampwave_scale

            self.canvas.move(self.canvas_obj[ic_no], -ans, 0)

        if (framenow == "submenuScn" and dampwave_scale > 0.1):
            self.after(10, self.animation)
        else:
            self.moving = 0


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

        self.canvas = tk.Canvas(self, width=800, height=400, bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

       # image2 = Image.open('ic_recog.png')

       # self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
       # canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        text1 = "QR Not Recognised"
        text2 = "Please try again. Only insert official\nSwirl Pods or kindly seek assistance\nfrom staff.(Tel: 9798 2556)"

        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        font2 = ImageFont.truetype(pathtoDir+"/font/OpenSans-SemiBold.ttf", 20)

        img = Image.new("RGB", (500, 400))
        draw = ImageDraw.Draw(img)
        draw.text((30, 180), text1, font=font1)
        draw.text((30, 235), text2, font=font2)

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(250, 200, image=tkimage4)

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
        self.scale += 0.05
        self.angle -= 5
        self.angle %= 360
        ########### animation- rotation

    def animation(self):

        dampwave_scale=math.exp(-self.scale)*math.sin(2*math.pi*self.scale)+1 #decay wave
        img_a = self.image_animated.resize((int(self.imga_h*dampwave_scale),int(self.imga_w*dampwave_scale)), Image.ANTIALIAS)
        self.tkimage = tkimage = ImageTk.PhotoImage(img_a)
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        self.scale +=0.05
        self.angle -= 5
        self.angle %= 360
        if (framenow == "errorScn1" and self.scale<2.5):
            self.after(10, self.animation)
        else: self.scale=0.0

class errorScn2(tk.Frame):  ## temperature too high

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")

        ########### text and graphic

        self.canvas = tk.Canvas(self, width=800, height=400, bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)


        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        text1 = "Swirl Pod is Warm!  "
        text2 = "Please change to a colder Swirl Pods \n or kindly seek assistance from stuff."

        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        font2 = ImageFont.truetype(pathtoDir+"/font/OpenSans-SemiBold.ttf", 20)

        img = Image.new("RGB", (500, 400))
        draw = ImageDraw.Draw(img)
        draw.text((30, 180), text1, font=font1)
        draw.text((30, 235), text2, font=font2)

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(250, 200, image=tkimage4)

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
        self.scale += 0.05
        self.angle -= 5
        self.angle %= 360
        ########### animation- rotation

    def animation(self):

        dampwave_scale=math.exp(-self.scale)*math.sin(2*math.pi*self.scale)+1 #decay wave
        img_a = self.image_animated.resize((int(self.imga_h*dampwave_scale),int(self.imga_w*dampwave_scale)), Image.ANTIALIAS)
        self.tkimage = tkimage = ImageTk.PhotoImage(img_a)
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        self.scale +=0.05
        self.angle -= 5
        self.angle %= 360
        if (framenow == "errorScn2" and self.scale<2.5):
            self.after(10, self.animation)
        else: self.scale=0.0


class errorScn3(tk.Frame):  ## no selection and time out

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")

        ########### text and graphic

        self.canvas = tk.Canvas(self, width=800, height=400, bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        text1 = "Time's up!!"
        text2 = "Please try again. Only insert official\nSwirl Pods or kindly seek assistance\nfrom stuff."

        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        font2 = ImageFont.truetype(pathtoDir+"/font/OpenSans-SemiBold.ttf", 20)

        img = Image.new("RGB", (500, 400))
        draw = ImageDraw.Draw(img)
        draw.text((30, 180), text1, font=font1)
        draw.text((30, 235), text2, font=font2)

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(250, 200, image=tkimage4)

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
        self.scale += 0.05
        self.angle -= 5
        self.angle %= 360
        ########### animation- rotation

    def animation(self):

        dampwave_scale=math.exp(-self.scale)*math.sin(2*math.pi*self.scale)+1 #decay wave
        img_a = self.image_animated.resize((int(self.imga_h*dampwave_scale),int(self.imga_w*dampwave_scale)), Image.ANTIALIAS)
        self.tkimage = tkimage = ImageTk.PhotoImage(img_a)
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)
        self.scale +=0.05
        self.angle -= 5
        self.angle %= 360
        if (framenow == "errorScn3" and self.scale<2.5):
            self.after(10, self.animation)
        else: self.scale=0.0

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

        self.canvas = tk.Canvas(self, width=800, height=400, bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)


        image2 = Image.open(pathtoDir+iconfolder+'/ic_tick_inactive.png')
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        self.angle = 0

        self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_spinner2.png')

    def updatescreen(self):
        print "Displaying blendingScn"
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



        text1 = "Please Wait"
        text2 = "Processing ..."
        text3 = menuFLAVOR
        text4 = "Did you know we have a total of 80 flavours?"

        font1 = ImageFont.truetype(pathtoDir + "/font/Orbitron-Medium.ttf", 50)
        font2 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 35)
        font3 = ImageFont.truetype(pathtoDir+"/font/OpenSans-SemiBold.ttf", 25)
        font4 = ImageFont.truetype(pathtoDir+"/font/OpenSans-SemiBoldItalic.ttf", 20)


        self.img = Image.new("RGB", (500, 400))
        self.draw = ImageDraw.Draw(self.img)


        textline=["","",""]
        font1w, font1h = font3.getsize(text3)
        print "TT: ",font1w
        if font1w >500:
            wordlist=text1.split(" ")
            subtext=""
            textlineNo=0
            for subword in wordlist:
                if subtext=="":
                    subtext=subword
                else:
                    subtext=subtext+" "+subword
                fonts1w, fonts1h = font3.getsize(subtext)
                if fonts1w<500:
                    textline[textlineNo]=subtext
                else:
                    textlineNo+=1
                    subtext=subword
                    if textlineNo>=3:
                        textlineNo=-1
                        break
            text1=""
            # for i in range(textlineNo+1):
            #     print textline[i]
            #     if text1=="":
            #         text1=textline[i]
            #     else:
            #         text1=text1+"\n"+textline[i]
            # draw.text((30, (180-textlineNo*font1h)), text1, font=font1)
            for i in range(textlineNo + 1):
                print textline[i]
                self.draw.text((30, (275 + (textlineNo) * (font1h+5))),  textline[i], font=font3)#25

        else:
            self.draw.text((30, 275), text3, font=font3) #h25

        self.draw.text((30, 170), text1, font=font1)  # h50
        #draw.text((30, 180), text1, font=font1)


        self.draw.text((30, 230), text2, font=font2) #h35
        self.draw.text((30, 350), text4, font=font4, fill=(226, 167, 151, 255))#20

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.img)
        canvas_obj4 = self.canvas.create_image(250, 200, image=tkimage4)


        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)

        self.angle -= 5
        self.angle %= 360
        ########### animation- rotation

    def animation(self):
        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)

        self.angle -= 5
        self.angle %= 360
        if (framenow == "blendingScn"):
            self.after(10, self.animation)


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

        self.canvas = tk.Canvas(self, width=800, height=400, bg='black',highlightthickness=0)
        self.canvas.bind("<ButtonRelease-1>", self.click_release)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image2 = Image.open(pathtoDir+iconfolder+'/ic_cone.png')
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        self.canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        # image3 = Image.open(pathtoDir+'/blackring.png')
        # self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        # canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)
        #
        # text1 = "Ready "
        # text2 = "1. Pull to remove dispense cap. \n2. Position cup/cone below dispensing tip. \n3. Tap icon on the right to start dispense."


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
        self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_spin_complete.png')
        video_name = pathtoDir+animationfolder+"/Ready02022020.mp4"  # This is your video file path
        self.imagelist = imageio.get_reader(video_name)


        self.animationArrayImg=[]
        for idx in range(len(self.imagelist)):
            self.animationArrayImg.append(Image.fromarray(self.imagelist.get_data(idx)))


        del video_name



    def updatescreen(self):
        print
        "Displaying ReadyScn"


        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        self.canvas_obj4 = self.canvas.create_image(250, 200, image=tkimage4)

        # self.imgcover = Image.new("RGB", (300, 300))
        # self.tkimageCover = tkimageCover = ImageTk.PhotoImage(self.imgcover)

        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)
        self.angle -= 5
        self.angle %= 360
        self.fadeflag=False
        self.cover+=1
        self.frame+=1
        self.frame %= len(self.imagelist)

        # w,h= self.image_animated.size
        # imga=Image.new("RGBA", (w+6,h+6))
        # draw = ImageDraw.Draw(imga)
        # draw.rectangle([0,0,w+6,h+6], fill=(0,0,0,self.cover), outline=(0,0,0,0))
        # self.tkimage_a = tkimage_a = ImageTk.PhotoImage(imga)
        # self.canvas_obj_a = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1],image= tkimage_a)
        ########### animation- rotation
        self.timing=int(time.time()*2)
        self.coverflag=False

    def animation(self):

        #video display---------------


        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        self.frame+=1
        self.frame %= len(self.imagelist)
        self.canvas.itemconfig(self.canvas_obj4, image=tkimage4)
        #----------------------------


        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        # if self.timing != int(time.time()*2):
        #     self.timing=int(time.time()*2)
        #     self.coverflag ^= True
        # if self.coverflag:
        #
        #     self.canvas.itemconfig(self.canvas_obj, image=self.tkimage)
        # else:
        #
        #     self.canvas.itemconfig(self.canvas_obj, image=self.tkimageCover)

        self.canvas.itemconfig(self.canvas_obj, image=self.tkimage)

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
        self.frame+=1
        self.frame %= len(self.imagelist)
        self.angle -= 5
        self.angle %= 360
        if (framenow == "readyScn"):
            self.after(10, self.animation)


    def click_release(self, event):
        global screenpress
        screenpress=True
        pairlist = {"TOUCH": "1"}

        UI2MA_pipe_write(pair2str(pairlist))

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
        self.canvas = tk.Canvas(self, width=800, height=400, bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        image2 = Image.open(pathtoDir+iconfolder+'/ic_cone_swirl_inactive.png')
        self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)

        image3 = Image.open(pathtoDir+iconfolder+'/blackring.png')
        self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        text1 = "Dispensing..."

        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        img = Image.new("RGB", (500, 400))
        draw = ImageDraw.Draw(img)
        draw.text((30, 180), text1, font=font1)

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(250, 200, image=tkimage4)

        self.angle = 0
        self.cover=0
        self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_spinner2.png')
        self.image_animated2 = Image.open(pathtoDir+iconfolder+'/ic_cone_swirl.png')

    def updatescreen(self):
        print "Displaying dispensingScn"
        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage)

        self.img_a = copy.deepcopy(self.image_animated2)
        w, h = self.img_a.size
        self.draw = ImageDraw.Draw(self.img_a)
        self.draw.rectangle([0, 0, w, 53 - self.cover], fill=(0, 0, 0, 0), outline=(0, 0, 0, 0))
        self.tkimage_a = tkimage_a = ImageTk.PhotoImage(self.img_a)
        self.canvas_obj_a = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage_a)

        self.cover += 0.1
        self.angle -= 5
        self.angle %= 360

        ########### animation- rotation

    def animation(self):
        self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)

        self.img_a=copy.deepcopy(self.image_animated2)
        w,h=self.img_a.size
        self.draw = ImageDraw.Draw(self.img_a)
        self.draw.rectangle([0,0,w,53-self.cover],fill=(0,0,0,0),outline=(0,0,0,0))
        self.tkimage_a = tkimage_a = ImageTk.PhotoImage(self.img_a)
        self.canvas.itemconfig(self.canvas_obj_a, image=tkimage_a)

        self.cover += 0.1
        self.angle -= 5
        self.angle %= 360
        if (framenow == "dispensingScn"):
            self.after(10, self.animation)
        else:
            self.cover=0


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
        self.canvas = tk.Canvas(self, width=800, height=400, bg='black',highlightthickness=0)
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
        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Bold.ttf", 40)
        font2 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 22)
        font3 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Bold.ttf", 20)
        img = Image.new("RGB", (800, 400))
        draw = ImageDraw.Draw(img)
        f1w, f1h=font1.getsize(text1)
        f2w, f2h = font2.getsize(text2)
        f3w, f3h = font3.getsize(text3)
        f4w, f4h = font3.getsize(text4)
        draw.text((400-f1w/2, 100), text1, font=font1)
        draw.text((400-f2w/2, 180), text2, font=font2)
        draw.text((10, 380), text3, font=font3)
        draw.text((800-10-f4w, 380), text4, font=font3)

        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(400, 150, image=tkimage4)

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

                UI2MA_pipe_write(pair2str(pairlist))
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
                #self.canvas_obj[selno] = self.canvas.create_image(self.pitchsize * (selno + 0.5),
                #                                                  circleimagecentre[1], image=self.tkimage[selno])
                #self.controller.updatemenu("submenuScn")
                #self.controller.show_frame("submenuScn")
                #break


class thankyouScn(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="black")



        ########### text and graphic
        self.canvas = tk.Canvas(self, width=800, height=400, bg='black',highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)



        text1 = "Thanks for your feedback!"

        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Bold.ttf", 40)

        img = Image.new("RGB", (800, 400))
        draw = ImageDraw.Draw(img)
        f1w, f1h=font1.getsize(text1)

        draw.text((400-f1w/2, 200), text1, font=font1)


        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(400, 150, image=tkimage4)



    def updatescreen(self):
        print "Displaying Thankpage"

        ########### animation- rotation

    def animation(self):

        if (framenow == "thankyouScn" ):
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
        self.canvas = tk.Canvas(self, width=800, height=400, bg='black',highlightthickness=0)
        self.canvas.bind("<ButtonRelease-1>", self.click_release)
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # image2 = Image.open(pathtoDir+'/ic_pod.png')
        # self.tkimage2 = tkimage2 = ImageTk.PhotoImage(image2)
        # canvas_obj2 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage2)
        #
        # image3 = Image.open(pathtoDir+'/blackring.png')
        # self.tkimage3 = tkimage3 = ImageTk.PhotoImage(image3)
        # canvas_obj3 = self.canvas.create_image(circleimagecentre[0], circleimagecentre[1], image=tkimage3)

        text1 = "Please Remove"
        text12= "Empty Pod..."

        font1 = ImageFont.truetype(pathtoDir+"/font/Orbitron-Medium.ttf", 40)
        img = Image.new("RGB", (500, 400))
        draw = ImageDraw.Draw(img)
        draw.text((30, 180), text1, font=font1)
        draw.text((30, 230), text12, font=font1)
        self.tkimage4 = tkimage4 = ImageTk.PhotoImage(img)
        canvas_obj4 = self.canvas.create_image(250, 200, image=tkimage4)

        self.angle = 0
        self.image_animated = Image.open(pathtoDir+iconfolder+'/ic_spin_complete.png')
        video_name = pathtoDir+animationfolder+"/Remove2.mp4"  # This is your video file path
        self.imagelist = imageio.get_reader(video_name)
        frameicon = Image.open(pathtoDir + animationfolder + "/frame4.png").convert('L')

        self.animationArrayImg=[]
        for idx in range(len(self.imagelist)):
            image_frame = Image.fromarray(self.imagelist.get_data(idx))
            w, h = image_frame.size
            framecolor = Image.new("RGB", (w, h))
            image_frame = Image.composite(image_frame, framecolor, frameicon)
            self.animationArrayImg.append(image_frame)
        del image_frame
        del framecolor
        del w,h
        del frameicon
        del video_name

        ########### animation- rotation
    def updatescreen(self):
        print "Displaying removeScn"

        # video display --------
        self.frame=0


        self.tkimage = tkimage = ImageTk.PhotoImage(self.animationArrayImg[self.frame])

        #--------------------------

        #self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas_obj = self.canvas.create_image(circleimagecentre[0]-40, circleimagecentre[1], image=tkimage)

        self.angle -= 5
        self.angle %= 360
    
    ########### animation- rotation

    def animation(self):

        #video display---------------

        self.tkimage = tkimage = ImageTk.PhotoImage(self.animationArrayImg[self.frame])
        self.frame+=1
        self.frame %= len(self.imagelist)
        #----------------------------

        #self.tkimage = tkimage = ImageTk.PhotoImage(self.image_animated.rotate(self.angle))
        self.canvas.itemconfig(self.canvas_obj, image=tkimage)


        self.angle -= 5
        self.angle %= 360
        if (framenow == "removeScn"):
            self.after(40, self.animation)

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
            global screenpress, menuBRAND, menuFLAVOR, menuTYPE,MA2UI_FIFOOpenRead
            screenselect=""
            
            msgFromMA = MA2UI_FIFOOpenRead.read()

            if len(msgFromMA) != 0:
                print "MA2UI msg:",msgFromMA
                pairlist_MA=str2pair(msgFromMA)

                if "BRAND" in pairlist_MA:
                    menuBRAND=pairlist_MA["BRAND"]

                if "TYPE" in pairlist_MA:
                    menuTYPE=pairlist_MA["TYPE"]

                if "FLAVOR" in pairlist_MA:
                    menuFLAVOR=pairlist_MA["FLAVOR"]

                if "SCN" in pairlist_MA:
                    screenselect=pairlist_MA["SCN"]

                    if (screenselect in listofscreen) and framenow != screenselect:
                        print "select", screenselect
                        self.controller.show_frame(screenselect)
                    pairlist = {"SCN": framenow}
                    UI2MA_pipe_write(pair2str(pairlist))
            self.after(1, self.looping)        
        if TEST_UI:
            self.count+=1
            self.count=self.count%len(listofscreen)
            self.controller.show_frame(listofscreen[self.count])
            self.after(5000, self.looping)  

            #rootframe.show_frame("identifyScn")
        #    conn.send([42, None, 'hello'])
        #    conn.close()

            # try:
            #     screenselect=screenselectqu.get(block=False)
            # except Empty:
            #     screenselect="xx"










if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()

