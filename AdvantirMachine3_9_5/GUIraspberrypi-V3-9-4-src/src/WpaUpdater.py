import subprocess as sp

kbbuttons = [
	'~', '`', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=',
	'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '\\', '7', '8', '9', 'BACK',
	'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', '[', ']', '4', '5', '6', 'SHIFT',
	'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '?', '/', '1', '2', '3', 'SPACE',
]
kbbuttonsS = [
	'~', '`', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '+',
	'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '\\', '7', '8', '9', 'BACK',
	'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', '[', ']', '4', '5', '6', 'SHIFT',
	'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '?', '/', '1', '2', '3', 'SPACE',
]


def wificonnected():
	p2 = sp.Popen(['iwgetid'], stdout=sp.PIPE)
	tmpresult = str(p2.communicate()[0].decode("utf-8"))
	resultlines = tmpresult.splitlines()
	try:
		ssidconnect=resultlines[0].split('"')[1]
	except:
		ssidconnect=""
	if len(ssidconnect)>0:
		return True
	else:
		return False

def wifiscanlist():
	p2 = sp.Popen(['iwlist', 'wlan0', 'scan'], stdout=sp.PIPE)
	p3 = sp.Popen(['grep', 'ESSID'], stdin=p2.stdout, stdout=sp.PIPE)
	tmpresult = str(p3.communicate()[0].decode("utf-8"))
	resultlines = tmpresult.splitlines()
	scanwifilist = [None] * len(resultlines)
	for no, eachline in enumerate(resultlines):
		scanwifilist[no] = eachline.split('"')[1]
		print(scanwifilist[no])
	p2.kill()
	return scanwifilist

# convert save txt to save dict
def convertWpaFile2Dict(filedirectory):
	f=open(filedirectory, "r")
	f1= f.readlines()
	idxstop=0
	listSaveWifi={}
	inbracket=False
	stopidxbool=False
	for idx, line in enumerate(f1):
		if not stopidxbool:
			idxstop=idx
		if not inbracket and line.find("network")>=0:
			inbracket=True
			stopidxbool=True

		if inbracket and line.find("ssid")>=0:
			idx1=line.find("\"")+1
			idx2=line.find("\"",idx1)
			ssid=line[idx1:idx2]

		if inbracket and line.find("psk") >= 0:
			idx1=line.find("\"")+1
			idx2=line.find("\"",idx1)
			psk=line[idx1:idx2]

		if inbracket and line.find("}")>=0:
			inbracket=False
			listSaveWifi.update({ssid:psk})

	f.close()

	return f1[:(idxstop-1)], listSaveWifi

# scan wifi compare with save list
def compareScanAndSaveWifi(listSaveWifi,listScanWifi):
	dictWifiScan={}
	for scanwifiname in listScanWifi:
		dictWifiScan.update({scanwifiname:(scanwifiname in listSaveWifi)})
	return dictWifiScan

# update list wifi scan
# newssid="neswefeed"
# newpsk="pskww2"
#
# listSaveWifi.update({newssid:newpsk})

# update whole txt
def saveWifiFile(filedirectory, firsttext,listSaveWifi ):
	f= open(filedirectory,"w+")
	for ln in firsttext:
		f.write(ln)
	for ssidw, pskw in listSaveWifi.items():
		ln = "\nnetwork={"+ \
			 "\n	ssid=\"" + ssidw + "\""+\
			 "\n	psk=\"" + pskw + "\""+\
			 "\n}"
		f.write(ln)
	f.close()

def updateWpaFile(filedirectory, firsttext,ssidw,pskw ):
	f= open(filedirectory,"w+")
	for ln in firsttext:
		f.write(ln)

	ln = "\nnetwork={"+ \
		 "\n	ssid=\"" + ssidw + "\""+\
		 "\n	psk=\"" + pskw + "\""+\
		 "\n}"
	f.write(ln)
	f.close()


