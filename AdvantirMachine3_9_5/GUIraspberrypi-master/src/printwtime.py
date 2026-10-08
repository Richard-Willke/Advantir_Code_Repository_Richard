from datetime import datetime

def printtime(data):
    now = datetime.now()
    timestamp = now.strftime('%m/%d %H:%M:%S.%f')[:-5]
    print "["+timestamp+"] ",data

