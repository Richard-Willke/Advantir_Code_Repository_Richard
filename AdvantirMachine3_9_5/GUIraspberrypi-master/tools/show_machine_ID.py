import ConfigParser

machine_config = ConfigParser.ConfigParser()
machine_config.read("/home/pi/tools/swirlgo_machine.conf")
allinfo=dict(machine_config.items('machine-config'))
print  type(machine_config.get('machine-config','MID'))
print allinfo
# bsbb=82
# intee=0
# while True:

#     print ("Hello UI",intee);
#     time.sleep(0.3)
#     intee+=1

#     assert intee<10
