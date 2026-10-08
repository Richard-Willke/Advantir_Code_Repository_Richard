
import requests
from datetime import datetime
import csv
import errno
import os
import time
from requests.exceptions import Timeout, ConnectionError
#from machine_profile import machine_profile
import configparser

config = configparser.ConfigParser()
config.read('/home/pi/swirlgo_machine.conf')
machine_profile_id=config["machine-config"]["MID"]


upload_csv2server=True
write2csv=True
uploadingtimer=600 # in second

def pipe_write(filename_FIFO,data):
    OpenWrite = os.open(filename_FIFO, os.O_WRONLY)
    os.write(OpenWrite, data)
    os.close(OpenWrite)


def stringtime():
    now = datetime.now()
    timestamp = now.strftime('%m/%d %H:%M:%S.%f')[:-5]
    return timestamp



def pipe_receiver_connect(pipename):
    try:
        os.mkfifo(pipename)
    except OSError as oe:
        if oe.errno != errno.EEXIST:
            raise
    pipeprocess= open(pipename, 'r', buffering=1)
    pipeprocess.read()
    return pipeprocess

def write_to_csv(filename, data2d):
    try:
        f=open(filename,'w')
        writer = csv.writer(f)  
        for line in data2d:
            writer.writerow(line)
        f.close()
        return True
    except:
        return False

def append_to_csv(filename, data2d):
    try:
        try:
            filesize=os.stat(filename).st_size
            print "file size", filesize,"byte"
            if filesize>5000000: #5GB max
            
                with open(filename, "r") as f:
                    lines = f.readlines()
                with open(filename, "w") as f:
                    for line in lines[len(data2d):]:
                        f.write(line)
        except:
            pass
        f=open(filename,'a')
        writer = csv.writer(f)  
        for line in data2d:
            writer.writerow(line)
        f.close()
        return True
    except:
        return False

def upload2server(url, csvfile):
    webpagereturn=""
    for i in range(3):
        files = {'file': open(csvfile, 'rb')}
        try:
            r = requests.post(url, files = files, timeout=180.0)
            webpagereturn=r.text
            print webpagereturn
        except Timeout:
            print "[Error] request post Timeout"
        except ConnectionError:
            print "[Error] request post Connection Error"
        except :
            print "[Error] request post other Error"
        if webpagereturn.find("import complete")>-1:
            print "[Message] successful upload csv to server"
            return True
        else:
            print "[Error] Fail to upload csv to server"
    return False
    
def convertText22Darraytext(sub2uploader_text):
    sublines=[]
    if len(sub2uploader_text) >1:
        arrayline= sub2uploader_text.split("\n")
        for line in arrayline:
            if len(line)>1:
                #print line.split("\a")
                sublines.append(line.split("\a")) 
    return sublines
    
def convertText2arrayint_io(sub2uploader_text):
    sublines=[]
    if len(sub2uploader_text) >1:
        arrayline= sub2uploader_text.split("\n")
        for line in arrayline:
            if len(line)>1:
                #print line.split("\a")
                linearray=line.split("\a")
                stringbit=linearray[1].replace('[','').replace(']','')
                arraybit=[int(x) for x in stringbit.split()]
                del linearray[1]
                linearray.extend(arraybit)
                
                sublines.append(linearray) 
    return sublines

print "[Message] conencting sub Pipe"
subMA2uploader_FIFO = 'pipe_subMA2uploader'
subMA2uploader_FIFOOpenRead=pipe_receiver_connect(subMA2uploader_FIFO)
print "[Message] sub MA Pipe is CONNECTED"

subUI2uploader_FIFO = 'pipe_subUI2uploader'
subUI2uploader_FIFOOpenRead=pipe_receiver_connect(subUI2uploader_FIFO)
print "[Message] sub UI Pipe is CONNECTED"

subQR2uploader_FIFO = 'pipe_subQR2uploader'
subQR2uploader_FIFOOpenRead=pipe_receiver_connect(subQR2uploader_FIFO)
print "[Message] sub QR Pipe is CONNECTED"

ioMonitor2uploader_FIFO = 'pipe_ioMonitor2uploader'
ioMonitor2uploader_FIFOOpenRead=pipe_receiver_connect(ioMonitor2uploader_FIFO)
print "[Message] IO monitor Pipe is CONNECTED"

previous_upload_successful=False
previous_upload_IO_successful=False

uploadedtime=time.time()
uploadedtime2=time.time()
successwrite2IOcsv = False
successwrite2csv = False

while True:
        time.sleep(2)
        '''
        print "intputcheck", intputcheck
        if intputcheck==1:
            previous_upload_successful=True
        else:
            previous_upload_successful=False
        '''            
            
        subMA2uploader_text=subMA2uploader_FIFOOpenRead.read()
        subUI2uploader_text=subUI2uploader_FIFOOpenRead.read()    
        subQR2uploader_text=subQR2uploader_FIFOOpenRead.read()
        ioMonitor2uploader_text = ioMonitor2uploader_FIFOOpenRead.read()

        lineMA=convertText22Darraytext(subMA2uploader_text)
        lineUI=convertText22Darraytext(subUI2uploader_text)
        lineQR=convertText22Darraytext(subQR2uploader_text)
        lineIO=convertText2arrayint_io(ioMonitor2uploader_text)
        

        rows=max([len(lineMA),len(lineUI),len(lineQR)])
        

        if  len(lineIO)>0:
            if write2csv:
                successwrite2IOcsv = False
                for i in range(3):

                    if previous_upload_IO_successful:
                        print "[Message] overwrite IO csv"
                        successwrite2IOcsv = write_to_csv('IOstatus_uploader.csv', lineIO)

                    else:
                        print "[Message] append IO csv"
                        successwrite2IOcsv = append_to_csv('IOstatus_uploader.csv', lineIO)
                    if successwrite2IOcsv:
                        break
                    else:
                        print "[Error] Fail to write to IO csv"

        if  upload_csv2server and successwrite2IOcsv and (time.time()-uploadedtime)>uploadingtimer: #upload every 10min
            previous_upload_IO_successful = upload2server(
                'http://swirlgoadvantir.com/upload_iostatus_csv_id.php?id='+machine_profile_id,
                'IOstatus_uploader.csv')
            if previous_upload_IO_successful:
                write_to_csv('IOstatus_uploader.csv', [])  # delete the tmp file if upload success
                uploadedtime=time.time()
                successwrite2IOcsv=False
        else: 
            previous_upload_IO_successful=False


        if rows>0:
            cols=2*3
            
            bufsheet=[["" for i in range(cols)] for j in range(rows)]  #create empty matrix rows x cols
            i
            print "[Message] size of bufsheet:",len(bufsheet), len(bufsheet[0]), len(lineMA), len(lineUI)         
            
            for i in range(len(lineUI)):
                bufsheet[i][0]=lineUI[i][0]
                bufsheet[i][1]=lineUI[i][1]
                
            for i in range(len(lineQR)):
                bufsheet[i][2]=lineQR[i][0]
                bufsheet[i][3]=lineQR[i][1]
                
            for i in range(len(lineMA)):
                bufsheet[i][4]=lineMA[i][0]
                bufsheet[i][5]=lineMA[i][1]
            successwrite2csv = False
            if write2csv:
                for i in range(3):

                    if previous_upload_successful:
                        print "[Message] overwrite status csv"
                        successwrite2csv=write_to_csv('status_uploader.csv',bufsheet )

                        
                    else:
                        print "[Message] append status csv"
                        
                        successwrite2csv=append_to_csv('status_uploader.csv',bufsheet )
                    if successwrite2csv:
                        break
                    else:
                        print "[Error] Fail to write status to csv"
                    
        if upload_csv2server and successwrite2csv and  (time.time()-uploadedtime2)>uploadingtimer:
            previous_upload_successful=upload2server(
                'http://swirlgoadvantir.com/upload_status_csv_id_v2.php?id='+machine_profile_id,
                'status_uploader.csv') 
            if previous_upload_successful:
                write_to_csv('status_uploader.csv',[] ) # delete the tmp file if upload success
                uploadedtime2=time.time()
                successwrite2csv=False
        else : 
            previous_upload_successful=False
            
'''                  
        subQR2uploader_text=subQR2uploader_FIFOOpenRead.read()
        
        if len(subQR2uploader_text) >1:
            arrayline= subQR2uploader_text.split("\n")
            for line in arrayline:
                if len(line)>1:
                    print line.split("\a")
                    
                    
                  
        ioMonitor2uploader_text=ioMonitor2uploader_FIFOOpenRead.read()
        
        if len(ioMonitor2uploader_text) >1:
            arrayline= ioMonitor2uploader_text.split("\n")
            for line in arrayline:
                if len(line)>1:
                    print line.split("\a")
   
'''
'''
            f=open('subMA2uploader.csv','w')
            writer = csv.writer(f)  
            writer.writerow(lines)
                        f.close()
'''
        #run_command("python -u helo.py")

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
