import subprocess
import shlex

from datetime import datetime
import time
import errno
import os
import sys
sys.path.insert(1, "GUIraspberrypi/src")
import io_param as io
import RPi.GPIO as GPIO
import signal



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
    # poll_obj = select.poll()
    # poll_obj.register(process.stdout, select.POLLIN)

    while True:
        # poll_result = poll_obj.poll(0)
	    # if poll_result:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print (stringtime()+ " "+ output)
            pipe_write(sub2uploader_FIFO,stringtime()+ "\a"+ output.strip()+"\n")
            if output.find("[PauseMA]")!=-1:
                print "pause MA"
                os.kill(process.pid, signal.SIGSTOP)
                while True:
                    if not GPIO.input(io.IRcapdetectPin): #if press
                        k=k+1
                    else : 
                        k=0
                    if k>5:
                        break
                print "resume MA"
                os.kill(process.pid, signal.SIGCONT)

    rc = process.poll()
    return rc




sub2uploader_FIFO = 'pipe_subMA2uploader'
try:
    os.mkfifo(sub2uploader_FIFO)
except OSError as oe:
    if oe.errno != errno.EEXIST:
        raise
pipe_write(sub2uploader_FIFO,"")
print( "subMA2uploader_pipeopened_write")


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(io.IRcapdetectPin, GPIO.IN)

time_array=[]
coversafetyenabled=False


while True:
#    try:
        print("start restart")
        # /run_command("python -u heloMA.py")
        run_command(" python -u /home/pi/GUIraspberrypi/src/machinepipe.py")
        time_array.append(time.time())
        if len(time_array)>7 and False:
            
            if (time_array[-7]-time_array[-1])<120:
                break
                print "restart to developer mode due to multiple time failure"
                os.system("python ~/GUIraspberrypi/toola/starttodeveloper.py")
                os.system("sudo reboot")
        
        
        #run_command("ls")
#    except:
#        pass
    #run_command("sudo python machinepipe.py")

# from subprocess import Popen, PIPE
#
# def run(command):
#     process = Popen(command, stdout=PIPE, shell=True)
#     while True:
#         line = process.stdout.readline().rstrip()
#         if not line:
#             break
#         yield line
#
#
# if __name__ == "__main__":
#     for path in run("python helo.py"):
#         print path

# import subprocess
#
# def myrun(cmd):
#     """from http://blog.kagesenshi.org/2008/02/teeing-python-subprocesspopen-output.html
#     """
#     p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#     stdout = []
#     while True:
#         line = p.stdout.readline()
#         stdout.append(line)
#         print line,
#         if line == '' and p.poll() != None:
#             break
#     return ''.join(stdout)
#
# if __name__ == "__main__":
#    myrun("python -u helo.py")
#         # print path