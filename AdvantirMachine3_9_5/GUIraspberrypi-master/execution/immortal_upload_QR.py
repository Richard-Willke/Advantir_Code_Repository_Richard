
import subprocess
import shlex

from datetime import datetime
import time
import errno
import os




def pipe_write(filename_FIFO,input):
    OpenWrite = os.open(filename_FIFO, os.O_WRONLY)
    if input!="": 
        os.write(OpenWrite, input)
    os.close(OpenWrite)


def stringtime():
    now = datetime.now()
    timestamp = now.strftime('%m/%d %H:%M:%S.%f')[:-5]
    return timestamp

def run_command(command):
    process = subprocess.Popen(shlex.split(command), bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
    while True:
        output = process.stdout.readline()
 
        if output == '' and process.poll() is not None:
            break
        if output:
            print (stringtime()+ " "+ output)
            pipe_write(sub2uploader_FIFO,stringtime()+ "\a"+ output.strip()+"\n")



    rc = process.poll()
    return rc



sub2uploader_FIFO = 'pipe_subQR2uploader'
try:
    os.mkfifo(sub2uploader_FIFO)
except OSError as oe:
    if oe.errno != errno.EEXIST:
        raise
pipe_write(sub2uploader_FIFO,"")
print( "subQR2uploader_pipeopened_write")

time_array=[]
while True:
#    try:
        print("start restart")
        #run_command("python -u heloQR.py")
        run_command(" python -u /home/pi/GUIraspberrypi/src/QRscannercode.py")
        time_array.append(time.time())
        if len(time_array)>7: 
            if (time_array[-7]-time_array[-1])<120:
                break
 