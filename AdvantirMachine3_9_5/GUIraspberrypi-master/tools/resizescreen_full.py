
# import subprocess as sp
touchfile='/etc/X11/xorg.conf.d/40-libinput.conf'
displayfile='/boot/config.txt'
# filedirectory="/home/pi/fastvideo.py"


def edittouchscreen(filedirectory):
    f=open(filedirectory, "r")
    fz= f.readlines()
    new_lines_to_overwrite=[]

    for line in fz:

        if line.find("Option \"CalibrationMatrix\"")>=0:
            print "found:",line
            line="        Option \"CalibrationMatrix\" \"1 0 0 0 1 0 0 0 1\"\n"


        new_lines_to_overwrite.append(line)
    f.close()

    f = open(filedirectory, "w+")
    for ln in new_lines_to_overwrite:
        f.write(ln)
    f.close()

    return new_lines_to_overwrite


def editdisplayscreen(filedirectory):
    f=open(filedirectory, "r")
    fz= f.readlines()
    new_lines_to_overwrite=[]

    for line in fz:

        if line.find("overscan_left")>=0 or line.find("overscan_right")>=0 or line.find("overscan_top")>=0 or line.find("overscan_bottom")>=0:
            pass
        else:
            new_lines_to_overwrite.append(line)
    f.close()

    f = open(filedirectory, "w+")
    for ln in new_lines_to_overwrite:
        f.write(ln)
    f.close()

    return new_lines_to_overwrite

lists=edittouchscreen(touchfile)
listr=editdisplayscreen(displayfile)
