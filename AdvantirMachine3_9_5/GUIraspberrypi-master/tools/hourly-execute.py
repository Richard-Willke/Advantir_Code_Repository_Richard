import configparser
import os
config = configparser.ConfigParser()
#config.read('/home/pi/swirlgo_machine.conf')
config.read('/home/pi/swirlgo_machine.conf')
#update git flavour param
brand_param_branch=config["machine-config"]["customer_brand"]
#cmd1="cd /home/pi/GUIraspberrypi/swirlgo_param &&"+ 
cmd1=("cd /home/pi/GUIraspberrypi/swirlgo_param &&"+ 
     "git reset --hard origin/" +brand_param_branch+" &&"+
     "git pull origin "+brand_param_branch)

os.system(cmd1)

#update git firmware
firmware_version_branch=config["machine-config"]["firmware_version"]
#cmd1="cd /home/pi/GUIraspberrypi/swirlgo_param &&"+ 
cmd2=("cd /home/pi/GUIraspberrypi/ &&"+ 
     "git reset --hard origin/" +firmware_version_branch+" &&"+
     "git pull origin "+firmware_version_branch)

os.system(cmd2) 