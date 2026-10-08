import configparser
import os



def get_git_headercode():
    try :
        config = configparser.ConfigParser()
        config.read('/home/pi/swirlgo_machine.conf')
        firmware_version_branch=config["machine-config"]["firmware_version"]
        last_line=""
        with open('/home/pi/GUIraspberrypi/.git/logs/refs/heads/'+firmware_version_branch) as f:
            for line in f:
                pass
            last_line = line
        s=last_line.split()
        return s[1]
    except:
        return ""


def get_git_headercode_param():
    try:
        config = configparser.ConfigParser()
        config.read('/home/pi/swirlgo_machine.conf')
        firmware_version_branch=config["machine-config"]["customer_brand"]
        last_line=""
        with open('/home/pi/GUIraspberrypi/swirlgo_param/.git/logs/refs/heads/'+firmware_version_branch) as f:
            for line in f:
                pass
            last_line = line
        s=last_line.split()
        return s[1]
    except:
        return ""