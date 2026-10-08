import configparser
import os



def get_git_headercode():
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
