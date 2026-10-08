import os
import time
filedirectory='/home/pi/.config/lxsession/LXDE-pi/autostart'
new_lines_to_overwrite=[]
def editautostart_to_clientmode(filedirectory):
    f=open(filedirectory, "r")
    fz= f.readlines()

    for line in fz:
        if line.find("@lxpanel") >= 0:
            if line.find("#@lxpanel")>=0:
                pass
            else:
                line = "#" + line

        if line.find("@pcmanfm") >= 0:
            if line.find("#@pcmanfm")>=0:
                pass
            else:
                line = "#" + line

        if line.find("@xscreensaver") >= 0:
            if line.find("#@xscreensaver")>=0:
                pass
            else:
                line = "#" + line



        # if line.find("sudo") >= 0:
        #     if line.find("#sudo") >= 0:
        #         line=line.replace("#", "")
        #
        #     else:
        #         pass
        #for new machine
        if line.find("@lxterminal") >= 0:
            if line.find("#@lxterminal") >= 0:
                line=line.replace("#", "")
            else:
                pass


        new_lines_to_overwrite.append(line)
    f.close()

    f = open(filedirectory, "w+")
    for ln in new_lines_to_overwrite:
        f.write(ln)
    f.close()

    return new_lines_to_overwrite


list=editautostart_to_clientmode(filedirectory)
os.system("sudo python ~/GUIraspberrypi/tools/resizescreen_full.py")
time.sleep(1)