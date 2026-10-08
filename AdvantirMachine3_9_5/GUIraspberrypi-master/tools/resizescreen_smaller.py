
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
            line="        Option \"CalibrationMatrix\" \"1.1875 0 -0.09375 0 1.1875 -0.09375 0 0 1\"\n"


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

        if line.find("# goes off screen, and negative if there")>=0:
            new_lines_to_overwrite.append(line)
            new_lines_to_overwrite.append("overscan_left=60\n")
            new_lines_to_overwrite.append("overscan_right=60\n")
            new_lines_to_overwrite.append("overscan_top=34\n")
            new_lines_to_overwrite.append("overscan_bottom=34\n")
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
