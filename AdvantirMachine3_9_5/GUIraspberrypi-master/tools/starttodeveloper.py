import os
import time
# import subprocess as sp
filedirectory='/home/pi/.config/lxsession/LXDE-pi/autostart'
# filedirectory="/home/pi/fastvideo.py"

new_lines_to_overwrite=[]
def editautostart_to_developermode(filedirectory):
    f=open(filedirectory, "r")
    fz= f.readlines()

    for line in fz:

        if line.find("#@lxpanel")>=0:
            line=line.replace("#", "")

        if line.find("#@pcmanfm") >= 0:
            line = line.replace("#", "")

        if line.find("#@xscreensaver")>=0:
            line=line.replace("#", "")


        # if line.find("sudo") >= 0:
        #     if line.find("#sudo") >= 0:
        #         pass
        #
        #     else:
        #         line="#"+line
       # for new machine
        if line.find("@lxterminal") >= 0:
            if line.find("#@lxterminal") >= 0:
                pass
            else:
                line="#"+line


        new_lines_to_overwrite.append(line)
    f.close()

    f = open(filedirectory, "w+")
    for ln in new_lines_to_overwrite:
        f.write(ln)
    f.close()

    return new_lines_to_overwrite


list=editautostart_to_developermode(filedirectory)
os.system("sudo python ~/GUIraspberrypi/tools/resizescreen_smaller.py")
time.sleep(1)